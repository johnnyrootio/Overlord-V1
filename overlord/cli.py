"""Overlord CLI — entry point and commands (docs/OVERLORD-CLI-SPEC.md)."""
import json
import os
import queue
import subprocess
import sys
import threading
import time
import warnings
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

# Suppress urllib3/OpenSSL version warning (common on macOS with system Python)
warnings.filterwarnings("ignore", module="urllib3")

# Ensure readline is loaded when available (Unix) for proper line editing (arrow keys, backspace, delete)
try:
    import readline  # noqa: F401
except ImportError:
    pass

import click

from overlord.claude_api import (
    create_phase_client_sync,
    create_phase4_client_sync,
    disconnect_phase4_client,
    is_api_configured,
)
from overlord.graph import invoke_pipeline
from overlord.prompts import get_monitor_prompt
from overlord.interactive_phase import PHASE_DONE, run_phase_interactive
from overlord.monitor import StatusSnapshot, format_snapshot_tables, gather_status
from overlord.phase_log import ensure_phase_log_paths
from overlord.multiclaude_recovery import (
    ReconcileResult,
    get_multiclaude_repo_name,
    is_repo_inited,
    multiclaude_daemon_restart,
    multiclaude_daemon_start,
    multiclaude_daemon_status,
    multiclaude_daemon_stop,
    get_multiclaude_repo_clone_path,
    multiclaude_remove_repo_clone,
    multiclaude_repo_init,
    multiclaude_repo_key,
    multiclaude_repo_rm,
    reconcile_issues,
)
from overlord.scenario import load_scenario
from overlord.repo_utils import repo_url_to_owner_repo
from overlord.gh_utils import get_gh_default_owner, gh_repo_exists, gh_repo_create
from overlord.agents.phase2 import _extract_workgraph_yaml
from overlord.state import SessionState
from overlord.storage import StateManager
from overlord.ui import step_name
from overlord.slash_commands import (
    SLASH_HELP,
    handle_slash_command,
    parse_slash_command,
    parse_slash_command_with_arg,
)


def _echo_monitor_tables(snapshot: StatusSnapshot, repo_name: Optional[str] = None) -> None:
    """Echo monitor snapshot in multiclaude-style tables."""
    click.echo(format_snapshot_tables(snapshot, repo_name=repo_name))


def _state_dir(state_dir: Optional[str]) -> str:
    return state_dir if state_dir is not None else os.path.expanduser("~/.overlord")


def _overlord_scripts_dir() -> str:
    """Overlord repo scripts/ (create-worker-with-auto-accept, etc.). Override with OVERLORD_SCRIPTS_DIR."""
    env = os.environ.get("OVERLORD_SCRIPTS_DIR")
    if env and os.path.isdir(env):
        return env
    root = Path(__file__).resolve().parent.parent
    return str(root / "scripts")


def _multiclaude_init_error_hint(err: str) -> Optional[str]:
    """If multiclaude init failed due to tmux/session, return a hint to append. Otherwise None."""
    if not err:
        return None
    lower = err.lower()
    if "tmux" in lower or "create session" in lower or "session failed" in lower:
        return (
            "\nHint: multiclaude uses tmux. Try: (1) ensure tmux is installed (e.g. brew install tmux); "
            "(2) run 'tmux kill-server' if a previous session is stuck; then run overlord again."
        )
    return None


def _format_repo_init_success(project_id: str, repo_url: str) -> str:
    """Overlord-contextualized message after multiclaude repo init succeeds. No raw multiclaude dump."""
    repo_name = get_multiclaude_repo_name(repo_url)
    session = f"mc-{repo_name}" if repo_name else "mc-<repo>"
    return (
        f"Repo initialized. Use 'overlord status {project_id}' for workers and health, "
        f"or attach to the session: tmux attach -t {session}"
    )


def _echo_project_context(state: SessionState) -> None:
    """Always show project identity so the user never has to remind the system."""
    click.echo(f"Project: {state.project_id}")
    if state.repo_url:
        click.echo(f"Repo: {state.repo_url}")


def _looks_like_github_url(s: str) -> bool:
    s = (s or "").strip()
    if s.startswith("https://github.com/") or s.startswith("http://github.com/") or (
        "github.com" in s and "/" in s
    ):
        return True
    # owner/repo (one slash, no space) → treat as GitHub repo identifier
    if "/" in s and " " not in s and not s.startswith("http") and len(s.split("/")) == 2:
        return True
    return False


def _normalize_github_url(s: str) -> str:
    s = (s or "").strip()
    if not s:
        return s
    if not s.startswith("http"):
        # owner/repo → https://github.com/owner/repo
        if "/" in s and " " not in s and len(s.split("/")) == 2:
            s = "https://github.com/" + s
        else:
            s = "https://" + s
    if s.endswith(".git"):
        s = s[:-4]
    return s


REPO_QUESTION = (
    "Repo will be created or used as <your-gh-user>/<project-id>. "
    "Press Enter to use that, or type owner/repo or a full GitHub URL."
)
VISIBILITY_QUESTION = "Create repo as public or private? (public/private)"


def _is_repo_name_or_url_prompt(prompt: str) -> bool:
    p = (prompt or "").lower()
    return "name of this repo" in p or "github url" in p or "repo will be" in p


def _is_visibility_prompt(prompt: str) -> bool:
    p = (prompt or "").strip()
    return p == VISIBILITY_QUESTION or "public or private" in p.lower()


def _is_gate_prompt(prompt: str) -> bool:
    """True if prompt is one of the old Gate 1–5 questions (no longer used for new projects)."""
    p = (prompt or "").strip()
    return any(p.startswith(f"Gate {n}:") for n in range(1, 6))


def _migrate_old_gates(state: SessionState) -> None:
    """One-time: remove old Gate 1–5 from pending_questions so existing projects get the new flow."""
    state.pending_questions = [q for q in state.pending_questions if not _is_gate_prompt(q)]


def _resolve_repo_from_answer(answer: str, project_id: str) -> Tuple[Optional[str], str, Optional[Tuple[str, str]]]:
    """
    Resolve repo URL from first-question answer. We check if repo exists; if we would create, we ask public/private first.
    Returns (repo_url or None, message to echo, pending_create=(owner, repo) when user must answer visibility next).
    """
    raw = (answer or "").strip()
    # Full GitHub URL: use as-is
    if _looks_like_github_url(raw):
        url = _normalize_github_url(raw)
        return url, f"Using existing repo: {url}", None
    # Default: use gh user + project_id; check or ask visibility then create
    if not raw or raw.lower() in ("y", "yes"):
        owner = get_gh_default_owner()
        if not owner:
            return None, "Run `gh auth login` so Overlord can create or use the repo.", None
        repo = project_id
        if gh_repo_exists(owner, repo):
            url = f"https://github.com/{owner}/{repo}"
            return url, f"Using existing repo: {url}", None
        return None, "Next: " + VISIBILITY_QUESTION, (owner, repo)
    # owner/repo
    if "/" in raw and " " not in raw:
        parts = raw.split("/", 1)
        if len(parts) == 2:
            owner, repo = parts[0].strip(), parts[1].strip()
            if owner and repo:
                if gh_repo_exists(owner, repo):
                    url = f"https://github.com/{owner}/{repo}"
                    return url, f"Using existing repo: {url}", None
                return None, "Next: " + VISIBILITY_QUESTION, (owner, repo)
    # Just repo name: use gh user + that name
    owner = get_gh_default_owner()
    if not owner:
        return None, "Run `gh auth login` so Overlord can create or use the repo.", None
    repo = raw or project_id
    if gh_repo_exists(owner, repo):
        url = f"https://github.com/{owner}/{repo}"
        return url, f"Using existing repo: {url}", None
    return None, "Next: " + VISIBILITY_QUESTION, (owner, repo)


def _cleanup_project_workers(state: SessionState) -> None:
    """Remove all multiclaude workers (Claude Code sessions) for the current project's repo. No-op if no repo_url."""
    if not state.repo_url:
        return
    repo = repo_url_to_owner_repo(state.repo_url)
    if not repo:
        return
    removed, err = multiclaude_workers_remove_all(repo, accept_prompts=True)
    if err:
        click.echo(f"Cleanup: {err}", err=True)
        return
    if removed:
        click.echo(f"Stopped {removed} worker(s) for {repo}.", err=True)


def _project_id_from_spec(spec_path: str) -> str:
    base = os.path.basename(spec_path)
    name, _ = os.path.splitext(base)
    return name.replace(" ", "-") if name else "project"


def _invoke_graph(
    project_id: str,
    state_root: str,
    state: SessionState,
    start_phase: int,
    max_phase: Optional[int] = None,
    scripts_dir: Optional[str] = None,
    message_source: Optional[str] = None,
    injected_message: Optional[str] = None,
    phase_4_client: Optional[Any] = None,
) -> Dict[str, Any]:
    """Run the pipeline from start_phase (graph owns all phase logic). Returns result dict. When message_source and injected_message are set (e.g. from monitor or user), Phase 4 uses them. When phase_4_client is set, Phase 4 reuses that long-lived client."""
    return invoke_pipeline(
        project_id=project_id,
        state_root=state_root,
        genesis_spec_path=state.genesis_spec_path or "",
        repo_url=state.repo_url,
        artifact_paths=state.artifact_paths,
        scripts_dir=scripts_dir,
        start_phase=start_phase,
        max_phase=max_phase,
        message_source=message_source,
        injected_message=injected_message,
        phase_4_client=phase_4_client,
    )


def _sync_state_from_result(state: SessionState, result: Dict[str, Any]) -> None:
    """Merge graph result back into SessionState."""
    state.phase = result.get("phase", state.phase)
    state.artifact_paths = result.get("artifact_paths") or state.artifact_paths
    if result.get("repo_url"):
        state.repo_url = result["repo_url"]


def _safe_input() -> str:
    """Read a line from stdin. On EOF or Ctrl+C, re-prompt; never exit. Only returns when a line is read."""
    while True:
        try:
            return input().strip()
        except EOFError:
            click.echo("(EOF received. Only /exit ends the session. Type /exit to quit.)", err=True)
        except KeyboardInterrupt:
            click.echo("(Interrupted. Type /exit to quit.)", err=True)


def _session_idle_until_exit(project_id: str) -> None:
    """
    Golden rule: only /exit (or /quit) ends the session. Loop until user types /exit or /quit.
    Use after phases complete or when Phase 0 fails so we never exit prematurely.
    CLI must never exit on EOF, Ctrl+C, or error—only on explicit /exit.
    """
    click.echo("Staying in session. Type /exit to quit.", err=True)
    while True:
        line = _safe_input()
        cmd, _ = parse_slash_command_with_arg(line)
        if cmd in ("exit", "quit"):
            click.echo("Exiting. State is saved.")
            return
        if line and line.strip():
            click.echo("Staying in session. Type /exit to quit.", err=True)


def _interactive_get_user_input(
    project_id: str,
    state_root: str,
    state: SessionState,
    scripts_dir: str,
    phase: int,
    verbose_ref: Optional[Dict[str, Any]] = None,
):
    """Return a get_user_input(assistant_text) callable for run_phase_interactive. Handles /done, /exit, /help, /status, /phase, /query, /verbose, /terse."""
    repo_name = repo_url_to_owner_repo(state.repo_url) if state.repo_url else None
    first_turn = [True]

    def get_user_input(assistant_text: str):
        if (assistant_text or "").strip():
            click.echo(assistant_text)
        else:
            click.echo("(Phase agent returned no response. Check Claude Code CLI and API key. Type /exit to quit or type a message to continue.)", err=True)
        if first_turn[0]:
            click.echo("(Type /help for commands, /done when this phase is complete, /exit to quit)", err=True)
            first_turn[0] = False
        while True:
            line = _safe_input()
            cmd, arg = parse_slash_command_with_arg(line)
            if cmd in ("exit", "quit"):
                click.echo("Exiting. State is saved.")
                return None
            if cmd == "done":
                return PHASE_DONE
            if cmd == "help":
                click.echo(SLASH_HELP)
                continue
            if cmd == "status":
                snapshot = gather_status(
                    project_id, state_root,
                    repo_name=repo_name,
                    scripts_dir=scripts_dir,
                )
                workers = ", ".join(snapshot.workers) if snapshot.workers else "(none)"
                click.echo(f"workers: {workers}  health={snapshot.health}  liveness={snapshot.liveness[:80]}...")
                continue
            if cmd == "phase":
                click.echo(f"step={step_name(state.phase)}  pending={len(state.pending_questions)}")
                continue
            if cmd == "query":
                return arg or "(no question)"
            if cmd == "verbose":
                if verbose_ref is not None:
                    verbose_ref["verbose"] = True
                click.echo("(verbose on)", err=True)
                continue
            if cmd == "terse":
                if verbose_ref is not None:
                    verbose_ref["verbose"] = False
                click.echo("(terse)", err=True)
                continue
            if cmd:
                click.echo(f"(unknown command: /{cmd})", err=True)
                continue
            # Unstructured feedback: pass to agent (prompts govern agent; CLI only flows I/O)
            return line

    return get_user_input


def _run_interactive_phases(
    pid: str,
    root: str,
    state: SessionState,
    manager: StateManager,
    scripts_dir: str,
) -> bool:
    """
    Run human-in-the-loop phases 0, 1, 2 (interactive) then graph phases 3, 4.
    Returns True if completed, False if user exited early.
    Phase logs (conversation + execution_log) are written from the first interaction.
    """
    project_dir = Path(root) / "projects" / pid
    artifacts_dir = project_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    for phase in (0, 1, 2):
        conv_path, log_path = ensure_phase_log_paths(artifacts_dir, phase)
        state.artifact_paths[f"phase_{phase}_conversation"] = conv_path
        state.artifact_paths[f"phase_{phase}_execution_log"] = log_path
    manager.save(pid, state)

    verbose_ref: Dict[str, Any] = {"verbose": False}
    # Pre-connect Phase 0 when not TTY (async path) so first response is faster
    phase0_client = None
    if not sys.stdin.isatty() and is_api_configured():
        phase0_client = create_phase_client_sync(0, pid, root, state.repo_url)
    get_user_input = _interactive_get_user_input(pid, root, state, scripts_dir, 0, verbose_ref=verbose_ref)
    final0 = run_phase_interactive(
        0, pid, root, state.genesis_spec_path, state.artifact_paths,
        get_user_input=get_user_input,
        repo_url=state.repo_url,
        artifacts_dir=str(artifacts_dir),
        verbose_ref=verbose_ref,
        prewarmed_client=phase0_client,
    )
    disconnect_phase4_client(phase0_client)
    if final0 is None:
        return False
    # Overlap: start Phase 1 client connect in background while we do graph + bootstrap write
    phase1_client_ref: Dict[str, Any] = {"client": None}

    def _warm_phase1() -> None:
        if is_api_configured():
            phase1_client_ref["client"] = create_phase_client_sync(1, pid, root, None)

    warm1_thread = threading.Thread(target=_warm_phase1, daemon=True)
    warm1_thread.start()
    result = _invoke_graph(pid, root, state, start_phase=0, max_phase=0, scripts_dir=scripts_dir)
    _sync_state_from_result(state, result)
    manager.save(pid, state)

    # Phase 0 → Phase 1 wiring: persist bootstrap deliverable so Phase 1 receives it
    bootstrap_file = artifacts_dir / "bootstrap_plan.md"
    bootstrap_file.write_text(final0, encoding="utf-8")
    state.artifact_paths["bootstrap_plan"] = str(bootstrap_file)
    manager.save(pid, state)

    warm1_thread.join(timeout=60)  # allow up to 60s for Phase 1 client to connect
    get_user_input = _interactive_get_user_input(pid, root, state, scripts_dir, 1, verbose_ref=verbose_ref)
    final1 = run_phase_interactive(
        1, pid, root, state.genesis_spec_path, state.artifact_paths,
        get_user_input=get_user_input,
        artifacts_dir=str(artifacts_dir),
        verbose_ref=verbose_ref,
        prewarmed_client=phase1_client_ref.get("client"),
    )
    disconnect_phase4_client(phase1_client_ref.get("client"))
    if final1 is None:
        return False
    plan_file = artifacts_dir / "plan.md"
    tasks_file = artifacts_dir / "tasks.md"
    operational_spec_file = artifacts_dir / "operational_specification.md"
    testing_strategy_file = artifacts_dir / "testing_strategy.md"
    plan_file.write_text(final1, encoding="utf-8")
    tasks_file.write_text(final1, encoding="utf-8")
    operational_spec_file.write_text(final1, encoding="utf-8")
    testing_strategy_file.write_text(final1, encoding="utf-8")
    state.artifact_paths["plan"] = str(plan_file)
    state.artifact_paths["tasks"] = str(tasks_file)
    state.artifact_paths["operational_specification"] = str(operational_spec_file)
    state.artifact_paths["testing_strategy"] = str(testing_strategy_file)
    # Write same two docs into multiclaude clone docs/ (hyphenated names) so workers can read them
    if state.repo_url:
        clone_path = get_multiclaude_repo_clone_path(state.repo_url)
        if clone_path and os.path.isdir(clone_path):
            docs_dir = Path(clone_path) / "docs"
            docs_dir.mkdir(parents=True, exist_ok=True)
            (docs_dir / "operational-specification.md").write_text(final1, encoding="utf-8")
            (docs_dir / "testing-strategy.md").write_text(final1, encoding="utf-8")
    state.phase = 1
    manager.save(pid, state)

    # Overlap: start Phase 2 client connect in background while we prepare for Phase 2
    phase2_client_ref: Dict[str, Any] = {"client": None}

    def _warm_phase2() -> None:
        if is_api_configured():
            phase2_client_ref["client"] = create_phase_client_sync(2, pid, root, None)

    warm2_thread = threading.Thread(target=_warm_phase2, daemon=True)
    warm2_thread.start()
    warm2_thread.join(timeout=60)
    get_user_input = _interactive_get_user_input(pid, root, state, scripts_dir, 2, verbose_ref=verbose_ref)
    final2 = run_phase_interactive(
        2, pid, root, state.genesis_spec_path, state.artifact_paths,
        get_user_input=get_user_input,
        artifacts_dir=str(artifacts_dir),
        verbose_ref=verbose_ref,
        prewarmed_client=phase2_client_ref.get("client"),
    )
    disconnect_phase4_client(phase2_client_ref.get("client"))
    if final2 is None:
        return False
    workgraph_file = artifacts_dir / "workgraph.yml"
    extracted = _extract_workgraph_yaml(final2)
    if extracted:
        workgraph_file.write_text(extracted, encoding="utf-8")
    else:
        workgraph_file.write_text(
            "waves:\n  - id: wave-1\n    tasks:\n      - id: task-1\n        title: Stub\n        depends_on: []\n",
            encoding="utf-8",
        )
    state.artifact_paths["workgraph"] = str(workgraph_file)
    state.phase = 2
    manager.save(pid, state)

    # Phase 3 only: emit issues; then Phase 4 runs in execution loop until workgraph complete or /exit
    result = _invoke_graph(pid, root, state, start_phase=3, max_phase=3, scripts_dir=scripts_dir)
    _sync_state_from_result(state, result)
    manager.save(pid, state)
    _run_phase4_execution_loop(pid, root, state, manager, scripts_dir)
    return True


def _run_monitor_daemon(
    pid: str,
    root: str,
    repo_name: Optional[str],
    scripts_dir: str,
    stop_event: threading.Event,
    request_queue: "queue.Queue[Tuple[str, str]]",
    status_display_queue: "queue.Queue[str]",
    status_request_queue: "queue.Queue[Any]",
    status_response_queue: "queue.Queue[str]",
    interval_sec: int,
    quiet_ref: Dict[str, Any],
) -> None:
    """
    Monitor daemon thread: every interval_sec gather multiclaude status, push one line to
    status_display_queue, and enqueue a (monitor, status_ping) request for the graph runner.
    When status_request_queue receives a request (e.g. from /status), do full status and put
    result on status_response_queue. Plain old software (no agent); outputs flow to CLI as status.
    """
    last_tick = 0.0
    while not stop_event.is_set():
        # Check for /status request (short timeout so we wake often)
        try:
            status_request_queue.get(timeout=1)
            snapshot = gather_status(pid, root, repo_name=repo_name, scripts_dir=scripts_dir)
            formatted = format_snapshot_tables(snapshot, repo_name=repo_name)
            status_response_queue.put(formatted)
        except queue.Empty:
            pass
        now = time.time()
        if now - last_tick >= interval_sec:
            last_tick = now
            if not quiet_ref.get("quiet"):
                try:
                    snapshot = gather_status(pid, root, repo_name=repo_name, scripts_dir=scripts_dir)
                    line = (
                        f"[status] health={snapshot.health} daemon={snapshot.daemon_status} "
                        f"repo_inited={snapshot.repo_inited} workers={len(snapshot.workers)}"
                    )
                    status_display_queue.put(line)
                except Exception:
                    pass
            ping_prompt = get_monitor_prompt("status_ping")
            if ping_prompt:
                try:
                    request_queue.put(("monitor", ping_prompt))
                except Exception:
                    pass


def _run_graph_runner(
    pid: str,
    root: str,
    state: "SessionState",
    manager: StateManager,
    scripts_dir: str,
    request_queue: "queue.Queue[Tuple[Optional[str], Optional[str]]]",
    user_reply_queue: "queue.Queue[str]",
    status_display_queue: "queue.Queue[str]",
    state_lock: threading.Lock,
    stop_event: threading.Event,
    phase_4_client_ref: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Graph runner thread: drain request_queue; for each (source, message) invoke Phase 4 with
    message_source and injected_message when set; sync state and save; if source is user,
    put agent reply on user_reply_queue; if source is monitor, optionally put summary on status_display_queue.
    (None, None) means one default round (no injected message). When phase_4_client_ref is set,
    creates and reuses a long-lived Phase 4 client for the session.
    """
    while not stop_event.is_set():
        try:
            item = request_queue.get(timeout=1)
        except queue.Empty:
            continue
        source, message = item
        msg_src: Optional[str] = source if source else None
        msg_body: Optional[str] = message if message is not None else None
        if source is not None and message is not None and (message or source == "monitor"):
            msg_body = (message or "").strip() or msg_body
        phase_4_client = None
        if phase_4_client_ref is not None and is_api_configured():
            if phase_4_client_ref.get("client") is None:
                with state_lock:
                    ap = dict(state.artifact_paths)
                client = create_phase4_client_sync(pid, root, ap)
                if client is not None:
                    phase_4_client_ref["client"] = client
            phase_4_client = phase_4_client_ref.get("client")
        result = _invoke_graph(
            pid,
            root,
            state,
            start_phase=4,
            max_phase=4,
            scripts_dir=scripts_dir,
            message_source=msg_src,
            injected_message=msg_body,
            phase_4_client=phase_4_client,
        )
        with state_lock:
            _sync_state_from_result(state, result)
            manager.save(pid, state)
        if source == "user":
            response_path = state.artifact_paths.get("phase_4_claude_response")
            reply_text = ""
            if response_path and Path(response_path).is_file():
                try:
                    reply_text = Path(response_path).read_text(encoding="utf-8", errors="replace").strip()
                except Exception:
                    pass
            try:
                user_reply_queue.put(reply_text or "(No response captured.)")
            except Exception:
                pass
        elif source == "monitor":
            try:
                response_path = state.artifact_paths.get("phase_4_claude_response")
                if response_path and Path(response_path).is_file():
                    summary = Path(response_path).read_text(encoding="utf-8", errors="replace").strip()
                    if len(summary) > 200:
                        summary = summary[:200] + "..."
                    status_display_queue.put(f"[monitor] Execution Manager: {summary}")
            except Exception:
                pass


def _run_phase4_execution_loop(
    pid: str,
    root: str,
    state: "SessionState",
    manager: StateManager,
    scripts_dir: str,
) -> None:
    """
    Phase 4 execution loop with monitor daemon and graph runner. Monitor is a separate thread
    that watches multiclaude and injects status pings into the Execution Manager via the graph.
    User and monitor messages are serialized through request_queue; /status invokes the monitor
    for full status; outputs from monitor flow to CLI as status messages.
    Loop runs until workgraph complete or user types /exit.
    """
    repo = repo_url_to_owner_repo(state.repo_url) if state.repo_url else None
    if not repo:
        click.echo("No repo_url; cannot run Phase 4 loop. Set repo and run again.", err=True)
        return

    interval_sec = max(1, int(os.environ.get("OVERLORD_STATUS_INTERVAL_SEC", "60")))
    stop_event = threading.Event()
    state_lock = threading.Lock()
    request_queue: "queue.Queue[Tuple[Optional[str], Optional[str]]]" = queue.Queue()
    user_reply_queue: "queue.Queue[str]" = queue.Queue()
    status_display_queue: "queue.Queue[str]" = queue.Queue()
    status_request_queue: "queue.Queue[Any]" = queue.Queue()
    status_response_queue: "queue.Queue[str]" = queue.Queue()
    quiet_ref: Dict[str, Any] = {"quiet": False}
    verbose_ref: Dict[str, Any] = {"verbose": False}
    phase_4_client_ref: Dict[str, Any] = {"client": None}

    monitor_thread = threading.Thread(
        target=_run_monitor_daemon,
        kwargs={
            "pid": pid,
            "root": root,
            "repo_name": repo,
            "scripts_dir": scripts_dir,
            "stop_event": stop_event,
            "request_queue": request_queue,
            "status_display_queue": status_display_queue,
            "status_request_queue": status_request_queue,
            "status_response_queue": status_response_queue,
            "interval_sec": interval_sec,
            "quiet_ref": quiet_ref,
        },
        daemon=True,
    )
    runner_thread = threading.Thread(
        target=_run_graph_runner,
        kwargs={
            "pid": pid,
            "root": root,
            "state": state,
            "manager": manager,
            "scripts_dir": scripts_dir,
            "request_queue": request_queue,
            "user_reply_queue": user_reply_queue,
            "status_display_queue": status_display_queue,
            "state_lock": state_lock,
            "stop_event": stop_event,
            "phase_4_client_ref": phase_4_client_ref,
        },
        daemon=True,
    )
    monitor_thread.start()
    runner_thread.start()

    try:
        while True:
            try:
                with state_lock:
                    issues_path = state.artifact_paths.get("issues")
                    issues_list: list = []
                    if issues_path and Path(issues_path).is_file():
                        try:
                            with open(issues_path, encoding="utf-8") as f:
                                issues_list = json.load(f)
                        except Exception:
                            pass
                    if issues_list:
                        r = reconcile_issues(repo, issues_list)
                        if not r.open_issues:
                            click.echo("Workgraph complete. All issues closed.")
                            break

                while True:
                    try:
                        line = status_display_queue.get_nowait()
                        click.echo(line, err=True)
                    except queue.Empty:
                        break

                click.echo("Type /exit to quit, /status for full status, or a message for the Execution Manager.", err=True)
                line = _safe_input()
                cmd, arg = parse_slash_command_with_arg(line)
                if cmd in ("exit", "quit"):
                    click.echo("Exiting Phase 4. State saved.")
                    break
                if cmd == "status":
                    status_request_queue.put(None)
                    try:
                        formatted = status_response_queue.get(timeout=30)
                        click.echo(formatted)
                    except queue.Empty:
                        click.echo("(Status request timed out.)", err=True)
                    continue
                if cmd == "quiet":
                    quiet_ref["quiet"] = not quiet_ref["quiet"]
                    click.echo("Proactive status " + ("off" if quiet_ref["quiet"] else "on"), err=True)
                    continue
                if cmd == "verbose":
                    verbose_ref["verbose"] = True
                    click.echo("(verbose on)", err=True)
                    continue
                if cmd == "terse":
                    verbose_ref["verbose"] = False
                    click.echo("(terse)", err=True)
                    continue
                if line == "":
                    request_queue.put((None, None))
                    continue
                request_queue.put(("user", line))
                if verbose_ref.get("verbose"):
                    click.echo("[Phase 4] Working on your request…", err=True)
                try:
                    reply = user_reply_queue.get(timeout=120)
                    click.echo(reply)
                except queue.Empty:
                    click.echo("(Reply timed out.)", err=True)
    except Exception as e:  # never exit on error—stay in session
        click.echo(f"Error: {e}", err=True)
        click.echo("Staying in session. Type /exit to quit.", err=True)
    finally:
        stop_event.set()
        disconnect_phase4_client(phase_4_client_ref.get("client"))


@click.group()
def cli() -> None:
    """Overlord Agent V1 — stateful multi-agent CLI for greenfield development."""
    pass


@cli.command("start")
@click.argument("spec_path", type=click.Path(exists=True, path_type=str))
@click.option("--project-id", type=str, help="Project identifier.")
@click.option("--state-dir", type=click.Path(path_type=str), help="Override state root.")
def start(spec_path: str, project_id: Optional[str], state_dir: Optional[str]) -> None:
    """Start a new greenfield project from a genesis spec, or continue an existing one."""
    root = _state_dir(state_dir)
    pid = project_id if project_id else _project_id_from_spec(spec_path)
    manager = StateManager(root)
    if pid in manager.list_projects():
        # Continue existing project: load state and run interactive flow (don't exit)
        state = manager.load(pid)
        # One-time migration: strip old Gate 1–5 so existing projects get repo-only then Phase 0+1
        _migrate_old_gates(state)
        if not state.pending_questions and not state.repo_url:
            state.add_pending_question(REPO_QUESTION)
        manager.save(pid, state)
        _echo_project_context(state)
        scripts_dir = _overlord_scripts_dir()
        # If migration left no pending and we're still at phase 0 with repo, run phases 0–4 (interactive if API set)
        if not state.pending_questions and state.phase == 0 and state.repo_url and sys.stdin.isatty():
            if is_api_configured():
                if not _run_interactive_phases(pid, root, state, manager, scripts_dir):
                    # User typed /exit during a phase: state already saved in phase; ensure persisted then exit
                    manager.save(pid, state)
                    return
            else:
                result = _invoke_graph(pid, root, state, start_phase=0, max_phase=1, scripts_dir=scripts_dir)
                _sync_state_from_result(state, result)
                manager.save(pid, state)
            click.echo("Planning and execution ready.")
            click.echo(f"Project: {pid}  step={step_name(state.phase)}" + (f"  Repo: {state.repo_url}" if state.repo_url else ""))
            _session_idle_until_exit(pid)
            return
        if sys.stdin.isatty():
            while state.pending_questions:
                prompt = state.pending_questions[0]
                click.echo("---")
                click.echo(prompt)
                click.echo(f"{step_name(state.phase).capitalize()} – type your answer and press Enter.  (/help for commands, /exit to quit)", err=True)
                answer = _read_answer(
                    None, state,
                    project_id=pid, state_root=root, repo_url=state.repo_url, scripts_dir=scripts_dir,
                    phase=state.phase,
                )
                state.pending_questions.pop(0)
                if _is_visibility_prompt(prompt) or state.repo_pending_create:
                    # Answer: public or private for repo we're creating
                    owner_repo = state.repo_pending_create or ""
                    if "/" in owner_repo:
                        owner, repo = owner_repo.split("/", 1)
                        public = (answer or "").strip().lower() != "private"
                        created = gh_repo_create(owner, repo, public=public)
                        if created:
                            state.repo_url = created
                            click.echo(f"Created repo: {created}")
                        else:
                            click.echo("Could not create repo (check `gh auth status`).", err=True)
                        state.repo_pending_create = None
                elif _is_repo_name_or_url_prompt(prompt):
                    url, msg, pending_create = _resolve_repo_from_answer(answer, pid)
                    if pending_create:
                        state.repo_pending_create = f"{pending_create[0]}/{pending_create[1]}"
                        state.pending_questions.insert(0, VISIBILITY_QUESTION)
                        click.echo(msg)
                    elif url:
                        state.repo_url = url
                        click.echo(msg)
                    else:
                        click.echo(msg)
                manager.save(pid, state)
                if state.pending_questions:
                    click.echo("")
            _advance_phase_if_ready(pid, state, manager, root)
            if state.phase >= 4:
                repo = repo_url_to_owner_repo(state.repo_url) if state.repo_url else None
                snapshot = gather_status(pid, root, repo_name=repo, scripts_dir=scripts_dir)
                workers_running = ", ".join(snapshot.workers) if snapshot.workers else "(none)"
                click.echo(f"[status] workers: {workers_running}  health={snapshot.health}", err=True)
            click.echo(f"Project: {pid}  step={step_name(state.phase)}" + (f"  Repo: {state.repo_url}" if state.repo_url else ""))
            _session_idle_until_exit(pid)
            return
        click.echo("---")
        click.echo(state.pending_questions[0] if state.pending_questions else "(no pending)")
        click.echo(f"Run `overlord run {pid}` to answer.", err=True)
        return
    state = SessionState(project_id=pid)
    state.genesis_spec_path = os.path.abspath(spec_path)
    # Phase 0 procedural: only one question (repo); no Gate 1–5
    state.add_pending_question(REPO_QUESTION)
    manager.save(pid, state)
    _echo_project_context(state)
    scripts_dir = _overlord_scripts_dir()
    # Interactive: ask repo, resolve, multiclaude init, Phase 0 graph, then Phase 1.
    # Retry loop so we never exit on error—only /exit can end the session.
    if sys.stdin.isatty():
        while True:
            if not state.pending_questions:
                state.add_pending_question(REPO_QUESTION)
            prompt = state.pending_questions[0]
            click.echo("---")
            click.echo(prompt)
            click.echo(f"{step_name(state.phase).capitalize()} – type your answer and press Enter.  (/help for commands, /exit to quit)", err=True)
            answer = _read_answer(
                None, state,
                project_id=pid, state_root=root, repo_url=state.repo_url, scripts_dir=scripts_dir,
                phase=state.phase,
            )
            state.pending_questions.pop(0)
            if _is_visibility_prompt(prompt) or state.repo_pending_create:
                owner_repo = state.repo_pending_create or ""
                if "/" in owner_repo:
                    owner, repo = owner_repo.split("/", 1)
                    public = (answer or "").strip().lower() != "private"
                    created = gh_repo_create(owner, repo, public=public)
                    if created:
                        state.repo_url = created
                        click.echo(f"Created repo: {created}")
                    else:
                        click.echo("Could not create repo (check `gh auth status`).", err=True)
                    state.repo_pending_create = None
            elif _is_repo_name_or_url_prompt(prompt):
                url, msg, pending_create = _resolve_repo_from_answer(answer, pid)
                if pending_create:
                    state.repo_pending_create = f"{pending_create[0]}/{pending_create[1]}"
                    state.pending_questions.insert(0, VISIBILITY_QUESTION)
                    # Ask visibility in the same run so we don't exit
                    prompt = state.pending_questions[0]
                    click.echo("---")
                    click.echo(prompt)
                    click.echo(f"{step_name(state.phase).capitalize()} – type your answer and press Enter.  (/help for commands, /exit to quit)", err=True)
                    answer = _read_answer(
                        None, state,
                        project_id=pid, state_root=root, repo_url=state.repo_url, scripts_dir=scripts_dir,
                        phase=state.phase,
                    )
                    state.pending_questions.pop(0)
                    owner_repo = state.repo_pending_create or ""
                    if "/" in owner_repo:
                        owner, repo = owner_repo.split("/", 1)
                        public = (answer or "").strip().lower() != "private"
                        created = gh_repo_create(owner, repo, public=public)
                        if created:
                            state.repo_url = created
                            click.echo(f"Created repo: {created}")
                        else:
                            click.echo("Could not create repo (check `gh auth status`).", err=True)
                        state.repo_pending_create = None
                elif url:
                    state.repo_url = url
                    click.echo(msg)
                else:
                    click.echo(msg)
            manager.save(pid, state)
            if not state.repo_url:
                click.echo(f"Repo not set. Fix (e.g. `gh auth login`) and try again, or type /exit to quit.", err=True)
                state.add_pending_question(REPO_QUESTION)
                manager.save(pid, state)
                continue
            ok, init_msg = multiclaude_repo_init(state.repo_url)
            if ok:
                click.echo(_format_repo_init_success(pid, state.repo_url))
            else:
                click.echo(init_msg, err=True)
                hint = _multiclaude_init_error_hint(init_msg)
                if hint:
                    click.echo(hint, err=True)
                state.add_pending_question(REPO_QUESTION)
                manager.save(pid, state)
                continue
            # Phase 0: ensure multiclaude repo is inited (verify after init)
            repo_for_check = repo_url_to_owner_repo(state.repo_url)
            if repo_for_check:
                inited, err = is_repo_inited(repo_for_check)
                if not inited:
                    click.echo("Multiclaude repo init succeeded but repo not tracked. Retrying init once.", err=True)
                    ok2, _ = multiclaude_repo_init(state.repo_url)
                    inited2, _ = is_repo_inited(repo_for_check)
                    if not inited2:
                        click.echo(f"Repo still not inited: {err or 'unknown'}. Fix and try again, or type /exit to quit.", err=True)
                        state.add_pending_question(REPO_QUESTION)
                        manager.save(pid, state)
                        continue
            if is_api_configured():
                if not _run_interactive_phases(pid, root, state, manager, scripts_dir):
                    # User typed /exit during a phase: state already saved in phase; ensure persisted then exit
                    manager.save(pid, state)
                    return
            else:
                result = _invoke_graph(pid, root, state, start_phase=0, max_phase=1, scripts_dir=scripts_dir)
                _sync_state_from_result(state, result)
                manager.save(pid, state)
            click.echo("Planning and execution ready.")
            click.echo(f"Project: {pid}  step={step_name(state.phase)}" + (f"  Repo: {state.repo_url}" if state.repo_url else ""))
            _session_idle_until_exit(pid)
            return
    else:
        # Non-interactive: print repo question and exit (only when stdin is not a TTY)
        click.echo("---")
        click.echo(state.pending_questions[0])
        click.echo(f"Setup. Run `overlord run {pid}` (or `overlord resume {pid}`) to answer.", err=True)
        raise SystemExit(0)


@cli.command("list")
@click.option("--state-dir", type=click.Path(path_type=str), help="Override state root.")
@click.option("--format", "fmt", type=click.Choice(["human", "json"]), default="human")
def list_projects(state_dir: Optional[str], fmt: str) -> None:
    """List known projects and indicate which have pending questions."""
    root = _state_dir(state_dir)
    manager = StateManager(root)
    projects = manager.list_projects()
    if fmt == "json":
        items = []
        for pid in sorted(projects):
            s = manager.load(pid)
            items.append({"project_id": pid, "phase": s.phase, "pending_questions": len(s.pending_questions)})
        click.echo(json.dumps(items))
        return
    if not projects:
        click.echo("(no projects)")
        return
    for pid in sorted(projects):
        s = manager.load(pid)
        pending = len(s.pending_questions)
        line = f"{pid}  step={step_name(s.phase)}  pending={pending}"
        if s.repo_url:
            line += f"  repo={s.repo_url}"
        click.echo(line)


@cli.command("rm")
@click.argument("project_id", type=str)
@click.option("--state-dir", type=click.Path(path_type=str), help="Override state root.")
@click.option("--yes", "yes_flag", is_flag=True, help="Skip confirmation.")
def rm_project(project_id: str, state_dir: Optional[str], yes_flag: bool) -> None:
    """Remove a project by name. Deletes Overlord state and multiclaude clone for the project's repo."""
    root = _state_dir(state_dir)
    manager = StateManager(root)
    try:
        state = manager.load(project_id)
    except FileNotFoundError:
        click.echo(f"No such project: {project_id}", err=True)
        raise SystemExit(1)
    if not yes_flag:
        click.confirm(f"Delete project '{project_id}' and all its state?", abort=True)
    # Remove from multiclaude (state, tmux session) then remove clone dir if present
    if state.repo_url:
        ok, msg = multiclaude_repo_rm(state.repo_url)
        if ok:
            click.echo("Removed repo from multiclaude.", err=True)
        else:
            click.echo(f"multiclaude repo rm: {msg}", err=True)
        if multiclaude_remove_repo_clone(state.repo_url):
            click.echo(f"Removed multiclaude clone for {state.repo_url}", err=True)
    manager.delete_project(project_id)
    click.echo(f"Removed project: {project_id}")


def _run_proactive_status_loop(
    project_id: str,
    state_root: str,
    repo_name: Optional[str],
    scripts_dir: str,
    stop_event: threading.Event,
    quiet_ref: Dict[str, Any],
    interval_sec: int = 60,
) -> None:
    """Background loop: every interval_sec, gather status and echo one line to stderr unless quiet. Stops when stop_event is set."""
    while not stop_event.wait(interval_sec):
        if quiet_ref.get("quiet"):
            continue
        try:
            snapshot = gather_status(
                project_id, state_root,
                repo_name=repo_name,
                scripts_dir=scripts_dir,
            )
            workers_running = ", ".join(snapshot.workers) if snapshot.workers else "(none)"
            liv = snapshot.liveness[:80] + "..." if len(snapshot.liveness) > 80 else snapshot.liveness
            click.echo(f"[status] workers: {workers_running}  health={snapshot.health}  liveness={liv}", err=True)
        except Exception:
            pass


def _read_answer(
    responses_path: Optional[str],
    state: SessionState,
    project_id: Optional[str] = None,
    state_root: Optional[str] = None,
    repo_url: Optional[str] = None,
    scripts_dir: Optional[str] = None,
    phase: int = 0,
) -> str:
    """Read one answer: from responses file (at gate_response_index) or stdin. When stdin, /status, /phase, /help are handled and re-prompt. In execution phase (4+), proactive status is printed every minute unless /quiet."""
    if responses_path and os.path.isfile(responses_path):
        with open(responses_path) as f:
            lines = f.readlines()
        idx = state.gate_response_index
        answer = lines[idx].strip() if idx < len(lines) else ""
        state.gate_response_index = idx + 1
        return answer

    repo_name = repo_url_to_owner_repo(repo_url) if repo_url else None
    stop_event = threading.Event()
    quiet_ref: Dict[str, Any] = {"quiet": False}
    interval_sec = int(os.environ.get("OVERLORD_STATUS_INTERVAL_SEC", "60"))
    status_thread: Optional[threading.Thread] = None
    if phase >= 4 and repo_name and project_id and state_root and scripts_dir and interval_sec > 0:
        status_thread = threading.Thread(
            target=_run_proactive_status_loop,
            kwargs={
                "project_id": project_id,
                "state_root": state_root,
                "repo_name": repo_name,
                "scripts_dir": scripts_dir,
                "stop_event": stop_event,
                "quiet_ref": quiet_ref,
                "interval_sec": interval_sec,
            },
            daemon=True,
        )
        status_thread.start()
    try:
        while True:
            line = _safe_input()
            cmd, arg = parse_slash_command_with_arg(line)
            if cmd:
                if cmd in ("exit", "quit"):
                    _cleanup_project_workers(state)
                    click.echo("Exiting. State is saved.")
                    raise SystemExit(0)
                if project_id and state_root is not None:
                    snapshot = gather_status(
                        project_id, state_root,
                        repo_name=repo_name,
                        scripts_dir=scripts_dir,
                    )
                    out, new_quiet, _ = handle_slash_command(cmd, state, snapshot, query_arg=arg)
                    quiet_ref["quiet"] = new_quiet
                    click.echo(out)
                    continue
            return line
    finally:
        stop_event.set()


@cli.command("run")
@click.argument("project_id", type=str)
@click.option("--state-dir", type=click.Path(path_type=str), help="Override state root.")
@click.option("--responses", type=click.Path(path_type=str), help="Canned responses file.")
def run(project_id: str, state_dir: Optional[str], responses: Optional[str]) -> None:
    """Attach to an existing project and continue execution."""
    root = _state_dir(state_dir)
    manager = StateManager(root)
    try:
        state = manager.load(project_id)
    except FileNotFoundError:
        click.echo(f"Project not found: {project_id}", err=True)
        raise SystemExit(2)
    _echo_project_context(state)
    _handle_pending_or_continue(project_id, state, manager, root, responses, _overlord_scripts_dir())
    _advance_phase_if_ready(project_id, state, manager, root)
    # C14: proactive status when in execution step
    if state.phase >= 4:
        repo = repo_url_to_owner_repo(state.repo_url) if state.repo_url else None
        snapshot = gather_status(project_id, root, repo_name=repo, scripts_dir=_overlord_scripts_dir())
        liv = snapshot.liveness[:80] + "..." if len(snapshot.liveness) > 80 else snapshot.liveness
        workers_running = ", ".join(snapshot.workers) if snapshot.workers else "(none)"
        click.echo(f"[status] workers running: {workers_running}  health={snapshot.health}  liveness={liv}", err=True)
    click.echo(f"Project: {project_id}  step={step_name(state.phase)}" + (f"  Repo: {state.repo_url}" if state.repo_url else ""))


def _handle_pending_or_continue(
    project_id: str,
    state: SessionState,
    manager: StateManager,
    state_root: str,
    responses: Optional[str],
    scripts_dir: Optional[str] = None,
) -> None:
    """If pending questions: show first, read answer, pop; save; if more pending exit 0 else run Phase 0 (if repo just set) + Phase 1 and advance."""
    if not state.pending_questions:
        return
    prompt = state.pending_questions[0]
    click.echo("---")
    click.echo(prompt)
    click.echo(f"{step_name(state.phase).capitalize()} – answer to continue.  (/help for commands, /exit to quit)", err=True)
    answer = _read_answer(
        responses, state,
        project_id=project_id, state_root=state_root, repo_url=state.repo_url, scripts_dir=scripts_dir,
        phase=state.phase,
    )
    state.pending_questions.pop(0)
    just_answered_visibility = _is_visibility_prompt(prompt) or bool(state.repo_pending_create)
    just_answered_repo = _is_repo_name_or_url_prompt(prompt)
    if just_answered_visibility:
        owner_repo = state.repo_pending_create or ""
        if "/" in owner_repo:
            owner, repo = owner_repo.split("/", 1)
            public = (answer or "").strip().lower() != "private"
            created = gh_repo_create(owner, repo, public=public)
            if created:
                state.repo_url = created
                click.echo(f"Created repo: {created}")
            else:
                click.echo("Could not create repo (check `gh auth status`).", err=True)
            state.repo_pending_create = None
    elif just_answered_repo:
        url, msg, pending_create = _resolve_repo_from_answer(answer, project_id)
        if pending_create:
            state.repo_pending_create = f"{pending_create[0]}/{pending_create[1]}"
            state.pending_questions.insert(0, VISIBILITY_QUESTION)
            # Consume visibility question in same run so we don't exit
            prompt = state.pending_questions[0]
            click.echo("---")
            click.echo(prompt)
            click.echo(f"{step_name(state.phase).capitalize()} – answer to continue.  (/help for commands, /exit to quit)", err=True)
            answer = _read_answer(
                responses, state,
                project_id=project_id, state_root=state_root, repo_url=state.repo_url, scripts_dir=scripts_dir,
                phase=state.phase,
            )
            state.pending_questions.pop(0)
            just_answered_visibility = True
            owner_repo = state.repo_pending_create or ""
            if "/" in owner_repo:
                owner, repo = owner_repo.split("/", 1)
                public = (answer or "").strip().lower() != "private"
                created = gh_repo_create(owner, repo, public=public)
                if created:
                    state.repo_url = created
                    click.echo(f"Created repo: {created}")
                else:
                    click.echo("Could not create repo (check `gh auth status`).", err=True)
                state.repo_pending_create = None
        elif url:
            state.repo_url = url
            click.echo(msg)
        else:
            click.echo(msg)
    manager.save(project_id, state)
    if state.pending_questions:
        click.echo("Next: " + state.pending_questions[0], err=True)
        raise SystemExit(0)
    # No more pending: if we just set repo (repo or visibility answer), run multiclaude init + pipeline
    if (just_answered_repo or just_answered_visibility) and state.repo_url:
        ok, init_msg = multiclaude_repo_init(state.repo_url)
        if ok:
            click.echo(_format_repo_init_success(project_id, state.repo_url))
        else:
            click.echo(init_msg, err=True)
            hint = _multiclaude_init_error_hint(init_msg)
            if hint:
                click.echo(hint, err=True)
            state.add_pending_question(REPO_QUESTION)
            manager.save(project_id, state)
            click.echo(f"Fix and run `overlord run {project_id}` again, or type /exit to quit.", err=True)
            return
        # Phase 0: ensure multiclaude repo is inited (verify after init)
        repo_for_check = repo_url_to_owner_repo(state.repo_url)
        if repo_for_check:
            inited, err = is_repo_inited(repo_for_check)
            if not inited:
                ok2, _ = multiclaude_repo_init(state.repo_url)
                inited2, _ = is_repo_inited(repo_for_check)
                if not inited2:
                    click.echo(f"Repo still not inited: {err or 'unknown'}. Fix and run `overlord run {project_id}` again, or type /exit to quit.", err=True)
                    state.add_pending_question(REPO_QUESTION)
                    manager.save(project_id, state)
                    return
        result = _invoke_graph(project_id, state_root, state, start_phase=0, max_phase=1, scripts_dir=scripts_dir)
        _sync_state_from_result(state, result)
        manager.save(project_id, state)
    else:
        # Run Phase 1 only (planning)
        result = _invoke_graph(project_id, state_root, state, start_phase=1, max_phase=1, scripts_dir=scripts_dir)
        _sync_state_from_result(state, result)
        manager.save(project_id, state)
    click.echo("Planning complete.")


def _advance_phase_if_ready(
    project_id: str,
    state: SessionState,
    manager: StateManager,
    state_root: str,
) -> None:
    """When no pending questions, run pipeline from next phase to END (graph owns phase logic)."""
    if state.pending_questions:
        return
    if state.phase >= 4:
        return
    result = _invoke_graph(
        project_id, state_root, state,
        start_phase=state.phase + 1,
        max_phase=None,
        scripts_dir=_overlord_scripts_dir(),
    )
    _sync_state_from_result(state, result)
    manager.save(project_id, state)
    if state.phase >= 2:
        click.echo("Work graph ready.", err=True)
    if state.phase >= 3:
        click.echo("GitHub issues created.", err=True)
    if state.phase >= 4:
        click.echo("Execution ready.", err=True)


@cli.command("resume")
@click.argument("project_id", type=str)
@click.option("--state-dir", type=click.Path(path_type=str), help="Override state root.")
@click.option("--responses", type=click.Path(path_type=str), help="Canned responses file.")
def resume(project_id: str, state_dir: Optional[str], responses: Optional[str]) -> None:
    """Resume a project (alias for run when pending questions)."""
    root = _state_dir(state_dir)
    manager = StateManager(root)
    try:
        state = manager.load(project_id)
    except FileNotFoundError:
        click.echo(f"Project not found: {project_id}", err=True)
        raise SystemExit(2)
    _echo_project_context(state)
    _handle_pending_or_continue(project_id, state, manager, root, responses, _overlord_scripts_dir())
    _advance_phase_if_ready(project_id, state, manager, root)
    click.echo(f"Project: {project_id}  step={step_name(state.phase)}" + (f"  Repo: {state.repo_url}" if state.repo_url else ""))


@cli.command("scenario")
@click.argument("scenario_path", type=click.Path(exists=True, path_type=str))
@click.option("--state-dir", type=click.Path(path_type=str), help="Override state root.")
def scenario_cmd(scenario_path: str, state_dir: Optional[str]) -> None:
    """Run a scripted scenario (YAML: spec_path, gate_responses). Start then resume with responses."""
    root = _state_dir(state_dir)
    data = load_scenario(scenario_path)
    spec_path = data["spec_path"]
    if not os.path.isabs(spec_path):
        spec_path = os.path.abspath(spec_path)
    if not os.path.isfile(spec_path):
        click.echo(f"Spec file not found: {spec_path}", err=True)
        raise SystemExit(1)
    project_id = data.get("project_id") or _project_id_from_spec(spec_path)
    gate_responses = data.get("gate_responses") or []
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        for r in gate_responses:
            f.write(str(r).strip() + "\n")
        responses_file = f.name
    try:
        from click.testing import CliRunner
        runner = CliRunner()
        runner.invoke(cli, ["start", spec_path, "--state-dir", root, "--project-id", project_id])
        # Resume once per gate response (each resume consumes one answer from file)
        for _ in range(len(gate_responses)):
            runner.invoke(cli, ["resume", project_id, "--state-dir", root, "--responses", responses_file])
        click.echo("Scenario completed.")
    finally:
        os.unlink(responses_file)


@cli.command("status")
@click.argument("project_id", type=str)
@click.option("--state-dir", type=click.Path(path_type=str), help="Override state root.")
@click.option("--format", "fmt", type=click.Choice(["human", "json"]), default="human")
@click.option("--raw", "show_raw", is_flag=True, help="Also run multiclaude raw status (default agents, Claude processes CPU/MEM, worktrees).")
def status(project_id: str, state_dir: Optional[str], fmt: str, show_raw: bool) -> None:
    """Show status of a project (phase, pending, workers). Use --raw for full multiclaude output."""
    root = _state_dir(state_dir)
    manager = StateManager(root)
    try:
        state = manager.load(project_id)
    except FileNotFoundError:
        click.echo(f"Project not found: {project_id}", err=True)
        raise SystemExit(2)
    repo = repo_url_to_owner_repo(state.repo_url) if state.repo_url else None
    snapshot = gather_status(project_id, root, repo_name=repo, scripts_dir=_overlord_scripts_dir())
    if fmt == "json":
        out = {
            "project_id": project_id,
            "phase": state.phase,
            "repo_url": state.repo_url,
            "pending_questions": len(state.pending_questions),
            "status": {
                "workers": snapshot.workers,
                "issues_in_progress": snapshot.issues_in_progress,
                "liveness": snapshot.liveness,
                "health": snapshot.health,
                "default_agents": getattr(snapshot, "default_agents", []),
                "active_workers": getattr(snapshot, "active_workers", []),
                "claude_processes": getattr(snapshot, "claude_processes", []),
                "resource_usage": getattr(snapshot, "resource_usage", None),
                "repo_changes": getattr(snapshot, "repo_changes", []),
            },
        }
        click.echo(json.dumps(out))
        return
    _echo_project_context(state)
    click.echo(f"step={step_name(state.phase)}  pending={len(state.pending_questions)}")
    workers_running = ", ".join(snapshot.workers) if snapshot.workers else "(none)"
    click.echo(f"workers running: {workers_running}")
    click.echo(f"health={snapshot.health}  liveness={snapshot.liveness}")

    if repo and snapshot.health == "ok":
        _echo_monitor_tables(snapshot, repo_name=repo)

    if show_raw and repo:
        script = Path(_overlord_scripts_dir()) / "multiclaude-raw-status.sh"
        if script.exists():
            click.echo("")
            try:
                subprocess.run(
                    [str(script), repo],
                    cwd=Path(_overlord_scripts_dir()).parent,
                    timeout=30,
                )
            except (subprocess.TimeoutExpired, FileNotFoundError):
                click.echo("(raw status failed)", err=True)
        else:
            click.echo("(multiclaude-raw-status.sh not found)", err=True)
    elif show_raw and not repo:
        click.echo("(--raw requires a project with repo_url)", err=True)


@cli.group("worker", help="Multiclaude worker commands (list, rm).")
def worker_cmd() -> None:
    pass


@worker_cmd.command("rm")
@click.argument("repo_name", type=str)
@click.argument("worker_name", type=str)
@click.option("--yes", "yes_flag", is_flag=True, help="Non-interactive: accept cleanup prompt (unpushed commits).")
def worker_rm(repo_name: str, worker_name: str, yes_flag: bool) -> None:
    """Remove a multiclaude worker (kills tmux window, removes worktree, unregisters). Use when a worker is stuck or done but still running.
    repo_name can be owner/repo; multiclaude expects short name (multiclaude_repo_key)."""
    mc_repo = multiclaude_repo_key(repo_name) or repo_name
    try:
        stdin_input = b"y\n" if yes_flag else None
        result = subprocess.run(
            ["multiclaude", "worker", "rm", worker_name, "--repo", mc_repo],
            input=stdin_input,
            timeout=30,
        )
        if result.returncode != 0:
            raise SystemExit(result.returncode)
    except FileNotFoundError:
        click.echo("multiclaude not found. Install with: go install github.com/dlorenc/multiclaude/cmd/multiclaude@latest", err=True)
        raise SystemExit(1)
    except subprocess.TimeoutExpired:
        click.echo("Timed out.", err=True)
        raise SystemExit(1)


@worker_cmd.command("list")
@click.argument("repo_name", type=str)
def worker_list(repo_name: str) -> None:
    """List multiclaude workers for a repo (runs multiclaude worker list --repo <repo>).
    repo_name can be owner/repo; multiclaude expects short name (multiclaude_repo_key)."""
    mc_repo = multiclaude_repo_key(repo_name) or repo_name
    try:
        subprocess.run(
            ["multiclaude", "worker", "list", "--repo", mc_repo],
            timeout=10,
        )
    except FileNotFoundError:
        click.echo("multiclaude not found.", err=True)
        raise SystemExit(1)


@cli.group("multiclaude", help="Multiclaude daemon and status commands.")
def multiclaude_cmd() -> None:
    pass


@multiclaude_cmd.command("daemon")
@click.argument("action", type=click.Choice(["status", "start", "stop", "restart"]))
def multiclaude_daemon(action: str) -> None:
    """Multiclaude daemon: status | start | stop | restart. Use restart to recover from worker errors."""
    if action == "status":
        s = multiclaude_daemon_status()
        click.echo(f"multiclaude daemon: {s}")
        return
    if action == "start":
        ok, msg = multiclaude_daemon_start()
        if not ok:
            click.echo(msg, err=True)
            raise SystemExit(1)
        click.echo(msg)
        return
    if action == "stop":
        ok, msg = multiclaude_daemon_stop()
        if not ok:
            click.echo(msg, err=True)
            raise SystemExit(1)
        click.echo(msg)
        return
    if action == "restart":
        ok, msg = multiclaude_daemon_restart()
        if not ok:
            click.echo(msg, err=True)
            raise SystemExit(1)
        click.echo(msg)
        return


@multiclaude_cmd.command("status")
@click.argument("repo_name", type=str)
@click.option("--state-dir", type=click.Path(path_type=str), help="Override state root (for scripts path).")
def multiclaude_status_cmd(repo_name: str, state_dir: Optional[str]) -> None:
    """Show raw multiclaude status: default agents, workers, Claude Code processes (CPU/MEM), worktrees."""
    scripts_dir = _overlord_scripts_dir()
    script = Path(scripts_dir) / "multiclaude-raw-status.sh"
    if not script.exists():
        click.echo(f"Script not found: {script}", err=True)
        raise SystemExit(2)
    mc_repo = multiclaude_repo_key(repo_name) or repo_name
    try:
        result = subprocess.run(
            [str(script), mc_repo],
            cwd=Path(scripts_dir).parent,
            timeout=30,
        )
        if result.returncode != 0:
            raise SystemExit(result.returncode)
    except subprocess.TimeoutExpired:
        click.echo("Timed out.", err=True)
        raise SystemExit(1)
    except FileNotFoundError:
        click.echo("multiclaude or tmux not found.", err=True)
        raise SystemExit(1)


@cli.command("multiclaude-status")
@click.argument("repo_name", type=str)
@click.option("--state-dir", type=click.Path(path_type=str), help="Override state root.")
def multiclaude_status_legacy(repo_name: str, state_dir: Optional[str]) -> None:
    """Alias for: overlord multiclaude status <repo>. Show raw multiclaude status."""
    multiclaude_status_cmd(repo_name, state_dir)


@cli.command("reconcile")
@click.argument("project_id", type=str)
@click.option("--state-dir", type=click.Path(path_type=str), help="Override state root.")
@click.option("--cleanup-stuck", is_flag=True, help="Remove running workers (use with care; only for stuck workers).")
@click.option("--dispatch", is_flag=True, help="Dispatch workers for open issues that have no running worker.")
@click.option("--yes", "yes_flag", is_flag=True, help="Non-interactive: accept cleanup prompts.")
def reconcile_cmd(
    project_id: str,
    state_dir: Optional[str],
    cleanup_stuck: bool,
    dispatch: bool,
    yes_flag: bool,
) -> None:
    """Reconcile GH issues with multiclaude workers: show open/closed, workers running, and what to dispatch. Optionally cleanup stuck workers and/or dispatch for open issues."""
    root = _state_dir(state_dir)
    manager = StateManager(root)
    try:
        state = manager.load(project_id)
    except FileNotFoundError:
        click.echo(f"Project not found: {project_id}", err=True)
        raise SystemExit(2)
    repo = repo_url_to_owner_repo(state.repo_url) if state.repo_url else None
    if not repo:
        click.echo("No repo_url in project state. Run overlord run until repo is set.", err=True)
        raise SystemExit(2)
    issues_path = state.artifact_paths.get("issues")
    if not issues_path or not Path(issues_path).is_file():
        click.echo("No issues.json found. Run through Phase 3 (issues) first.", err=True)
        raise SystemExit(2)
    with open(issues_path, encoding="utf-8") as f:
        issues_from_json = json.load(f)
    if not isinstance(issues_from_json, list):
        issues_from_json = []
    r = reconcile_issues(repo, issues_from_json)
    if r.gh_fetch_error:
        click.echo(f"GitHub fetch error: {r.gh_fetch_error}", err=True)
    if r.multiclaude_error:
        click.echo(f"Multiclaude error: {r.multiclaude_error}", err=True)
    click.echo("")
    click.echo("--- Reconcile ---")
    click.echo(f"Repo: {r.repo}")
    click.echo(f"Open issues (GH): {len(r.open_issues)}")
    for i in r.open_issues:
        click.echo(f"  #{(i.get('number'))} {(i.get('title') or '')[:50]}")
    click.echo(f"Closed issues (GH): {len(r.closed_issues)}")
    click.echo(f"Workers running: {r.workers_running}")
    click.echo(f"Workers finished: {r.workers_finished}")
    click.echo(f"Issues to dispatch (open, no running worker): {len(r.issues_to_dispatch)}")
    for i in r.issues_to_dispatch:
        click.echo(f"  #{(i.get('number'))} {(i.get('title') or '')[:50]}")
    if cleanup_stuck and r.workers_running:
        scripts_dir = _overlord_scripts_dir()
        mc_repo = multiclaude_repo_key(repo) or repo
        for w in r.workers_running:
            click.echo(f"Removing worker: {w}")
            stdin_input = b"y\n" if yes_flag else None
            subprocess.run(
                ["multiclaude", "worker", "rm", w, "--repo", mc_repo],
                input=stdin_input,
                timeout=30,
            )
    if dispatch and r.issues_to_dispatch:
        scripts_dir = _overlord_scripts_dir()
        from overlord.agents.multiclaude_dispatch import create_worker
        for i in r.issues_to_dispatch:
            num = i.get("number")
            title = (i.get("title") or "").strip()
            task = f"Issue #{num}: {title}" if num is not None else title
            if task:
                click.echo(f"Dispatching: {task[:60]}...")
                create_worker(repo, task, scripts_dir=scripts_dir)


def main() -> None:
    """Entry point for overlord CLI (pyproject.toml [project.scripts])."""
    cli()


if __name__ == "__main__":
    main()

"""
Phase 4 (Execution Manager): dispatch multiclaude workers, monitor status, capture replies.
When Claude API is configured, invokes Phase 4 agent; otherwise stub persists prompt.
C13: Uses multiclaude CLI/scripts when available — create-worker-with-auto-accept per issue.
Ensures multiclaude daemon running and repo inited before dispatch; dispatches in wave order (ready issues only).
"""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    import yaml
except ImportError:
    yaml = None

from overlord.claude_api import invoke_phase_agent, invoke_phase_agent_messages, is_api_configured, send_one_sync
from overlord.repo_utils import repo_url_to_owner_repo
from overlord.phase_log import (
    load_conversation,
    save_conversation,
    append_execution_log,
    ensure_phase_log_paths,
)

from overlord.agents.multiclaude_dispatch import create_worker, list_workspace_replies
from overlord.multiclaude_recovery import (
    is_repo_inited,
    multiclaude_daemon_start,
    multiclaude_daemon_status,
    multiclaude_repo_init,
    reconcile_issues,
)


def _load_issues(issues_path: Optional[str]) -> List[Dict[str, Any]]:
    """Load issues.json; return list of {task_id, number, title} or []."""
    if not issues_path or not issues_path.strip():
        return []
    p = Path(issues_path)
    if not p.is_file():
        return []
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _load_workgraph(workgraph_path: Optional[str]) -> Optional[Dict[str, Any]]:
    """Load workgraph.yml; return dict with 'waves' or None."""
    if not workgraph_path or not Path(workgraph_path).is_file() or not yaml:
        return None
    try:
        with open(workgraph_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data if isinstance(data, dict) and "waves" in data else None
    except Exception:
        return None


def get_ready_issues(
    workgraph_path: Optional[str],
    issues: List[Dict[str, Any]],
    closed_issue_numbers: Set[int],
) -> List[Dict[str, Any]]:
    """
    Return issues that are ready to dispatch: in the current wave (first wave with open issues)
    and whose depends_on are all closed. Respects wave order; only issues from current wave.
    """
    if not issues or not workgraph_path:
        return list(issues)
    workgraph = _load_workgraph(workgraph_path)
    if not workgraph:
        return list(issues)
    task_id_to_number = {str(i.get("task_id", "")): i.get("number") for i in issues if i.get("number") is not None}
    number_to_issue = {i.get("number"): i for i in issues if i.get("number") is not None}
    closed = set(closed_issue_numbers)
    waves = workgraph.get("waves") or []
    for wave in waves:
        tasks = wave.get("tasks") or []
        open_in_wave = [
            t for t in tasks
            if task_id_to_number.get(t.get("id")) not in closed
        ]
        if not open_in_wave:
            continue
        ready_numbers = [
            task_id_to_number.get(t["id"])
            for t in tasks
            if task_id_to_number.get(t["id"]) not in closed
            and all(
                task_id_to_number.get(dep) in closed
                for dep in (t.get("depends_on") or [])
            )
        ]
        ready_numbers = [n for n in ready_numbers if n is not None]
        return [number_to_issue[n] for n in ready_numbers if n in number_to_issue]
    return []


def ensure_multiclaude_ready(
    repo: str,
    repo_url: Optional[str],
) -> Tuple[bool, Optional[str]]:
    """
    Ensure multiclaude daemon is running and repo is inited. If not, try to start daemon and init repo.
    Returns (True, None) if ready, (False, error_message) otherwise.
    """
    daemon = multiclaude_daemon_status()
    if daemon != "running":
        ok, msg = multiclaude_daemon_start()
        if not ok:
            return False, f"Daemon not running: {msg}"
        daemon = multiclaude_daemon_status()
        if daemon != "running":
            return False, "Daemon failed to start."
    inited, err = is_repo_inited(repo)
    if not inited and repo_url:
        ok, init_msg = multiclaude_repo_init(repo_url)
        if ok:
            inited, err = is_repo_inited(repo)
        if not inited:
            return False, err or "Repo not inited."
    elif not inited:
        return False, err or "Repo not inited."
    return True, None


def run_phase4_execution_manager(
    project_id: str,
    state_root: str,
    artifact_paths: Optional[Dict[str, str]] = None,
    system_prompt: Optional[str] = None,
    repo_name: Optional[str] = None,
    repo_url: Optional[str] = None,
    scripts_dir: Optional[str] = None,
    message_source: Optional[str] = None,
    injected_message: Optional[str] = None,
    phase_4_client: Any = None,
) -> Dict[str, Any]:
    """
    Run Phase 4 execution manager: dispatch workers per work graph, monitor, unblock.
    When API configured: invokes Claude with Phase 4 prompt + work graph/issues context; persists response.
    When message_source and injected_message are set (from monitor or user), uses them as the user message
    with a [From: source] prefix so the agent can distinguish and respond appropriately.
    C13: When repo and scripts_dir available, loads issues and creates one multiclaude worker per issue
    via create-worker-with-auto-accept; then captures replies via list-workspace-replies.
    Returns updated phase and artifact_paths.
    """
    project_dir = Path(state_root) / "projects" / project_id
    artifacts_dir = project_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    paths = dict(artifact_paths or {})

    conv_path, log_path = ensure_phase_log_paths(artifacts_dir, 4)
    paths["phase_4_conversation"] = conv_path
    paths["phase_4_execution_log"] = log_path

    if system_prompt:
        prompt_file = artifacts_dir / "phase_4_system_prompt.md"
        prompt_file.write_text(system_prompt, encoding="utf-8")
        paths["phase_4_system_prompt"] = str(prompt_file)

        # Phase 4 agent: invoke Claude when API configured
        if is_api_configured():
            if message_source and injected_message is not None:
                user_message = f"[From: {message_source}]\n\n{injected_message.strip()}\n\n"
                # Append work graph/issues context so agent has current state
                for key in ("workgraph", "issues"):
                    path = (artifact_paths or {}).get(key)
                    if path and Path(path).is_file():
                        try:
                            user_message += f"--- {key} (context) ---\n"
                            user_message += Path(path).read_text(encoding="utf-8", errors="replace")
                            user_message += "\n\n"
                        except Exception:
                            pass
            else:
                user_message = "Begin Phase 4 (Execution Manager). You have the work graph and issues below. Produce a brief execution plan (which issues to dispatch first, monitoring strategy). Real multiclaude dispatch is done by the system; your output guides the approach.\n\n"
                for key in ("workgraph", "issues"):
                    path = (artifact_paths or {}).get(key)
                    if path and Path(path).is_file():
                        try:
                            user_message += f"--- {key} ---\n"
                            user_message += Path(path).read_text(encoding="utf-8", errors="replace")
                            user_message += "\n\n"
                        except Exception:
                            pass
                if user_message.count("---") == 0:
                    user_message += "(No work graph or issues file available yet.)\n"
            append_execution_log(log_path, 4, "context", "Phase 4 user message", payload={"message_source": message_source, "user_message_preview": user_message[:500]})
            messages = load_conversation(conv_path)
            messages.append({"role": "user", "content": user_message})
            cwd = str(project_dir)
            if phase_4_client is not None:
                response = send_one_sync(phase_4_client, user_message)
            elif len(messages) > 1:
                response = invoke_phase_agent_messages(4, system_prompt, messages, cwd=cwd)
            else:
                response = invoke_phase_agent(4, system_prompt, user_message, cwd=cwd)
            if response:
                messages.append({"role": "assistant", "content": response})
                save_conversation(conv_path, messages)
                response_file = artifacts_dir / "phase_4_claude_response.txt"
                response_file.write_text(response, encoding="utf-8")
                paths["phase_4_claude_response"] = str(response_file)
                append_execution_log(log_path, 4, "assistant", "Phase 4 agent response", payload={"response_preview": response[:500]})
            append_execution_log(log_path, 4, "action", "invoke_phase_agent(4) completed")

    # Ensure multiclaude is running and repo inited before dispatch
    repo = repo_url_to_owner_repo(repo_url) if repo_url else (repo_name.strip() if repo_name and "/" in str(repo_name) else None)
    issues_path = (artifact_paths or {}).get("issues")
    workgraph_path = (artifact_paths or {}).get("workgraph")
    issues = _load_issues(issues_path)
    if repo and issues and scripts_dir:
        append_execution_log(log_path, 4, "action", "ensure_multiclaude_ready", payload={"repo": repo})
        ready_ok, ensure_err = ensure_multiclaude_ready(repo, repo_url)
        if not ready_ok:
            append_execution_log(log_path, 4, "action", "ensure_multiclaude_ready failed", payload={"error": ensure_err})
            paths["phase_4_ensure_error"] = str(artifacts_dir / "phase_4_ensure_error.txt")
            (artifacts_dir / "phase_4_ensure_error.txt").write_text(
                ensure_err or "multiclaude not ready",
                encoding="utf-8",
            )
        else:
            append_execution_log(log_path, 4, "action", "reconcile_issues", payload={"repo": repo})
            r = reconcile_issues(repo, issues)
            if r.multiclaude_error and repo_url:
                multiclaude_repo_init(repo_url)
                r = reconcile_issues(repo, issues)
            append_execution_log(
                log_path, 4, "action", "reconcile_issues result",
                payload={"open_count": len(r.open_issues or []), "closed_count": len(r.closed_issues or []), "workers_running": len(r.workers_running or [])},
            )
            closed_numbers = {i.get("number") for i in (r.closed_issues or []) if i.get("number") is not None}
            ready_issues = get_ready_issues(workgraph_path, issues, closed_numbers)
            to_dispatch = [i for i in ready_issues if any(i.get("number") == j.get("number") for j in (r.issues_to_dispatch or []))]
            if not to_dispatch and ready_issues:
                to_dispatch = ready_issues
            n_running = len(r.workers_running)
            n_open = len(r.open_issues)
            if n_running > 0 and n_open > 0 and len(to_dispatch) > max(0, n_open - n_running):
                to_dispatch = to_dispatch[: max(0, n_open - n_running)]
            append_execution_log(log_path, 4, "action", "get_ready_issues", payload={"ready_count": len(ready_issues), "to_dispatch_count": len(to_dispatch)})
            for issue in to_dispatch:
                number = issue.get("number")
                title = (issue.get("title") or "").strip()
                task_string = f"Issue #{number}: {title}" if number is not None else title
                if task_string:
                    create_worker(repo, task_string, scripts_dir=scripts_dir)
                    append_execution_log(log_path, 4, "action", "create_worker", payload={"issue": number, "task_string": task_string[:200]})
        append_execution_log(log_path, 4, "action", "list_workspace_replies", payload={"repo": repo})
        replies = list_workspace_replies(repo, scripts_dir=scripts_dir)
        if replies:
            append_execution_log(log_path, 4, "action", "list_workspace_replies result", payload={"reply_count": len(replies)})
            replies_file = artifacts_dir / "phase_4_workspace_replies.txt"
            replies_file.write_text("\n".join(replies), encoding="utf-8")
            paths["phase_4_workspace_replies"] = str(replies_file)

    paths["phase_4"] = str(artifacts_dir)

    return {
        "phase": 4,
        "artifact_paths": paths,
        "phase_4_done": True,
    }

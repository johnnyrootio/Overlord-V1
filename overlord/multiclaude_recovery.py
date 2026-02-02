"""
Multiclaude recovery and reconciliation: daemon control, worker errors, GH issue reconciliation.
Lets Overlord restart multiclaude, clean up stuck workers, and pick up where it left off.
"""
import json
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse


@dataclass
class ReconcileResult:
    """Result of reconciling Overlord issues with GitHub and multiclaude workers."""
    repo: str = ""
    open_issues: List[Dict[str, Any]] = field(default_factory=list)  # GH open, from our issues.json
    closed_issues: List[Dict[str, Any]] = field(default_factory=list)  # GH closed
    workers_running: List[str] = field(default_factory=list)  # worker names currently running
    workers_finished: List[str] = field(default_factory=list)  # worker names no longer in list (finished/removed)
    stuck_workers: List[str] = field(default_factory=list)  # running but optional to clean (e.g. completed work, agent complete failed)
    issues_to_dispatch: List[Dict[str, Any]] = field(default_factory=list)  # open issues that have no running worker
    gh_fetch_error: Optional[str] = None
    multiclaude_error: Optional[str] = None


def multiclaude_daemon_status() -> str:
    """Return 'running', 'stopped', or 'unknown'."""
    try:
        r = subprocess.run(
            ["multiclaude", "daemon", "status"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        out = (r.stdout or "").lower()
        if r.returncode == 0 and "running" in out:
            return "running"
        return "stopped"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return "unknown"


def multiclaude_daemon_start() -> Tuple[bool, str]:
    """Start multiclaude daemon. Returns (success, message)."""
    try:
        r = subprocess.run(
            ["multiclaude", "start"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if r.returncode == 0:
            return True, (r.stdout or "").strip() or "Daemon started."
        return False, (r.stderr or r.stdout or "Unknown error").strip()
    except FileNotFoundError:
        return False, "multiclaude not found. Install with: go install github.com/dlorenc/multiclaude/cmd/multiclaude@latest"
    except subprocess.TimeoutExpired:
        return False, "Timed out starting daemon."


def multiclaude_daemon_stop() -> Tuple[bool, str]:
    """Stop multiclaude daemon. Returns (success, message)."""
    try:
        r = subprocess.run(
            ["multiclaude", "daemon", "stop"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if r.returncode == 0:
            return True, (r.stdout or "").strip() or "Daemon stopped."
        return False, (r.stderr or r.stdout or "Unknown error").strip()
    except FileNotFoundError:
        return False, "multiclaude not found."
    except subprocess.TimeoutExpired:
        return False, "Timed out stopping daemon."


def multiclaude_daemon_restart() -> Tuple[bool, str]:
    """Stop then start multiclaude daemon. Returns (success, message)."""
    ok, msg = multiclaude_daemon_stop()
    if not ok and multiclaude_daemon_status() != "running":
        pass  # already stopped
    elif not ok:
        return False, f"Stop failed: {msg}"
    ok2, msg2 = multiclaude_daemon_start()
    if not ok2:
        return False, f"Start failed: {msg2}"
    return True, "Daemon restarted."


def _multiclaude_repos_dir_for(repo_url: str) -> Optional[str]:
    """Path where multiclaude clones this repo: ~/.multiclaude/repos/<repo-name>. Repo name = last path segment of URL or owner/repo."""
    return get_multiclaude_repo_name(repo_url)


def get_multiclaude_repo_name(repo_url: str) -> Optional[str]:
    """Repo name used by multiclaude (session name is mc-<this>). For display and CLI messages."""
    url = (repo_url or "").strip()
    if not url:
        return None
    if "/" in url and " " not in url and not url.startswith("http"):
        return url.split("/")[-1]
    parsed = urlparse(url)
    path = (parsed.path or "").strip("/")
    if not path:
        return None
    return path.split("/")[-1].replace(".git", "")


def _multiclaude_repo_clone_path(repo_url: str) -> Optional[str]:
    """Full path to multiclaude's clone for this repo, or None."""
    repo_name = _multiclaude_repos_dir_for(repo_url)
    if not repo_name:
        return None
    base = os.environ.get("MULTICLAUDE_HOME") or os.path.expanduser("~/.multiclaude")
    return os.path.join(base, "repos", repo_name)


def multiclaude_remove_repo_clone(repo_url: str) -> bool:
    """Remove multiclaude's clone (and worktrees) for this repo. Returns True if a dir was removed."""
    dest = _multiclaude_repo_clone_path(repo_url)
    if not dest or not os.path.isdir(dest):
        return False
    try:
        shutil.rmtree(dest)
        return True
    except OSError:
        return False


def multiclaude_repo_rm(repo_url: str) -> Tuple[bool, str]:
    """Run `multiclaude repo rm <name>` so multiclaude forgets the repo (state, tmux session, etc.).
    Uses repo name derived from URL (e.g. trivial-todo-app). Returns (success, message)."""
    repo_name = _multiclaude_repos_dir_for(repo_url)
    if not repo_name:
        return False, "Could not derive repo name from URL."
    try:
        r = subprocess.run(
            ["multiclaude", "repo", "rm", repo_name],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if r.returncode == 0:
            return True, (r.stdout or "").strip() or f"Removed {repo_name} from multiclaude."
        return False, (r.stderr or r.stdout or "Unknown error").strip()
    except FileNotFoundError:
        return False, "multiclaude not found."
    except subprocess.TimeoutExpired:
        return False, "Timed out running multiclaude repo rm."


def multiclaude_repo_init(repo_url: str) -> Tuple[bool, str]:
    """Run `multiclaude repo init <repo_url>`. Returns (success, message).
    If multiclaude's clone destination already exists (e.g. from a previous run), removes it so init can clone clean.
    Also kills any existing tmux session for this repo (mc-<name>) so init can create a fresh one after overlord rm."""
    url = (repo_url or "").strip()
    if not url:
        return False, "No repo_url provided."
    repo_name = get_multiclaude_repo_name(url)
    dest = _multiclaude_repo_clone_path(url)
    if dest and os.path.isdir(dest):
        try:
            shutil.rmtree(dest)
        except OSError:
            pass  # proceed anyway; multiclaude may still fail
    if repo_name:
        try:
            subprocess.run(
                ["tmux", "kill-session", "-t", f"mc-{repo_name}"],
                capture_output=True,
                timeout=5,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            pass  # tmux not installed or session didn't exist; proceed with init
    try:
        r = subprocess.run(
            ["multiclaude", "repo", "init", url],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if r.returncode == 0:
            return True, (r.stdout or "").strip() or "Repo initialized."
        return False, (r.stderr or r.stdout or "Unknown error").strip()
    except FileNotFoundError:
        return False, "multiclaude not found. Install with: go install github.com/dlorenc/multiclaude/cmd/multiclaude@latest"
    except subprocess.TimeoutExpired:
        return False, "Timed out running multiclaude repo init."


def gh_issue_list(repo: str, state: str = "all", limit: int = 100) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """Fetch issue list from GitHub. Returns (list of {number, state, title}, error)."""
    try:
        r = subprocess.run(
            ["gh", "issue", "list", "--repo", repo, "--state", state, "--limit", str(limit), "--json", "number,state,title"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if r.returncode != 0:
            return [], (r.stderr or r.stdout or "gh issue list failed").strip()
        data = json.loads(r.stdout or "[]")
        return data if isinstance(data, list) else [], None
    except json.JSONDecodeError as e:
        return [], str(e)
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        return [], str(e)


def multiclaude_workers_remove_all(repo: str, accept_prompts: bool = True) -> Tuple[int, Optional[str]]:
    """
    Remove all multiclaude workers for a repo (kills tmux/Claude Code sessions).
    Returns (count_removed, error_message or None). Uses stdin 'y\\n' when accept_prompts to avoid blocking.
    """
    workers, _, err = multiclaude_worker_list_with_status(repo)
    if err:
        return 0, err
    if not workers:
        return 0, None
    stdin_input = b"y\n" if accept_prompts else None
    removed = 0
    for name in workers:
        try:
            r = subprocess.run(
                ["multiclaude", "worker", "rm", name, "--repo", repo],
                input=stdin_input,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if r.returncode == 0:
                removed += 1
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
    return removed, None


def multiclaude_worker_list_with_status(repo: str) -> Tuple[List[str], Dict[str, str], Optional[str]]:
    """Get worker names and status from multiclaude. Returns (workers, name->status, error)."""
    try:
        r = subprocess.run(
            ["multiclaude", "worker", "list", "--repo", repo],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if r.returncode != 0:
            return [], {}, (r.stderr or r.stdout or "worker list failed").strip()
        workers: List[str] = []
        statuses: Dict[str, str] = {}
        for line in (r.stdout or "").splitlines():
            line = line.strip()
            if not line or "Workspace in" in line or "No workers" in line or "Create a worker" in line or "repository '" in line:
                continue
            if line.startswith("---") or ("NAME" in line and "STATUS" in line):
                continue
            if "●" in line and "running" in line:
                parts = line.split()
                if parts:
                    name = parts[0]
                    workers.append(name)
                    statuses[name] = "running"
            elif line and not line.startswith("-") and " " in line:
                name = line.split()[0]
                if name.replace("-", "").replace("_", "").isalnum():
                    workers.append(name)
                    statuses[name] = "finished" if "running" not in line else "running"
        return workers, statuses, None
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        return [], {}, str(e)


def reconcile_issues(
    repo: str,
    issues_from_json: List[Dict[str, Any]],
    worker_names_to_issue: Optional[Dict[str, int]] = None,
) -> ReconcileResult:
    """
    Reconcile Overlord issues (from issues.json) with GitHub state and multiclaude workers.
    - Fetches GH issue list (open/closed).
    - Fetches multiclaude worker list (running/finished).
    - Computes: open_issues, closed_issues, workers_running, issues_to_dispatch (open with no running worker).
    worker_names_to_issue: optional map worker_name -> issue number (if we persist it); else we infer from task string.
    """
    result = ReconcileResult(repo=repo)
    gh_issues, err = gh_issue_list(repo, state="all")
    if err:
        result.gh_fetch_error = err
        result.open_issues = list(issues_from_json)
        result.issues_to_dispatch = result.open_issues
        return result
    gh_by_number = {int(i["number"]): i for i in gh_issues if i.get("number") is not None}
    workers, statuses, mc_err = multiclaude_worker_list_with_status(repo)
    if mc_err:
        result.multiclaude_error = mc_err
    result.workers_running = [w for w in workers if statuses.get(w) == "running"]
    result.workers_finished = [w for w in workers if statuses.get(w) != "running"]
    open_numbers = {num for num, i in gh_by_number.items() if (i.get("state") or "").lower() == "open"}
    closed_numbers = {num for num, i in gh_by_number.items() if (i.get("state") or "").lower() == "closed"}
    for i in issues_from_json:
        num = i.get("number")
        if num is None:
            continue
        rec = {**i, "gh_state": gh_by_number.get(num, {}).get("state", "unknown")}
        if num in open_numbers:
            result.open_issues.append(rec)
        elif num in closed_numbers:
            result.closed_issues.append(rec)
    if worker_names_to_issue:
        running_for_numbers = {worker_names_to_issue[w] for w in result.workers_running if w in worker_names_to_issue}
        result.issues_to_dispatch = [i for i in result.open_issues if i.get("number") not in running_for_numbers]
    else:
        result.issues_to_dispatch = list(result.open_issues)
    result.stuck_workers = []  # caller can treat long-running workers as stuck if desired
    return result

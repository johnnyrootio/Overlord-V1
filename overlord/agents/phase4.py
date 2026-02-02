"""
Phase 4 (Execution Manager): dispatch multiclaude workers, monitor status, capture replies.
When Claude API is configured, invokes Phase 4 agent; otherwise stub persists prompt.
C13: Uses multiclaude CLI/scripts when available — create-worker-with-auto-accept per issue.
"""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from overlord.claude_api import invoke_phase_agent, is_api_configured
from overlord.repo_utils import repo_url_to_owner_repo

from overlord.agents.multiclaude_dispatch import create_worker, list_workspace_replies
from overlord.multiclaude_recovery import reconcile_issues


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


def run_phase4_execution_manager(
    project_id: str,
    state_root: str,
    artifact_paths: Optional[Dict[str, str]] = None,
    system_prompt: Optional[str] = None,
    repo_name: Optional[str] = None,
    repo_url: Optional[str] = None,
    scripts_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run Phase 4 execution manager: dispatch workers per work graph, monitor, unblock.
    When API configured: invokes Claude with Phase 4 prompt + work graph/issues context; persists response.
    C13: When repo and scripts_dir available, loads issues and creates one multiclaude worker per issue
    via create-worker-with-auto-accept; then captures replies via list-workspace-replies.
    Returns updated phase and artifact_paths.
    """
    project_dir = Path(state_root) / "projects" / project_id
    artifacts_dir = project_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    paths = dict(artifact_paths or {})

    if system_prompt:
        prompt_file = artifacts_dir / "phase_4_system_prompt.md"
        prompt_file.write_text(system_prompt, encoding="utf-8")
        paths["phase_4_system_prompt"] = str(prompt_file)

        # Phase 4 agent: invoke Claude when API configured
        if is_api_configured():
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
            response = invoke_phase_agent(4, system_prompt, user_message)
            if response:
                response_file = artifacts_dir / "phase_4_claude_response.txt"
                response_file.write_text(response, encoding="utf-8")
                paths["phase_4_claude_response"] = str(response_file)

    # C13: multiclaude dispatch — reconcile GH + workers, then create workers only for open issues that have no running worker
    repo = repo_url_to_owner_repo(repo_url) if repo_url else (repo_name.strip() if repo_name and "/" in str(repo_name) else None)
    issues_path = (artifact_paths or {}).get("issues")
    issues = _load_issues(issues_path)
    if repo and issues and scripts_dir:
        r = reconcile_issues(repo, issues)
        to_dispatch = r.issues_to_dispatch if r.issues_to_dispatch else issues
        # On resume: don't over-dispatch; only add workers for open issues that don't have one yet (heuristic: gap = open - running)
        n_running = len(r.workers_running)
        n_open = len(r.open_issues)
        if n_running > 0 and n_open > 0 and len(to_dispatch) > max(0, n_open - n_running):
            to_dispatch = to_dispatch[: max(0, n_open - n_running)]
        for issue in to_dispatch:
            number = issue.get("number")
            title = (issue.get("title") or "").strip()
            task_string = f"Issue #{number}: {title}" if number is not None else title
            if task_string:
                create_worker(repo, task_string, scripts_dir=scripts_dir)
        replies = list_workspace_replies(repo, scripts_dir=scripts_dir)
        if replies:
            replies_file = artifacts_dir / "phase_4_workspace_replies.txt"
            replies_file.write_text("\n".join(replies), encoding="utf-8")
            paths["phase_4_workspace_replies"] = str(replies_file)

    paths["phase_4"] = str(artifacts_dir)

    return {
        "phase": 4,
        "artifact_paths": paths,
        "phase_4_done": True,
    }

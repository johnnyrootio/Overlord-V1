"""
Phase 4 multiclaude dispatch: create workers (via script), worker status and replies in Python.
C13: create_worker uses create-worker-with-auto-accept.sh; monitoring/replies done in Python.
See foundational/palpatine/WORKER-DISPATCH-GUIDE.md, MULTICLAUDE-INTERFACE-RULES.md.
Multiclaude keys repos by short name (last path segment); we pass that to CLI and paths.
"""
import json
import os
import subprocess
from pathlib import Path
from typing import List, Optional

from overlord.multiclaude_recovery import multiclaude_repo_key


def _multiclaude_root() -> Path:
    return Path(os.environ.get("MULTICLAUDE_ROOT", os.path.expanduser("~/.multiclaude")))


def create_worker(repo_name: str, task: str, scripts_dir: Optional[str] = None) -> bool:
    """
    Create multiclaude worker via create-worker-with-auto-accept.sh.
    repo_name can be owner/repo; multiclaude expects short name (multiclaude_repo_key).
    Returns True if script succeeded. Stub when script not found.
    """
    mc_repo = multiclaude_repo_key(repo_name) or repo_name
    if scripts_dir is None:
        scripts_dir = os.environ.get("OVERLORD_SCRIPTS_DIR", "scripts")
    script = Path(scripts_dir) / "create-worker-with-auto-accept.sh"
    if not script.exists():
        return False
    try:
        result = subprocess.run(
            [str(script), mc_repo, task],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=Path(scripts_dir).parent,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def check_worker_status(repo_name: str, scripts_dir: Optional[str] = None) -> str:
    """Run check-worker-status.sh if present; return output or 'stub'. Monitor uses Python instead.
    repo_name can be owner/repo; multiclaude paths use short name."""
    mc_repo = multiclaude_repo_key(repo_name) or repo_name
    if scripts_dir is None:
        scripts_dir = os.environ.get("OVERLORD_SCRIPTS_DIR", "scripts")
    script = Path(scripts_dir) / "check-worker-status.sh"
    if not script.exists():
        return "stub"
    try:
        result = subprocess.run(
            [str(script), mc_repo],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=Path(scripts_dir).parent,
        )
        return result.stdout or result.stderr or "stub"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return "stub"


def list_workspace_replies(repo_name: str, scripts_dir: Optional[str] = None) -> List[str]:
    """List workspace inbox messages. Uses Python (reads ~/.multiclaude/messages/<repo>/workspace/).
    repo_name can be owner/repo; multiclaude uses short name for paths."""
    mc_repo = multiclaude_repo_key(repo_name) or repo_name
    if scripts_dir:
        script = Path(scripts_dir) / "list-workspace-replies.sh"
        if script.exists():
            try:
                result = subprocess.run(
                    [str(script), mc_repo],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    cwd=Path(scripts_dir).parent,
                )
                if result.returncode == 0:
                    return [line.strip() for line in (result.stdout or "").splitlines() if line.strip()]
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass
    root = _multiclaude_root()
    inbox = root / "messages" / mc_repo / "workspace"
    if not inbox.is_dir():
        return []
    lines: List[str] = []
    for f in sorted(inbox.glob("msg-*.json")):
        if not f.is_file():
            continue
        try:
            with open(f, "r") as fp:
                data = json.load(fp)
            msg_id = f.stem.replace("msg-", "")
            ts = data.get("timestamp", "")
            from_ = data.get("from", "")
            status = data.get("status", "")
            body = (data.get("body") or "").strip()
            lines.append("---")
            lines.append(f"ID: {msg_id} | {ts} | From: {from_} | Status: {status}")
            if body:
                lines.append(body)
        except (json.JSONDecodeError, OSError):
            lines.append("---")
            lines.append(f"(read error: {f.name})")
    return lines

"""
Status subsystem (multiclaude monitor): snapshot of workers, issues, liveness, health.
All logic in Python: calls multiclaude CLI, tmux, ps; no shell scripts required.
See docs/DESIGN-AND-ARCHITECTURE.md Section 8.4, docs/OVERLORD-CLI-SPEC.md Section 6.
"""
import os
import re
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from overlord.agents.multiclaude_dispatch import list_workspace_replies
from overlord.multiclaude_recovery import is_repo_inited, multiclaude_daemon_status, multiclaude_repo_key


@dataclass
class StatusSnapshot:
    """Snapshot for proactive display and /status. Stub when multiclaude not available."""
    workers: List[str] = field(default_factory=list)
    issues_in_progress: List[str] = field(default_factory=list)
    liveness: str = "unknown"
    health: str = "unknown"  # "ok" | "daemon_down" | "repo_not_inited" | "stub"
    raw: Optional[str] = None
    active_workers: List[str] = field(default_factory=list)
    processes_summary: str = ""
    resource_usage: Optional[Dict[str, Any]] = None  # cpu_pct, mem_pct, disk_mb
    repo_changes: List[str] = field(default_factory=list)
    default_agents: List[str] = field(default_factory=list)  # supervisor, merge-queue, default
    claude_processes: List[Dict[str, Any]] = field(default_factory=list)  # real only: {"pid","cpu","mem","agent"}
    worker_statuses: Dict[str, str] = field(default_factory=dict)  # name -> "running" | "finished" | "unknown"
    daemon_status: str = "unknown"  # "running" | "stopped" | "unknown"
    repo_inited: bool = False  # True if multiclaude has this repo tracked
    multiclaude_error: Optional[str] = None  # e.g. "repo not inited" when repo_inited is False


def format_snapshot_tables(snapshot: StatusSnapshot, repo_name: Optional[str] = None) -> str:
    """Format StatusSnapshot in multiclaude-style: banner, numbered --- N) --- sections, dashed tables, no box-drawing."""
    lines: List[str] = []
    default_agents = getattr(snapshot, "default_agents", []) or []
    claude_processes = getattr(snapshot, "claude_processes", []) or []
    active_workers = getattr(snapshot, "active_workers", []) or []
    worker_statuses = getattr(snapshot, "worker_statuses", {}) or {}
    workers = snapshot.workers or []
    repo_changes = getattr(snapshot, "repo_changes", []) or []
    resource_usage = getattr(snapshot, "resource_usage", None) or {}

    # Banner (multiclaude-style)
    title = "OVERLORD MONITOR" + (f": {repo_name}" if repo_name else "")
    lines.append("==============================================")
    lines.append(title)
    lines.append("==============================================")
    lines.append("")

    # --- 1) Summary ---
    lines.append("--- 1) Summary ---")
    daemon_status = getattr(snapshot, "daemon_status", "unknown")
    repo_inited = getattr(snapshot, "repo_inited", False)
    lines.append(f"health: {snapshot.health}")
    lines.append(f"daemon: {daemon_status}")
    lines.append(f"repo_inited: {'yes' if repo_inited else 'no'}")
    if getattr(snapshot, "multiclaude_error", None):
        lines.append(f"multiclaude_error: {snapshot.multiclaude_error}")
    liv = (snapshot.liveness or "").strip()
    lines.append(f"liveness: {liv}")
    lines.append("")

    # --- 2) Agents / Workers ---
    lines.append("--- 2) Agents / Workers ---")
    if default_agents or workers:
        lines.append("NAME                 STATUS")
        lines.append("-" * 40)
        for name in default_agents:
            lines.append(f"{name:<20} ● running")
        for name in workers:
            if name in default_agents:
                continue
            st = worker_statuses.get(name) or ("active" if name in active_workers else "running")
            if st == "running":
                lines.append(f"{name:<20} ● running")
            else:
                lines.append(f"{name:<20} {st}")
        lines.append("")
    else:
        lines.append("(none)")
        lines.append("")

    # --- 3) Claude Code processes (CPU, MEM) ---
    lines.append("--- 3) Claude Code processes (CPU, MEM) ---")
    if claude_processes:
        lines.append("PID       %CPU  %MEM  AGENT")
        lines.append("-" * 50)
        for p in claude_processes:
            agent = (p.get("agent") or "?")[:20]
            pid = str(p.get("pid", "?"))
            cpu = p.get("cpu", 0)
            mem = p.get("mem", 0)
            lines.append(f"{pid:<9} {cpu:>5.1f} {mem:>5.1f}  {agent}")
        total_cpu = resource_usage.get("cpu_pct", 0)
        total_mem = resource_usage.get("mem_pct", 0)
        lines.append("")
        lines.append("Totals:")
        lines.append(f"  processes: {len(claude_processes)}  CPU%: {total_cpu:.1f}  MEM%: {total_mem:.1f}")
    else:
        lines.append("(no Claude processes)")
    lines.append("")

    # --- 4) Recent file changes (worktrees) ---
    lines.append("--- 4) Recent file changes (worktrees) ---")
    if repo_changes:
        n = len(repo_changes)
        workers_list = ", ".join(active_workers) if active_workers else "—"
        lines.append(f"  {n} file(s) in last 10 min (workers: {workers_list})")
        sample = repo_changes[:10]
        for path in sample:
            lines.append("  " + path)
        if n > len(sample):
            lines.append(f"  ... and {n - len(sample)} more")
    elif workers and snapshot.health == "ok":
        lines.append("  (no changes in last 10 min)")
    else:
        lines.append("  (none)")
    lines.append("")

    lines.append("==============================================")
    return "\n".join(lines)


def _multiclaude_root() -> Path:
    return Path(os.environ.get("MULTICLAUDE_ROOT", os.path.expanduser("~/.multiclaude")))


def _tmux_session_for_repo(repo_name: str) -> str:
    """mc-<repo> with / and . replaced by -"""
    s = "mc-" + repo_name.replace("/", "-").replace(".", "-")
    return s


def _worker_list_with_status(repo_name: str) -> Tuple[List[str], Dict[str, str]]:
    """Run multiclaude worker list; return (worker names, name -> status).
    repo_name can be owner/repo; multiclaude expects short name (multiclaude_repo_key)."""
    workers: List[str] = []
    statuses: Dict[str, str] = {}
    mc_repo = multiclaude_repo_key(repo_name) if repo_name else ""
    if not mc_repo:
        return workers, statuses
    try:
        r = subprocess.run(
            ["multiclaude", "worker", "list", "--repo", mc_repo],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if r.returncode != 0:
            return workers, statuses
        skip = ("Workspace in", "No workers", "Create a worker", "repository '", "Workers in ")
        for line in (r.stdout or "").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if any(s in line for s in skip):
                continue
            if re.match(r"^-+$", line):
                continue
            if "NAME" in line and "STATUS" in line:
                continue
            # "  workspace ● running" or "nice-dolphin  ● running    work/..."
            if "●" in line and "running" in line:
                name = line.split()[0] if line.split() else ""
                if name and re.match(r"^[a-zA-Z0-9_-]+$", name):
                    workers.append(name)
                    statuses[name] = "running"
            # Table row when finished: "name  ○ done" (no ●)
            elif re.match(r"^[a-zA-Z0-9_-]+\s", line) and "●" not in line:
                name = line.split()[0]
                statuses[name] = "running" if "running" in line else "finished"
                if name and name not in workers:
                    workers.append(name)
            elif re.match(r"^[a-zA-Z0-9_-]+$", line):
                workers.append(line)
                statuses[line] = "unknown"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return workers, statuses


def _default_agents(repo_name: str) -> List[str]:
    """Tmux window names for repo session = default agents (supervisor, merge-queue, default)."""
    session = _tmux_session_for_repo(repo_name)
    try:
        r = subprocess.run(
            ["tmux", "list-windows", "-t", session, "-F", "#{window_name}"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if r.returncode != 0:
            return []
        return [w.strip() for w in (r.stdout or "").splitlines() if w.strip()]
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []


def _ps_aux_claude_lines() -> List[str]:
    """Run ps aux; return lines matching Claude/multiclaude (same as script)."""
    try:
        r = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if r.returncode != 0:
            return []
        out = r.stdout or ""
        return [line for line in out.splitlines() if "grep" not in line and ("claude" in line.lower() or "multiclaude" in line.lower())]
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []


def _parse_ps_line(line: str) -> Optional[Tuple[str, float, float, str]]:
    """Parse ps aux line: (pid, cpu_pct, mem_pct, command). ps aux has PID col 2, %CPU 3, %MEM 4; command can have spaces."""
    parts = line.split(None, 10)  # max 11 parts: first 10 are fixed, rest is command
    if len(parts) < 11:
        return None
    try:
        pid = parts[1]
        cpu = float(parts[2])
        mem = float(parts[3])
        cmd = parts[10]
        return (pid, cpu, mem, cmd)
    except (ValueError, IndexError):
        return None


def _agent_from_command(cmd: str) -> Optional[str]:
    """Classify process: daemon, supervisor, merge-queue, default, or named worker from prompts/NAME.md. None = skip (log/generic)."""
    if "multiclaude" in cmd and "daemon" in cmd:
        return "daemon"
    if "supervisor.md" in cmd:
        return "supervisor"
    if "merge-queue.md" in cmd:
        return "merge-queue"
    if "default.md" in cmd:
        return "default"
    m = re.search(r"\.multiclaude/prompts/([^/]+)\.md", cmd)
    if m:
        return m.group(1)
    if "worker" in cmd and "merge-queue" not in cmd:
        return None  # log process workers/xxx.log
    if "cat >>" in cmd and ".multiclaude/output" in cmd:
        return None  # (log) processes
    return None


def _claude_processes_real() -> List[Dict[str, Any]]:
    """Only real processes: default agents by name, daemon, named task workers. No log/generic 'worker'."""
    result: List[Dict[str, Any]] = []
    for line in _ps_aux_claude_lines():
        parsed = _parse_ps_line(line)
        if not parsed:
            continue
        pid, cpu, mem, cmd = parsed
        agent = _agent_from_command(cmd)
        if agent is None:
            continue
        result.append({"pid": pid, "cpu": cpu, "mem": mem, "agent": agent})
    return result


def _active_workers_and_repo_changes(repo_name: str, recent_mins: int = 10) -> Tuple[List[str], List[str]]:
    """Worktrees with files modified in last recent_mins; return (active worker names, relative paths)."""
    root = _multiclaude_root()
    mc_repo = multiclaude_repo_key(repo_name) if repo_name else ""
    wts = root / "wts" / mc_repo if mc_repo else root / "wts" / "__none__"
    if not wts.is_dir():
        return [], []
    active: List[str] = []
    changes: List[str] = []
    cutoff = time.time() - recent_mins * 60
    for agent_dir in wts.iterdir():
        if not agent_dir.is_dir():
            continue
        name = agent_dir.name
        count = 0
        for f in agent_dir.rglob("*"):
            if f.is_file():
                try:
                    if f.stat().st_mtime >= cutoff:
                        count += 1
                        try:
                            rel = f.relative_to(agent_dir)
                            changes.append(str(rel))
                        except ValueError:
                            pass
                except OSError:
                    pass
        if count > 0:
            active.append(name)
    return active, changes[:50]


def _worktree_disk_mb(repo_name: str) -> int:
    """Total disk usage of worktrees for repo in MB."""
    root = _multiclaude_root()
    mc_repo = multiclaude_repo_key(repo_name) if repo_name else ""
    wts = root / "wts" / mc_repo if mc_repo else root / "wts" / "__none__"
    if not wts.is_dir():
        return 0
    try:
        r = subprocess.run(
            ["du", "-sk", str(wts)],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if r.returncode != 0:
            return 0
        line = (r.stdout or "").strip().split(None, 1)
        if line:
            return int(line[0]) // 1024
    except (ValueError, FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return 0


def gather_status(
    project_id: str,
    state_root: str,
    repo_name: Optional[str] = None,
    scripts_dir: Optional[str] = None,
) -> StatusSnapshot:
    """
    Gather multiclaude status using only Python and CLI (multiclaude, tmux, ps).
    No shell scripts required. When repo_name is set, runs worker list, tmux, ps, worktree scan.
    """
    if not repo_name or not repo_name.strip():
        return StatusSnapshot(
            workers=[],
            issues_in_progress=[],
            liveness="unknown",
            health="stub",
            raw=None,
        )

    # Multiclaude health: daemon and repo inited (monitor must track and surface these)
    daemon_status_val = multiclaude_daemon_status()
    repo_inited_ok, multiclaude_err = is_repo_inited(repo_name)
    workers, worker_statuses = _worker_list_with_status(repo_name)
    default_agents = _default_agents(repo_name)
    active_workers, repo_changes = _active_workers_and_repo_changes(repo_name)
    claude_processes = _claude_processes_real()
    disk_mb = _worktree_disk_mb(repo_name)

    cpu_total = sum(p.get("cpu", 0) for p in claude_processes)
    mem_total = sum(p.get("mem", 0) for p in claude_processes)
    resource_usage: Optional[Dict[str, Any]] = None
    if claude_processes:
        resource_usage = {"cpu_pct": cpu_total, "mem_pct": mem_total, "disk_mb": disk_mb}
    process_count = len(claude_processes)
    processes_summary = f"{process_count} Claude process(es)" if process_count else ""
    liveness = f"LIVENESS: {len(active_workers)} active of {len(workers)} workers; {process_count} Claude process(es); CPU {cpu_total:.1f}% MEM {mem_total:.1f}%; disk {disk_mb}MB"
    if len(liveness) > 200:
        liveness = liveness[:200]

    # Issues in progress: list_workspace_replies is Python (reads inbox dir)
    replies = list_workspace_replies(repo_name)
    skip_prefixes = ("No workspace", "Path:", "Total:", "---", "(read error")
    issues_in_progress = [r for r in replies[:30] if r.strip() and not any(r.startswith(p) for p in skip_prefixes)]

    # Health: ok only when daemon running and repo inited; otherwise surface daemon_down or repo_not_inited
    if daemon_status_val != "running":
        health = "daemon_down"
    elif not repo_inited_ok:
        health = "repo_not_inited"
    elif workers or default_agents or process_count or issues_in_progress:
        health = "ok"
    else:
        health = "stub"

    return StatusSnapshot(
        workers=workers,
        issues_in_progress=issues_in_progress,
        liveness=liveness,
        health=health,
        raw=None,
        active_workers=active_workers,
        processes_summary=processes_summary,
        resource_usage=resource_usage,
        repo_changes=repo_changes,
        default_agents=default_agents,
        claude_processes=claude_processes,
        worker_statuses=worker_statuses,
        daemon_status=daemon_status_val,
        repo_inited=repo_inited_ok,
        multiclaude_error=multiclaude_err,
    )


# Legacy: parser for script output kept for tests / optional fallback
def _parse_check_worker_status_output(status_out: str) -> Dict[str, Any]:
    """Parse check-worker-status.sh key=value output (used by tests; monitor no longer runs script)."""
    out: Dict[str, Any] = {
        "active_workers": [],
        "processes_summary": "",
        "resource_usage": None,
        "repo_changes": [],
        "liveness": "unknown",
        "default_agents": [],
        "claude_processes": [],
        "worker_statuses": {},
    }
    if not status_out or status_out == "stub":
        return out
    resource: Dict[str, Any] = {}
    process_count: Optional[int] = None
    for line in (status_out or "").splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("DEFAULT_AGENTS="):
            val = line.split("=", 1)[1].strip()
            out["default_agents"] = [a.strip() for a in val.split(",") if a.strip()]
        elif line.startswith("ACTIVE_WORKERS="):
            val = line.split("=", 1)[1].strip()
            out["active_workers"] = [w.strip() for w in val.split(",") if w.strip()]
        elif line.startswith("WORKER_STATUS="):
            val = line.split("=", 1)[1].strip()
            parts = val.split(",", 1)
            if len(parts) >= 2:
                out["worker_statuses"][parts[0].strip()] = parts[1].strip()
        elif line.startswith("PROCESS_COUNT="):
            try:
                process_count = int(line.split("=", 1)[1].strip())
            except ValueError:
                pass
        elif line.startswith("CPU_PCT="):
            try:
                resource["cpu_pct"] = float(line.split("=", 1)[1].strip())
            except ValueError:
                pass
        elif line.startswith("MEM_PCT="):
            try:
                resource["mem_pct"] = float(line.split("=", 1)[1].strip())
            except ValueError:
                pass
        elif line.startswith("DISK_MB="):
            try:
                resource["disk_mb"] = int(line.split("=", 1)[1].strip())
            except ValueError:
                pass
        elif line.startswith("REPO_CHANGES="):
            val = line.split("=", 1)[1].strip()
            out["repo_changes"] = [p.strip() for p in val.split(",") if p.strip()]
        elif line.startswith("CLAUDE_PROCESS="):
            val = line.split("=", 1)[1].strip()
            parts = [p.strip() for p in val.split(",", 3)]
            if len(parts) >= 4:
                try:
                    out["claude_processes"].append({
                        "pid": parts[0],
                        "cpu": float(parts[1]),
                        "mem": float(parts[2]),
                        "agent": parts[3],
                    })
                except ValueError:
                    pass
        elif line.startswith("LIVENESS:"):
            out["liveness"] = line
    if process_count is not None:
        out["processes_summary"] = f"{process_count} Claude process(es)"
    if resource:
        out["resource_usage"] = resource
    return out

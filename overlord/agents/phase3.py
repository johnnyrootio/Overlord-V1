"""
Phase 3 (Issue Emitter): create GitHub issues from work graph.
C12: Parses workgraph.yml; when gh CLI and repo are available creates real issues
via gh; otherwise writes issues.json with stub/placeholder data for tests.
"""
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from overlord.repo_utils import repo_url_to_owner_repo

try:
    import yaml
except ImportError:
    yaml = None


def is_gh_available() -> bool:
    """True if gh CLI is available and authenticated."""
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            timeout=10,
            text=True,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _load_workgraph(path: str) -> Optional[Dict[str, Any]]:
    """Load and return work graph YAML, or None if missing/invalid."""
    if not path or not path.strip():
        return None
    p = Path(path)
    if not p.is_file():
        return None
    if not yaml:
        return None
    try:
        with open(p, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data if isinstance(data, dict) and "waves" in data else None
    except Exception:
        return None


def _tasks_in_order(workgraph: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Flatten waves into task list (wave order, then task order). Each task gets wave_index and task fields."""
    out: List[Dict[str, Any]] = []
    waves = workgraph.get("waves") or []
    for wi, wave in enumerate(waves):
        wave_id = wave.get("id") or f"wave{wi}"
        tasks = wave.get("tasks") or []
        for t in tasks:
            task = dict(t)
            task["_wave_index"] = wi
            task["_wave_id"] = wave_id
            task.setdefault("id", f"T{wi}.{len(out) + 1}")
            task.setdefault("title", "Untitled task")
            task.setdefault("depends_on", [])
            task.setdefault("type", "implementation")
            task.setdefault("area", "general")
            task.setdefault("risk", "low")
            out.append(task)
    return out


def _build_labels(task: Dict[str, Any]) -> List[str]:
    """Build label list per GITHUB-ISSUE-FORMAT-GUIDANCE."""
    wave_index = task.get("_wave_index", 0)
    area = (task.get("area") or "general").strip().lower().replace(" ", "-")
    risk = (task.get("risk") or "low").strip().lower()
    task_type = (task.get("type") or "implementation").strip().lower()
    labels = [
        f"wave:{wave_index}",
        f"area:{area}",
        f"risk:{risk}",
        f"type:{task_type}",
    ]
    if task_type == "test":
        layer = (task.get("layer") or "unit").strip().lower()
        labels.append(f"layer:{layer}")
    if task_type == "implementation" and task.get("tdd_required"):
        labels.append("tdd:required")
    return labels


def _build_body(task: Dict[str, Any], task_id_to_issue_number: Dict[str, int]) -> str:
    """Build issue body (Markdown) with header, Depends on #N, and sections from task."""
    lines = []
    task_type = (task.get("type") or "implementation").strip().capitalize()
    wave_index = task.get("_wave_index", 0)
    # Header
    lines.append(f"**Type**: {task_type}")
    if (task.get("type") or "").strip().lower() == "test":
        layer = (task.get("layer") or "unit").strip().capitalize()
        lines.append(f"**Layer**: {layer}")
    lines.append(f"**Wave**: {wave_index}")
    deps = task.get("depends_on") or []
    issue_nums = [task_id_to_issue_number[d] for d in deps if d in task_id_to_issue_number]
    if issue_nums:
        lines.append("**Depends on**: " + ", ".join(f"#{n}" for n in sorted(issue_nums)))
    lines.append("")
    # Title as section
    title = task.get("title") or "Task"
    lines.append(f"## {title}")
    lines.append("")
    # Description / goal
    if task.get("primary_goal"):
        lines.append("### Primary Goal")
        lines.append("")
        lines.append(task.get("primary_goal", "").strip())
        lines.append("")
    if task.get("description") and not task.get("primary_goal"):
        lines.append("### Description")
        lines.append("")
        lines.append(task.get("description", "").strip())
        lines.append("")
    if task.get("implementation_guidance"):
        lines.append("### Implementation Guidance")
        lines.append("")
        lines.append(task.get("implementation_guidance", "").strip())
        lines.append("")
    if task.get("test_specification"):
        lines.append("### Test Specification")
        lines.append("")
        lines.append(task.get("test_specification", "").strip())
        lines.append("")
    if task.get("access_restriction"):
        lines.append("### Access Restrictions")
        lines.append("")
        lines.append(task.get("access_restriction", "").strip())
        lines.append("")
    if task.get("validation"):
        lines.append("### Validation")
        lines.append("")
        lines.append(task.get("validation", "").strip())
        lines.append("")
    # Definition of Done
    lines.append("### Definition of Done")
    lines.append("")
    lines.append("- [ ] `./scripts/check.sh` passes")
    lines.append("")
    return "\n".join(lines)


def _ensure_labels(repo: str, labels: List[str]) -> None:
    """Ensure labels exist in repo (create if missing). Ignores errors."""
    for label in labels:
        try:
            # gh label create "wave:0" --repo owner/repo  (fails if exists; use create or list)
            subprocess.run(
                ["gh", "label", "create", label, "--repo", repo, "--force"],
                capture_output=True,
                timeout=5,
            )
        except Exception:
            pass


def _gh_create_issue(
    repo: str,
    title: str,
    body: str,
    labels: List[str],
) -> Optional[int]:
    """Create one issue via gh; return issue number or None."""
    try:
        cmd = [
            "gh", "issue", "create",
            "--repo", repo,
            "--title", title,
            "--body", body,
        ]
        for lb in labels:
            cmd.extend(["--label", lb])
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=30,
            text=True,
        )
        if result.returncode != 0:
            return None
        # Output is typically a URL: https://github.com/owner/repo/issues/3
        out = (result.stdout or result.stderr or "").strip()
        m = re.search(r"/issues/(\d+)", out)
        if m:
            return int(m.group(1))
        m = re.search(r"#(\d+)", out)
        if m:
            return int(m.group(1))
        return None
    except Exception:
        return None


def emit_issues(
    work_graph_path: str,
    repo_name: Optional[str],
    state_root: str,
    project_id: str,
    repo_url: Optional[str] = None,
) -> List[str]:
    """
    Emit GitHub issues from work graph. Returns list of issue numbers or identifiers.

    - If workgraph.yml exists and is valid, parses it and builds one issue per task.
    - When gh CLI is available and repo is set (repo_url or repo_name), creates
      real issues via gh and persists issue numbers to issues.json.
    - Otherwise writes issues.json with stub/placeholder data (for tests).
    """
    project_dir = Path(state_root) / "projects" / project_id
    project_dir.mkdir(parents=True, exist_ok=True)
    issues_file = project_dir / "issues.json"

    repo = repo_url_to_owner_repo(repo_url) if repo_url else None
    if not repo and repo_name and "/" in str(repo_name):
        repo = repo_name.strip()
    elif not repo and repo_name:
        # repo_name might be "owner/repo" or just "repo" (we can't create without owner)
        repo = repo_name.strip() if repo_name else None

    workgraph = _load_workgraph(work_graph_path)
    if not workgraph:
        # Stub: no work graph
        stub_issues = [
            {"task_id": "stub-1", "number": 1, "title": "stub-issue-1"},
            {"task_id": "stub-2", "number": 2, "title": "stub-issue-2"},
        ]
        with open(issues_file, "w", encoding="utf-8") as f:
            json.dump(stub_issues, f, indent=2)
        return [str(i["number"]) for i in stub_issues]

    tasks = _tasks_in_order(workgraph)
    if not tasks:
        stub_issues = [{"task_id": "stub-1", "number": 1, "title": "No tasks"}]
        with open(issues_file, "w", encoding="utf-8") as f:
            json.dump(stub_issues, f, indent=2)
        return ["1"]

    use_gh = is_gh_available() and bool(repo)
    task_id_to_number: Dict[str, int] = {}
    issues_payload: List[Dict[str, Any]] = []

    if use_gh:
        all_labels = set()
        for t in tasks:
            all_labels.update(_build_labels(t))
        _ensure_labels(repo, list(all_labels))

    for task in tasks:
        task_id = task.get("id") or "unknown"
        title = (task.get("title") or "Task").strip()
        body = _build_body(task, task_id_to_number)
        labels = _build_labels(task)

        if use_gh:
            number = _gh_create_issue(repo, title, body, labels)
            if number is not None:
                task_id_to_number[task_id] = number
                issues_payload.append({"task_id": task_id, "number": number, "title": title})
            else:
                # Fallback: assign placeholder so Depends on still works
                placeholder = len(issues_payload) + 1
                task_id_to_number[task_id] = placeholder
                issues_payload.append({"task_id": task_id, "number": placeholder, "title": title})
        else:
            placeholder = len(issues_payload) + 1
            task_id_to_number[task_id] = placeholder
            issues_payload.append({"task_id": task_id, "number": placeholder, "title": title})

    with open(issues_file, "w", encoding="utf-8") as f:
        json.dump(issues_payload, f, indent=2)

    return [str(i["number"]) for i in issues_payload]

"""
Integration test: monitor (gather_status) against a real Multiclaude deployment.

- Creates a repo (or uses OVERLORD_MONITOR_TEST_REPO), Multiclaude inits it.
- Creates contrived issues with real programming tasks (see monitor_test_issues.yaml).
- Dispatches workers, waits, then asserts gather_status sees workers, health, and
  optionally active_workers, processes, resource_usage, repo_changes.
- Leaves the repo in place for further monitor iteration and unit testing.

Prerequisites (skip if missing): gh (authenticated), multiclaude daemon running,
OVERLORD scripts dir, ANTHROPIC_API_KEY.
"""
import os
import subprocess
import time
from pathlib import Path

import pytest

from overlord.agents.multiclaude_dispatch import create_worker
from overlord.monitor import gather_status

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
_FIXTURE_PATH = Path(__file__).resolve().parent / "monitor_test_issues.yaml"


def _has_gh_auth() -> bool:
    try:
        r = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return r.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _multiclaude_running() -> bool:
    try:
        r = subprocess.run(
            ["multiclaude", "daemon", "status"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return r.returncode == 0 and "running" in (r.stdout or "").lower()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _require_prereqs():
    if not _has_gh_auth():
        pytest.skip("gh CLI not found or not authenticated; run gh auth login")
    if not _multiclaude_running():
        pytest.skip("multiclaude daemon not running; run multiclaude start")
    if not _SCRIPTS_DIR.is_dir() or not (_SCRIPTS_DIR / "check-worker-status.sh").exists():
        pytest.skip("Overlord scripts dir or check-worker-status.sh not found")
    if not os.environ.get("ANTHROPIC_API_KEY") and not os.environ.get("CLAUDE_CODE_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY or CLAUDE_CODE_API_KEY required for real workers")


def _get_gh_user() -> str:
    r = subprocess.run(
        ["gh", "api", "user", "--jq", ".login"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if r.returncode != 0 or not (r.stdout or "").strip():
        pytest.skip("Could not determine gh user (gh api user)")
    return r.stdout.strip()


def _repo_exists(owner: str, repo: str) -> bool:
    r = subprocess.run(
        ["gh", "repo", "view", f"{owner}/{repo}"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    return r.returncode == 0


def _create_repo(owner: str, name: str) -> str:
    # Empty repo (no --source) so multiclaude can init and workers can push
    r = subprocess.run(
        ["gh", "repo", "create", name, "--public"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if r.returncode != 0:
        pytest.fail(f"gh repo create failed: {r.stderr or r.stdout}")
    return f"{owner}/{name}"


def _seed_repo_with_initial_commit(owner_repo: str, clone_url: str) -> None:
    """Push one commit so repo has valid HEAD (multiclaude needs it for worktrees)."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        r = subprocess.run(
            ["git", "clone", clone_url, tmp],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if r.returncode != 0:
            pytest.fail(f"git clone failed: {r.stderr or r.stdout}")
        readme = Path(tmp) / "README.md"
        readme.write_text("# Overlord monitor test repo\n\nInitial commit so multiclaude can create worktrees.\n")
        for cmd in [
            ["git", "-C", tmp, "add", "README.md"],
            ["git", "-C", tmp, "commit", "-m", "Initial commit"],
        ]:
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if out.returncode != 0:
                pytest.fail(f"Seed commit failed: {out.stderr or out.stdout}")
        out = subprocess.run(
            ["git", "-C", tmp, "push", "-u", "origin", "HEAD:main"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if out.returncode != 0:
            pytest.fail(f"Seed push failed: {out.stderr or out.stdout}")


def _multiclaude_repo_inited(repo_name: str) -> bool:
    r = subprocess.run(
        ["multiclaude", "repo", "list"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if r.returncode != 0:
        return False
    return repo_name in (r.stdout or "")


def _multiclaude_repo_init(repo_name: str, clone_url: str) -> None:
    r = subprocess.run(
        ["multiclaude", "repo", "init", clone_url, repo_name],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if r.returncode != 0:
        pytest.fail(f"multiclaude repo init failed: {r.stderr or r.stdout}")


def _load_issue_fixtures():
    if not _FIXTURE_PATH.is_file():
        return [
            ("[Monitor test] Add src/math.py", "Add src/math.py with add(a,b) returning a+b. Create src/ if needed."),
            ("[Monitor test] Add tests/test_math.py", "Add tests/test_math.py testing add() with pytest."),
        ]
    import yaml
    with open(_FIXTURE_PATH) as f:
        data = yaml.safe_load(f)
    issues = data.get("issues", [])
    return [(i["title"], i.get("body", "").strip()) for i in issues]


def _list_open_monitor_test_issues(owner_repo: str, limit: int = 2) -> list:
    """List open issues with '[Monitor test]' in title; return [(num, title), ...]."""
    r = subprocess.run(
        ["gh", "issue", "list", "--repo", owner_repo, "--state", "open", "--limit", str(limit), "--json", "number,title"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if r.returncode != 0:
        return []
    try:
        import json
        data = json.loads(r.stdout or "[]")
        return [(item["number"], item["title"]) for item in data if "[Monitor test]" in (item.get("title") or "")]
    except Exception:
        return []


def _create_issues(owner_repo: str, issues_spec) -> list:
    created = []
    for title, body in issues_spec:
        r = subprocess.run(
            ["gh", "issue", "create", "--repo", owner_repo, "--title", title, "--body", body],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if r.returncode != 0:
            continue
        line = (r.stdout or "").strip()
        num = None
        for part in line.replace("#", " ").split():
            if part.isdigit():
                num = int(part)
                break
        if num is not None:
            created.append((num, title))
    return created


@pytest.mark.integration
@pytest.mark.real_multiclaude
def test_monitor_gather_status_real_multiclaude(tmp_path):
    """
    Create repo (or use OVERLORD_MONITOR_TEST_REPO), init Multiclaude, create issues
    with programming tasks, dispatch workers, then assert gather_status sees workers
    and health. Repo is left in place.
    """
    _require_prereqs()
    owner = _get_gh_user()
    scripts_dir = str(_SCRIPTS_DIR)

    # Single test repo: OVERLORD_MONITOR_TEST_REPO or owner/overlord-monitor-test (create only if missing)
    existing = os.environ.get("OVERLORD_MONITOR_TEST_REPO", "").strip()
    if existing and "/" in existing:
        owner_repo = existing
        if not _repo_exists(*owner_repo.split("/", 1)):
            pytest.skip(f"OVERLORD_MONITOR_TEST_REPO={existing} repo not found on GitHub")
    else:
        name = "overlord-monitor-test"
        owner_repo = f"{owner}/{name}"
        if not _repo_exists(owner, name):
            _create_repo(owner, name)
            r = subprocess.run(
                ["gh", "repo", "view", owner_repo, "--json", "url", "-q", ".url"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if r.returncode != 0 or not (r.stdout or "").strip():
                pytest.fail("Could not get clone URL")
            clone_url = r.stdout.strip()
            if not clone_url.endswith(".git"):
                clone_url = clone_url.rstrip("/") + ".git"
            _seed_repo_with_initial_commit(owner_repo, clone_url)
        if not _multiclaude_repo_inited(owner_repo):
            r = subprocess.run(
                ["gh", "repo", "view", owner_repo, "--json", "url", "-q", ".url"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            clone_url = (r.stdout or "").strip()
            if clone_url and not clone_url.endswith(".git"):
                clone_url = clone_url.rstrip("/") + ".git"
            if clone_url:
                _multiclaude_repo_init(owner_repo, clone_url)
        time.sleep(2)

    if not _multiclaude_repo_inited(owner_repo):
        pytest.skip("multiclaude repo init did not register repo")

    # Contrived issues: reuse open "[Monitor test]" issues if any, else create from fixture
    issues_spec = _load_issue_fixtures()
    created_issues = _list_open_monitor_test_issues(owner_repo, limit=2)
    if not created_issues:
        created_issues = _create_issues(owner_repo, issues_spec[:2])
    if not created_issues:
        pytest.skip("Could not find or create GitHub issues for monitor test")

    # Dispatch workers for each issue
    for num, title in created_issues:
        task = f"Issue #{num}: {title}"
        ok = create_worker(owner_repo, task, scripts_dir=scripts_dir)
        if not ok:
            pytest.skip("create_worker failed (script or multiclaude)")
        time.sleep(18)

    # Monitor: gather_status
    state_root = str(tmp_path / "state")
    os.makedirs(state_root, exist_ok=True)
    project_id = "monitor-test"
    snapshot = gather_status(project_id, state_root, repo_name=owner_repo, scripts_dir=scripts_dir)

    assert isinstance(snapshot.workers, list), "workers should be a list"
    assert len(snapshot.workers) >= 1, f"expected at least one worker, got {snapshot.workers}"
    assert snapshot.health == "ok", f"expected health ok, got {snapshot.health}"

    # Optional: monitor can report active workers, processes, resources, repo changes
    assert hasattr(snapshot, "active_workers")
    assert hasattr(snapshot, "processes_summary")
    assert hasattr(snapshot, "resource_usage")
    assert hasattr(snapshot, "repo_changes")

    # Repo is left in place for further testing; issues remain open unless closed manually.

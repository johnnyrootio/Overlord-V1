"""
Repo resolution for the Test Harness: create (gh) or use repo_url; unique name per run.

Run manifest (run_id, repo, repo_created) is produced by the capture layer; this module
resolves the repo identifier and URL for a scenario. See roadmap/features/autonomous-test-bench.md §3.3.
"""
import re
import subprocess
import time
from dataclasses import dataclass
from typing import Optional

from test_harness.scenario import Scenario


@dataclass
class ResolvedRepo:
    """Result of resolving the scenario's repo for a run."""

    identifier: str  # owner/name or full URL
    repo_url: str
    repo_created: bool


def _generate_run_id() -> str:
    """Unique run id (timestamp-based for readability)."""
    return f"run-{int(time.time())}"


def _gh_repo_create(repo_name: str) -> str:
    """
    Create a new public repo via gh. Returns repo URL (https://github.com/owner/name).
    Raises RuntimeError if gh fails.
    """
    out = subprocess.run(
        ["gh", "repo", "create", repo_name, "--public", "--description", "Overlord Test Harness run"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if out.returncode != 0:
        raise RuntimeError(f"gh repo create failed: {out.stderr or out.stdout or 'unknown'}")
    # gh repo create prints the URL on success
    url = (out.stdout or "").strip() or (out.stderr or "").strip()
    if not url:
        # Fallback: resolve via gh repo view
        view = subprocess.run(
            ["gh", "repo", "view", repo_name, "--json", "url", "-q", ".url"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if view.returncode == 0 and view.stdout:
            url = view.stdout.strip()
    if not url:
        raise RuntimeError("gh repo create succeeded but could not get repo URL")
    return url


def _url_to_identifier(repo_url: str) -> str:
    """Normalize URL to owner/name."""
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$", repo_url.strip())
    if m:
        return f"{m.group(1)}/{m.group(2)}"
    return repo_url


def resolve_repo(
    scenario: Scenario,
    run_id: Optional[str] = None,
) -> ResolvedRepo:
    """
    Resolve repo for this run: use scenario.repo_url if set; otherwise create via gh
    with a unique name (scenario.repo_name + run_id). Returns ResolvedRepo(identifier, repo_url, repo_created).
    """
    run_id = run_id or _generate_run_id()
    if scenario.repo_url:
        identifier = _url_to_identifier(scenario.repo_url)
        return ResolvedRepo(
            identifier=identifier,
            repo_url=scenario.repo_url.rstrip("/").replace(".git", ""),
            repo_created=False,
        )
    if not scenario.repo_name:
        raise ValueError("Scenario has no repo_url and no repo_name")
    if not scenario.repo_create:
        # Use repo_name as-is (must exist); resolve to URL via gh
        view = subprocess.run(
            ["gh", "repo", "view", scenario.repo_name, "--json", "url", "-q", ".url"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if view.returncode != 0:
            raise RuntimeError(f"Repo {scenario.repo_name} not found: {view.stderr or view.stdout}")
        url = view.stdout.strip()
        return ResolvedRepo(
            identifier=_url_to_identifier(url),
            repo_url=url,
            repo_created=False,
        )
    unique_name = f"{scenario.repo_name}-{run_id}"
    url = _gh_repo_create(unique_name)
    return ResolvedRepo(
        identifier=_url_to_identifier(url),
        repo_url=url,
        repo_created=True,
    )

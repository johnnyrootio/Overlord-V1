"""
Test-repo README: write a README in the test repo describing the run.

When the Test Harness creates a repo (or at the start of a run), it writes a README
with: test-harness-driven statement, essence of the test, run context.
See roadmap/features/autonomous-test-bench.md §3.4.
"""
import base64
import subprocess
from datetime import datetime, timezone
from typing import Optional


def write_repo_readme(
    repo_identifier: str,
    goals_or_essence: str,
    run_id: str,
    scenario_name: Optional[str] = None,
) -> None:
    """
    Write README.md to the repo via gh api. repo_identifier is owner/name.
    goals_or_essence: e.g. "Trivial todo list" or scenario goals.
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    parts = [
        "# Test Harness Run",
        "",
        "This repository was created and used by the **Overlord Test Harness** for an end-to-end run.",
        "",
        "## Test",
        "",
        goals_or_essence[:500] or "(No description)",
        "",
        "## Run context",
        "",
        f"- **Run id:** {run_id}",
        f"- **Started:** {now}",
    ]
    if scenario_name:
        parts.append(f"- **Scenario:** {scenario_name}")
    parts.append("")
    body = "\n".join(parts)
    payload = base64.b64encode(body.encode("utf-8")).decode("ascii")

    # gh api repos/OWNER/REPO/contents/README.md -f content=... -f message="..."
    owner, name = repo_identifier.split("/", 1)
    out = subprocess.run(
        [
            "gh",
            "api",
            f"repos/{owner}/{name}/contents/README.md",
            "-X",
            "PUT",
            "-f",
            f"content={payload}",
            "-f",
            "message=Add Test Harness README",
        ],
        capture_output=True,
        text=True,
        timeout=15,
    )
    if out.returncode != 0:
        raise RuntimeError(f"Failed to write README: {out.stderr or out.stdout}")

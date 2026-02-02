"""
GitHub CLI helpers: default owner, repo exists, create repo.
Used in Phase 0 to check or create the project repo when gh is authed.
Creates repos with an initial commit so multiclaude repo init (worktree) succeeds.
"""
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple


def get_gh_default_owner() -> Optional[str]:
    """Return the authenticated GitHub user login (gh api user -q .login)."""
    try:
        r = subprocess.run(
            ["gh", "api", "user", "-q", ".login"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if r.returncode == 0 and r.stdout:
            return r.stdout.strip()
        return None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def gh_repo_exists(owner: str, repo: str) -> bool:
    """True if gh repo view owner/repo succeeds."""
    try:
        r = subprocess.run(
            ["gh", "repo", "view", f"{owner}/{repo}"],
            capture_output=True,
            timeout=10,
        )
        return r.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def gh_repo_create(owner: str, repo: str, public: bool = True) -> Optional[str]:
    """Create repo with an initial commit via gh repo create --source . --push.
    An empty repo would break multiclaude repo init (worktree needs HEAD). Returns URL or None."""
    try:
        with tempfile.TemporaryDirectory(prefix="overlord_repo_") as tmp:
            path = Path(tmp)
            (path / "README.md").write_text(f"# {repo}\n", encoding="utf-8")
            env = os.environ.copy()
            env.setdefault("GIT_AUTHOR_NAME", "Overlord")
            env.setdefault("GIT_AUTHOR_EMAIL", "overlord@local")
            env.setdefault("GIT_COMMITTER_NAME", "Overlord")
            env.setdefault("GIT_COMMITTER_EMAIL", "overlord@local")
            r = subprocess.run(
                ["git", "init"],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=10,
                env=env,
            )
            if r.returncode != 0:
                return None
            subprocess.run(
                ["git", "add", "README.md"],
                cwd=path,
                capture_output=True,
                timeout=10,
                env=env,
            )
            r = subprocess.run(
                ["git", "commit", "-m", "Initial commit"],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=10,
                env=env,
            )
            if r.returncode != 0:
                return None
            cmd = [
                "gh", "repo", "create", f"{owner}/{repo}",
                "--public" if public else "--private",
                "--source", str(path),
                "--push",
            ]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=60, env=env)
            if r.returncode != 0:
                return None
            return f"https://github.com/{owner}/{repo}"
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None

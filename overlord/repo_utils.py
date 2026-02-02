"""
Shared repo helpers: GitHub URL to owner/repo for gh and multiclaude.
"""
import re
from typing import Optional


def repo_url_to_owner_repo(repo_url: Optional[str]) -> Optional[str]:
    """Convert GitHub URL to owner/repo. Returns None if not a GitHub URL."""
    if not repo_url or not repo_url.strip():
        return None
    url = repo_url.strip().rstrip("/")
    m = re.match(r"https?://github\.com/([^/]+)/([^/?#]+)", url)
    if m:
        return f"{m.group(1)}/{m.group(2)}"
    m = re.match(r"git@github\.com:([^/]+)/([^/]+?)(\.git)?$", url)
    if m:
        return f"{m.group(1)}/{m.group(2)}"
    if "/" in url and " " not in url and not url.startswith("http"):
        return url
    return None

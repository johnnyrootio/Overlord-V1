#!/usr/bin/env python3
"""
Detect file changes in multiclaude local project worktrees.

Usage:
  python scripts/detect-worktree-changes.py [--recent-mins 10] [REPO]
  # REPO optional: owner/repo (e.g. myorg/trivial-todo-app) or short name (e.g. trivial-todo-app)
  # If omitted, lists wts/ contents and scans all repos under wts.

Worktree path: MULTICLAUDE_ROOT or ~/.multiclaude, then wts/<repo>.
Multiclaude may use short name (e.g. trivial-todo-app) or owner/repo (e.g. owner/repo);
this script tries the path you pass and also lists wts/ so you can see actual layout.
"""
import argparse
import os
import sys
import time
from pathlib import Path


def multiclaude_root() -> Path:
    return Path(os.environ.get("MULTICLAUDE_ROOT", os.path.expanduser("~/.multiclaude")))


def repo_key(repo: str) -> str:
    """Short name: owner/repo -> repo."""
    if not (repo or "").strip():
        return ""
    s = repo.strip()
    return s.split("/")[-1] if "/" in s else s


def scan_recent_changes(wts_path: Path, recent_mins: int):
    """Yield (worker_dir_name, rel_path, mtime) for files modified in last recent_mins."""
    if not wts_path.is_dir():
        return
    cutoff = time.time() - recent_mins * 60
    for agent_dir in sorted(wts_path.iterdir()):
        if not agent_dir.is_dir():
            continue
        name = agent_dir.name
        for f in agent_dir.rglob("*"):
            if f.is_file():
                try:
                    mtime = f.stat().st_mtime
                    if mtime >= cutoff:
                        try:
                            rel = f.relative_to(agent_dir)
                            yield name, str(rel), mtime
                        except ValueError:
                            pass
                except OSError:
                    pass


def main() -> int:
    parser = argparse.ArgumentParser(description="Detect file changes in multiclaude worktrees.")
    parser.add_argument(
        "repo",
        nargs="?",
        help="Repo: owner/repo or short name (e.g. trivial-todo-app). If omitted, list wts/ and scan all.",
    )
    parser.add_argument(
        "--recent-mins",
        type=int,
        default=10,
        metavar="N",
        help="Consider files modified in last N minutes (default: 10).",
    )
    parser.add_argument(
        "--list-only",
        action="store_true",
        help="Only list wts/ contents and exit (no change scan).",
    )
    args = parser.parse_args()

    root = multiclaude_root()
    wts_base = root / "wts"

    print(f"MULTICLAUDE_ROOT / wts: {root} / wts")
    print(f"Full path: {wts_base}")
    if not wts_base.is_dir():
        print("(wts directory does not exist)", file=sys.stderr)
        return 1

    # List what's under wts/ so we know actual layout
    entries = sorted(wts_base.iterdir())
    print(f"Contents of wts/: {[e.name for e in entries]}")
    if args.list_only:
        for e in entries:
            if e.is_dir():
                sub = list(e.iterdir()) if e.is_dir() else []
                print(f"  {e.name}/ -> {[s.name for s in sub[:15]]}{'...' if len(sub) > 15 else ''}")
        return 0

    if not args.repo:
        # No repo given: scan every top-level dir under wts/
        print(f"\nScanning all repos under wts/ (recent_mins={args.recent_mins})")
        total = 0
        for d in entries:
            if not d.is_dir():
                continue
            for worker, rel, mtime in scan_recent_changes(d, args.recent_mins):
                total += 1
                age_mins = (time.time() - mtime) / 60
                print(f"  [{d.name}] {worker}/{rel}  (mtime {age_mins:.1f} min ago)")
        if total == 0:
            print("  (no files modified in last {} min)".format(args.recent_mins))
        return 0

    # Repo given: try as literal path (owner/repo = two segments), then as short name
    repo = args.repo.strip()
    candidates = [
        wts_base / repo,           # literal: owner/repo or short
        wts_base / repo_key(repo), # short name only
    ]
    wts_path = None
    for c in candidates:
        if c.is_dir():
            wts_path = c
            break
    if not wts_path:
        print(f"Repo path not found. Tried: {[str(c) for c in candidates]}", file=sys.stderr)
        return 1

    print(f"\nScanning: {wts_path} (recent_mins={args.recent_mins})")
    count = 0
    for worker, rel, mtime in scan_recent_changes(wts_path, args.recent_mins):
        count += 1
        age_mins = (time.time() - mtime) / 60
        print(f"  {worker}/{rel}  (mtime {age_mins:.1f} min ago)")
    if count == 0:
        print("  (no files modified in last {} min)".format(args.recent_mins))
    return 0


if __name__ == "__main__":
    sys.exit(main())

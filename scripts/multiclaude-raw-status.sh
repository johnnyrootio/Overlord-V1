#!/usr/bin/env bash
# Raw multiclaude status: default agents (supervisor, merge-queue, workspace), workers,
# and Claude Code processes with CPU/MEM. Uses multiclaude CLI and tmux/ps.
# Usage: ./scripts/multiclaude-raw-status.sh <repo-name>
# Example: ./scripts/multiclaude-raw-status.sh johnnyrootio/overlord-monitor-test-1769830395

set -euo pipefail

REPO_NAME="${1:-}"
if [[ -z "$REPO_NAME" ]]; then
  echo "usage: $0 <repo-name>" >&2
  echo "  repo-name: e.g. owner/repo or robotic-barista" >&2
  exit 2
fi

# Tmux session: mc-<repo> with / and . replaced by -
TMUX_SESSION="mc-${REPO_NAME//\//-}"
TMUX_SESSION="${TMUX_SESSION//./-}"

echo "=============================================="
echo "MULTICLAUDE RAW STATUS: $REPO_NAME"
echo "=============================================="
echo ""

echo "--- 1) multiclaude repo list ---"
multiclaude repo list 2>&1 || true
echo ""

echo "--- 2) multiclaude worker list --repo $REPO_NAME ---"
multiclaude worker list --repo "$REPO_NAME" 2>&1 || true
echo ""

echo "--- 3) Default agents (tmux windows in session $TMUX_SESSION) ---"
if tmux has-session -t "$TMUX_SESSION" 2>/dev/null; then
  tmux list-windows -t "$TMUX_SESSION" -F "#{window_index}: #{window_name}" 2>/dev/null || true
else
  echo "(tmux session not found)"
fi
echo ""

echo "--- 4) Claude Code processes (CPU, MEM) ---"
if ps aux 2>/dev/null | grep -E '[Cc]laude' | grep -v grep >/dev/null; then
  echo "PID       %CPU  %MEM  COMMAND"
  ps aux 2>/dev/null | grep -E '[Cc]laude' | grep -v grep | awk '{ printf "%-9s %5s %5s  ", $2, $3, $4; for(i=11;i<=NF;i++) printf "%s ", $i; print "" }'
  echo ""
  echo "Totals:"
  ps aux 2>/dev/null | grep -E '[Cc]laude' | grep -v grep | awk '{ cpu+=$3; mem+=$4; n++ } END { printf "  processes: %d  CPU%%: %.1f  MEM%%: %.1f\n", n, cpu, mem }'
else
  echo "(no Claude processes found)"
fi
echo ""

echo "--- 5) Worktrees disk usage (~/.multiclaude/wts/$REPO_NAME) ---"
WTS="${MULTICLAUDE_ROOT:-$HOME/.multiclaude}/wts/$REPO_NAME"
if [[ -d "$WTS" ]]; then
  du -sh "$WTS" 2>/dev/null || true
  echo "Per-agent:"
  for d in "$WTS"/*; do
    [[ -d "$d" ]] || continue
    name=$(basename "$d")
    du -sh "$d" 2>/dev/null | awk -v n="$name" '{ print "  " n ": " $1 }'
  done
else
  echo "(no worktrees dir)"
fi
echo ""
echo "=============================================="

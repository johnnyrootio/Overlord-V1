#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./scripts/auto_accept_workers.sh <repo-name>
# Example:
#   ./scripts/auto_accept_workers.sh robotic-barista

REPO_NAME="${1:-}"
if [[ -z "$REPO_NAME" ]]; then
  echo "usage: $0 <repo-name>" >&2
  exit 2
fi

STATE_FILE="${HOME}/.multiclaude/state.json"
if [[ ! -f "$STATE_FILE" ]]; then
  echo "state file not found: $STATE_FILE" >&2
  exit 2
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "jq is required" >&2
  exit 2
fi

TMUX_SESSION=$(jq -r --arg repo "$REPO_NAME" '.repos[$repo].tmux_session // empty' "$STATE_FILE")
if [[ -z "$TMUX_SESSION" ]]; then
  echo "repo not found in state.json: $REPO_NAME" >&2
  exit 2
fi

# Send keystrokes to every window. This is intentionally blunt: it unblocks the permissions prompt.
# The prompt expects: Down arrow (to select option 2), then Enter (to confirm).
# Use window names (not indices) to target specific windows
WINDOWS=$(tmux list-windows -t "$TMUX_SESSION" -F '#{window_name}')
SENT_COUNT=0
for w in $WINDOWS; do
  # Skip supervisor, merge-queue, and other system windows if desired
  # For now, send to all windows
  # Send Down arrow to select option 2, wait a moment, then Enter to confirm
  tmux send-keys -t "${TMUX_SESSION}:${w}" Down
  sleep 0.2  # Brief pause to ensure selection is registered
  tmux send-keys -t "${TMUX_SESSION}:${w}" C-m
  SENT_COUNT=$((SENT_COUNT + 1))
done

echo "Sent auto-accept to session ${TMUX_SESSION} (${SENT_COUNT} windows: ${WINDOWS})" >&2

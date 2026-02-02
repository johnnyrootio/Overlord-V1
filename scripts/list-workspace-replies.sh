#!/usr/bin/env bash
# List messages in the workspace inbox (replies to the Overlord).
# Usage: ./scripts/list-workspace-replies.sh [repo-name] [--ack-all]
# Default repo: robotic-barista
# --ack-all: mark all listed messages as acked (updates JSON on disk).
# See: palpatine/CAPTURING-REPLIES.md

set -uo pipefail

ACK_ALL=""
if [[ "${1:-}" == "--ack-all" ]]; then
  ACK_ALL=1
  REPO="${2:-robotic-barista}"
elif [[ "${2:-}" == "--ack-all" ]]; then
  ACK_ALL=1
  REPO="${1:-robotic-barista}"
else
  REPO="${1:-robotic-barista}"
fi

INBOX="$HOME/.multiclaude/messages/$REPO/workspace"

if [[ ! -d "$INBOX" ]]; then
  echo "No workspace inbox found for repo: $REPO"
  echo "Path: $INBOX"
  exit 0
fi

count=0
for f in "$INBOX"/msg-*.json; do
  [[ -f "$f" ]] || continue
  count=$((count + 1))
  id=$(basename "$f" .json)
  # Parse with jq if available
  if command -v jq >/dev/null 2>&1; then
    ts=$(jq -r '.timestamp // ""' "$f")
    from=$(jq -r '.from // ""' "$f")
    status=$(jq -r '.status // ""' "$f")
    body=$(jq -r '.body // ""' "$f")
    echo "---"
    echo "ID: $id | $ts | From: $from | Status: $status"
    echo "$body"
    echo ""
    if [[ -n "$ACK_ALL" ]] && [[ "$status" != "acked" ]]; then
      now=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
      jq --arg t "$now" '.status = "acked" | .acked_at = $t' "$f" > "${f}.tmp" && mv "${f}.tmp" "$f"
      echo "(acked)"
      echo ""
    fi
  else
    echo "---"
    cat "$f"
    echo ""
  fi
done

if [[ $count -eq 0 ]]; then
  echo "No messages in workspace inbox for repo: $REPO"
fi

echo "Total: $count message(s)"

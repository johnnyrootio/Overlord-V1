#!/usr/bin/env bash
set -euo pipefail

# Create a worker and automatically accept the security prompt
# Usage:
#   ./scripts/create-worker-with-auto-accept.sh <repo-name> "<task-description>"
# Example:
#   ./scripts/create-worker-with-auto-accept.sh robotic-barista "Implement #101: Add feature"

REPO_NAME="${1:-}"
TASK="${2:-}"

if [[ -z "$REPO_NAME" ]] || [[ -z "$TASK" ]]; then
  echo "usage: $0 <repo-name> \"<task-description>\"" >&2
  exit 2
fi

# Step 1: Create the worker
echo "Creating worker for task: $TASK"
WORKER_OUTPUT=$(multiclaude worker create --repo "$REPO_NAME" "$TASK" 2>&1)
echo "$WORKER_OUTPUT"

# Extract worker name from output
WORKER_NAME=$(echo "$WORKER_OUTPUT" | grep -E "Name:|Worker created" | head -1 | sed -E 's/.*Name: ([a-z-]+).*/\1/' | sed -E 's/.*worker '\''([^'\'']+)'\''.*/\1/')

if [[ -z "$WORKER_NAME" ]]; then
  # Try alternative extraction
  WORKER_NAME=$(echo "$WORKER_OUTPUT" | grep -oE "worker '[a-z-]+'" | head -1 | sed "s/worker '//" | sed "s/'//")
fi

if [[ -z "$WORKER_NAME" ]]; then
  echo "ERROR: Could not extract worker name from output" >&2
  echo "Output was:"
  echo "$WORKER_OUTPUT"
  exit 1
fi

echo ""
echo "Worker created: $WORKER_NAME"
echo "Waiting for security prompt to appear..."

# Step 2: Wait for security prompt (4-5 seconds is optimal)
sleep 5

# Step 3: Run auto-accept script
echo "Running auto-accept script..."
./scripts/auto_accept_workers.sh "$REPO_NAME"

# Step 4: Wait for Claude Code to start
echo "Waiting for Claude Code to start..."
sleep 3

# Step 5: Verify Claude Code is running
SESSION_ID=$(jq -r --arg repo "$REPO_NAME" --arg worker "$WORKER_NAME" '.repos[$repo].agents[$worker].session_id // empty' ~/.multiclaude/state.json 2>/dev/null)

if [[ -n "$SESSION_ID" ]]; then
  CLAUDE_PROCESS=$(ps aux | grep "claude.*$SESSION_ID" | grep -v grep || echo "")
  
  if [[ -n "$CLAUDE_PROCESS" ]]; then
    echo ""
    echo "✓ SUCCESS: Worker '$WORKER_NAME' is running!"
    echo "  Session ID: $SESSION_ID"
    echo ""
    echo "Monitor with: multiclaude agent attach --repo $REPO_NAME $WORKER_NAME --read-only"
    echo "Check status: multiclaude worker list --repo $REPO_NAME"
    exit 0
  else
    echo ""
    echo "⚠ WARNING: Worker created but Claude Code process not found"
    echo "  Session ID: $SESSION_ID"
    echo "  Worker may still be starting, or there may be an issue"
    echo ""
    echo "Check manually:"
    echo "  multiclaude agent attach --repo $REPO_NAME $WORKER_NAME --read-only"
    echo "  ps aux | grep claude | grep $SESSION_ID"
    exit 1
  fi
else
  echo ""
  echo "⚠ WARNING: Could not find session ID for worker"
  echo "  Worker: $WORKER_NAME"
  exit 1
fi

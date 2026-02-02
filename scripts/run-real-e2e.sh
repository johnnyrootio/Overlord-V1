#!/usr/bin/env sh
# Run real E2E: trivial todo app with real Claude, real GitHub, real multiclaude.
# Prerequisites: gh auth, multiclaude repo init <url>, ANTHROPIC_API_KEY or CLAUDE_CODE_API_KEY.
#
# Usage:
#   1. Create repo and init multiclaude (once):
#      gh repo create YOUR_USERNAME/trivial-todo-app --public
#      multiclaude repo init https://github.com/YOUR_USERNAME/trivial-todo-app
#
#   2. Copy scenario template and set your repo:
#      cp scenarios/real-e2e-todo-template.yaml scenarios/real-e2e-todo.yaml
#      # Edit real-e2e-todo.yaml: replace YOUR_USERNAME in the first gate_response.
#
#   3. Run from Overlord repo root:
#      ./scripts/run-real-e2e.sh
#
# Or run step-by-step interactively: see docs/REAL-E2E-RUN.md

set -e
cd "$(dirname "$0")/.."
SCENARIO="${1:-scenarios/real-e2e-todo.yaml}"

if [ ! -f "$SCENARIO" ]; then
  echo "Scenario not found: $SCENARIO"
  echo "Copy scenarios/real-e2e-todo-template.yaml to scenarios/real-e2e-todo.yaml"
  echo "and replace YOUR_USERNAME in the first gate_response, then run:"
  echo "  ./scripts/run-real-e2e.sh"
  exit 1
fi

echo "Running real E2E scenario: $SCENARIO"
echo "Ensure: gh auth, multiclaude repo init, API key set."
echo ""
python3 -m overlord scenario "$SCENARIO"
echo ""
echo "Done. Check: overlord status trivial-todo-app"

#!/usr/bin/env bash
# Run the Overlord Test Harness.
# Usage:
#   ./scripts/run-test-harness.sh <scenario.yaml>
#   ./scripts/run-test-harness.sh --from-spec greenfield-specs/trivial-todo-app.md
#   ./scripts/run-test-harness.sh --no-repo --from-spec greenfield-specs/trivial-todo-app.md
set -e
cd "$(dirname "$0")/.."
exec python -m test_harness.runner "$@"

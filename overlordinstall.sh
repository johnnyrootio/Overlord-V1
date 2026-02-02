#!/usr/bin/env sh
# Install Overlord in a virtual environment. Run from repo root.
# After install: source .venv/bin/activate (or use .venv/bin/overlord), then source .env and run overlord.
set -e
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
  echo "Created .venv"
fi

. .venv/bin/activate
pip install --upgrade pip --quiet
pip install -e . --quiet
echo ""
echo "Overlord is installed. To use it:"
echo "  source .venv/bin/activate"
echo "  source .env   # or: set -a && source .env && set +a"
echo "  overlord --help"
echo ""
echo "Real E2E: see docs/REAL-E2E-RUN.md and run ./scripts/run-real-e2e.sh from repo root."

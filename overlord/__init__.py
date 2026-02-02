"""Overlord Agent V1 — stateful multi-agent CLI for greenfield development."""

from pathlib import Path

# Load .env from project root so ANTHROPIC_API_KEY is available for CLI and tests
try:
    from dotenv import load_dotenv
    _root = Path(__file__).resolve().parent.parent
    load_dotenv(_root / ".env")
except Exception:
    pass

__version__ = "0.1.0"

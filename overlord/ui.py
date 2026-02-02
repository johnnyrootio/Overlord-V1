"""
UI-facing step names. Phases (0–4) are an internal abstraction; the UI uses colloquial step names.
"""
from typing import Dict

# Phase number -> human-facing step name (no "Phase N" in UI)
STEP_NAMES: Dict[int, str] = {
    0: "setup",
    1: "planning",
    2: "work graph",
    3: "issues",   # programmatic: creating GitHub issues
    4: "execution",
}


def step_name(phase: int) -> str:
    """Return colloquial step name for a phase number. Used in CLI and slash commands."""
    return STEP_NAMES.get(phase, f"step-{phase}")

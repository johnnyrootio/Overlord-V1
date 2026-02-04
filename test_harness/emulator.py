"""
User-emulator agent for the Test Harness: produces the next line to send to Overlord.

Input: goals, greenfield spec, recent Overlord output. Output: one line (gate answer,
slash command, or natural language). See roadmap/features/autonomous-test-bench.md §2.

Implementations:
- StubEmulator: returns fixed lines from a list (for tests).
- ClaudeEmulator: Claude Code–based (optional; use when API configured).
"""
from dataclasses import dataclass
from typing import Callable, List, Optional


@dataclass
class EmulatorContext:
    """Input context for the emulator when deciding the next reply."""

    goals: str
    greenfield_spec_path: str
    greenfield_spec_content: str
    emulator_prompt: Optional[str]
    recent_output: str  # Overlord output since last user input (or since start)
    decisions: Optional[dict] = None  # scenario decisions to steer Overlord toward (e.g. cli: "click")


EmulatorFn = Callable[[EmulatorContext], str]


class StubEmulator:
    """
    Emulator that returns predefined lines in order. Used for integration tests.
    When the list is exhausted, returns fallback (default /exit).
    """

    def __init__(
        self,
        lines: Optional[List[str]] = None,
        fallback: str = "/exit",
    ) -> None:
        self._lines = list(lines) if lines else []
        self._fallback = fallback

    def __call__(self, context: EmulatorContext) -> str:
        if self._lines:
            return self._lines.pop(0)
        return self._fallback


def stub_emulator(
    lines: Optional[List[str]] = None,
    fallback: str = "/exit",
) -> EmulatorFn:
    """Build a stub emulator callable (list of lines, then fallback)."""
    stub = StubEmulator(lines=lines, fallback=fallback)
    return stub

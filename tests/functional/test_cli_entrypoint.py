"""
Functional test: overlord CLI entry point.
overlord --help exits 0 and shows required commands (start, list, run, resume, status).
"""
import subprocess
import sys

import pytest


@pytest.mark.functional
def test_overlord_help_exits_zero():
    """overlord --help exits with code 0."""
    result = subprocess.run(
        [sys.executable, "-m", "overlord", "--help"],
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 0, f"stderr: {result.stderr!r}"


@pytest.mark.functional
def test_overlord_help_shows_required_commands():
    """overlord --help output includes start, list, run, resume, status."""
    result = subprocess.run(
        [sys.executable, "-m", "overlord", "--help"],
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 0
    out = result.stdout + result.stderr
    for cmd in ("start", "list", "run", "resume", "status"):
        assert cmd in out, f"Expected command {cmd!r} in help output"

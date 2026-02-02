"""
Unit tests: gates and HITL — pending_question persisted; answer clears and advances.
"""
import os
import tempfile

import pytest
from click.testing import CliRunner

from overlord.cli import cli
from overlord.state import SessionState
from overlord.storage import StateManager


@pytest.mark.unit
def test_state_with_pending_question_persists_and_loads():
    """State with pending_questions persists; load returns same pending."""
    with tempfile.TemporaryDirectory() as tmp:
        manager = StateManager(tmp)
        state = SessionState(project_id="p")
        state.add_pending_question("Gate 1: Confirm tech stack?")
        manager.save("p", state)
        loaded = manager.load("p")
        assert loaded.pending_questions == ["Gate 1: Confirm tech stack?"]


@pytest.mark.unit
def test_start_blocks_with_pending_and_exits_zero():
    """Start with spec; after Phase 0, start exits 0 and output contains first prompt (repo name or Gate 1)."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmp:
        spec = os.path.join(tmp, "s.md")
        with open(spec, "w") as f:
            f.write("# Spec\n")
        state_dir = os.path.join(tmp, "state")
        result = runner.invoke(cli, ["start", spec, "--state-dir", state_dir])
        assert result.exit_code == 0, result.output
        assert "name of this repo" in result.output or "Gate 1" in result.output or "gate" in result.output.lower()
        assert "Project:" in result.output
        manager = StateManager(state_dir)
        state = manager.load("s")
        assert len(state.pending_questions) >= 1

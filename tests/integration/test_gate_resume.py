"""
Integration: run until gate → exit → resume with answer → progression.
"""
import os
import tempfile

import pytest
from click.testing import CliRunner

from overlord.cli import cli
from overlord.storage import StateManager


@pytest.mark.integration
def test_start_then_resume_with_answer_clears_pending_and_advances():
    """Start (blocks at repo name + gates 1–5); resume 6 times with answers; pending cleared, phase advanced."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmp:
        spec = os.path.join(tmp, "app.md")
        with open(spec, "w") as f:
            f.write("# App\n")
        state_dir = os.path.join(tmp, "state")
        runner.invoke(cli, ["start", spec, "--state-dir", state_dir, "--project-id", "proj"])
        manager = StateManager(state_dir)
        state_before = manager.load("proj")
        assert len(state_before.pending_questions) == 6  # repo name + 5 gates
        # Responses file: 6 lines (repo name or URL, then 5 gate answers)
        responses_path = os.path.join(tmp, "responses.txt")
        with open(responses_path, "w") as f:
            f.write("my-app\n")  # first: repo name (or GitHub URL)
            for _ in range(5):
                f.write("yes\n")
        for _ in range(6):
            result = runner.invoke(cli, ["resume", "proj", "--state-dir", state_dir, "--responses", responses_path])
            assert result.exit_code == 0, result.output
        state_after = manager.load("proj")
        assert len(state_after.pending_questions) == 0
        assert state_after.phase >= 1

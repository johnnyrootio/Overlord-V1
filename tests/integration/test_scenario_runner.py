"""
Integration: run with scenario file; gate responses fed from scenario; state progresses.
"""
import os
import tempfile

import pytest
from click.testing import CliRunner

from overlord.cli import cli
from overlord.storage import StateManager


@pytest.mark.integration
def test_run_with_scenario_feeds_responses_and_progresses():
    """Run overlord scenario <file> with spec_path and gate_responses; start then resume with responses."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmp:
        spec_path = os.path.join(tmp, "x.md")
        with open(spec_path, "w") as f:
            f.write("# X\n")
        scenario_path = os.path.join(tmp, "scenario.yaml")
        import yaml
        with open(scenario_path, "w") as f:
            yaml.dump({"spec_path": os.path.abspath(spec_path), "gate_responses": ["yes"] * 5}, f)
        state_dir = os.path.join(tmp, "state")
        result = runner.invoke(cli, ["scenario", scenario_path, "--state-dir", state_dir])
        assert result.exit_code == 0, result.output
        manager = StateManager(state_dir)
        # Project id derived from spec basename "x"
        state = manager.load("x")
        assert len(state.pending_questions) == 0
        assert state.phase >= 1

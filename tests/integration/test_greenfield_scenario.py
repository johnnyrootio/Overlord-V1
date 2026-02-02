"""
P4 C9: First scripted greenfield scenario with example-todo-app.md; Gate 1–5 canned answers.
P4 C10: Two-step run (start → gate → exit; resume → answer → continue); pending surfaced, state correct.
"""
import os

import pytest
from click.testing import CliRunner

from overlord.cli import cli
from overlord.storage import StateManager


# Repo root (parent of tests/)
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


@pytest.mark.integration
def test_scenario_with_example_todo_app_and_five_gates_progresses():
    """C9: Run scenario with greenfield-specs/example-todo-app.md and 5 gate_responses; phase progression and state."""
    spec_path = os.path.join(_REPO_ROOT, "greenfield-specs", "example-todo-app.md")
    if not os.path.isfile(spec_path):
        pytest.skip("greenfield-specs/example-todo-app.md not found")
    runner = CliRunner()
    with runner.isolated_filesystem() as tmp:
        # Scenario file with absolute spec path and 5 responses
        scenario_path = os.path.join(tmp, "scenario.yaml")
        import yaml
        with open(scenario_path, "w") as f:
            yaml.dump({
                "spec_path": spec_path,
                "project_id": "example-todo-app",
                "gate_responses": ["example-todo-app", "yes", "yes", "yes", "yes", "yes"],  # repo name + 5 gates
            }, f)
        state_dir = os.path.join(tmp, "state")
        result = runner.invoke(cli, ["scenario", scenario_path, "--state-dir", state_dir])
        assert result.exit_code == 0, result.output
        manager = StateManager(state_dir)
        state = manager.load("example-todo-app")
        assert len(state.pending_questions) == 0
        assert state.phase >= 1


@pytest.mark.integration
def test_two_step_run_start_then_resume_pending_surfaced_and_state_correct():
    """C10: Start → exit at gate; resume with answer → continue. Pending surfaced and state correct after resume."""
    runner = CliRunner()
    with runner.isolated_filesystem() as tmp:
        spec_path = os.path.join(tmp, "app.md")
        with open(spec_path, "w") as f:
            f.write("# App\n")
        state_dir = os.path.join(tmp, "state")
        # Step 1: start (blocks at first question: repo name or URL, exits 0)
        result_start = runner.invoke(cli, ["start", spec_path, "--state-dir", state_dir, "--project-id", "two-step"])
        assert result_start.exit_code == 0, result_start.output
        assert "name of this repo" in result_start.output or "Gate 1" in result_start.output
        assert "Project:" in result_start.output
        manager = StateManager(state_dir)
        state_after_start = manager.load("two-step")
        assert len(state_after_start.pending_questions) >= 1
        assert state_after_start.phase == 0
        # Step 2: resume with one answer (clears first question; 5 gates remain)
        result_resume = runner.invoke(cli, ["resume", "two-step", "--state-dir", state_dir], input="my-app\n")
        assert result_resume.exit_code == 0, result_resume.output
        state_after_resume = manager.load("two-step")
        # One pending cleared; 5 remain (Gates 1–5); phase still 0 until all gates answered
        assert len(state_after_resume.pending_questions) == 5
        assert state_after_resume.phase == 0

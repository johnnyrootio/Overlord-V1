"""
Integration test: start → exit → resume same project (C4).
Start with spec in temp state dir, list shows project; run/resume with project_id loads same project.
"""
import os
import tempfile

import pytest
from click.testing import CliRunner

from overlord.cli import cli


def _default_state_dir():
    return os.path.expanduser("~/.overlord")


@pytest.mark.integration
def test_start_creates_project_then_list_shows_it():
    """Start with a temp spec and temp state dir; list shows one project."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmp:
        spec_path = os.path.join(tmp, "my-spec.md")
        with open(spec_path, "w") as f:
            f.write("# Spec\n")
        state_dir = os.path.join(tmp, "state")
        result_start = runner.invoke(cli, ["start", spec_path, "--state-dir", state_dir])
        assert result_start.exit_code == 0, result_start.output
        result_list = runner.invoke(cli, ["list", "--state-dir", state_dir])
        assert result_list.exit_code == 0, result_list.output
        assert "my-spec" in result_list.output or "my_spec" in result_list.output


@pytest.mark.integration
def test_start_then_resume_loads_same_project():
    """Start with spec, then resume with project_id; resume exits 0 (loads same project)."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmp:
        spec_path = os.path.join(tmp, "app.md")
        with open(spec_path, "w") as f:
            f.write("# App\n")
        state_dir = os.path.join(tmp, "state")
        runner.invoke(cli, ["start", spec_path, "--state-dir", state_dir, "--project-id", "my-app"])
        result_resume = runner.invoke(cli, ["resume", "my-app", "--state-dir", state_dir], input="yes\n")
        assert result_resume.exit_code == 0, result_resume.output


@pytest.mark.integration
def test_start_runs_phase0_and_creates_artifact():
    """Start with spec; project dir has artifacts/phase_0_done.txt (Phase 0 stub ran)."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmp:
        spec_path = os.path.join(tmp, "x.md")
        with open(spec_path, "w") as f:
            f.write("# X\n")
        state_dir = os.path.join(tmp, "state")
        result = runner.invoke(cli, ["start", spec_path, "--state-dir", state_dir, "--project-id", "proj"])
        assert result.exit_code == 0, result.output
        artifact_file = os.path.join(state_dir, "projects", "proj", "artifacts", "phase_0_done.txt")
        assert os.path.isfile(artifact_file), f"Phase 0 artifact should exist: {artifact_file}"

"""
Unit tests: CLI commands parse and behave (start exits 0, list prints expected format).
Uses Click CliRunner for fast, isolated tests. List tests use isolated state dir.
"""
import json
import os
import tempfile

import pytest
from click.testing import CliRunner

from overlord.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


@pytest.mark.unit
def test_start_with_valid_spec_path_exits_zero(runner):
    """overlord start <spec-path> with existing file exits 0."""
    with tempfile.TemporaryDirectory() as tmp:
        spec_path = os.path.join(tmp, "spec.md")
        with open(spec_path, "w") as f:
            f.write("# Spec\n")
        state_dir = os.path.join(tmp, "state")
        result = runner.invoke(cli, ["start", spec_path, "--state-dir", state_dir])
        assert result.exit_code == 0, result.output


@pytest.mark.unit
def test_list_prints_expected_format(runner):
    """overlord list prints human-readable format (no projects or step= lines)."""
    with tempfile.TemporaryDirectory() as tmp:
        state_dir = os.path.join(tmp, "state")
        result = runner.invoke(cli, ["list", "--state-dir", state_dir])
        assert result.exit_code == 0
        out = result.output
        assert out.strip() == "(no projects)"
        # With a project: start then list
        spec_path = os.path.join(tmp, "app.md")
        with open(spec_path, "w") as f:
            f.write("# App\n")
        runner.invoke(cli, ["start", spec_path, "--state-dir", state_dir])
        result2 = runner.invoke(cli, ["list", "--state-dir", state_dir])
        assert result2.exit_code == 0
        assert "step=" in result2.output and "pending=" in result2.output


@pytest.mark.unit
def test_status_command_shows_phase_and_status_snapshot(runner):
    """overlord status <project-id> shows step, pending, and status (health, workers)."""
    with tempfile.TemporaryDirectory() as tmp:
        state_dir = os.path.join(tmp, "state")
        spec_path = os.path.join(tmp, "s.md")
        with open(spec_path, "w") as f:
            f.write("# S\n")
        runner.invoke(cli, ["start", spec_path, "--state-dir", state_dir])
        # Resume once so we have a project (start exits 0 at gate; project exists)
        runner.invoke(cli, ["resume", "s", "--state-dir", state_dir], input="yes\n")
        result = runner.invoke(cli, ["status", "s", "--state-dir", state_dir])
        assert result.exit_code == 0
        assert "step=" in result.output and "pending=" in result.output
        assert "status:" in result.output and "health=" in result.output


@pytest.mark.unit
def test_list_json_format_returns_array(runner):
    """overlord list --format json returns JSON array (empty or with project objects)."""
    with tempfile.TemporaryDirectory() as tmp:
        state_dir = os.path.join(tmp, "state")
        result = runner.invoke(cli, ["list", "--format", "json", "--state-dir", state_dir])
        assert result.exit_code == 0
        assert result.output.strip() == "[]"
        data = json.loads(result.output)
        assert data == []

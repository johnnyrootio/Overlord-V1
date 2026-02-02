"""
P6 C16: First working V1 E2E test.
Overlord builds trivial todo app (human at gates only, scripted); project exists; check.sh passes.
"""
import os
import subprocess

import pytest
from click.testing import CliRunner

from overlord.cli import cli
from overlord.storage import StateManager


_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


@pytest.mark.integration
def test_first_working_v1_scenario_then_check_sh_passes(monkeypatch):
    """C16: Run overlord scenario with trivial-todo-app; project exists; ./scripts/check.sh passes.
    Uses stub path (no Claude API) so the test is fast and deterministic."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    monkeypatch.setenv("CLAUDE_CODE_API_KEY", "")
    spec_path = os.path.join(_REPO_ROOT, "greenfield-specs", "trivial-todo-app.md")
    if not os.path.isfile(spec_path):
        pytest.skip("greenfield-specs/trivial-todo-app.md not found")
    runner = CliRunner()
    with runner.isolated_filesystem() as tmp:
        state_dir = os.path.join(tmp, "state")
        # Scenario with absolute spec path so spec is found (repo file)
        import yaml
        scenario_path = os.path.join(tmp, "scenario.yaml")
        with open(scenario_path, "w") as f:
            yaml.dump({
                "spec_path": os.path.abspath(spec_path),
                "project_id": "trivial-todo-app",
                "gate_responses": ["trivial-todo-app", "public", "yes", "yes", "yes", "yes", "yes"],  # repo, public/private, gates
            }, f)
        result = runner.invoke(cli, ["scenario", scenario_path, "--state-dir", state_dir])
        assert result.exit_code == 0, result.output
        manager = StateManager(state_dir)
        state = manager.load("trivial-todo-app")
        assert len(state.pending_questions) == 0
        assert state.phase >= 1, "After gates cleared, Phase 1 runs"
        project_dir = os.path.join(state_dir, "projects", "trivial-todo-app")
        artifacts_dir = os.path.join(project_dir, "artifacts")
        assert os.path.isfile(os.path.join(artifacts_dir, "plan.md")), "Phase 1 plan.md"
        assert os.path.isfile(os.path.join(artifacts_dir, "tasks.md")), "Phase 1 tasks.md"
        # Phase 2 runs when no pending after Phase 1
        assert state.phase >= 2, "After Phase 1, Phase 2 (Wave Planner) runs"
        assert os.path.isfile(os.path.join(artifacts_dir, "workgraph.yml")), "Phase 2 workgraph.yml"
        # Phase 3 runs when no pending after Phase 2
        assert state.phase >= 3, "After Phase 2, Phase 3 (Issue Emitter) runs"
        assert os.path.isfile(os.path.join(project_dir, "issues.json")), "Phase 3 issues.json"
        # Phase 4 runs when no pending after Phase 3
        assert state.phase == 4, "After Phase 3, Phase 4 (Execution Manager) runs"
        assert os.path.isfile(os.path.join(artifacts_dir, "phase_4_system_prompt.md")), "Phase 4 system prompt persisted"
        assert os.path.isdir(project_dir)
        check_sh = os.path.join(project_dir, "scripts", "check.sh")
        assert os.path.isfile(check_sh), f"check.sh should exist: {check_sh}"
        run_result = subprocess.run(
            ["sh", check_sh],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert run_result.returncode == 0, f"check.sh must pass: {run_result.stderr!r}"

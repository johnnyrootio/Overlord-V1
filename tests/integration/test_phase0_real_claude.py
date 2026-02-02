"""
C11: Phase 0 real / Claude Code integration tests.
When ANTHROPIC_API_KEY is set, Phase 0 invokes one Claude Code instance and persists phase_0_claude_response.txt.
When not set, Phase 0 runs stub only (no API call); artifacts still exist.
API verification tests do not skip: they fail with a clear message if the key is missing.
"""
import os

import pytest
from click.testing import CliRunner

from overlord.cli import cli
from overlord.claude_api import is_api_configured
from overlord.storage import StateManager


_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

_API_KEY_REQUIRED_MSG = (
    "ANTHROPIC_API_KEY or CLAUDE_CODE_API_KEY must be set to run API verification tests. "
    "Set one of them and re-run to verify the Claude Code API works."
)


def _require_api_key() -> None:
    if not is_api_configured():
        pytest.fail(_API_KEY_REQUIRED_MSG)


@pytest.mark.integration
def test_phase0_stub_when_no_api_key():
    """Without ANTHROPIC_API_KEY, Phase 0 completes with stub only; no phase_0_claude_response.txt."""
    spec_path = os.path.join(_REPO_ROOT, "greenfield-specs", "trivial-todo-app.md")
    if not os.path.isfile(spec_path):
        spec_path = os.path.join(_REPO_ROOT, "agent_prompts", "README.md")  # fallback
    if not os.path.isfile(spec_path):
        pytest.skip("No spec file found")
    # Ensure no API key in env for this test
    api_key = os.environ.pop("ANTHROPIC_API_KEY", None)
    claude_key = os.environ.pop("CLAUDE_CODE_API_KEY", None)
    try:
        runner = CliRunner()
        with runner.isolated_filesystem() as tmp:
            state_dir = os.path.join(tmp, "state")
            result = runner.invoke(
                cli,
                ["start", os.path.abspath(spec_path), "--state-dir", state_dir, "--project-id", "p0-stub"],
            )
            assert result.exit_code == 0, result.output
            manager = StateManager(state_dir)
            state = manager.load("p0-stub")
            assert state.phase == 0
            project_dir = os.path.join(state_dir, "projects", "p0-stub")
            artifacts_dir = os.path.join(project_dir, "artifacts")
            assert os.path.isfile(os.path.join(artifacts_dir, "phase_0_done.txt"))
            assert os.path.isfile(os.path.join(artifacts_dir, "phase_0_system_prompt.md"))
            # Stub path: no API call, so no phase_0_claude_response
            response_file = os.path.join(artifacts_dir, "phase_0_claude_response.txt")
            assert not os.path.isfile(response_file), "Should not create response file when API not configured"
    finally:
        if api_key is not None:
            os.environ["ANTHROPIC_API_KEY"] = api_key
        if claude_key is not None:
            os.environ["CLAUDE_CODE_API_KEY"] = claude_key


@pytest.mark.integration
def test_phase0_real_claude_when_api_key_set():
    """C11: With API key set, Phase 0 invokes Claude and persists phase_0_claude_response.txt. Fails if key missing or API fails."""
    _require_api_key()
    spec_path = os.path.join(_REPO_ROOT, "greenfield-specs", "trivial-todo-app.md")
    if not os.path.isfile(spec_path):
        spec_path = os.path.join(_REPO_ROOT, "agent_prompts", "README.md")
    if not os.path.isfile(spec_path):
        pytest.fail("No spec file found for Phase 0 integration test")
    runner = CliRunner()
    with runner.isolated_filesystem() as tmp:
        state_dir = os.path.join(tmp, "state")
        result = runner.invoke(
            cli,
            ["start", os.path.abspath(spec_path), "--state-dir", state_dir, "--project-id", "p0-real"],
        )
        assert result.exit_code == 0, result.output
        manager = StateManager(state_dir)
        state = manager.load("p0-real")
        assert state.phase == 0
        project_dir = os.path.join(state_dir, "projects", "p0-real")
        artifacts_dir = os.path.join(project_dir, "artifacts")
        assert os.path.isfile(os.path.join(artifacts_dir, "phase_0_done.txt"))
        response_file = os.path.join(artifacts_dir, "phase_0_claude_response.txt")
        assert os.path.isfile(response_file), (
            "Phase 0 with API key must create phase_0_claude_response.txt. "
            "Check key validity, network, and model (OVERLORD_CLAUDE_MODEL)."
        )
        with open(response_file, encoding="utf-8") as f:
            content = f.read()
        assert len(content.strip()) > 0, "Claude response must be non-empty"

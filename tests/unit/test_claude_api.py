"""Unit tests: Claude API phase agent invocation (overlord/claude_api.py). C11."""
import os

import pytest

from overlord.claude_api import is_api_configured, invoke_phase_agent

# Message when API key is required but missing (do not skip — fail so verification is explicit)
_API_KEY_REQUIRED_MSG = (
    "ANTHROPIC_API_KEY or CLAUDE_CODE_API_KEY must be set to run API verification tests. "
    "Set one of them and re-run to verify the Claude Code API works."
)


def _require_api_key() -> None:
    """Fail with clear message if API key is not set. Do not skip."""
    if not is_api_configured():
        pytest.fail(_API_KEY_REQUIRED_MSG)


@pytest.mark.unit
def test_is_api_configured_false_when_no_key():
    """is_api_configured returns False when ANTHROPIC_API_KEY and CLAUDE_CODE_API_KEY are unset."""
    # Clear both so test is isolated
    env_anthropic = os.environ.pop("ANTHROPIC_API_KEY", None)
    env_claude = os.environ.pop("CLAUDE_CODE_API_KEY", None)
    try:
        assert is_api_configured() is False
        assert is_api_configured(api_key=None) is False
        assert is_api_configured(api_key="") is False
    finally:
        if env_anthropic is not None:
            os.environ["ANTHROPIC_API_KEY"] = env_anthropic
        if env_claude is not None:
            os.environ["CLAUDE_CODE_API_KEY"] = env_claude


@pytest.mark.unit
def test_is_api_configured_true_when_key_passed():
    """is_api_configured returns True when api_key is passed and non-empty."""
    assert is_api_configured(api_key="sk-fake") is True


@pytest.mark.unit
def test_invoke_phase_agent_returns_empty_when_not_configured():
    """invoke_phase_agent returns empty string when API key is not configured."""
    env_anthropic = os.environ.pop("ANTHROPIC_API_KEY", None)
    env_claude = os.environ.pop("CLAUDE_CODE_API_KEY", None)
    try:
        result = invoke_phase_agent(0, "You are Phase 0.", "Hello.")
        assert result == ""
    finally:
        if env_anthropic is not None:
            os.environ["ANTHROPIC_API_KEY"] = env_anthropic
        if env_claude is not None:
            os.environ["CLAUDE_CODE_API_KEY"] = env_claude


@pytest.mark.unit
def test_invoke_phase_agent_returns_empty_with_empty_key():
    """invoke_phase_agent returns empty when api_key is empty string."""
    result = invoke_phase_agent(0, "You are Phase 0.", "Hello.", api_key="")
    assert result == ""


@pytest.mark.unit
def test_invoke_phase_agent_returns_non_empty_when_configured():
    """Verify Claude Code API works: call API with simple prompt, assert non-empty response. Requires ANTHROPIC_API_KEY."""
    _require_api_key()
    system_prompt = "You are a helpful assistant. Reply in one short sentence."
    user_message = "Say exactly: API verification passed."
    result = invoke_phase_agent(0, system_prompt, user_message, max_tokens=64)
    assert isinstance(result, str), "invoke_phase_agent must return str"
    assert len(result.strip()) > 0, (
        "Claude API must return non-empty response when key is set. "
        "Check key validity, network, and model availability (OVERLORD_CLAUDE_MODEL)."
    )
    # Basic sanity: response should look like real content (not an error message)
    assert len(result) >= 5, "Response too short to be a real completion"

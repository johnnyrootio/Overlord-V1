"""
Phase agent invocation via Anthropic Messages API (Claude Code API).
C11: One new Claude Code instance per phase; no recycling across phases.
When ANTHROPIC_API_KEY is set, invoke_phase_agent() calls the API and returns the assistant response.
Multi-turn: invoke_phase_agent_messages() for human-in-the-loop conversation.
"""
import os
from typing import Any, List, Optional


# Default model for phase agents: Claude Opus 4.5
# Override via OVERLORD_CLAUDE_MODEL if needed
DEFAULT_MODEL = os.environ.get("OVERLORD_CLAUDE_MODEL", "claude-opus-4-5-20251101")
DEFAULT_MAX_TOKENS = 4096


def is_api_configured(api_key: Optional[str] = None) -> bool:
    """True if Anthropic API key is available (env or passed). Explicit empty string means not configured."""
    if api_key is not None and (not api_key or not api_key.strip()):
        return False
    key = api_key if (api_key and api_key.strip()) else os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("CLAUDE_CODE_API_KEY")
    return bool(key and key.strip())


def invoke_phase_agent(
    phase: int,
    system_prompt: str,
    user_message: str,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> str:
    """
    Invoke a single phase agent via Anthropic Messages API (one instance per phase).
    Returns the assistant's text response, or empty string if not configured or on error.
    """
    if not is_api_configured(api_key):
        return ""
    key = (api_key if (api_key and api_key.strip()) else None) or os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("CLAUDE_CODE_API_KEY")
    if not key or not key.strip():
        return ""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=key.strip())
        resp = client.messages.create(
            model=model or DEFAULT_MODEL,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        if resp.content and len(resp.content) > 0 and hasattr(resp.content[0], "text"):
            return resp.content[0].text or ""
        return ""
    except Exception:
        return ""


def invoke_phase_agent_messages(
    phase: int,
    system_prompt: str,
    messages: List[dict],
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> str:
    """
    Multi-turn: invoke phase agent with full message history (human-in-the-loop).
    messages: list of {"role": "user"|"assistant", "content": str}.
    Returns the assistant's text response, or empty string if not configured or on error.
    """
    if not is_api_configured(api_key):
        return ""
    key = (api_key if (api_key and api_key.strip()) else None) or os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("CLAUDE_CODE_API_KEY")
    if not key or not key.strip():
        return ""
    if not messages:
        return ""
    try:
        import anthropic
        # API expects alternating user/assistant; we pass as-is (Anthropic allows multiple in a row)
        formatted: List[Any] = [{"role": m["role"], "content": m["content"]} for m in messages]
        client = anthropic.Anthropic(api_key=key.strip())
        resp = client.messages.create(
            model=model or DEFAULT_MODEL,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=formatted,
        )
        if resp.content and len(resp.content) > 0 and hasattr(resp.content[0], "text"):
            return resp.content[0].text or ""
        return ""
    except Exception:
        return ""

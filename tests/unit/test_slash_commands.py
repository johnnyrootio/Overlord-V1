"""Unit tests: slash command parsing and handling."""
import pytest

from overlord.monitor import StatusSnapshot
from overlord.slash_commands import handle_slash_command, parse_slash_command
from overlord.state import SessionState


@pytest.mark.unit
def test_parse_slash_command_returns_command_name():
    """parse_slash_command returns command name without /."""
    assert parse_slash_command("/status") == "status"
    assert parse_slash_command("/phase") == "phase"
    assert parse_slash_command("  /help  ") == "help"
    assert parse_slash_command("not a command") is None
    assert parse_slash_command("") is None


@pytest.mark.unit
def test_handle_slash_status_returns_snapshot_info():
    """handle_slash_command /status returns health, workers, liveness."""
    state = SessionState(project_id="x")
    snapshot = StatusSnapshot(health="ok", workers=["w1"], liveness="ok")
    out, _, _ = handle_slash_command("status", state, snapshot)
    assert "health=" in out and "workers=" in out and "liveness=" in out


@pytest.mark.unit
def test_handle_slash_phase_returns_phase_and_pending():
    """handle_slash_command /phase returns step name and pending count."""
    state = SessionState(project_id="x")
    state.set_phase(2)
    state.add_pending_question("Q?")
    snapshot = StatusSnapshot()
    out, _, _ = handle_slash_command("phase", state, snapshot)
    assert "step=work graph" in out and "pending=1" in out


@pytest.mark.unit
def test_handle_slash_help_lists_commands():
    """handle_slash_command /help returns list of slash commands."""
    state = SessionState(project_id="x")
    snapshot = StatusSnapshot()
    out, _, _ = handle_slash_command("help", state, snapshot)
    assert "/status" in out and "/phase" in out and "/help" in out

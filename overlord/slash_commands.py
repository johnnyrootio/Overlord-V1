"""
Slash commands: command-specific CLI actions. They are never sent to the phase agent.

The CLI flows the agent's messages to the user and passes the user's unstructured input to the
agent. Only lines that do not start with / are sent to the agent; lines starting with / invoke
these commands (e.g. /help, /status, /done, /exit, /query) and are handled entirely by the CLI.
See docs/OVERLORD-CLI-SPEC.md Section 4b.
"""
from typing import Optional, Tuple

from overlord.monitor import StatusSnapshot
from overlord.state import SessionState
from overlord.ui import step_name

SLASH_HELP = (
    "Definitive commands (use anytime):\n"
    "  /help   – show this list\n"
    "  /status – workers, health, liveness (execution); phase/turn (planning)\n"
    "  /phase  – current step and pending count\n"
    "  /query [question] – ask about execution state (during Phase 4) or send to agent (during phase)\n"
    "  /done   – mark current phase complete; agent outputs final deliverable\n"
    "  /quiet  – toggle proactive status lines off\n"
    "  /verbose – toggle verbose output\n"
    "  /exit   – stop this project's workers, save state, exit\n"
    "Anything else is ad hoc conversation: your message goes to the phase agent."
)


def parse_slash_command(line: str) -> Optional[str]:
    """Return slash command name (without /) if line is a slash command, else None."""
    s = (line or "").strip()
    if s.startswith("/"):
        cmd = s[1:].split()[0] if s[1:].strip() else ""
        return cmd.lower() if cmd else None
    return None


def parse_slash_command_with_arg(line: str) -> Tuple[Optional[str], str]:
    """Return (command, rest_of_line) for slash commands, else (None, line). E.g. /query how many issues? -> ('query', 'how many issues?')."""
    s = (line or "").strip()
    if not s.startswith("/"):
        return None, s
    rest = s[1:].strip()
    if not rest:
        return None, s
    parts = rest.split(maxsplit=1)
    cmd = parts[0].lower()
    arg = parts[1].strip() if len(parts) > 1 else ""
    return cmd, arg


def handle_slash_command(
    cmd: str,
    state: SessionState,
    snapshot: StatusSnapshot,
    quiet: bool = False,
    verbose: bool = False,
    query_arg: str = "",
) -> Tuple[str, bool, bool]:
    """
    Handle /status, /phase, /help, /query, /quiet, /verbose. (/exit, /done handled in CLI.)
    Returns (output_line, new_quiet, new_verbose).
    """
    if cmd == "status":
        workers_running = ", ".join(snapshot.workers) if snapshot.workers else "(none)"
        out = f"workers running: {workers_running}  health={snapshot.health}  liveness={snapshot.liveness}"
        if snapshot.issues_in_progress:
            out += f"  issues={snapshot.issues_in_progress}"
        return out, quiet, verbose
    if cmd == "phase":
        return f"step={step_name(state.phase)}  pending={len(state.pending_questions)}", quiet, verbose
    if cmd == "help":
        return SLASH_HELP, quiet, verbose
    if cmd == "query":
        workers_running = ", ".join(snapshot.workers) if snapshot.workers else "(none)"
        out = f"[query] {query_arg}\nworkers: {workers_running}  health={snapshot.health}  liveness={snapshot.liveness}"
        if snapshot.issues_in_progress:
            out += f"  issues_in_progress={snapshot.issues_in_progress}"
        return out, quiet, verbose
    if cmd == "quiet":
        return "(quiet toggled)", not quiet, verbose
    if cmd == "verbose":
        return "(verbose toggled)", quiet, not verbose
    return f"(unknown slash command: /{cmd})", quiet, verbose

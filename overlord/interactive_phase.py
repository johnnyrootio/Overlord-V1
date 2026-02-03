"""
Human-in-the-loop: interactive conversation per phase (0, 1, 2).

Phase 0, 1, 2 are agent-driven and highly interactive: the CLI orchestrates (moves to the phase,
hands off to Claude Code, does I/O). The agent uses its system prompt and tools (Superpowers
brainstorming, Context7, MCP) to reason and guide the conversation; the prompts give a minimum
set of topics but the agent drives the Q&A. When the user types /done, the agent outputs the
final deliverable and the phase ends. Phase 3 is deterministic (Issue Emitter, no agent).
Phase 4 is an endless-loop execution manager (different mode).

Slash commands (/help, /status, /done, /exit, /query) are handled by the CLI and never sent
to the agent—only non-command user input reaches the agent.
"""
import os
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import asyncio

from overlord.claude_api import (
    invoke_phase_agent_messages,
    is_api_configured,
    run_phase_interactive_async,
    run_phase_interactive_via_subprocess,
)
from overlord.multiclaude_recovery import get_multiclaude_repo_clone_path
from overlord.phase_log import (
    append_execution_log,
    ensure_phase_log_paths,
    load_conversation,
    save_conversation,
)
from overlord.prompts import get_phase_system_prompt

# Sentinel: get_user_input returns this to signal phase complete
PHASE_DONE = "__DONE__"
# Sentinel: get_user_input returns None to signal exit
USER_EXIT = None

# Max conversation turns per phase (avoid runaway)
DEFAULT_MAX_TURNS = 50


# One-time context prepended so the agent knows: prompts govern behavior; CLI flows I/O; slash commands never reach the agent.
_AGENT_CONTEXT = (
    "[Context: Your system prompt governs your behavior and the workflow. "
    "The CLI shows your messages to the user and passes the user's unstructured feedback back to you. "
    "Incorporate the user's input and continue in the direction of the phase workflow. "
    "Slash commands (/done, /help, etc.) are handled by the CLI and never appear here—you only see the user's conversational replies.]\n\n"
)


def _initial_message_for_phase(
    phase: int,
    genesis_spec_path: Optional[str],
    artifact_paths: Optional[Dict[str, str]],
    project_id: Optional[str] = None,
    repo_url: Optional[str] = None,
) -> str:
    """Build the first user message that primes the agent for this phase."""
    if phase == 0:
        msg = _AGENT_CONTEXT
        if repo_url:
            msg += (
                f"Project: {project_id or 'unknown'}. The repo is already set: {repo_url}. "
                "Do not ask for the repo name; proceed with bootstrap planning (e.g. tech stack, Gate 1). "
                "The CLI has already run multiclaude repo init for this repo. "
                "Do not include 'Run multiclaude repo init' (or repo creation) in your Gate 5 execution checklist; omit it and start with the next step (e.g. create directory structure).\n\n"
            )
        msg += (
            "Begin Phase 0 (Bootstrap). Use your brainstorming and the phase gates to guide the conversation. "
            "Minimum topics include tech stack, repo layout, check.sh scope, and CI—reason and ask as needed. "
            "When we are aligned, I will type /done and you will output the final bootstrap summary.\n\n"
        )
        if genesis_spec_path and Path(genesis_spec_path).is_file():
            try:
                msg += "Genesis spec:\n" + Path(genesis_spec_path).read_text(encoding="utf-8", errors="replace")
            except Exception:
                msg += "(genesis spec not readable)\n"
        return msg
    if phase == 1:
        msg = (
            _AGENT_CONTEXT
            + "Begin Phase 1 (Specifier). Use your brainstorming and the phase prompt to guide the conversation. "
            "Minimum topics include scope, tech choices, and priorities—reason and refine the spec interactively. "
            "When we are aligned, I will type /done and you will output the final plan and tasks (markdown).\n\n"
        )
        # Phase 0 → Phase 1 wiring: include bootstrap plan so Specifier does not re-ask for tech stack
        bootstrap_path = (artifact_paths or {}).get("bootstrap_plan")
        if bootstrap_path and Path(bootstrap_path).is_file():
            try:
                msg += (
                    "--- Phase 0 bootstrap outcome (tech stack, repo layout, check.sh) ---\n"
                    "Do not re-ask for language/framework; use the bootstrap plan below and produce the operational spec and task list.\n\n"
                )
                msg += Path(bootstrap_path).read_text(encoding="utf-8", errors="replace") + "\n\n"
            except Exception:
                pass
        if genesis_spec_path and Path(genesis_spec_path).is_file():
            try:
                msg += "Genesis spec:\n" + Path(genesis_spec_path).read_text(encoding="utf-8", errors="replace")
            except Exception:
                msg += "(genesis spec not readable)\n"
        return msg
    if phase == 2:
        msg = (
            _AGENT_CONTEXT
            + "Begin Phase 2 (Wave Planner). Use your prompt to guide the work graph; minimum is waves, tasks, dependencies. "
            "Use the Plan and Tasks below as the agreed scope; reason and ask one question at a time if needed. "
            "When we are aligned, I will type /done and you will output the final work graph as valid YAML with a top-level 'waves' key.\n\n"
        )
        for key in ("plan", "tasks"):
            path = (artifact_paths or {}).get(key)
            if path and Path(path).is_file():
                try:
                    msg += f"--- {key} ---\n" + Path(path).read_text(encoding="utf-8", errors="replace") + "\n\n"
                except Exception:
                    pass
        if "---" not in msg:
            msg += "(No plan or tasks files yet.)\n"
        return msg
    return "Begin this phase. When I type /done, output the final deliverable.\n"


def _final_instruction_for_phase(phase: int) -> str:
    """Instruction sent to agent when user types /done: ask for final deliverable."""
    if phase == 0:
        return (
            "The user has approved. Output the final bootstrap deliverable: "
            "a short summary (2–3 paragraphs) of tech stack, repo layout, and check.sh scope. "
            "Plain text is fine."
        )
    if phase == 1:
        return (
            "The user has approved. Output the final deliverable for Phase 1: "
            "the plan and task list in markdown. Use headings ## Plan and ## Tasks so we can parse them."
        )
    if phase == 2:
        return (
            "The user has approved. Output the final deliverable for Phase 2: "
            "the work graph as valid YAML only, with a top-level 'waves' key. "
            "Each wave has 'id' and 'tasks'; each task has 'id', 'title', 'depends_on'."
        )
    return "The user has approved. Output the final deliverable for this phase."


def run_phase_interactive(
    phase: int,
    project_id: str,
    state_root: str,
    genesis_spec_path: Optional[str],
    artifact_paths: Optional[Dict[str, str]],
    get_user_input: Callable[[str], Optional[str]],
    max_turns: int = DEFAULT_MAX_TURNS,
    repo_url: Optional[str] = None,
    artifacts_dir: Optional[Union[str, Path]] = None,
    verbose_ref: Optional[Dict[str, Any]] = None,
    prewarmed_client: Any = None,
) -> Optional[str]:
    """
    Run one phase (0, 1, or 2) as human-in-the-loop conversation.
    get_user_input(assistant_text) is called after each agent reply; it should display assistant_text,
    then read user input and return: the user's message to send to the agent, or PHASE_DONE to end
    the phase and request final deliverable, or None to exit entirely.
    Returns the final deliverable text (for the caller to write to plan.md, workgraph.yml, etc.),
    or None if user exited or API not configured.
    When phase is 0 and repo_url is set, the initial message tells the agent the repo is already set
    so it does not ask for the repo name.
    When artifacts_dir is set, conversation and execution log are written every turn (streaming logs).
    When verbose_ref is set and verbose_ref["verbose"] is True, progress lines are shown before each agent call.
    When prewarmed_client is set (async path only), use that connected client instead of creating one; caller must disconnect after.
    """
    if not is_api_configured():
        return None
    system_prompt = get_phase_system_prompt(phase) or ""
    if not system_prompt.strip():
        return None
    initial = _initial_message_for_phase(
        phase, genesis_spec_path, artifact_paths,
        project_id=project_id if phase == 0 else None,
        repo_url=repo_url if phase == 0 else None,
    )

    conv_path: Optional[str] = None
    log_path: Optional[str] = None
    if artifacts_dir:
        _artifacts_dir = Path(artifacts_dir)
        conv_path, log_path = ensure_phase_log_paths(_artifacts_dir, phase)

    existing = load_conversation(conv_path) if conv_path else []
    if existing:
        messages = existing
    else:
        messages = [{"role": "user", "content": initial}]
        if log_path:
            append_execution_log(
                log_path, phase, "context",
                "Phase %d interactive started" % phase,
                payload={"project_id": project_id},
            )

    cwd = str(Path(state_root) / "projects" / project_id) if (state_root and project_id) else None
    # Phase 0: run in repo clone when available so agent can create bootstrap files directly
    if phase == 0 and repo_url and cwd:
        clone_path = get_multiclaude_repo_clone_path(repo_url)
        if clone_path and os.path.isdir(clone_path):
            cwd = clone_path
    final_instruction = _final_instruction_for_phase(phase)

    # Use single long-lived SDK client when starting fresh (no existing conversation).
    # Avoids per-turn connect/disconnect and can prevent stdin contention by running in one event loop.
    if not existing:
        messages_ref: List[dict] = [{"role": "user", "content": initial}]

        def get_user_input_sync(assistant_text: str):
            messages_ref.append({"role": "assistant", "content": assistant_text or ""})
            if conv_path:
                save_conversation(conv_path, messages_ref)
            if log_path:
                append_execution_log(
                    log_path, phase, "assistant",
                    "Phase %d agent response" % phase,
                    payload={"response_preview": (assistant_text or "")[:500]},
                )
            user_input = get_user_input(assistant_text)
            if user_input is None or user_input == PHASE_DONE:
                return user_input
            if len(messages_ref) // 2 >= max_turns:
                return PHASE_DONE  # cap turns
            messages_ref.append({"role": "user", "content": user_input})
            if conv_path:
                save_conversation(conv_path, messages_ref)
            if log_path:
                append_execution_log(
                    log_path, phase, "context",
                    "user message",
                    payload={"preview": (user_input or "")[:200]},
                )
            return user_input

        verbose = bool(verbose_ref and verbose_ref.get("verbose"))
        # In a TTY, run the SDK in a subprocess with stdin=DEVNULL so the Claude Code
        # process does not block on the same stdin (avoids "stuck" after repo init).
        if sys.stdin.isatty():
            final = run_phase_interactive_via_subprocess(
                phase=phase,
                system_prompt=system_prompt,
                initial_user_message=initial,
                final_instruction=final_instruction,
                cwd=cwd,
                get_user_input_sync=get_user_input_sync,
                phase_done_sentinel=PHASE_DONE,
                verbose=verbose,
            )
        else:
            final = asyncio.run(
                run_phase_interactive_async(
                    phase=phase,
                    system_prompt=system_prompt,
                    initial_user_message=initial,
                    final_instruction=final_instruction,
                    cwd=cwd,
                    get_user_input_sync=get_user_input_sync,
                    phase_done_sentinel=PHASE_DONE,
                    verbose=verbose,
                    prewarmed_client=prewarmed_client,
                )
            )
        if final is not None and conv_path and log_path:
            messages_ref.append({"role": "user", "content": final_instruction})
            messages_ref.append({"role": "assistant", "content": final})
            save_conversation(conv_path, messages_ref)
            append_execution_log(
                log_path, phase, "action",
                "phase complete",
                payload={"deliverable_preview": (final or "")[:300]},
            )
        return final or None

    # Resume from existing conversation: use per-turn invoke (reconnects each time).
    turns = 0
    while turns < max_turns:
        turns += 1
        response = invoke_phase_agent_messages(phase, system_prompt, messages, cwd=cwd)
        messages.append({"role": "assistant", "content": response or ""})
        if conv_path:
            save_conversation(conv_path, messages)
        if log_path:
            append_execution_log(
                log_path, phase, "assistant",
                "Phase %d agent response" % phase,
                payload={"response_preview": (response or "")[:500]},
            )
        user_input = get_user_input(response)
        if user_input is None:
            return None
        if user_input == PHASE_DONE:
            break
        messages.append({"role": "user", "content": user_input})
        if conv_path:
            save_conversation(conv_path, messages)
        if log_path:
            append_execution_log(
                log_path, phase, "context",
                "user message",
                payload={"preview": (user_input or "")[:200]},
            )
    messages.append({"role": "user", "content": final_instruction})
    if conv_path:
        save_conversation(conv_path, messages)
    if log_path:
        append_execution_log(log_path, phase, "context", "request final deliverable", payload={})
    final = invoke_phase_agent_messages(phase, system_prompt, messages, cwd=cwd)
    if final:
        messages.append({"role": "assistant", "content": final})
        if conv_path:
            save_conversation(conv_path, messages)
        if log_path:
            append_execution_log(
                log_path, phase, "action",
                "phase complete",
                payload={"deliverable_preview": (final or "")[:300]},
            )
    return final or None

"""
Human-in-the-loop: interactive conversation per phase (0, 1, 2).

Agents are guided LLMs: the phase system prompts (agent_prompts/*.md) govern their behavior and
the workflow direction. The CLI is diligent in: (1) flowing the agent's questions/messages to the
user, (2) passing the user's unstructured feedback to the agent as the next message. The agent
acts in the direction of the workflow but incorporates ad hoc user input (questions, clarifications,
"change X") and stays on track. Slash commands (/help, /status, /done, /exit, /query) invoke
command-specific CLI actions and are never sent to the agent—only non-command user input reaches
the agent.
"""
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from overlord.claude_api import invoke_phase_agent_messages, is_api_configured
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
                "Do not ask for the repo name; proceed with bootstrap planning (e.g. tech stack, Gate 1).\n\n"
            )
        msg += (
            "Begin Phase 0 (Bootstrap). We will work through this phase together. "
            "Ask me one question at a time about tech stack, repo layout, check.sh scope, and CI. "
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
            + "Begin Phase 1 (Specifier). We will work through plan and tasks together. "
            "Ask me one question at a time about scope, tech choices, and priorities. "
            "When we are aligned, I will type /done and you will output the final plan and tasks (markdown).\n\n"
        )
        if genesis_spec_path and Path(genesis_spec_path).is_file():
            try:
                msg += "Genesis spec:\n" + Path(genesis_spec_path).read_text(encoding="utf-8", errors="replace")
            except Exception:
                msg += "(genesis spec not readable)\n"
        return msg
    if phase == 2:
        msg = (
            _AGENT_CONTEXT
            + "Begin Phase 2 (Wave Planner). We will work through the work graph (waves, tasks, dependencies) together. "
            "Use the plan and tasks below. Ask me one question at a time if needed. "
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
    messages: List[Dict[str, str]] = [{"role": "user", "content": initial}]
    turns = 0
    while turns < max_turns:
        turns += 1
        response = invoke_phase_agent_messages(phase, system_prompt, messages)
        if not response:
            return None
        user_input = get_user_input(response)
        if user_input is None:
            return None
        if user_input == PHASE_DONE:
            break
        messages.append({"role": "assistant", "content": response})
        messages.append({"role": "user", "content": user_input})
    # User said /done: request final deliverable
    final_instruction = _final_instruction_for_phase(phase)
    messages.append({"role": "assistant", "content": response})
    messages.append({"role": "user", "content": final_instruction})
    final = invoke_phase_agent_messages(phase, system_prompt, messages)
    return final or None

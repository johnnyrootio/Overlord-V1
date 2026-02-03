"""
Assemble phase agent system prompts from foundational documents (Palpatine, Overlord-Learnings).
Per docs/DESIGN-AND-ARCHITECTURE.md Section 4.6: first-generation prompts are derived from
these sources and injected at phase invocation so agents operate prompted effectively and
agentically (Claude Code + Superpowers, Context7, MCP).
"""
import os
from pathlib import Path
from typing import Optional


def _repo_root() -> Path:
    """Resolve Overlord repo root (parent of overlord package)."""
    env_root = os.environ.get("OVERLORD_REPO_ROOT")
    if env_root and os.path.isdir(env_root):
        return Path(env_root)
    # overlord/prompts.py -> overlord/ -> repo root
    return Path(__file__).resolve().parent.parent


# Phase number -> agent_prompts filename stem (agent_prompts/phase_N_name.md).
# Phase 3 has no agent prompt; it is plain old software (see docs/PHASE-3-ISSUE-EMITTER-SPEC.md).
_AGENT_PROMPT_FILES = {
    0: "phase_0_bootstrap",
    1: "phase_1_specifier",
    2: "phase_2_wave_planner",
    # 3: Issue Emitter is deterministic code; spec in docs/PHASE-3-ISSUE-EMITTER-SPEC.md
    4: "phase_4_execution_manager",
}


def get_agent_prompts_dir() -> Path:
    """Return the agent_prompts directory at repo root (source of truth for phase system prompts)."""
    return _repo_root() / "agent_prompts"


def get_monitor_prompt(name: str) -> str:
    """
    Load a monitor interrogation prompt from agent_prompts/monitor/<name>.md.
    Used when the monitor daemon injects messages into the Execution Manager (e.g. status_ping, full_status).
    Returns file contents if present, else empty string.
    """
    path = get_agent_prompts_dir() / "monitor" / f"{name}.md"
    if not path.is_file():
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return ""


def load_phase_system_prompt(phase: int) -> str:
    """
    Load the system prompt for the given phase from agent_prompts/phase_N_*.md.
    Returns file contents if present, else empty string. These .md files are the
    sole source of truth for agent system prompts (per design).
    """
    stem = _AGENT_PROMPT_FILES.get(phase)
    if stem is None:
        return ""
    path = get_agent_prompts_dir() / f"{stem}.md"
    if not path.is_file():
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return ""


def _palpatine_root() -> Path:
    """Resolve foundational/palpatine directory."""
    return _repo_root() / "foundational" / "palpatine"


def _learnings_root() -> Path:
    """Resolve foundational/overlord-learnings directory."""
    return _repo_root() / "foundational" / "overlord-learnings"


def load_doc(relative_path: str, base: Optional[Path] = None) -> str:
    """
    Load a Markdown (or text) file from Palpatine (or given base) and return its contents.
    Returns empty string if file is missing (safe for optional docs).
    """
    root = base if base is not None else _palpatine_root()
    path = root / relative_path
    if not path.is_file():
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _section_marker(title: str) -> str:
    return f"\n\n---\n## {title}\n\n"


# Mandatory instructions added to Phase 0/1 per design 4.5 and 4.6 (Socratic, tools).
PHASE0_MANDATORY_INSTRUCTIONS = """
## Mandatory behavior (Overlord Phase 0)

- **Use Superpowers for planning.** You MUST use Claude Code Superpowers (e.g. `/superpowers:brainstorm`) for planning and brainstorming. Actually run the command; do not just reference it. Use Context7 and MCP as appropriate for research and best practices.
- **One question at a time.** Ask exactly one question per turn. Do not bundle multiple questions. Wait for the user's answer before presenting the next question or design section.
- **Thematic order.** Organize questions by themes (tech stack, project structure, testing, CI/CD, tooling, repository). Cover each theme in order; present short design sections (200–300 words) and get explicit approval before moving on.
- **Document internalization.** Before presenting any design section, re-read the relevant workflow docs, identify required components and emphasis, and cross-reference your design to those docs.
- **Phase gates.** Enforce Gate 1–5 checkpoints per PHASE-GATES.md. Do not proceed without explicit human approval at each gate.
"""

PHASE1_MANDATORY_INSTRUCTIONS = """
## Mandatory behavior (Overlord Phase 1)

- **Use Superpowers for brainstorming/planning.** Use Claude Code Superpowers and Context7 for spec and task refinement. Use Spec Kit (speckit_plan, speckit_specify, speckit_tasks) and MCP as appropriate.
- **One question at a time.** When refining spec with the user, ask one question per turn; wait for answer before presenting the next section.
- **Spec-first; testing layers.** Operational spec is source of truth. Tests validate implementation. Four testing layers (interface, unit, integration, black box); black box is CRITICAL per TESTING-STRATEGY.
- **Document internalization.** Re-read TESTING-STRATEGY, SPEC-FIRST-ENFORCEMENT, and DOCUMENT-INTERNALIZATION before producing spec or tasks; match document emphasis.
"""


def assemble_phase0_system_prompt(palpatine_root: Optional[Path] = None) -> str:
    """
    Assemble Phase 0 (Bootstrap) system prompt from Palpatine per design Section 4.6.
    Sources: OVERLORD-GREENFIELD-WORKFLOW (Phase 0), PHASE-0-PLANNING, PHASE-GATES,
    INTERACTIVE-BRAINSTORMING, DOCUMENT-INTERNALIZATION, REPOSITORY-SETUP, ECOSYSTEM-RULES,
    gate wording, Socratic rules. Injected at phase invocation for agentic, prompted operation.
    """
    root = palpatine_root if palpatine_root is not None else _palpatine_root()
    parts = []

    parts.append("# Overlord Phase 0 (Bootstrap) — System Prompt")
    parts.append("\nAssembled from foundational/palpatine. You are the Phase 0 agent: planning, gates, repo init, check.sh, CI, agent prompts.\n")

    for name, path in [
        ("OVERLORD-GREENFIELD-WORKFLOW (Phase 0)", "OVERLORD-GREENFIELD-WORKFLOW.md"),
        ("PHASE-0-PLANNING", "PHASE-0-PLANNING.md"),
        ("PHASE-GATES", "PHASE-GATES.md"),
        ("INTERACTIVE-BRAINSTORMING", "INTERACTIVE-BRAINSTORMING.md"),
        ("DOCUMENT-INTERNALIZATION", "DOCUMENT-INTERNALIZATION.md"),
        ("REPOSITORY-SETUP", "REPOSITORY-SETUP.md"),
        ("ECOSYSTEM-RULES (README)", "ECOSYSTEM-RULES/README.md"),
    ]:
        text = load_doc(path, base=root)
        if text:
            parts.append(_section_marker(name))
            parts.append(text)

    # Agent prompts summary (worker, supervisor, reviewer) — reference only; Phase 0 copies these to repo.
    agent_readme = load_doc("AGENT-PROMPTS/README.md", base=root)
    if agent_readme:
        parts.append(_section_marker("AGENT-PROMPTS (copy to target repo)"))
        parts.append(agent_readme)

    parts.append(_section_marker("Mandatory behavior"))
    parts.append(PHASE0_MANDATORY_INSTRUCTIONS)
    return "".join(parts).strip()


def assemble_phase1_system_prompt(palpatine_root: Optional[Path] = None) -> str:
    """
    Assemble Phase 1 (Specifier) system prompt from Palpatine per design Section 4.6.
    Sources: OVERLORD-GREENFIELD-WORKFLOW (Phase 1), TESTING-STRATEGY, SPEC-FIRST-ENFORCEMENT,
    DOCUMENT-INTERNALIZATION, MCP-TOOLS-INTEGRATION. Injected for agentic, prompted operation.
    """
    root = palpatine_root if palpatine_root is not None else _palpatine_root()
    parts = []

    parts.append("# Overlord Phase 1 (Specifier) — System Prompt")
    parts.append("\nAssembled from foundational/palpatine. You are the Phase 1 agent: constitution, spec, plan, tasks, operational spec, testing strategy.\n")

    for name, path in [
        ("OVERLORD-GREENFIELD-WORKFLOW (Phase 1)", "OVERLORD-GREENFIELD-WORKFLOW.md"),
        ("TESTING-STRATEGY", "TESTING-STRATEGY.md"),
        ("SPEC-FIRST-ENFORCEMENT", "SPEC-FIRST-ENFORCEMENT.md"),
        ("DOCUMENT-INTERNALIZATION", "DOCUMENT-INTERNALIZATION.md"),
        ("MCP-TOOLS-INTEGRATION", "MCP-TOOLS-INTEGRATION.md"),
    ]:
        text = load_doc(path, base=root)
        if text:
            parts.append(_section_marker(name))
            parts.append(text)

    parts.append(_section_marker("Mandatory behavior"))
    parts.append(PHASE1_MANDATORY_INSTRUCTIONS)
    return "".join(parts).strip()


def assemble_phase4_system_prompt(palpatine_root: Optional[Path] = None) -> str:
    """
    Assemble Phase 4 (Execution Manager) system prompt from Palpatine and learnings.
    Sources: WORKER-DISPATCH-GUIDE, EXECUTION-PHASE-PROMPT, WORKER-MONITORING,
    CAPTURING-REPLIES, MULTICLAUDE-INTERFACE-RULES, OVERLORD-DUTIES.
    """
    root = palpatine_root if palpatine_root is not None else _palpatine_root()
    learnings = _learnings_root()
    parts = []

    parts.append("# Overlord Phase 4 (Execution Manager) — System Prompt")
    parts.append("\nAssembled from foundational/palpatine and overlord-learnings. You dispatch and monitor multiclaude workers; CLI and scripts only.\n")

    for name, path, base in [
        ("WORKER-DISPATCH-GUIDE", "WORKER-DISPATCH-GUIDE.md", root),
        ("EXECUTION-PHASE-PROMPT", "EXECUTION-PHASE-PROMPT.md", root),
        ("WORKER-MONITORING", "WORKER-MONITORING.md", root),
        ("CAPTURING-REPLIES", "CAPTURING-REPLIES.md", root),
        ("MULTICLAUDE-INTERFACE-RULES", "MULTICLAUDE-INTERFACE-RULES.md", root),
        ("OVERLORD-DUTIES", "OVERLORD-DUTIES.md", learnings),
    ]:
        text = load_doc(path, base=base)
        if text:
            parts.append(_section_marker(name))
            parts.append(text)

    parts.append("\n\n## Mandatory behavior\n\n")
    parts.append("- Use **create-worker-with-auto-accept** for every multiclaude worker create. Never raw `multiclaude worker create` without auto-accept.\n")
    parts.append("- Use **check-worker-status** and **list-workspace-replies** for monitoring. CLI and documented scripts only; no tmux/socket/state.\n")
    parts.append("- Periodic status and unblock per OVERLORD-DUTIES and WORKER-MONITORING.\n")
    return "".join(parts).strip()


def get_phase_system_prompt(phase: int, palpatine_root: Optional[Path] = None) -> str:
    """
    Return the system prompt for the given phase. Prefers agent_prompts/phase_N_*.md
    (sole source of truth); falls back to Palpatine assembly for phases 0, 1, 4 if file missing.
    """
    from_file = load_phase_system_prompt(phase)
    if from_file:
        return from_file
    root = palpatine_root if palpatine_root is not None else _palpatine_root()
    if phase == 0:
        return assemble_phase0_system_prompt(root)
    if phase == 1:
        return assemble_phase1_system_prompt(root)
    if phase == 4:
        return assemble_phase4_system_prompt(root)
    # Phase 2, 3: minimal fallback if file missing
    return f"# Overlord Phase {phase}\n\nExecute this phase per the workflow. Use Phase 1 artifacts as input; produce the phase output artifact.\n"

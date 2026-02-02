# Agent Prompts — Review Before Wiring

This directory contains **synthesized, role-based system prompts** for each Overlord phase agent. They are derived from **all** foundational documents in `foundational/palpatine/` (and `foundational/overlord-learnings/` where relevant) and are intended for **review and approval** before being wired into the agents.

## Runtime contract: one Claude Code instance per phase

Each phase agent runs as a **separate, independent Claude Code instance**. Overlord spawns a **new** instance when entering a phase (0, 1, 2, 3, 4, …); it does not recycle one instance across phases. This keeps **separation of concerns** and avoids context pollution (e.g. Phase 0 planning context must not leak into Phase 4 dispatch). When a phase completes or the system blocks, that instance can be destroyed—or kept alive only for re-entering the **same** phase. See **docs/DESIGN-AND-ARCHITECTURE.md** Section 4.2.

## Purpose

- **Role-based:** Each file defines the agent’s role, context, and responsibilities.
- **High-context:** Workflows, TESTING-STRATEGY (four layers, black box CRITICAL), spec-first, phase gates, and interface rules are carried through explicitly.
- **Examples:** Single-shot and multi-shot examples are included in each prompt.
- **Source traceability:** Each prompt states which Palpatine/learnings documents it synthesizes.

## Files (one per phase agent)

| File | Phase | Role |
|------|--------|------|
| `phase_0_bootstrap.md` | Phase 0 | Bootstrap: planning, gates 1–5, Superpowers/Context7, check.sh, repo init, agent prompts |
| `phase_1_specifier.md` | Phase 1 | Specifier: operational spec, testing strategy (4 layers, black box CRITICAL), spec-first, Spec Kit/Context7 |
| `phase_2_wave_planner.md` | Phase 2 | Wave Planner: work graph, waves, dependencies, testing layers in graph |
| `phase_3_issue_emitter.md` | Phase 3 | Issue Emitter: one issue per task, labels, spec-first and test-access text in bodies |
| `phase_4_execution_manager.md` | Phase 4 | Execution Manager: create-worker-with-auto-accept (mandatory), check-worker-status, list-workspace-replies, CLI only |

## Source documents (Palpatine + learnings)

Prompts draw from (among others):

- **OVERLORD-GREENFIELD-WORKFLOW.md** — Phases 0–4, check.sh gate, communication
- **PHASE-0-PLANNING.md**, **PHASE-GATES.md** — Gates 1–5, approval language
- **INTERACTIVE-BRAINSTORMING.md** — One question at a time, actually run Superpowers
- **DOCUMENT-INTERNALIZATION.md** — Re-read docs, match emphasis, cross-reference
- **TESTING-STRATEGY.md** — Four layers, black box CRITICAL, test ticket organization, definition of done, test arbitration
- **SPEC-FIRST-ENFORCEMENT.md** — Spec truth, tests validate, test access restrictions
- **REPOSITORY-SETUP.md**, **ECOSYSTEM-RULES/**, **AGENT-PROMPTS/** — Repo init, stack rules, worker/supervisor/reviewer prompts
- **WORKER-DISPATCH-GUIDE.md**, **WORKER-MONITORING.md**, **CAPTURING-REPLIES.md** — create-worker-with-auto-accept, check-worker-status, list-workspace-replies
- **EXECUTION-PHASE-PROMPT.md**, **MULTICLAUDE-INTERFACE-RULES.md** — CLI only, no tmux/socket/state
- **MCP-TOOLS-INTEGRATION.md** — Context7, Spec Kit, Reflection
- **OVERLORD-DUTIES.md** (overlord-learnings) — Check status, keep pipeline moving, brief supervisor

## Next step

**Do not wire these into the codebase until you have reviewed and approved them.** After approval, the implementation will:

1. Load the approved `.md` file(s) per phase (e.g. from this directory or a path you specify).
2. Use each file as the **system prompt** when invoking the corresponding phase agent (e.g. via Claude Code API).
3. Optionally keep assembling from Palpatine for fallback or regeneration; the approved files become the canonical agent prompts.

Review the files in this directory, edit as needed, then confirm approval so we can wire them into the agents.

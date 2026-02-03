# Design Rationale (Post-Refactor)

## Who owns what

- **Graph (`overlord/graph.py`)** – Owns the full pipeline: Phase 0 → 1 → 2 → 3 → 4. All phase logic and agent calls live in graph nodes. The graph is the single place that runs phase agents.
- **CLI (`overlord/cli.py`)** – Thin: repo Q&A, persistence (load/save `SessionState`), and a single call to `invoke_pipeline()` with `start_phase` / `max_phase`. No direct agent calls; no phase orchestration.
- **Prompts (`overlord/prompts.py`)** – Used by the graph (and previously by the CLI). `get_phase_system_prompt(phase)` loads **`agent_prompts/phase_N_*.md` first** (source of truth); falls back to Palpatine assembly if the file is missing. The graph pulls prompts via this function in each phase node.
- **Agents (`overlord/agents/phase1.py`, `phase2.py`, `phase4.py`)** – Phase 0 (graph + interactive_phase), 1, 2, and 4 are Claude Code agents via the Claude Agent SDK: they call `invoke_phase_agent` / `invoke_phase_agent_messages` when `is_api_configured()`. Phase 3 is deterministic (Issue Emitter: gh + JSON).

## Plumbing

1. **Prompts** – `agent_prompts/*.md` are the source of truth. `prompts.py` exposes `get_phase_system_prompt(phase)`, which reads those files; the graph uses it in every phase node. Palpatine assembly is fallback only.
2. **State** – `SessionState` (phase, artifact_paths, repo_url, etc.) is persisted by the CLI. The CLI builds the input dict for `invoke_pipeline()` from `SessionState`, calls the graph, then merges the result back with `_sync_state_from_result()`.
3. **CLI ↔ graph** – One direction: CLI → graph (invoke with state) → result. CLI then syncs result into `SessionState` and saves. No bidirectional “dialogue” yet; Phase 1 multi-turn dialogue is still pending.

## Phase roles: agent-driven vs deterministic vs automaton

| Phase | Mode | Who drives | Implementation |
|-------|------|------------|-----------------|
| **0** | Agent-driven, interactive, brainstorming | Claude Code (prompt + Superpowers, Context7, MCP) | CLI orchestrates I/O; agent uses phase prompt and tools; user types /done to end phase. |
| **1** | Agent-driven, highly interactive, brainstorming | Claude Code (prompt + Superpowers, Spec Kit, Context7) | Same: CLI I/O; agent reasons and refines spec; /done → final plan and tasks. |
| **2** | Agent-driven, interactive | Claude Code (prompt + plan/tasks context) | Same: CLI I/O; agent produces work graph; /done → final YAML. |
| **3** | Deterministic | No agent | Issue Emitter: workgraph → GitHub issues (gh + JSON). Plain old software. |
| **4** | Endless-loop execution manager | Claude Code (Execution Manager agent) | CLI runs `while True` until workgraph complete or user /exit; agent gets user/monitor messages and acts (dispatch workers, reason, tools). Different mode: automaton to meet goals. |

**Phases 0, 1, 2:** The CLI moves to the phase and **hands off** to Claude Code. The agent uses its system prompt (and tools: Superpowers brainstorming, Context7, MCP) to **reason** and guide the conversation; the prompts give a **minimum set** of topics (e.g. framework, scope) but the **agent drives** the Q&A. When the user types **/done**, the agent outputs the final deliverable and the phase ends.

**Phase 4:** Executive execution manager; runs as an **endless-loop automaton** to meet its goals (dispatch workers, monitor, unblock). User/monitor can send messages or type **/exit** to quit.

## Phase 0, 1, 2, 4 as Claude Code agents (Agent SDK)

Phases 0, 1, 2, and 4 use `overlord/claude_api.py` with the **Claude Agent SDK** (Claude Code instances): `invoke_phase_agent` / `invoke_phase_agent_messages` when `ANTHROPIC_API_KEY` (or `CLAUDE_CODE_API_KEY`) is set. Phase 3 does not call Claude; it uses gh + YAML/JSON.

**Agents as guided by prompts:** The phase system prompts (`agent_prompts/*.md`) govern agent behavior. The CLI orchestrates: it flows the agent's replies to the user and passes the user's **unstructured feedback** back to the agent. **Slash commands** (/help, /status, /done, /exit, /query) are handled by the CLI and never sent to the agent.

**Human-in-the-loop (phases 0, 1, 2):** Interactive conversations: the agent proposes/asks (using its prompt and tools, e.g. Superpowers brainstorming), you respond, and you type **/done** when aligned; the agent then outputs the final deliverable.

**Execution (Phase 4):** Endless loop; the system tracks execution (workers, issues, health). You can **/status** (workers, health, liveness) and send messages to the Execution Manager, or **/exit** to quit.

## Note on `get_graph()`

With `StateGraph(dict)` and conditional entry, some LangGraph versions may raise when calling `compiled_graph.get_graph()` (used for drawing). `invoke()` and `invoke_pipeline()` work as intended.

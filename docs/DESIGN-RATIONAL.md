# Design Rationale (Post-Refactor)

## Who owns what

- **Graph (`overlord/graph.py`)** – Owns the full pipeline: Phase 0 → 1 → 2 → 3 → 4. All phase logic and agent calls live in graph nodes. The graph is the single place that runs phase agents.
- **CLI (`overlord/cli.py`)** – Thin: repo Q&A, persistence (load/save `SessionState`), and a single call to `invoke_pipeline()` with `start_phase` / `max_phase`. No direct agent calls; no phase orchestration.
- **Prompts (`overlord/prompts.py`)** – Used by the graph (and previously by the CLI). `get_phase_system_prompt(phase)` loads **`agent_prompts/phase_N_*.md` first** (source of truth); falls back to Palpatine assembly if the file is missing. The graph pulls prompts via this function in each phase node.
- **Agents (`overlord/agents/phase1.py`, `phase2.py`, `phase4.py`)** – Phase 1, 2, and 4 are Claude Code agents: they call `invoke_phase_agent(N, system_prompt, user_message)` when `is_api_configured()`. Phase 3 is deterministic (Issue Emitter: gh + JSON).

## Plumbing

1. **Prompts** – `agent_prompts/*.md` are the source of truth. `prompts.py` exposes `get_phase_system_prompt(phase)`, which reads those files; the graph uses it in every phase node. Palpatine assembly is fallback only.
2. **State** – `SessionState` (phase, artifact_paths, repo_url, etc.) is persisted by the CLI. The CLI builds the input dict for `invoke_pipeline()` from `SessionState`, calls the graph, then merges the result back with `_sync_state_from_result()`.
3. **CLI ↔ graph** – One direction: CLI → graph (invoke with state) → result. CLI then syncs result into `SessionState` and saves. No bidirectional “dialogue” yet; Phase 1 multi-turn dialogue is still pending.

## Phase 1, 2, 4 as Claude agents

Yes. Each of those phases uses `overlord/claude_api.py`: `invoke_phase_agent(phase, system_prompt, user_message)` when `ANTHROPIC_API_KEY` (or `CLAUDE_CODE_API_KEY`) is set. Phase 3 does not call Claude; it uses gh + YAML/JSON.

**Agents as guided LLMs:** The phase system prompts (agent_prompts/*.md) govern agent behavior and the workflow direction. The CLI is diligent in flowing the agent's questions to the user and passing the user's **unstructured feedback** to the agent; the agent incorporates that feedback and continues in the direction of the workflow. **Slash commands** (/help, /status, /done, /exit, /query) invoke **command-specific CLI actions** and are never sent to the agent—only non-command user input reaches the agent.

**Human-in-the-loop (phases 0, 1, 2):** When `ANTHROPIC_API_KEY` is set, phases 0, 1, and 2 run as interactive conversations: the agent proposes/asks (guided by the prompt), you respond with unstructured feedback, and you type **/done** when the phase is complete; the agent then outputs the final deliverable.

**Execution (Phase 4):** The system keeps track of execution (workers, issues, health). You can **query the system** while it runs: **/status** (workers, health, liveness) and **/query** &lt;question&gt; (returns current execution state plus your question so you can see state).

## Note on `get_graph()`

With `StateGraph(dict)` and conditional entry, some LangGraph versions may raise when calling `compiled_graph.get_graph()` (used for drawing). `invoke()` and `invoke_pipeline()` work as intended.

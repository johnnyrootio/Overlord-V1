# Overlord Agent V1 — Implementation Plan and Roadmap

> **For Claude:** Use **executing-plans** when implementing this plan task-by-task. Use **Context7** MCP for up-to-date LangGraph and Click docs. Use **SpecKit** MCP (speckit_plan, speckit_specify, speckit_tasks) when refining phase-agent specs or task breakdowns from foundational docs.

**Goal:** Deliver the first working Overlord Agent V1: CLI, stateful sessions, graph runtime, phase-aligned agents, human-in-the-loop (gates, resume), multiclaude integration (CLI + scripts only), status subsystem (multiclaude monitor), and interactive/chat-like CLI. Success = system autonomously builds a trivial todo app with human only at phase gates.

**Architecture:** Python app with Click CLI; LangGraph for phase graph (StateGraph, nodes = phases, checkpointing, interrupts for gates); local state under `~/.overlord/projects/<id>/`; phase agents invoked by graph runtime (Claude Code API); multiclaude monitor as timer-driven loop feeding CLI; CLI supports commands + in-session slash commands + proactive status stream. See **docs/DESIGN-AND-ARCHITECTURE.md** and **docs/OVERLORD-CLI-SPEC.md**.

**Tech stack:** Python 3.11+; LangGraph (StateGraph, add_node, add_edge, checkpointer, interrupt for human-in-the-loop); Click (group, commands, options); Claude Code API for phase agents; multiclaude CLI + documented scripts only. **Context7** and **SpecKit** used during implementation for docs and spec/task refinement.

**Key docs:** docs/DESIGN-AND-ARCHITECTURE.md, docs/OVERLORD-AGENT-V1-SPEC.md, docs/OVERLORD-CLI-SPEC.md, docs/SEQUENCE-PHASES-5-8.md, docs/MULTICLAUDE-REFERENCE.md, foundational/palpatine/, foundational/overlord-learnings/, scripts/.

---

## 1. Prototype progression (P0 → P6)

| Prototype | Name | Outcome |
|-----------|------|---------|
| **P0** | Skeleton | Project layout, package installable, `overlord --help` works. |
| **P1** | State and CLI | In-memory state model; CLI start/list (stub). Unit tests for state and CLI. |
| **P2** | Persistence and graph | State save/load to `~/.overlord/projects/<id>/`; minimal LangGraph (one Phase 0 stub node). Start → exit → resume loads same project. |
| **P3** | Gates and scripted input | Phase gates interrupt; pending question persisted; resume surfaces and accepts answer. Scenario file format and runner. |
| **P4** | Scripted greenfield path | Full greenfield scripted run (spec + Gate 1–5 answers) with stub Phase 0; resume-in-the-middle test. No real multiclaude/GitHub/Claude yet. |
| **P5** | Integrations | Real GitHub (repo, issues), multiclaude (CLI + scripts), Claude Code (phase agents/workers). Graph runs Phase 0 → Phase 3 → Phase 4 with real integrations. **Status subsystem (multiclaude monitor)** and **interactive CLI** (slash commands, proactive status stream) in scope. |
| **P6** | First working V1 | Trivial todo app spec; full autonomous run (human at gates only). Working trivial todo app; check.sh passes. |

---

## 2. Chunked implementation (C1–C16)

### P0 — Skeleton
- **C1. Layout and roadmap:** Create `overlord/` (Python package), `tests/`, `scenarios/`, this ROADMAP-V1.md; pyproject.toml with entry point `overlord`; Python 3.11+, LangGraph, Click. Verify: dirs exist, `pip install -e .`, `overlord --help`.

### P1 — State and CLI
- **C2. State model:** Session state schema (phase, project_id, pending_questions, artifact_paths); in-memory representation. Unit tests: state create, set phase, add pending question.
- **C3. CLI skeleton:** Click group; commands `start`, `list`, `run`, `resume`, `status` (stub behavior). Tests: CLI parses; `start <spec-path>` exits 0; `list` prints expected format. Align with **docs/OVERLORD-CLI-SPEC.md**.

### P2 — Persistence and graph
- **C4. State persistence:** State Manager save/load to `~/.overlord/projects/<project-id>/`; atomic writes. Tests: save, load, idempotent; integration: start → exit → resume same project.
- **C5. Graph runtime (minimal):** LangGraph StateGraph, one node (Phase 0 stub), single edge, checkpointer (e.g. InMemorySaver then file-based). Unit test: invoke graph, assert state update.
- **C6. Phase 0 stub agent:** Node reads genesis spec path from state, writes minimal artifact path, sets phase_0_done. Unit test: run node, assert artifact path and phase transition.

### P3 — Gates and scripted input
- **C7. Gates and HITL:** At gate (e.g. Gate 1), graph interrupts; state stores pending_question; CLI prints prompt and exits. Resume: read answer (stdin or scripted), clear pending, continue. Tests: state pending_question; integration: run until gate → exit → resume with answer → progression.
- **C8. Scripted scenario format:** Scenario file (e.g. YAML: spec_path, gate_responses). Runner feeds responses when Overlord blocks. Test: run with scenario; gate I/O and state.

### P4 — Scripted greenfield path
- **C9. First scripted scenario:** Greenfield with greenfield-specs/example-todo-app.md; canned Gate 1–5 answers. Integration test: run Overlord with scenario; phase progression and state.
- **C10. Resume in scripted run:** Two-step run (start → gate → exit; resume → answer → continue). Assert pending surfaced and state correct.

### P5 — Integrations + status + interactive CLI
- **C11. Phase 0 real / Claude Code:** Phase 0 node uses Claude Code API; real bootstrap (repo init, check.sh, CI, etc.) per workflow. Gate interrupts unchanged. Integration test: Phase 0 with real/minimal Claude; repo and artifacts exist.
- **C12. Phase 3 — GitHub issues:** Phase 3 creates real repo and issues from work graph (gh CLI or API); labels. Integration test: repo and issues exist.
- **C13. Phase 4 — multiclaude dispatch:** Phase 4 uses multiclaude CLI only: **create-worker-with-auto-accept** per worker, check-worker-status, list-workspace-replies. Per WORKER-DISPATCH-GUIDE and MULTICLAUDE-INTERFACE-RULES. Integration test: workers created, replies captured.
- **C14. Claude Code for workers + status subsystem:** Multiclaude workers run via Claude Code. **Multiclaude monitor:** Timer loop (e.g. every minute) gathers status (worker list, check-worker-status, list-workspace-replies, optional PR/issue state); feeds CLI. **Interactive CLI:** In-session slash commands (`/status`, `/phase`, `/help`, `/quiet`, `/verbose`); proactive status line each interval during execution phase; intercontextual chat (agents push questions, user answers). See docs/DESIGN-AND-ARCHITECTURE.md Section 8.4 and docs/OVERLORD-CLI-SPEC.md Sections 4 and 6. Integration test: one wave with real integrations; status visible in CLI.

### P6 — First working V1
- **C15. Trivial todo app spec:** Minimal greenfield spec (add, list, mark done); single or two waves; suitable for autonomous build.
- **C16. First working V1 test:** End-to-end: Overlord builds trivial todo app (human at gates only, scripted or real); target repo exists; app runs; ./scripts/check.sh passes.

---

## 3. Implementation layout

| Purpose | Location |
|---------|----------|
| Implementation | `overlord/` (cli, state, graph, agents, storage, monitor) |
| Tests | `tests/` (unit, integration) |
| Scenarios | `scenarios/` (YAML scenario files) |
| Plan / roadmap | This file (ROADMAP-V1.md) |
| Design and spec | docs/ (DESIGN-AND-ARCHITECTURE.md, OVERLORD-AGENT-V1-SPEC.md, OVERLORD-CLI-SPEC.md, SEQUENCE-PHASES-5-8.md) |

---

## 4. Tools and MCP (Context7, SpecKit)

- **Context7:** Use **query-docs** (after **resolve-library-id**) for LangGraph (StateGraph, checkpointer, interrupt) and Click (group, commands, options) when implementing graph runtime and CLI. Limit 3 calls per question; use best info if not found.
- **SpecKit:** Use **speckit_plan** (with a spec file and tech stack) if generating a technical plan from a spec; **speckit_specify**, **speckit_tasks** when refining phase-agent specs or task lists from foundational/palpatine. Phase 0/1 agents use Spec Kit and Context7 per design; implementation can use SpecKit MCP to derive or validate task breakdowns.

---

## 5. Status subsystem (multiclaude monitor) — ownership by the system

- **When:** Implement in P5 (C14 or dedicated sub-chunk). Required for execution-phase “very good status” (learnings).
- **What:** Timer-driven loop (e.g. every 60s) when a project session is active (Phase 4+). Gather via **CLI/scripts only**: `multiclaude worker list`, `check-worker-status.sh`, `list-workspace-replies.sh`, optional gh/API. Snapshot: workers, issues in progress, liveness, CPU/file activity (co-located host). Feed CLI for proactive display and `/status` interrogation. Surface multiclaude health (daemon up, repo inited). See docs/DESIGN-AND-ARCHITECTURE.md Section 8.4.
- **Wiring:** `overlord/monitor.py` provides `gather_status()` and `format_snapshot_tables()`. **CLI:** `overlord status <project_id>` calls `gather_status` and prints summary + tables; `overlord run` shows one status line after advancing; while **waiting for user input** in phase 4+ (stdin, no `--responses`), a **background thread** runs the monitor every 60s (env `OVERLORD_STATUS_INTERVAL_SEC`) and echoes a short line to stderr; `/quiet` suppresses. **Slash commands** (`/status`, `/phase`, `/help`) call `gather_status` on demand. Phase 4 agent uses reconciliation and dispatch; it does not run the timer.

---

## 6. Interactive CLI and slash commands

- **When:** P5; align with C14 and CLI spec.
- **What:** Planning phases (0, 1): chat-like (agent questions, user answers). Execution phase (4+): proactive status stream + Q&A. **Slash commands:** `/status`, `/phase`, `/help`, `/quiet`, `/verbose` in-session. **Intercontextual chat:** agents push questions to CLI; one shared context. See docs/OVERLORD-CLI-SPEC.md Sections 4 and 6.

---

## 7. Verification per chunk

- **C1:** Dirs + roadmap; `overlord --help`.
- **C2:** State unit tests.
- **C3:** CLI command tests.
- **C4:** Persistence tests; start → exit → resume.
- **C5:** Graph invoke test.
- **C6:** Phase 0 stub node test.
- **C7:** Gate interrupt + resume test.
- **C8:** Scenario runner test.
- **C9:** Scripted greenfield scenario test.
- **C10:** Resume-in-the-middle test.
- **C11:** Phase 0 real bootstrap test.
- **C12:** Phase 3 issues test.
- **C13:** Phase 4 dispatch test.
- **C14:** Full graph + status subsystem + interactive CLI test.
- **C15:** Todo spec exists.
- **C16:** E2E “Overlord builds trivial todo app.”

---

## 8. Out of scope for V1

- Brownfield and Project Ingester (later).
- Full Phase 0 superpowers (minimal/real Phase 0 in scope).
- Overlord section in target repo (optional/later).
- Packaging/test-reporting phases (learnings; optional for trivial todo).

---

## 9. Backlog

Planned or done items tracked as part of the roadmap:

| Item | Status | Notes |
|------|--------|--------|
| **List projects** | Done | `overlord list` lists known projects with phase and pending count; `--format json` for machine output. |
| **Remove project by name** | Done | `overlord rm <project_id>` deletes project state under `~/.overlord/projects/<id>/`; `--yes` skips confirmation. |
| Real-API E2E (gh + multiclaude + Claude) | Optional | Full “Overlord builds trivial todo app” in a real repo. |
| Maintenance commands | Later | e.g. `overlord inspect <project>`, `overlord checkpoint`, `overlord clean`, export/backup. |

---

## 10. Next step

1. **P0:** Execute C1 (layout + ROADMAP-V1.md).
2. **P1:** C2, C3 + tests.
3. **P2:** C4, C5, C6 + tests; verify start → exit → resume.
4. **P3:** C7, C8; gates and scenario runner.
5. **P4:** C9, C10; scripted greenfield and resume test.
6. **P5:** C11–C14; real integrations, multiclaude monitor, interactive CLI.
7. **P6:** C15, C16; trivial todo app and E2E success.
8. **Post-P6 (Phase 1 in workflow):** After gates cleared, run **Phase 1 (Specifier)** stub: writes plan.md, tasks.md; state advances to phase 1. Implemented: `overlord/agents/phase1.py`, CLI invokes Phase 1 when last gate answered; E2E asserts phase=1 and Phase 1 artifacts.
9. **Phase 2 (Wave Planner):** When phase=1 and no pending, run **Phase 2** stub: writes workgraph.yml (waves, tasks, depends_on); state advances to phase 2. Implemented: `overlord/agents/phase2.py`, `_advance_phase_if_ready()` in CLI; E2E asserts phase=2 and workgraph.yml.
10. **Phase 3 (Issue Emitter):** When phase=2 and no pending, run **Phase 3** stub: emit_issues(workgraph_path) writes issues.json; state advances to phase 3. `_advance_phase_if_ready()` runs phases in a loop (1→2→3) so one resume batch reaches phase 3. E2E asserts phase=3 and issues.json.
11. **Phase 4 (Execution Manager):** When phase=3 and no pending, run **Phase 4** stub: run_phase4_execution_manager() persists phase_4_system_prompt.md; state advances to phase 4. `_advance_phase_if_ready()` runs 1→2→3→4 in one batch. E2E asserts phase=4 and phase_4_system_prompt.md. Stub only; real multiclaude dispatch in C13.

**C11 (Phase 0 real / Claude Code) — in progress:** Anthropic SDK added; `overlord/claude_api.py` provides `invoke_phase_agent()` and `is_api_configured()`. Phase 0 graph node calls Claude when `ANTHROPIC_API_KEY` or `CLAUDE_CODE_API_KEY` is set (one instance per phase); persists `phase_0_claude_response.txt`. Gate interrupts unchanged. Integration test: stub path (no key) and optional real-API path (key set). Full agentic bootstrap (repo init, check.sh, CI via tools) is future work.

**C13 (Phase 4 multiclaude dispatch) — done:** Phase 4 loads issues.json, derives repo from repo_url (shared repo_utils.repo_url_to_owner_repo), and when repo + scripts_dir available calls create_worker(repo, "Issue #N: title") per issue via create-worker-with-auto-accept.sh; then list_workspace_replies and persists phase_4_workspace_replies.txt. CLI passes repo_url and scripts_dir (Overlord repo scripts/ or OVERLORD_SCRIPTS_DIR). Unit test: stub scripts → workers created, replies captured.

**C14 (status subsystem + interactive CLI) — done:** gather_status is implemented in Python (monitor.py; no shell scripts). Status command and `overlord status <project_id>` use it; full tables when repo and health ok. **Timer loop:** When in execution phase (phase >= 4) and waiting for user input (stdin), a background thread runs the monitor every 60s (configurable via `OVERLORD_STATUS_INTERVAL_SEC`) and echoes a short status line to stderr; `/quiet` suppresses proactive lines. Slash commands `/status`, `/phase`, `/help`, `/quiet`, `/verbose` handled in-session.

**C15 (trivial todo app spec) — done:** `greenfield-specs/trivial-todo-app.md` exists: minimal spec (add, list, mark done; single wave). Scenario `scenarios/trivial-todo-app.yaml` has repo name + 5 gate responses for scripted run.

**C16 (first working V1 test) — done:** E2E test `tests/integration/test_first_working_v1.py` runs scenario with trivial-todo-app (stub path: no Claude API so test is fast); asserts phase 1→4, artifacts (plan.md, tasks.md, workgraph.yml, issues.json, phase_4_system_prompt.md), and `./scripts/check.sh` exists and passes.

**Next (post-P6):** Optional: real-API E2E (with gh + multiclaude + Claude) for full “Overlord builds trivial todo app” in a real repo.

Use **executing-plans** for task-by-task implementation; use **Context7** and **SpecKit** as needed during implementation.

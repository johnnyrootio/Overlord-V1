# Overlord Agent V1 — Design and Architecture

This document describes the design and architecture of Overlord Agent V1: a semi-autonomous, multi-agent system that orchestrates software development workflows via a CLI, with stateful sessions, reentrant phases, and integration with multiclaude and GitHub.

**Foundational documents**: The **Palpatine** directory and **Overlord-Learnings** directory are the source of truth for workflow definition, phase gates, spec-first enforcement, testing strategy, **multiclaude worker dispatch**, worker monitoring, and prior learnings. **In this bundle**: Palpatine = `foundational/palpatine/`, Overlord-Learnings = `foundational/overlord-learnings/`; scripts = `scripts/`. Overlord Agent V1 does not redefine these—it implements them. See the spec (`OVERLORD-AGENT-V1-SPEC.md`) for the full Foundational Documents table and synthesis requirements. This design doc references them where they shape architecture and components.

**multiclaude as a system**: Design and workflows are grounded in **multiclaude’s actual behavior**. Source and a short reference live in this repo: **multiclaude-src/** (clone of `github.com/dlorenc/multiclaude`) and **MULTICLAUDE-REFERENCE.md** (in this folder). Implementers and the Execution Manager (Phase 4) must align with multiclaude’s CLI, daemon, state, messages, and worker lifecycle as described there.

**Distinction: Overlord phase agents vs multiclaude workers.** Overlord's **phase agents** (Phase 0, Phase 1, Phase 4, etc.) are the core of Overlord Agent V1; they are communicated with via the **Claude Code API** and do **not** have a dispatch or security-prompt problem. **Multiclaude worker instances** are different: they are the workers that **multiclaude** spawns (separate Claude Code processes) to implement work on the **target project**. **Multiclaude worker dispatch** is the act of creating and unblocking those multiclaude-managed workers; *those* instances can get stuck at a security prompt, which is why create-worker-with-auto-accept is mandatory when the Phase 4 agent instructs multiclaude to create workers. References to "worker dispatch," "worker creation," and the auto-accept script in this doc mean **multiclaude worker dispatch**—not the Overlord phase agents themselves.

---

## 1. Overview

Overlord Agent V1 replaces the "Cursor session as Overlord" model with a **stateful, resumable agentic system**. A human interacts with it through a **CLI**. The system:

- Walks the user through a **multi-phase workflow** (planning, brainstorm, work graph, issues, dispatch, review, etc.)
- Uses **multiple phase-aligned agents** (Phase 0, Phase 1, …) with well-defined interfaces (state + file artifacts)
- Runs on a **graph runtime** (e.g. LangGraph) with **reentrant** phases (e.g. return to Phase 0 for more brainstorming)
- Supports **three entry scenarios**: greenfield (from genesis spec), resume (from checkpoint), brownfield (project ingester → Phase 1)
- **Blocks only when human input is required** (phase gates, unstick, optional review); in later phases, multiclaude keeps running while Overlord waits
- **Exits when blocked**, persists state and pending questions; on re-entry, **automatically surfaces and asks** pending questions and reminds the user which phase they are in
- Keeps **state** locally (per-project) and **durable context** in the **target repo** (Overlord section)

One Overlord run **actively manages one project** at a time; the project list is used to **select which project to re-enter**.

---

## 2. High-Level Interfaces

The following diagram shows the main actors and interfaces.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              HUMAN (Visionary)                                   │
└───────────────────────────────────────┬─────────────────────────────────────────┘
                                        │
                                        │ CLI (start, resume, list, run, status)
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         OVERLORD AGENT V1 (This System)                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Graph     │  │   State     │  │   Phase     │  │   Human-in-the-Loop     │  │
│  │   Runtime   │  │   Manager   │  │   Agents    │  │   (gates, unstick,     │  │
│  │   (e.g.     │  │   (local +  │  │   (0,1,2..  │  │    pending questions)  │  │
│  │   LangGraph)│  │   checkpoint)│  │   Ingester) │  │                         │  │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └────────────┬────────────┘  │
│         │                │                │                       │                │
│         └────────────────┴────────────────┴───────────────────────┘                │
│                                    │                                                │
│                          State + Artifacts (MD/JSON)                                │
└────────────────────────────────────┬───────────────────────────────────────────────┘
                                     │
         ┌───────────────────────────┼───────────────────────────┐
         │                           │                           │
         ▼                           ▼                           ▼
┌─────────────────┐       ┌─────────────────────┐       ┌─────────────────────┐
│  Local State    │       │  Target Repo        │       │  multiclaude        │
│  ~/.overlord/   │       │  (e.g. barista)     │       │  (CLI only)         │
│  projects/      │       │  .overlord/         │       │  worker create,     │
│  <project-id>/  │       │  decisions, spec    │       │  message send,      │
│  state,         │       │  history, context,  │       │  work list, etc.    │
│  checkpoints/   │       │  optional checkpoints│       │  + scripts          │
└─────────────────┘       └─────────────────────┘       └─────────────────────┘
```

**Summary of interfaces:**

| Interface | Direction | Description |
|-----------|-----------|-------------|
| Human ↔ CLI | Bidirectional | Commands (start, resume, list, run, status); prompts and user answers; status output. See **OVERLORD-CLI-SPEC.md** in this folder for the CLI specification. |
| Graph Runtime ↔ Phase Agents | Internal | Invokes phase agents; passes state; agents return updated state + next-step hint |
| Phase Agents ↔ State Manager | Read/Write | Read/write state object; read/write artifact files (project directory + optional repo) |
| Overlord ↔ Target Repo | Write (Overlord section), Read (rest) | Overlord section: decisions, spec history, context summary, optional checkpoint blobs. Issues/PRs via multiclaude or GitHub API as defined by workflow |
| Overlord ↔ multiclaude | Via CLI only | All interaction through multiclaude CLI (and documented scripts); no tmux/socket/state bypass |

---

## 3. Session and State Model

### 3.1 Session

- **One session = one target project** from start to finish.
- Sessions are **long-lived**: the process may start and stop; after a failure or exit, the user can resume.
- **Resume** = load project state (and optional checkpoint), then continue; if there are **pending questions**, surface and ask them first and remind the current phase.

### 3.2 State Storage

**Local (per project):**

- **Location**: e.g. `~/.overlord/projects/<project-id>/`
- **Contents**: Current state (phase, history, pointers to artifacts, pending prompts), checkpoint files (e.g. `checkpoints/phase-0-done.json`), ephemeral data.
- **Durability**: Atomic writes (e.g. write to temp file, then rename) so a crash does not corrupt state.

**Target repo (Overlord section):**

- **Location**: e.g. `<target-repo>/.overlord/` or `overlord/`
- **Contents** (always): Decisions log, spec/requirements history, context summary (for resume and context graph).
- **Optional** (config/flag): Checkpoint blobs at phase boundaries so the repo is self-contained and state can be reconstructed from repo alone.
- **Sync**: Written at phase boundaries (and optionally at key sub-steps); committed and pushed so the repo holds a versioned history.

### 3.3 Checkpointing and Aggregation

- **Local checkpoint**: On phase completion (and optionally after critical sub-steps), write a checkpoint file atomically; resume loads "last good" state.
- **Repo sync**: After the same milestones, aggregate from local state into the Overlord section (decisions, spec history, context summary; optionally checkpoint blobs), then commit and push.
- **Episodic memory** (e.g. MCP or future integration) can store "what we were doing" for the current run; the repo stores the long-term record.

---

## 4. Agent Topology and Graph

### 4.1 Phase-Aligned Agents

- **One agent per phase** (Phase 0, Phase 1, Phase 2, …) plus an optional **Project Ingester** for brownfield.
- Each agent has:
  - A **system prompt** derived from **Palpatine** workflow docs. Concretely:
    - **Phase 0**: OVERLORD-GREENFIELD-WORKFLOW (Phase 0 section), PHASE-0-PLANNING, PHASE-GATES (Gate 1–5), INTERACTIVE-BRAINSTORMING, DOCUMENT-INTERNALIZATION, REPOSITORY-SETUP, ECOSYSTEM-RULES for selected stack, hooks.json.template, AGENT-PROMPTS (to copy to repo). **Socratic brainstorming**: Planning and brainstorming MUST be Socratic (one question at a time, themed, comprehensive design in mind); see **Section 4.5** below.
    - **Phase 1**: OVERLORD-GREENFIELD-WORKFLOW (Phase 1), TESTING-STRATEGY (all four layers; black box CRITICAL), SPEC-FIRST-ENFORCEMENT, DOCUMENT-INTERNALIZATION, MCP-TOOLS-INTEGRATION (SpecKit, Context7). Same Socratic discipline applies when refining spec with the user; see **Section 4.5**.
    - **Phase 2–3**: Work graph and issues per workflow; TESTING-STRATEGY (test ticket organization), SPEC-FIRST-ENFORCEMENT. **Phase 3** creates GitHub issues in the target repo; those issues are the formal work items for multiclaude workers.
    - **Phase 4 (dispatch)**: WORKER-DISPATCH-GUIDE (**multiclaude worker dispatch**—create-worker-with-auto-accept **mandatory** when instructing multiclaude to create workers), EXECUTION-PHASE-PROMPT, WORKER-MONITORING (check-worker-status for multiclaude workers), CAPTURING-REPLIES (list-workspace-replies), MULTICLAUDE-INTERFACE-RULES, OVERLORD-DUTIES.
    - **Phase 5+**: Review, deadlock breakers per OVERLORD-GREENFIELD-WORKFLOW; SPEC-FIRST-ENFORCEMENT (reviewer checks spec compliance).
  - **Sequence diagram (Worker + Phases 5–8)**: See **SEQUENCE-PHASES-5-8.md** in this folder for the Mermaid sequence diagram of how multiclaude workers and Phase 5 (Review Orchestrator) through Phase 8 (Loop Controller) interact. A rendered view is in **sequence-phases-5-8-diagram.html** (open in a browser).
  - **Prompt augmentation** at spawn: current phase, phase history, paths to read (spec, decisions, context summary), and any directive (e.g. "re-entering Phase 0 to expand scope").
  - A **tool set** for that phase (hard-coded at first): e.g. Phase 0 → superpowers, Context7, file I/O; Phase 4 → multiclaude CLI **only**, scripts **create-worker-with-auto-accept** (for multiclaude worker dispatch), **check-worker-status**, **list-workspace-replies** (no tmux/socket/state access). Overlord phase agents are driven via Claude Code API and do not have the security-prompt dispatch problem.

### 4.1a. Agent Specifications (by Function)

Agents are named by function. The **work graph** is developed in **Phase 2 (Wave Planner)**; **GitHub issues** are emitted from the work graph in **Phase 3 (Issue Emitter)**. The work graph is the execution plan (waves, dependencies); issues are the concrete work items workers implement.

**Work graph vs. issues:**

- **Work graph** (Phase 2): Single artifact (e.g. `workgraph.yml`). Defines tasks, waves, and dependencies. Source of truth for what to do and in what order. Stored in project/repo.
- **GitHub issues** (Phase 3): One issue per task from the work graph. Labels (wave, area, risk) come from the work graph. Issues are the formal work items multiclaude workers consume.

**multiclaude interface:** Overlord MUST interact with multiclaude ONLY via multiclaude CLI and documented scripts (create-worker-with-auto-accept, auto_accept_workers, check-worker-status, list-workspace-replies). No tmux, socket API, or direct access to `~/.multiclaude/state.json` or worktrees. See **foundational/palpatine/MULTICLAUDE-INTERFACE-RULES.md**.

| Agent | Name | Function | Key inputs | Key outputs | Tools |
|-------|------|----------|------------|-------------|-------|
| Phase 0 | Bootstrap | Make repo agent-ready: planning (gates 1–5), repo create/init, check.sh, CI, agent prompts, hooks. | Genesis spec path; human at Gate 1–5. | Repo on GitHub; check.sh; CI; CLAUDE.md; agent overrides; hooks. | Superpowers, Context7, gh CLI, multiclaude repo init, file I/O. |
| Phase 1 | Specifier | Turn intent into executable spec + tasks: constitution, spec, plan, tasks, operational spec, testing strategy; prescribe interface contracts in contracts/. | State; genesis spec; Phase 0 artifacts. | specs/ (constitution, plan, specify, tasks); docs/ (operational-specification, testing-strategy); prescribe contracts/ (cli-commands.yaml, data-schema.json). | Spec Kit, Context7, superpowers, file I/O. |
| Phase 2 | Wave Planner | Develop the work graph: order Phase 1 tasks into waves with dependencies; produce workgraph.yml; Wave 0 tasks reference contracts/. | specs/, docs/ (plan, tasks, operational-spec, testing-strategy). | workgraph.yml (waves, tasks, depends_on, area, risk; tasks reference contracts/ paths). | File I/O. |
| Phase 3 | Issue Emitter | Emit GitHub issues from work graph: one issue per task with goal, acceptance criteria, labels (wave, area, risk). | workgraph.yml; repo name. | GitHub issues in target repo; issue ids. | gh CLI or GitHub API. |
| Phase 4 | Execution Manager | Manage execution: dispatch workers (create-worker-with-auto-accept), monitor (check-worker-status, list-workspace-replies), unblock, report status. | State; work graph; GitHub issues; multiclaude. | Workers created/unblocked; PRs merged; state updated. | multiclaude CLI + scripts only (no tmux/socket/state). |
| Phase 5 | Review Orchestrator | Ensure quality: trigger review, handle feedback, spawn fix workers, spec compliance. | State; PR list; multiclaude. | Reviews done; blocking issues fixed; PRs merged. | multiclaude CLI; gh/API. |
| Phase 6 | Deadlock Breaker | Detect and resolve deadlocks (merge conflicts, duplicate work, stalls). | State; multiclaude status; PR/issue state. | Blocker issues; deadlocks cleared. | multiclaude CLI; gh/API. |
| Phase 7 | Stop Controller | Evaluate stop conditions (wave complete, budget guard); emit progress summary. | State; work graph; issue/PR status. | Decision (continue/pause/stop); summary. | gh/API; state. |
| Phase 8 | Loop Controller | Repeat from Specifier (or Bootstrap) for next features; optional human checkpoints. | State; prior cycle outcomes. | Transition to Phase 1 (or 0). | — |

All phase agents derive system prompts and behavior from **foundational/palpatine/** (OVERLORD-GREENFIELD-WORKFLOW, PHASE-GATES, TESTING-STRATEGY, SPEC-FIRST-ENFORCEMENT, WORKER-DISPATCH-GUIDE, etc.). Testing strategy is defined in **foundational/palpatine/TESTING-STRATEGY.md** (four layers, black box CRITICAL, test ticket organization, definition of done, test arbitration).

### 4.2 Graph Structure

- **Nodes**: Phase 0, Phase 1, Phase 2, Phase 3, Phase 4, … ; optional Ingester.
- **Edges**: Allow transitions between phases as defined by the workflow; **reentrant** edges (e.g. Phase 2 → Phase 0) when "more brainstorming" or similar is needed.
- **Orchestrator**: The **graph runtime** (e.g. LangGraph) decides the next node from current state and edges; agents do not invoke each other.
- **Entry points**:
  - **Greenfield**: Start at Phase 0; input = path to genesis spec (greenfield-specs format).
  - **Resume**: Load state; resume at node indicated by state.
  - **Brownfield**: Run **Ingester** first; then **always** enter at **Phase 1** (Brainstorm & Converge).

```
                    ┌──────────────┐
                    │   Ingester   │
                    │  (brownfield)│
                    └──────┬───────┘
                           │
                           ▼
    ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
    │   Phase 0    │──▶│   Phase 1    │──▶│   Phase 2    │
    │  Bootstrap   │   │  Brainstorm  │   │  Work Graph  │
    └──────┬───────┘   └──────┬───────┘   └──────┬───────┘
           ▲                  │                   │
           │                  │                   ▼
           │                  │            ┌──────────────┐
           │                  └───────────▶│   Phase 3    │   ...
           │                               │   Issues     │
           │                               └──────┬───────┘
           │                                      │
           └──────────────────────────────────────┘
                    (reentrant edges)
```

### 4.2 One Claude Code Instance per Phase (Separation of Concerns)

- **Each phase agent runs as a separate, independent Claude Code instance.** Overlord must **not** recycle a single Claude Code instance across phases. When entering a phase (Phase 0, 1, 2, 3, 4, …), Overlord **spawns a new Claude Code instance** for that phase, injects that phase’s system prompt and inputs (state, artifact paths), and uses that instance only for the duration of that phase. When the phase completes or the system blocks/exits, that instance can be destroyed—or kept alive only if the design explicitly supports re-entering the **same** phase with the same instance to preserve in-session context.
- **No context pollution between phases.** Different phases have different duties, prompts, and tool sets. Sharing one instance across phases would mix context (e.g. Phase 0 planning vs Phase 4 dispatch) and violate separation of concerns. Implementations must ensure: **one running Claude Code instance per phase (or per phase invocation)**; no reuse of one instance for multiple phases.
- **Re-entry:** If the user resumes and re-enters a phase (e.g. back to Phase 0 for more brainstorming), Overlord may either spawn a **new** instance for that phase (clean context, with state/artifacts passed in) or reuse a previously kept-alive instance for that **same** phase if the system is designed to keep phase instances alive for state. In either case, Phase 1 must never run in the same instance as Phase 0 or Phase 4; each phase identity has its own instance.

### 4.3 Handoff Between Agents

- **State object** (in-memory / checkpointed): Holds current phase, phase history, project id, **pointers** (paths or keys) to artifacts, pending prompts, etc.
- **Artifacts on disk**: The actual contract between agents is **files** in a well-known layout (e.g. `spec.md`, `decisions.md`, `workgraph.yaml`, `context-summary.md`). Agents read and update these; state holds only references.
- When a phase agent finishes, it (1) updates the state object (e.g. `phase_0_complete`, artifact paths), (2) writes/updates artifact files. The graph runtime chooses the next node (including reentry).

### 4.3a Target Repo Layout (Prescribed)

The **target project repository** (the repo Overlord plans and workers implement) follows a **prescribed layout**. See **docs/PROJECT-REPO-LAYOUT.md** for the full specification; reference implementation: [johnnyrootio/robotic-barista](https://github.com/johnnyrootio/robotic-barista).

- **specs/** — **Mandatory** Overlord planning outputs (Phase 1): `constitution.md`, `plan.md`, `specify.md`, `tasks.md`. These are the source of truth for Phase 2 (work graph) and Phase 3 (issues).
- **docs/** — Operational and testing docs: `operational-specification.md` (source of truth for behavior), `testing-strategy.md` (four layers, definition of done). Phase 1 produces these; Phase 2 and workers consume them.
- **contracts/** — **Mandatory**: all interfaces must be defined and have contracts. At minimum: CLI interface (`contracts/cli-commands.yaml`), data/API schema (`contracts/data-schema.json` or equivalent). Interface contract tests (Wave 0) create or update contract files and verify behavior; implementers implement to spec and contracts, not to test code.
- **workgraph.yml** — Phase 2 output; repo root or known path. Schema and example: **docs/WORKGRAPH-EXAMPLE.md**.
- **scripts/check.sh** — Gate for "working software"; Phase 0 ensures it exists; definition of done in issues requires it to pass.

Phase 1 must produce artifacts in **specs/** and **docs/**; Phase 2 reads from them and writes **workgraph.yml**; Phase 3 emits issues that reference **contracts/** and **specs/** in task bodies. All interfaces must have contracts; Wave 0 tasks in the work graph define and verify them.

### 4.4 Tool and MCP Configuration

- **Graph runtime**: We use **core LangGraph** (`StateGraph`, nodes, edges, state, interrupts) for V1. **Deep Agents** (dynamic planning, subagent spawning) are an optional future refinement—e.g. Phase 1 could later be implemented as a Deep Agent if it needs internal dynamic planning or sub-delegation.
- **Tools in LangGraph**: Tools are standard Python functions or LangChain `Runnable`s. For each phase node we **inject the relevant tools** into that node (or into the LLM it uses, e.g. via `bind_tools()`). Example: Phase 0 gets superpowers + Context7; Phase 4 gets multiclaude CLI and scripts (create-worker-with-auto-accept, check-worker-status, list-workspace-replies). LangGraph `context_schema` can pass config or tool sets at runtime.
- **Separation**: **Agent code** (Python LangGraph nodes), **prompts** (external Markdown from Palpatine), and **tools** (dedicated Python modules) are kept separate; tools are passed in explicitly, not hard-wired in agent code.
- **MCP for phase agents**: Phase agents run as **Claude Code** instances driven by the Overlord Python app via the **Claude Code API**. **One instance per phase** (see Section 4.2): each phase gets its own Claude Code instance; no recycling of one instance across phases. **V1 assumption**: Claude Code instances on the local system have all MCP servers they need (e.g. via Cursor/Claude Code project or environment config). Phase agents use whatever MCP is already available in that environment; Overlord does not discover or pass MCP config in the first iteration. **Future release**: Orchestrator-configured MCP—Overlord holds config listing MCP servers, instantiates the Claude Code API client **per phase** (new instance per phase) with the required MCP server information (URLs, discovery paths, or pre-configured MCP client), and phase agents use MCP through that pre-configured client so Overlord, not the environment, controls which MCPs each phase sees.
- **Claude Code plugins and prompting**: The **Claude Code instances** used by Overlord (the phase agents) are assumed to have **several plugins** available: **MCP servers**, **MCP**, **Superpowers**, **Context7**, and others. In **early phases** (Phase 0 planning, Phase 1 brainstorming and spec), it must be **assumed and explicitly prompted** that those phase agents **use Superpowers for planning** (e.g. brainstorming, design exploration) and use Context7, MCP, and other tools as appropriate. Phase 0 and Phase 1 system prompts MUST instruct the agent to use Superpowers (and other available tools) for planning and brainstorming—not rely on the agent to infer it.

### 4.5 Socratic Planning and Brainstorming

Planning and brainstorming (Phase 0 and Phase 1) must be **Socratic**: the system asks questions **one at a time**, organized around **themes**, with a **comprehensive design in mind** so that key elements of a good design are explicitly explored and validated with the user.

- **One question at a time**: During the brainstorming session, ask **one question at a time** and wait for the user's response before asking the next. Phase 0 / Phase 1 agent prompts MUST state: ask exactly one question per turn; do not bundle multiple questions; wait for the user's answer before presenting the next question or design section (per **INTERACTIVE-BRAINSTORMING.md** and **PHASE-GATES.md**).
- **Questions organized by themes**: Group questions by themes that map to a comprehensive design. Suggested themes (from **PHASE-0-PLANNING.md**, **INTERACTIVE-BRAINSTORMING.md**, **PHASE-GATES.md**): tech stack (Gate 1), project structure, testing (layers, tooling, black box), CI/CD (gate and pipeline), development tooling, repository and agents (multiclaude, Overlord section). Cover each theme in order; within a theme, ask one question at a time and only after user validation present a short design section (200–300 words) and get explicit approval before moving on.
- **Comprehensive design in mind**: The agent should have a **comprehensive design checklist** derived from foundational documents (e.g. **OVERLORD-GREENFIELD-WORKFLOW**, **TESTING-STRATEGY**, **ECOSYSTEM-RULES**, **DOCUMENT-INTERNALIZATION**). Before presenting any design section, the agent MUST re-read the relevant workflow docs, identify required components and emphasis, and cross-reference the design to those docs. Questions are aimed at filling in and validating that design so nothing critical is skipped.
- **Use of Superpowers and tools**: Phase 0 and Phase 1 prompts must **explicitly instruct** the agent to use **Superpowers** for planning and brainstorming (e.g. invoke Superpowers brainstorming/planning flows) and to use **Context7**, **MCP**, and other available plugins as appropriate. Do not assume the agent will use them without being prompted; the assembled system prompt must state that these tools are available and should be used for planning and design exploration.
- **Prompt improvements for first generation**: Phase 0 / Phase 1 system prompts must explicitly require one question per turn, thematic order, document internalization before each design section, and short validated sections (200–300 words). Scenario and test fixtures should reflect one-answer-per-gate and per-question flows. First-generation prompts must be extracted and consolidated from foundational documents (see **Section 4.6**).

### 4.6 First-Generation Prompts: Extraction from Foundational Documents

Overlord's first-generation phase prompts must be **derived from** the existing Palpatine and Overlord-Learnings documents rather than written from scratch.

**Extraction map:**

| Use | Source document(s) | What to extract |
|-----|--------------------|-----------------|
| **Phase 0 system prompt** | OVERLORD-GREENFIELD-WORKFLOW (Phase 0), PHASE-0-PLANNING, PHASE-GATES, INTERACTIVE-BRAINSTORMING, DOCUMENT-INTERNALIZATION, REPOSITORY-SETUP, ECOSYSTEM-RULES, hooks.json.template, AGENT-PROMPTS (README, worker, supervisor, reviewer) | Planning workflow; **use Superpowers (and Context7/MCP) for planning**; one question at a time; thematic order; gate checkpoints (Gate 1–5); document internalization before each section; repo create/init; check.sh and CI; agent prompts copy to repo; ecosystem rules application. |
| **Phase 1 system prompt** | OVERLORD-GREENFIELD-WORKFLOW (Phase 1), TESTING-STRATEGY, SPEC-FIRST-ENFORCEMENT, DOCUMENT-INTERNALIZATION, MCP-TOOLS-INTEGRATION (SpecKit, Context7) | **Use Superpowers for brainstorming/planning**, Spec Kit, Context7; spec and tasks production; testing layers (black box CRITICAL); spec-first; internalization. |
| **Phase 4 system prompt** | WORKER-DISPATCH-GUIDE, EXECUTION-PHASE-PROMPT, WORKER-MONITORING, CAPTURING-REPLIES, MULTICLAUDE-INTERFACE-RULES, OVERLORD-DUTIES | create-worker-with-auto-accept mandatory; check-worker-status; list-workspace-replies; CLI-only; no tmux/socket/state; periodic status; unblock. |
| **Phase 5–8 behavior** | OVERLORD-GREENFIELD-WORKFLOW (Phases 5–8), AGENT-PROMPTS/reviewer.md, SPEC-FIRST-ENFORCEMENT (review layer) | Review loop (spec compliance first); deadlock types and actions; stop conditions; loop back to Phase 1/0. |
| **Socratic brainstorming** | INTERACTIVE-BRAINSTORMING, PHASE-GATES (Gate 2), PHASE-0-PLANNING (Step 1–3) | One question at a time; **prompt agent to use Superpowers for planning**; present 200–300 word sections; validate before proceeding; actually run superpowers; thematic areas. |
| **Gate wording** | PHASE-GATES (each gate) | Exact checkpoint text and required approval language for Gate 1–5. |
| **multiclaude agent prompts (target repo)** | AGENT-PROMPTS/worker.md, supervisor.md, reviewer.md | Copy into target repo per Phase 0; spec-first overrides; reply to workspace; test arbitration. |

**Where prompts live:** Overlord phase agents: system prompts are **assembled** by the Overlord app from the above sources (e.g. Markdown under `foundational/palpatine/`) and injected at phase invocation. multiclaude agents (worker, supervisor, reviewer): templates live in **foundational/palpatine/AGENT-PROMPTS/**; Phase 0 **copies** them into the target repo (e.g. `<repo>/.multiclaude/agents/`) so multiclaude loads them as repository overrides. When doing the detailed design of each phase agent, implementers should (1) pull the listed sources into a single "phase prompt assembly" per phase, and (2) add explicit Socratic rules (Section 4.5) into the Phase 0 and Phase 1 prompt assembly.

**Implementation (prompted, agentic operation):** The Overlord codebase implements **prompt assembly** in `overlord/prompts.py`: it loads Palpatine (and Overlord-Learnings) docs per the extraction map above and assembles Phase 0, Phase 1, and Phase 4 system prompts, including mandatory instructions (Superpowers for planning, one question at a time, Socratic rules, spec-first, etc.). These assembled prompts are **persisted** per project (e.g. `artifacts/phase_0_system_prompt.md`) when each phase runs, so that when Overlord invokes phase agents via the **Claude Code API**, it passes the assembled system prompt and the agent operates **prompted effectively** and **agentically** (using Claude Code capabilities, Superpowers, Context7, MCP). **When wiring the Claude Code API (C11+), spawn one new Claude Code instance per phase**; do not reuse one instance across phases (see Section 4.2). Stub phase implementations (file-writing only) are placeholders until the Claude Code API is wired; the prompt layer is in place so agents are ready to operate with full Palpatine-derived prompts.

---

## 5. Human-in-the-Loop

### 5.1 When the System Blocks

- **Phase gates** (per **PHASE-GATES.md**): Gate 1 (Tech Stack), Gate 2 (Brainstorming completion), Gate 3 (Context7 research if separate), Gate 4 (Implementation plan approval), Gate 5 (Execution approval). **Hard block** — no progress without explicit human approval. Required approval language (e.g. "Yes, proceed to planning", "Yes, approve plan"); vague responses must be confirmed. Phase 0 agent MUST enforce these before proceeding.
- **Explicit "human decision needed"** (unstick, arbitration, ambiguous requirement): **Soft block** in Phase 4+ — orchestration pauses, **multiclaude keeps running**; when human responds, Overlord resumes.
- **Optional review checkpoints** (e.g. review work graph before Phase 3): Configurable; when enabled, block until human confirms or provides feedback.

### 5.2 Exit and Resume

- When blocking, Overlord **persists state** (including pending questions), **prints the prompt** (and reminder of current phase), then **exits**.
- User does **not** need to remember to "resume": when they run Overlord again for that project, the system **automatically** surfaces pending questions and asks them, and reminds which phase they are in.
- **Discovery**: `overlord` or `overlord list` shows projects and which have pending questions; user selects project to re-enter.

### 5.3 Proactive Pending

- On any run, after loading project state, if there are **pending questions**, Overlord presents them and gets answers before doing any other work.
- It is Overlord's **duty** to ensure these questions are asked and satisfied.

---

## 6. Three Entry Scenarios

| Scenario   | Entry        | First node   | Input / State source                    |
|-----------|--------------|--------------|-----------------------------------------|
| Greenfield| start        | Phase 0      | Path to genesis spec (greenfield-specs) |
| Resume    | resume/run   | From state   | Local + optional repo checkpoint        |
| Brownfield| ingest       | Ingester → Phase 1 | Repo path; ingester output = draft spec + context |

- **Brownfield**: Ingester produces initial spec-like document and context; workflow **always** enters at **Phase 1** (Brainstorm & Converge), not Phase 0.

---

## 7. Overlord Section in Target Repo

- **Purpose**: Durable, shareable context so any Overlord run (or another Overlord instance) can resume and understand "what we decided and why"; also for a broader context graph.
- **Always**: Decisions log, spec/requirements history, context summary.
- **Optional** (config): Checkpoint blobs at phase boundaries for full reconstruction from repo.
- **Layout** (example):  
  `overlord/` or `.overlord/`  
  - `decisions.md` or `decisions/`  
  - `spec-history/` or evolving spec doc  
  - `context.md` (or small set of files)  
  - `checkpoints/` (if enabled)

---

## 8. Integration Rules

### 8.1 multiclaude Integration (Design Grounding)

Design and workflows **take into account multiclaude’s real behavior** (see **multiclaude-src/** and **MULTICLAUDE-REFERENCE.md** in this folder). Summary:

- **Architecture**: multiclaude is a Go CLI + daemon; CLI talks to daemon over Unix socket; daemon owns `~/.multiclaude/state.json`, drives tmux (one session per repo, one window per agent), and starts Claude Code via `pkg/claude`. Workers get a dedicated git worktree and tmux window; messages live under `~/.multiclaude/messages/<repo>/<agent>/`.
- **Why create-worker-with-auto-accept is required (CLI idiosyncrasy)**: multiclaude starts workers by running Claude Code with `--dangerously-skip-permissions`. In practice, **Claude Code can still show a “Bypass Permissions” security prompt before honoring that flag**, so the worker process blocks waiting for user input. If no one sends the accept key, the worker never starts. **`scripts/create-worker-with-auto-accept.sh`** exists to avoid that: it (1) runs `multiclaude worker create --repo <repo> "<task>"`, (2) waits ~5 seconds for the security prompt to appear, (3) runs `scripts/auto_accept_workers.sh <repo>` to send the accept key(s) into the worker’s tmux pane(s), (4) optionally verifies the Claude process is running. Without this sequence, workers frequently get stuck; with it, non-interactive dispatch is reliable. **Overlord’s Execution Manager MUST use this script (or the same sequence) for every worker create**; raw `multiclaude worker create` alone is not sufficient.
- **Replies**: Supervisor and workers are instructed to reply via `multiclaude message send workspace "..."`. Those messages land in the **workspace** agent’s inbox (`~/.multiclaude/messages/<repo>/workspace/`). Overlord uses **`scripts/list-workspace-replies.sh [repo-name]`** to read them (CAPTURING-REPLIES). So “workspace” is the designated inbox for Overlord.
- **Interface boundary**: Overlord MUST use **only** multiclaude CLI and **documented scripts**. No tmux, socket API, or direct access to `~/.multiclaude/state.json` or worktrees (except documented debug with human approval). Documented scripts (e.g. create-worker-with-auto-accept, auto_accept_workers, check-worker-status, list-workspace-replies) may perform steps that would otherwise be forbidden (e.g. reading state for verification); Overlord itself must not parse state.json or manipulate tmux/worktrees.

### 8.2 Integration Rules (Summary)

- **multiclaude** (per **MULTICLAUDE-INTERFACE-RULES.md** and **WORKER-DISPATCH-GUIDE.md**):
  - Interact **only** via multiclaude CLI and **documented scripts**. No tmux, socket API, or direct access to `~/.multiclaude/state.json` or worktrees except documented debug exceptions with **human approval**.
  - **Multiclaude worker dispatch**: When the Phase 4 agent instructs multiclaude to create workers (for the target project), MUST use `./scripts/create-worker-with-auto-accept.sh <repo-name> "<task>"` for **every** such worker. Those multiclaude worker instances get stuck at the security prompt without the auto-accept step; this script is the only reliable path. If the script is unavailable, fallback is `multiclaude worker create` followed by `./scripts/auto_accept_workers.sh <repo-name>` after ~5s (MANDATORY). Overlord's own phase agents use Claude Code API and do not have this dispatch problem.
  - **Multiclaude worker monitoring**: Use `./scripts/check-worker-status.sh <repo-name>` to determine liveness of **multiclaude workers** (shell + Claude Code process + activity). Per **WORKER-MONITORING.md**: check before creating new multiclaude workers; act on stuck workers (nudge, kill/recreate) per activity/stuck scores.
  - **Capturing replies**: Supervisor and multiclaude workers reply to workspace; Overlord captures via `./scripts/list-workspace-replies.sh [repo-name]` per **CAPTURING-REPLIES.md**.
- **Target repo**: Overlord section for state/context; repo creation/init per **REPOSITORY-SETUP.md**; issues and collaboration via multiclaude and GitHub API as per workflow; no heavy direct repo manipulation beyond that.
- **Issue generation**: **Phase 3** is solely responsible for **creating GitHub issues** in the target repository. Those issues are the formal work items that multiclaude workers consume. This defines the work-generation contract between Overlord and multiclaude.
- **Repository initialization (greenfield)**: The **first question** in Phase 0 is **"What's the name of this repo?"** (see **docs/PROJECT-REPO-LAYOUT.md** §0). After getting repo name (and optionally visibility/owner), Overlord **creates the GitHub repository** (e.g. via `gh repo create <repo-name>` or GitHub API). Immediately after, Overlord **calls `multiclaude repo init <url>`** for that newly created repo so **multiclaude initializes the repo**; then Overlord **adds its layout** (specs/, contracts/, docs/, scripts/check.sh, agent prompts) on top. Multiclaude owns repo/worktree state; Overlord adds the prescribed skeleton.
- **Tools**: Phase agents use superpowers, Spec Kit, Context7, GitHub API/CLI as defined per phase and **MCP-TOOLS-INTEGRATION.md**.

### 8.3 Other multiclaude-Related Considerations

- **Daemon must be running**: All multiclaude commands (repo init, worker create, message send, etc.) require the multiclaude daemon. Overlord’s Bootstrap or runbook must assume `multiclaude start` (or equivalent) has been run, or document it as a prerequisite; optionally, Overlord can check `multiclaude daemon status` before Phase 4 and surface a clear error if the daemon is down.
- **Repo init before workers**: `multiclaude repo init <url>` must have been run for the target repo before any worker create. Phase 0 performs this after creating the GitHub repo; resume/brownfield must assume the repo is already inited or run init when attaching to an existing repo.
- **Task string format**: multiclaude’s `worker create` takes a single task string. Overlord’s Issue Emitter produces GitHub issues; the Execution Manager maps each issue to a task string (e.g. `Implement #101: Add check.sh gate`). Consistency between issue title/body and task string improves traceability.
- **Worker lifecycle**: Workers are ephemeral; they signal completion with `multiclaude agent complete`. Overlord infers completion and PR status via list-workspace-replies, worker list, and/or gh/API (e.g. PR merged). No need for Overlord to parse state.json for routine operation.
- **Fork vs single-player**: If the target repo is a fork, multiclaude uses pr-shepherd instead of merge-queue. Greenfield typically creates a new repo (not a fork); if Overlord ever supports fork-based workflow, init with the fork URL and multiclaude will auto-detect.
- **Timing and robustness**: The ~5s delay in create-worker-with-auto-accept is a heuristic (security prompt appearance time). If Claude Code or environment changes, the delay may need tuning; the script is the single place to adjust. Execution Manager should treat “worker create” as “run create-worker-with-auto-accept” and not implement its own delay/accept logic.
- **Agent prompts in target repo**: Phase 0 copies Palpatine’s AGENT-PROMPTS (worker, supervisor, reviewer) into the target repo’s `.multiclaude/agents/` (or equivalent) so multiclaude uses them. Supervisor and worker prompts must instruct agents to reply to **workspace** so Overlord can capture replies via list-workspace-replies.

### 8.4 Status Subsystem and Multiclaude Monitor

During the **execution phase** (Phase 4+), Overlord needs **very good status** from multiclaude: what issues workers are working on, how many workers, whether they are running, CPU usage, and file activity (learnings and dialogue in Overlord-Learnings). Agents are often **not good at recurring tasks**; multiclaude itself uses a **daemon** that reminds agents to do things. Overlord should have analogous **ownership by the system**: a dedicated subsystem that proactively gathers and surfaces status on a schedule.

**Multiclaude monitor (status subsystem):**

- **Role**: A daemon-like component (or a timer-driven loop within the Overlord process when a project is active) that periodically gathers status from the multiclaude system and exposes it to the CLI. It answers: Is multiclaude healthy? What workers exist? What issues are they working on? Are workers running (process, CPU, file activity)? This provides the "very good status" required during execution (learnings).
- **Data sources** (via multiclaude CLI and documented scripts only): `multiclaude worker list`, `check-worker-status.sh` (liveness: shell + Claude Code process + activity such as CPU and file changes), `list-workspace-replies.sh`, and optionally gh/API for PR/issue state. All co-located on the same host for V1, so CPU and file activity are observable via documented scripts.
- **Update interval**: A **status loop** (e.g. every minute) that: (1) runs the status-gathering steps above for the active project's repo, (2) updates an in-memory or short-lived status snapshot, (3) feeds the CLI so the user can **interrogate** status at any time and so the CLI can **proactively** display progress (e.g. "3 workers active; issues #101, #102 in progress; 2 PRs open").
- **Health**: The monitor can infer multiclaude health (daemon up, repo inited, workers responsive) and surface clear errors to the CLI (e.g. "multiclaude daemon not running") so the operator knows why status is missing.
- **Integration**: The monitor does **not** replace the Phase 4 agent's duties (dispatch, unblock, nudge); it **feeds** the CLI and optionally the Phase 4 agent with fresh status so both the human and the agent have a consistent view. The Phase 4 agent still uses check-worker-status and list-workspace-replies when making decisions; the monitor provides a **recurring**, **proactive** stream so the system "remembers" to refresh status (ownership by the system).

**Daemon / timer rationale:** Because agents tend to forget recurring tasks, a **timer-driven** loop (inside Overlord when a session is running, or a separate small daemon if desired) ensures status is gathered and pushed to the CLI every minute (or configured interval). This matches the pattern of multiclaude's own daemon reminding agents; Overlord applies the same discipline for status visibility.

---

## 9. Operational Requirements from Palpatine and Learnings

These requirements are **intrinsic** to the design: they come from Palpatine workflow docs and Overlord-Learnings and must be implemented by the phase agents and runtime, not re-specified here.

### 9.1 The check.sh Gate (OVERLORD-GREENFIELD-WORKFLOW)

- **Single gate**: There is one definition of "safe to merge": `./scripts/check.sh`. Same script runs locally and in CI; CI must **call** `./scripts/check.sh` only (no duplicated commands in CI YAML).
- **Phase 0** creates the **initial** `scripts/check.sh` (executable, `set -euo pipefail`) and CI that runs it. Agent prompts (worker, reviewer) in the target repo require running check.sh before PR and verifying it in review.
- **Workers own and evolve check.sh (and repo scripts)**: **Multiclaude workers** (dispatched in Phase 4+) do the implementation work in the **target repo**. As they implement features and tests, they **edit and evolve** `check.sh` and other scripts in `scripts/` (e.g. `check.sh`, or any `scripts/*.sh`) as tests and implementation evolve—workers do most of the ongoing editing of these scripts; Phase 0 only bootstraps the initial versions. Overlord does **not** overwrite or freeze check.sh or other repo scripts after bootstrap. The model: workers own the target repo content; scripts, tests, and CI evolve with the work.
- **Hooks** (e.g. `.multiclaude/hooks.json` per hooks.json.template) can enforce check.sh before PR-related commands; Phase 0 sets these up.

### 9.2 Spec-First Enforcement (SPEC-FIRST-ENFORCEMENT, TESTING-STRATEGY)

- **Testing strategy** is defined in **foundational/palpatine/TESTING-STRATEGY.md**. Implementers and phase agents MUST reference that document for: four testing layers (interface, unit, integration, black box); black box CRITICAL; test ticket organization; definition of done; test arbitration protocol; CI evolution strategy.
- **Operational spec** is the source of truth; tests **validate** implementation, they do not guide it. Workers implement to spec; test access restrictions (no test implementation code to workers); test arbitration via `blocker:test-arbitration` and supervisor.
- **Phase 1** produces operational spec and testing strategy; **Phase 0** copies AGENT-PROMPTS (worker, supervisor, reviewer) to target repo so multiclaude agents enforce spec-first. Four testing layers (interface, unit, integration, **black box**); black box is CRITICAL and derived from operational spec (DOCUMENT-INTERNALIZATION).

### 9.3 Phase 0: Planning and Gates (PHASE-GATES, INTERACTIVE-BRAINSTORMING, DOCUMENT-INTERNALIZATION)

- **Brainstorming** is interactive: actually run `claude -p "/superpowers:brainstorm"`; ask one question at a time; present design sections (200–300 words) and validate; create files only after validation (INTERACTIVE-BRAINSTORMING).
- **Document internalization**: Before presenting any design section, re-read relevant workflow docs, identify required components and emphasis, cross-reference design to docs, match emphasis (DOCUMENT-INTERNALIZATION).
- **Gates 1–5**: Tech stack approval → Brainstorming completion → Context7 (if separate) → Plan approval → Execution approval. Explicit approval language; no proceeding without approval. MCP (Reflection) retrieve/store episodes at gates per PHASE-GATES and MCP-TOOLS-INTEGRATION.

### 9.4 Phase 4: Multiclaude Worker Dispatch and Monitoring (WORKER-DISPATCH-GUIDE, EXECUTION-PHASE-PROMPT, WORKER-MONITORING, OVERLORD-DUTIES)

- **Multiclaude worker dispatch**: When creating workers via multiclaude (for the target project), only via `./scripts/create-worker-with-auto-accept.sh <repo-name> "<task>"`. Never raw `multiclaude worker create` without immediate auto-accept (those multiclaude worker instances stick at security prompt—learnings). Overlord's Phase 4 agent itself is driven via Claude Code API and does not have this problem.
- **Multiclaude worker liveness**: Shell + Claude Code process + activity (CPU, file changes, git). Use `check-worker-status.sh`; activity score ≥ 5 = active; stuck score ≥ 5 = intervention. Check before creating new multiclaude workers; act on stuck within ~15 min (WORKER-MONITORING).
- **Status and unblock**: Periodic status (current wave, multiclaude workers, PRs, blockers); nudge reviewer/merge-queue when needed; brief supervisor; capture replies via `list-workspace-replies.sh` (EXECUTION-PHASE-PROMPT, OVERLORD-DUTIES, CAPTURING-REPLIES).
- **Execution-phase status (learnings)**: The execution phase needs **very good status** from multiclaude—what issues workers are working on, how many workers, whether they are running, CPU and file activity. This is provided by the **status subsystem (multiclaude monitor)** described in Section 8.4: a timer-driven status loop (e.g. every minute) gathers status via CLI/scripts and feeds the CLI so the operator can interrogate it and see proactive progress updates.

### 9.5 Packaging, Test Reporting, and Done (Overlord-Learnings)

- **Packaging**: Deliverables must be installable/runnable (install script, entry points, user-facing docs in project repo). "Done" includes "user can clone, install, and use" (COMPREHENSIVE-LEARNINGS).
- **Test results**: Capture and share (e.g. test-summary doc or report); consider a finalization phase with test-summary ticket (learnings).
- **Done criteria**: Clear completion signals (e.g. wave issues merged, gate green, README/status updated) so Overlord knows when to proceed or declare done (learnings, project-overlord issues).

### 9.6 Summary Table

| Area | Source | Requirement |
|------|--------|-------------|
| multiclaude interface | MULTICLAUDE-INTERFACE-RULES | CLI + documented scripts only; no tmux/socket/state |
| Multiclaude worker dispatch | WORKER-DISPATCH-GUIDE, learnings | create-worker-with-auto-accept when creating multiclaude workers |
| Multiclaude worker liveness | WORKER-MONITORING, learnings | check-worker-status; shell + Claude + activity (for multiclaude workers) |
| Replies | CAPTURING-REPLIES | list-workspace-replies for workspace inbox |
| Phase gates | PHASE-GATES | Gate 1–5; explicit approval; no proceed without |
| Brainstorming | INTERACTIVE-BRAINSTORMING | Actually run superpowers; ask one at a time; validate |
| Design presentation | DOCUMENT-INTERNALIZATION | Re-read docs; match emphasis; cross-reference |
| check.sh | OVERLORD-GREENFIELD-WORKFLOW | Single gate; CI runs only check.sh; Phase 0 bootstraps; **workers evolve** scripts/ (e.g. check.sh) as tests evolve |
| Spec-first | SPEC-FIRST-ENFORCEMENT, TESTING-STRATEGY | Spec truth; tests validate; four layers; black box CRITICAL |
| Agent prompts | AGENT-PROMPTS | Copy to target repo in Phase 0; worker/supervisor/reviewer |
| Packaging / test report | Overlord-Learnings | Installable deliverables; test results captured |

### 9.7 Usable Software (Delivered System)

The **delivered system** (the software Overlord builds in the target repo) MUST be **installable and usable**. This is intrinsic to "done" (COMPREHENSIVE-LEARNINGS, Overlord-Learnings).

- **README**: Must describe project purpose, how to set up and run, how to run the gate (`./scripts/check.sh`), and current status. Kept up to date per OVERLORD-GREENFIELD-WORKFLOW (README maintenance).
- **Interface specs**: Specs for interfaces, especially **CLI** and any **user-facing interfaces**, so users and agents know how to invoke and use the system. Operational specification (Phase 1) defines commands and workflows.
- **Packaged and installable**: Deliverables must be installable/runnable (install script, entry points, dependency declaration). "Done" includes "user can clone, install, and use."
- **Getting started / quick start**: A getting-started guide or quick start (in README or separate doc) so a new user can run the software with minimal steps.

### 9.8 Caveats and Learnings (Palpatine and Overlord-Learnings)

Overlord Agent V1 MUST account for the following (from **foundational/overlord-learnings/COMPREHENSIVE-LEARNINGS.md** and Palpatine):

- **Workflow docs are requirements, not suggestions.** Brainstorming must be interactive with user validation; never skip to implementation without exploration and validation (INTERACTIVE-BRAINSTORMING).
- **Document emphasis must be matched.** When Palpatine/TESTING-STRATEGY emphasize something (e.g. black box CRITICAL), design and behavior must give it equal or greater emphasis (DOCUMENT-INTERNALIZATION).
- **Multiclaude worker dispatch:** create-worker-with-auto-accept (or immediate auto_accept_workers after worker create) is **mandatory** for multiclaude worker instances; they get stuck at the security prompt otherwise.
- **Worker liveness:** Shell + Claude Code process + activity (CPU, file changes). Use check-worker-status.sh; do not assume workers are working just because they exist in state.
- **Use multiclaude formal interfaces only.** No tmux, socket, or state file access (MULTICLAUDE-INTERFACE-RULES).
- **Packaging and test reporting:** Deliverables must be installable/runnable; test results captured and shareable; consider packaging and test-summary phases (learnings).
- **Capturing replies:** Supervisor/workers reply to workspace; Overlord captures via list-workspace-replies.sh (CAPTURING-REPLIES).
- **CLI entry points:** Delivered packages need explicit CLI entry point configuration (e.g. pyproject.toml `[project.scripts]`) so the installed command is available after install.

---

## 10. Status and Roadmap

### 10.1 Overlord Status (First-Class)

- **Overlord status** answers: current phase, current wave (if applicable), pending questions count, last checkpoint, and optionally a short progress summary.
- Planned as a core concept and CLI surface (exact command names TBD).

### 10.2 Roadmap / Feature List

**V1 (first working system):**

- CLI: start, resume, list, run; one project per run; auto-ask pending + phase reminder.
- State: local per-project + Overlord section in repo; checkpointing at phase boundaries.
- Graph: Phase 0 → … with reentrant edges; Ingester → Phase 1 for brownfield.
- Phase agents: Phase 0, then 1, 2, … (incremental build and test).
- Human-in-the-loop: gates, unstick, optional review; exit-and-resume; proactive pending.

**Later / Backlog / Roadmap:**

- **Overlord status**: Current phase, wave, pending questions, last checkpoint, progress summary. **Status subsystem / multiclaude monitor**: Timer-driven status loop (e.g. every minute) feeding multiclaude status (workers, issues, liveness, CPU, file activity) to the CLI; see Section 8.4.
- **Maintenance commands**: e.g. `overlord list`, `overlord inspect <project>`, `overlord checkpoint`, `overlord clean`, export/backup state, config (e.g. repo checkpoint on/off).
- **Diagnostics system**: A diagnostics capability that reports the state of **Overlord** and **multiclaude** so the operator can query it, get ideas, and understand what is going on. E.g. current phase, pending questions, multiclaude worker list and liveness, PR/issue status, last checkpoint, optional suggestions for next actions.
- **Reporter / Summarizer**: At the end of a run (or on demand), a Reporter/Summarizer that produces a **summary of what was built**: deliverables, key decisions, test results, README/quick start location, how to install and run. Supports handoff and audit.
- **Enhancements**: Configurable review checkpoints, richer context graph, episodic memory integration, multiple projects per Overlord (if ever desired). **Optional**: Implement a phase (e.g. Phase 1 Brainstorm) as a **Deep Agent** if it needs internal dynamic planning or sub-delegation.
- **Orchestrator-configured MCP** (future release): Overlord discovers MCP servers from config, passes MCP server information into the Claude Code API client when invoking phase agents, and controls which MCPs each phase sees—instead of relying on the local environment to have all required MCPs pre-configured.

---

## 11. Component Summary

| Component           | Responsibility |
|---------------------|----------------|
| CLI                 | Entry point; start, resume, list, run, status; present prompts and read answers; surface pending questions and phase reminder; **interactive/chat-like** mode (planning = chat, execution = status stream + Q&A). Spec: **OVERLORD-CLI-SPEC.md**. |
| Multiclaude Monitor | Timer-driven status subsystem; every minute (or configured interval) gathers multiclaude status (workers, issues, liveness, CPU, file activity) via CLI/scripts only; feeds CLI for interrogation and proactive progress; ensures "ownership by the system" for recurring status (Section 8.4). |
| Graph Runtime       | Run phase graph; decide next node; checkpoint state; invoke human-in-the-loop when needed |
| State Manager       | Load/save state (local); aggregate and sync to repo Overlord section; atomic writes |
| Phase Agents        | Execute one phase; read/write state and artifacts; use tools; return control to runtime; can push questions to CLI (intercontextual chat). |
| Project Ingester    | Brownfield only; repo path → draft spec + context; then hand off to Phase 1 |
| Human-in-the-Loop   | Persist pending questions; on re-entry, surface and ask; remind phase |

---

## 12. Diagram: State and Artifact Flow

```
  ┌─────────────┐     read/write      ┌─────────────────────────────────────┐
  │   Phase     │◀──────────────────▶│  State object (current phase,       │
  │   Agents    │                     │  history, artifact paths, pending)   │
  └──────┬──────┘                     └────────────────┬────────────────────┘
         │                                             │
         │ read/write                                  │ checkpoint / sync
         ▼                                             ▼
  ┌─────────────────────────────────────┐     ┌─────────────────────────────┐
  │  Artifact files (project dir)       │     │  Local store                 │
  │  spec.md, decisions.md,             │     │  ~/.overlord/projects/<id>/  │
  │  workgraph.yaml, context-summary.md │     │  state, checkpoints/         │
  └────────────────┬────────────────────┘     └─────────────────────────────┘
         │                                             │
         │ optional sync (phase boundaries)             │
         ▼                                             ▼
  ┌─────────────────────────────────────┐     ┌─────────────────────────────┐
  │  Target repo .overlord/              │     │  Resume: load state +         │
  │  decisions, spec-history, context,  │     │  optional checkpoint;        │
  │  optional checkpoints/              │     │  if pending → ask first      │
  └─────────────────────────────────────┘     └─────────────────────────────┘
```

---

This design and architecture document, together with the greenfield spec in this folder, defines Overlord Agent V1. All operational behavior (phase gates, **multiclaude worker dispatch**, multiclaude worker monitoring, spec-first, check.sh, etc.) is anchored in **Palpatine** and **Overlord-Learnings**; this doc and the spec reference them so implementers and phase agents have a single source of truth. Overlord's phase agents are driven via Claude Code API; the dispatch problem (security prompt) applies only to **multiclaude worker instances** that multiclaude spawns for the target project. Decomposition into phases and waves (Overlord methodology) is done separately.

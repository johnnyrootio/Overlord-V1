# Overlord Agent V1 - Greenfield Specification

## Project Overview

**Name**: Overlord Agent V1  
**Description**: A semi-autonomous, multi-agent system that orchestrates greenfield (and brownfield) software development by walking the human through a multi-phase workflow, managing state and checkpoints, and coordinating with multiclaude and GitHub to deliver working software.  
**Goal**: Replace the current "Cursor session as Overlord" model with a stateful, resumable agentic system that one human can run via CLI; the system guides the user through phases, asks the right questions, and autonomously drives execution (especially in later phases where multiclaude is running) while blocking only when human input is required.

---

## Foundational Documents (Palpatine and Overlord-Learnings)

Overlord Agent V1 **must** treat the following as **authoritative**. The essence of Overlord—phases, gates, spec-first enforcement, testing strategy, **multiclaude worker dispatch**, worker monitoring, and learnings from prior human-in-the-loop runs—is already defined there. Phase agents derive their system prompts, tool use, and behavior from these documents.

**Distinction: Overlord agents vs multiclaude workers.** Overlord's **phase agents** (Phase 0, Phase 1, Phase 4, etc.) are the core of Overlord Agent V1; they are communicated with via the **Claude Code API** and do **not** have a dispatch or security-prompt problem. The **multiclaude worker instances** are different: they are the workers that **multiclaude** spawns (separate Claude Code processes) to implement work on the **target project** (e.g. the repo being built). **Multiclaude worker dispatch** is the act of creating and unblocking those multiclaude-managed workers; *those* instances can get stuck at a security prompt, which is why create-worker-with-auto-accept is mandatory when the Phase 4 agent instructs multiclaude to create workers. All references to "worker dispatch," "worker creation," and the auto-accept script in this spec mean **multiclaude worker dispatch**—not the Overlord phase agents themselves.

### Palpatine (multiclaude/palpatine/)

| Document | Role for Overlord Agent V1 |
|----------|----------------------------|
| **OVERLORD-GREENFIELD-WORKFLOW.md** | Master workflow: phases 0–8, check.sh gate, CI gate, bootstrap steps, Phase 4 dispatch algorithm, Phase 5 review, deadlock breakers, README maintenance. Source for phase definitions and exit criteria. |
| **PHASE-GATES.md** | **CRITICAL.** Pre-code phase gates (Gate 1: Tech Stack; Gate 2: Brainstorming completion; Gate 3: Context7 research; Gate 4: Plan approval; Gate 5: Execution approval). Explicit approval language required; no proceeding without approval. MCP (Reflection) at gates. Phase 0 agent MUST enforce these. |
| **MULTICLAUDE-INTERFACE-RULES.md** | **CRITICAL.** Strict prohibitions: no tmux, socket API, or direct access to ~/.multiclaude/state.json or worktrees. ALL interaction via multiclaude CLI and documented scripts only. Any agent that talks to multiclaude MUST follow this. |
| **WORKER-DISPATCH-GUIDE.md** | **CRITICAL.** **Multiclaude worker dispatch**: When creating workers via multiclaude (for the target project), MUST use `./scripts/create-worker-with-auto-accept.sh <repo-name> "<task>"` for EVERY such worker. Those multiclaude worker instances get stuck at the security prompt without auto-accept; this script is the only reliable path. Manual fallback: multiclaude worker create then `./scripts/auto_accept_workers.sh <repo-name>` after ~5s (MANDATORY). Phase 4 agent MUST use this when dispatching multiclaude workers. |
| **EXECUTION-PHASE-PROMPT.md** | Active facilitation during Phase 4+: know what's happening, check work via multiclaude CLI only, periodic status updates, unblock (multiclaude worker dispatch via create-worker-with-auto-accept, nudge supervisor), ensure quality and README maintenance. Informs Phase 4+ agent behavior. |
| **PHASE-0-PLANNING.md** | Planning before code: superpowers (brainstorm, write-plan), Context7 research, step-by-step. Phase 0 agent MUST actually run superpowers and conduct interactive brainstorming per INTERACTIVE-BRAINSTORMING.md. |
| **INTERACTIVE-BRAINSTORMING.md** | **CRITICAL.** Brainstorming is a conversation, not document creation. MUST actually run `claude -p "/superpowers:brainstorm"`; ask questions one at a time; present design sections (200–300 words) and validate; only create files after validation. Phase 0/1 agents MUST follow this. |
| **DOCUMENT-INTERNALIZATION.md** | Before presenting any design section: re-read relevant workflow docs, identify required components and emphasis, cross-reference design to docs, match emphasis (e.g. black box tests as CRITICAL). Phase 0/1 agents MUST internalize before presenting. |
| **TESTING-STRATEGY.md** | **CRITICAL.** Four layers (interface contract, unit, integration, black box). Black box (Layer 4) is CRITICAL and derived from operational spec. Cumulative tests; wave-aware; spec-first validation. Test ticket organization, definition of done, test arbitration protocol. Informs Phase 1 spec and all implementation phases. **Explicit reference:** `foundational/palpatine/TESTING-STRATEGY.md`. Overlord Agent V1 MUST reference this document for testing behavior and phase agent behavior. |
| **SPEC-FIRST-ENFORCEMENT.md** | Operational spec is source of truth; tests validate, don't guide; workers implement to spec; test access restrictions; test arbitration (blocker:test-arbitration). Agent prompts (worker, supervisor, reviewer) enforce this. Phase 1 and Phase 4+ agents MUST uphold spec-first. |
| **REPOSITORY-SETUP.md** | Option A: existing repo (multiclaude repo init). Option B: create new (gh repo create, then init). Phase 0 agent uses this for repo creation/init. |
| **GITHUB-PERMISSIONS.md** | GitHub CLI auth and permissions for repo create, issues, etc. Prerequisite for Phase 0 and Phase 3. |
| **AGENT-PROMPTS/** (worker.md, supervisor.md, reviewer.md, README) | Augmenting overrides for spec-first; copied to target repo in Phase 0. worker: run check.sh before PR, implement to spec. supervisor: test arbitration, reply to workspace. reviewer: spec compliance primary. |
| **CAPTURING-REPLIES.md** | Overlord sends messages via multiclaude message send; replies land in workspace inbox. Use `./scripts/list-workspace-replies.sh [repo-name]` to capture. Phase 4+ agent MUST use this for status from supervisor/workers. |
| **WORKER-MONITORING.md** | Worker liveness = shell + Claude Code process + activity (CPU, file changes, git). Use `./scripts/check-worker-status.sh <repo-name>` before creating new workers and periodically. Stuck detection (activity score, stuck score). Phase 4+ agent MUST monitor and act on stuck workers. |
| **MCP-TOOLS-INTEGRATION.md** | Reflection MCP (retrieve_episodes, store_episode) at gates and phase transitions; Context7 for research; SpecKit for specs. Phase 0/1 agents SHOULD use at gates per PHASE-GATES.md. |
| **EVOLUTION-NOTES.md** | Tracked evolution (e.g. reliable capture of status stream). Overlord Agent V1 should consider these for future improvements. |
| **ECOSYSTEM-RULES/** | Per-stack rules (e.g. python/, go/): best-practices, cursor-rules, project-structure, check.sh-template. Phase 0 agent applies selected ecosystem. |
| **GETTING-STARTED.md**, **QUICK-START.md**, **INITIAL-OVERLORD-PROMPT.md** | Onboarding and prompt templates; useful for CLI onboarding and initial context. |
| **HOOKS-FIX.md**, **hooks.json.template** | Valid hooks.json format; Phase 0 creates hooks in target repo per workflow. |
| **OVERLORD-DISPATCH-INSTRUCTIONS.md** | Condensed dispatch: create-worker-with-auto-accept mandatory; script location; no direct multiclaude worker create. |
| **DEBUGGING-WORKER-ISSUES.md** | Security prompt, tmux window state; supports troubleshooting when workers are stuck. |

### Overlord-Learnings (Overlord-Learnings/)

| Document | Role for Overlord Agent V1 |
|----------|----------------------------|
| **COMPREHENSIVE-LEARNINGS.md** | **CRITICAL.** Episodic lessons: workflow docs are requirements not suggestions; interactive validation essential; document emphasis must be matched; **multiclaude worker dispatch**—create-worker-with-auto-accept and worker init/auth are mandatory for the *multiclaude* worker instances (not for Overlord's own phase agents); worker liveness = shell + Claude + activity; use multiclaude formal interfaces only; packaging/publish and test reporting must be phases; test results captured and shared. Informs Phase 4 agent and packaging/finalization. |
| **OVERLORD-DUTIES.md** | Routine: check status (work list, PRs, check-worker-status); keep pipeline moving (dispatch when idle, nudge reviewer/merge-queue); brief supervisor. Phase 4+ agent SHOULD follow this rhythm. |
| **CAPTURING-REPLIES.md** | Same as Palpatine; reinforces list-workspace-replies and workspace inbox. |
| **README.md** | Index of learnings; points to comprehensive learnings. |

### Synthesis Requirements (Must Be Intrinsic)

- **Multiclaude worker dispatch**: The Phase 4 agent (which communicates with multiclaude via CLI) MUST use `./scripts/create-worker-with-auto-accept.sh <repo-name> "<task>"` for every **multiclaude worker** it asks multiclaude to create. Those multiclaude worker instances (not Overlord's phase agents) get stuck at the security prompt without auto-accept. No direct `multiclaude worker create` without immediately following with auto_accept_workers. Overlord's own phase agents are driven via Claude Code API and do not have this dispatch problem.
- **Multiclaude worker monitoring**: Phase 4+ MUST use `check-worker-status.sh` (or equivalent) to determine if **multiclaude workers** (the instances multiclaude spawned for the target project) are actually alive (Claude Code process, CPU, file activity). Do not assume those workers are working just because they exist in state.
- **multiclaude interface**: No tmux, socket, or state file access. Only multiclaude CLI and documented scripts (create-worker-with-auto-accept, auto_accept_workers, list-workspace-replies, check-worker-status).
- **Phase gates**: Gate 1–5 (tech stack, brainstorming complete, Context7 if separate, plan approval, execution approval) MUST be enforced by Phase 0 agent with explicit approval language and no proceeding until user confirms.
- **Interactive brainstorming**: Phase 0/1 MUST actually run superpowers brainstorm; ask **one question at a time** (Socratic); present sections and validate; create files only after validation. Questions MUST be organized by **themes** (tech stack, structure, testing, CI, tooling, repo/agents) with a **comprehensive design** in mind. See DESIGN-AND-ARCHITECTURE.md Section 4.5 (Socratic Planning and Brainstorming) and Section 4.6 (First-Generation Prompts: Extraction from Foundational Documents).
- **Document internalization**: Before presenting design sections, re-read relevant docs and match emphasis (e.g. black box tests CRITICAL).
- **check.sh gate**: Single gate for "safe to merge"; CI must run `./scripts/check.sh` only (no duplicated commands in CI YAML). Phase 0 creates it; workflow docs define it.
- **Spec-first and testing**: Operational spec is truth; tests validate; four layers including black box; test arbitration via blocker:test-arbitration. Agent prompts in target repo enforce this.
- **Packaging and test reporting**: From learnings—deliverables must be installable/runnable; test results captured and shareable; consider packaging and test-summary phases (see roadmap).

**Palpatine folder:** Overlord Agent V1 MUST treat **foundational/palpatine/** as authoritative. All workflow definition, phase gates, spec-first enforcement, testing strategy (foundational/palpatine/TESTING-STRATEGY.md), multiclaude worker dispatch, worker monitoring, and operational rules come from Palpatine. Implementers and phase agents MUST understand and account for everything in the Palpatine folder.

---

## Usable Software (Delivered System)

The **delivered system** (the software Overlord builds in the target repo) MUST be **installable and usable**. This is intrinsic to "done" (COMPREHENSIVE-LEARNINGS).

- **README**: Must describe project purpose, how to set up and run, how to run the gate (`./scripts/check.sh`), and current status. Kept up to date per OVERLORD-GREENFIELD-WORKFLOW (README maintenance).
- **Interface specs**: Specs for interfaces, especially **CLI** and any **user-facing interfaces**, so users and agents know how to invoke and use the system. Operational specification (Phase 1) defines commands and workflows.
- **Packaged and installable**: Deliverables must be installable/runnable (install script, entry points, dependency declaration). "Done" includes "user can clone, install, and use."
- **Getting started / quick start**: A getting-started guide or quick start (in README or separate doc) so a new user can run the software with minimal steps.

---

## Agent Specifications (by Function)

Agent names and functions are defined in **DESIGN-AND-ARCHITECTURE.md** (section 4.1a). **Sequence diagram (Worker + Phases 5–8)**: See **SEQUENCE-PHASES-5-8.md** in this folder for how workers and Phase 5 (Review Orchestrator) through Phase 8 (Loop Controller) interact; a rendered diagram is in **sequence-phases-5-8-diagram.html**. **Socratic brainstorming** and **first-generation prompt extraction** are defined in DESIGN-AND-ARCHITECTURE.md (sections 4.5 and 4.6). Summary:

- **Work graph** is developed in **Phase 2 (Wave Planner)**; it is the execution plan (waves, dependencies). **GitHub issues** are emitted from the work graph in **Phase 3 (Issue Emitter)**; issues are the formal work items multiclaude workers consume.
- **Phase 0 (Bootstrap)**, **Phase 1 (Specifier)**, **Phase 2 (Wave Planner)**, **Phase 3 (Issue Emitter)**, **Phase 4 (Execution Manager)**, **Phase 5 (Review Orchestrator)**, **Phase 6 (Deadlock Breaker)**, **Phase 7 (Stop Controller)**, **Phase 8 (Loop Controller)**. Phase 4 is the Execution Manager (dispatch, monitor, unblock via multiclaude CLI + scripts only).

---

## Caveats and Learnings (Palpatine and Overlord-Learnings)

Overlord Agent V1 MUST account for the following (from **foundational/overlord-learnings/COMPREHENSIVE-LEARNINGS.md** and Palpatine):

- **Workflow docs are requirements, not suggestions.** Brainstorming must be interactive with user validation; never skip to implementation without exploration and validation.
- **Document emphasis must be matched.** When Palpatine/TESTING-STRATEGY emphasize something (e.g. black box CRITICAL), design and behavior must give it equal or greater emphasis.
- **Multiclaude worker dispatch:** create-worker-with-auto-accept (or immediate auto_accept_workers after worker create) is **mandatory** for multiclaude worker instances; they get stuck at the security prompt otherwise.
- **Worker liveness:** Shell + Claude Code process + activity. Use check-worker-status.sh; do not assume workers are working just because they exist in state.
- **Use multiclaude formal interfaces only.** No tmux, socket, or state file access.
- **Packaging and test reporting:** Deliverables must be installable/runnable; test results captured and shareable.
- **Capturing replies:** Supervisor/workers reply to workspace; Overlord captures via list-workspace-replies.sh.
- **CLI entry points:** Delivered packages need explicit CLI entry point configuration so the installed command is available after install.

---

## Roadmap / Backlog / Later

- **Overlord status**: Current phase, wave, pending questions, last checkpoint, progress summary.
- **Maintenance commands**: e.g. `overlord list`, `overlord inspect <project>`, `overlord checkpoint`, `overlord clean`, export/backup state, config.
- **Diagnostics system**: A diagnostics capability that reports the state of **Overlord** and **multiclaude** so the operator can query it, get ideas, and understand what is going on (e.g. current phase, pending questions, multiclaude worker list and liveness, PR/issue status, last checkpoint).
- **Reporter / Summarizer**: At the end of a run (or on demand), a Reporter/Summarizer that produces a **summary of what was built**: deliverables, key decisions, test results, README/quick start location, how to install and run.
- **Enhancements**: Configurable review checkpoints, episodic memory integration, orchestrator-configured MCP, etc.

---

## Objectives

- [ ] One Overlord run = one target project (active management); project list for re-entry only
- [ ] Session = one target project from start to finish; long-lived, interruptible, resumable with checkpointing
- [ ] Multiple phase-aligned agents (Phase 0, 1, 2, …) with well-defined interfaces (state + file artifacts)
- [ ] Reentrant phase graph (e.g. return to Phase 0 for more brainstorming)
- [ ] Three entry scenarios: greenfield (from genesis spec), resume (from repo/local state), brownfield (project ingester → Phase 1)
- [ ] Human-in-the-loop: phase gates (per PHASE-GATES.md), unstick prompts, optional review checkpoints; hard block early, soft block later (multiclaude keeps running)
- [ ] Exit-and-resume when waiting for human; on re-entry, automatically surface and ask pending questions and remind phase
- [ ] State: local per-project storage + Overlord section in target repo (decisions, spec history, context summary; optional checkpoint blobs)
- [ ] Overlord status and maintenance commands (roadmap)
- [ ] All phase agents derive prompts and behavior from Palpatine and Overlord-Learnings; worker dispatch and monitoring follow WORKER-DISPATCH-GUIDE and WORKER-MONITORING; multiclaude interaction follows MULTICLAUDE-INTERFACE-RULES

## Key Requirements

### Functional Requirements

1. **CLI and entry**
   - CLI is the primary interface (v1). See **OVERLORD-CLI-SPEC.md** in this folder for the full CLI specification (commands, arguments, output format, exit codes, interactive mode, slash commands, status stream).
   - Commands: start (greenfield), list (projects; show which have pending questions), run/resume (attach and continue), status (project status).
   - When user runs Overlord for a project with pending questions: automatically ask those questions and remind which phase they are in; no "user must remember to resume."
   - One Overlord instance actively manages one project at a time; list is for selecting which project to re-enter.
   - **Interactive / chat-like**: Planning phases (0, 1) behave like a **chat window** (agent asks, user answers; one question at a time). Execution phase (4+) adds a **proactive status stream** and Q&A (unstick, arbitration). **Slash commands** (e.g. `/status`, `/phase`, `/help`, `/quiet`, `/verbose`) available in-session. **Intercontextual chat**: all agents can push questions to the CLI; user and CLI share one conversational context.
   - **Status subsystem (multiclaude monitor)**: A **timer-driven status loop** (e.g. every minute) gathers multiclaude status (workers, issues being worked on, liveness, CPU, file activity) via CLI/scripts only and feeds the CLI. User can **interrogate** status at any time; CLI **proactively** displays progress during execution. Ensures "very good status" (learnings) and **ownership by the system** for recurring status (agents are not good at recurring tasks; see DESIGN-AND-ARCHITECTURE.md Section 8.4).

2. **Session and state**
   - One session = one target project (start to done)
   - State is long-lived: start/stop, survive failure, resume where left off
   - Local: structured per-project storage (e.g. `~/.overlord/projects/<project-id>/`) with current state and checkpoints (atomic writes)
   - Target repo: Overlord section (e.g. `.overlord/` or `overlord/`) with durable context (decisions log, spec/requirements history, context summary); optional config/flag to also persist checkpoint blobs to repo for full reconstruction

3. **Agents and orchestration**
   - Multiple agents from day one, one per phase (Phase 0, Phase 1, …), with well-defined interfaces
   - I/O between agents: state object (graph runtime) + file artifacts (MD/JSON) in a well-known project layout
   - Graph runtime (e.g. LangGraph): nodes = phase agents (and optional Project Ingester); edges = allowed transitions including back-edges (reentrant)
   - Orchestrator = graph runtime; agents do not invoke each other; they read/write state and artifacts; runtime decides next node
   - Per-agent: **system prompt derived from Palpatine/workflow docs** (see Foundational Documents); prompt augmentation at spawn (phase, history, paths); tool selection per phase (hard-coded at first)
   - **Phase 0 agent**: MUST enforce PHASE-GATES.md (Gate 1–5), PHASE-0-PLANNING.md, INTERACTIVE-BRAINSTORMING.md, DOCUMENT-INTERNALIZATION.md; use superpowers and Context7; apply ECOSYSTEM-RULES for selected stack; create check.sh, CI that runs check.sh, CLAUDE.md, agent prompts (from AGENT-PROMPTS/), hooks per hooks.json.template
   - **Phase 1 agent**: MUST follow TESTING-STRATEGY.md (all four layers, black box CRITICAL), SPEC-FIRST-ENFORCEMENT.md; produce operational spec, testing strategy doc, constitution/spec/plan/tasks per workflow
   - **Phase 4 (dispatch) agent**: When instructing multiclaude to create workers (multiclaude worker dispatch), MUST use only `./scripts/create-worker-with-auto-accept.sh <repo-name> "<task>"` for each such worker; MUST use `check-worker-status.sh` for multiclaude worker liveness; MUST use `list-workspace-replies.sh` to capture supervisor/worker replies; MUST follow MULTICLAUDE-INTERFACE-RULES (no tmux/socket/state); MUST provide periodic status and unblock per EXECUTION-PHASE-PROMPT and OVERLORD-DUTIES. (Overlord's own phase agents use Claude Code API and do not have the security-prompt dispatch problem.)

4. **Three scenarios**
   - **Greenfield**: Start from genesis spec (e.g. greenfield-specs format); graph starts at Phase 0
   - **Resume**: Load state/checkpoint from local or repo; graph resumes at node indicated by state
   - **Brownfield**: Run Project Ingester first (repo path → initial spec-like doc + context); graph always enters at Phase 1 (Brainstorm & Converge)

5. **Human-in-the-loop**
   - **Phase gates** (per PHASE-GATES.md): Gate 1 Tech Stack, Gate 2 Brainstorming completion, Gate 3 Context7 (if separate), Gate 4 Plan approval, Gate 5 Execution approval. Hard block until explicit approval language (e.g. "Yes, proceed to planning"). No vague acceptance; request explicit confirmation if needed.
   - Explicit "human decision needed" (unstick, arbitration, ambiguous requirement): pause orchestration; in Phase 4+, multiclaude continues in background
   - Optional review checkpoints (e.g. review work graph before Phase 3) configurable
   - When waiting for human: persist state (including pending questions), exit process; on re-entry, surface and ask pending questions automatically; remind current phase

6. **Integration**
   - **multiclaude**: Interact ONLY via multiclaude CLI and documented scripts. STRICT: no tmux, socket API, or direct access to ~/.multiclaude/state.json or worktrees (MULTICLAUDE-INTERFACE-RULES.md). For **multiclaude worker dispatch** (creating the workers that multiclaude runs for the target project): create-worker-with-auto-accept (mandatory), auto_accept_workers (fallback), list-workspace-replies, check-worker-status.
   - **Target GitHub repo**: Create/issues, labels; Overlord section for state/context; no heavy direct repo manipulation beyond that and multiclaude-driven work. Repository creation/init per REPOSITORY-SETUP.md and GITHUB-PERMISSIONS.md.
   - **Tools**: Superpowers, Spec Kit, Context7, GitHub API/CLI as defined per phase and MCP-TOOLS-INTEGRATION.md.

7. **Operational requirements from Palpatine and learnings**
   - **check.sh**: Single gate; CI runs only `./scripts/check.sh`; Phase 0 creates it; workers run it before PR (enforced via agent prompts in target repo).
   - **Spec-first**: Operational spec is source of truth; tests validate; worker/supervisor/reviewer prompts in target repo (from AGENT-PROMPTS/) enforce spec-first and test arbitration.
   - **Worker liveness**: Defined as shell + Claude Code process + activity (CPU, file changes). Use check-worker-status.sh; act on stuck workers (e.g. nudge, kill/recreate) per WORKER-MONITORING.md.
   - **Capturing replies**: Supervisor/workers reply to workspace; Overlord captures via list-workspace-replies.sh per CAPTURING-REPLIES.md.
   - **Packaging and test reporting** (from Overlord-Learnings): Deliverables must be installable/runnable; test results captured and shareable; consider explicit packaging and test-summary phases in roadmap.

### Non-Functional Requirements

- **Reliability**: Checkpointing at phase boundaries (and key sub-steps); durable state; recover from crash and resume
- **Observability**: Overlord status (current phase, waves, pending questions, last checkpoint) as a first-class concept; maintenance commands on roadmap
- **Maintainability**: Prompts and behavior derived from Palpatine and Overlord-Learnings; clear separation of phase agents and handoff contracts
- **Extensibility**: Design allows adding phases, reentrant edges, and optional features (e.g. episodic memory integration) without rewriting core

## Constraints

- **Technology**: Python for implementation (v1); Claude Code APIs as the agent runtime; MCP servers as prerequisites where needed
- **Platform**: Runs on same machine as multiclaude/Claude Code (local-first)
- **Scope**: Specialized for software development workflow first; greenfield is primary path; brownfield and resume supported
- **Interfaces**: Agent-to-agent and agent-to-world via state + file artifacts (MD/JSON); conventional, industry-aligned patterns
- **Compliance**: MUST NOT bypass multiclaude interface (MULTICLAUDE-INTERFACE-RULES); MUST use create-worker-with-auto-accept for all **multiclaude worker** creation (WORKER-DISPATCH-GUIDE, learnings)

## Tech Stack Preferences

**Preferred**:
- Python 3.11+ for Overlord implementation
- LangGraph (or similar) for graph orchestration and state management
- Claude Code APIs for agent execution
- Markdown and JSON for handoff artifacts and Overlord section in repo

**Avoid**:
- Bypassing multiclaude's formal interfaces (tmux, socket, state file direct access) except documented debug exceptions with human approval
- Single monolithic agent (phase-aligned multi-agent from day one)
- Using `multiclaude worker create` without the create-worker-with-auto-accept flow (multiclaude worker instances will be stuck at security prompt)

## User Stories

- As a visionary, I want to start a greenfield project from a genesis spec so that Overlord walks me through phases and we get working software
- As a user, I want to stop and later resume so that I don't lose progress and Overlord asks pending questions when I return
- As a user, I want to see which projects have pending questions (list) so that I know what needs my attention
- As a user, I want Overlord to remind me which phase I'm in when I re-enter so that I have context
- As a user, I want to bring an existing repo (brownfield) into Overlord so that we can refine and extend it via the same workflow
- As an operator, I want Overlord status (phase, waves, progress) so that I know where we are in the process
- As the system, I want Phase 4 to always use create-worker-with-auto-accept when dispatching multiclaude workers so that those worker instances are never stuck at the security prompt

## Success Criteria

- [ ] User can start a greenfield project from a genesis spec and be guided through phases to delivered software
- [ ] User can exit when Overlord needs input and resume later; pending questions are surfaced and asked automatically
- [ ] State is persisted locally and (durable context) in target repo; checkpoints allow resume after failure
- [ ] Phase agents execute with clear handoffs (state + artifacts); graph supports reentrant phases
- [ ] Brownfield path: ingester produces draft context; workflow enters at Phase 1
- [ ] Overlord status (and roadmap for maintenance commands) is specified and planned
- [ ] All phase agents derive behavior from Palpatine and Overlord-Learnings; **multiclaude worker dispatch** uses create-worker-with-auto-accept only; multiclaude interaction is CLI/documented scripts only; phase gates (Gate 1–5) are enforced with explicit approval language; Overlord phase agents are driven via Claude Code API (no dispatch problem)

## Additional Context

- This spec is the result of a design Q&A plus a comprehensive pass over Palpatine and Overlord-Learnings. Foundational documents are listed and their roles defined; synthesis requirements (multiclaude worker dispatch, multiclaude worker monitoring, interface rules, phase gates, brainstorming, document internalization, check.sh, spec-first, packaging/test reporting) are intrinsic to the spec. Overlord's phase agents are distinct from multiclaude workers: phase agents use Claude Code API; multiclaude workers are the instances multiclaude spawns for the target project and have the security-prompt dispatch issue.
- Decomposition into phases and waves (Overlord methodology) will be done separately; this document is the greenfield spec and does not include that decomposition.
- Palpatine documents and Overlord-Learnings are the source of truth for workflow, prompts, and operational rules. **In this bundle**: Palpatine = `foundational/palpatine/`, Overlord-Learnings = `foundational/overlord-learnings/`; scripts = `scripts/`.

---

**Ready for next step:** Use this spec together with the design and architecture document in this folder to decompose the work into phases and waves using the Overlord methodology (in a separate exercise).

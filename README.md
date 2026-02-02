# Overlord Agent V1

This folder is a **self-contained bundle** for developing Overlord Agent V1: spec, design, foundational documents (Palpatine + Overlord-Learnings), scripts, and greenfield spec format. Copy this directory into a new Cursor session to start implementation.

## Install

From the repo root:

```bash
./overlordinstall.sh
```

Or with absolute path:

```bash
/Users/johnamaral/cursor_projects/Overlord-Agent-V1/overlordinstall.sh
```

This creates a `.venv` in the repo and installs Overlord there. Then:

```bash
source .venv/bin/activate
source .env   # or: set -a && source .env && set +a
overlord --help
```

You can also use your own virtual environment and run `pip install -e .`; the `overlord` command will be available when that venv is active.

### How the install works

- **Editable install:** The script runs `pip install -e .` (editable mode). The Python package is **not copied** into the venv; Python loads the `overlord` package **from this repo** at runtime. So the Overlord-Agent-V1 directory is the **source of truth** for code, prompts, scripts, and templates.
- **Where Overlord finds files:** At runtime, the code resolves the **repo root** as the parent of the `overlord` package (via `Path(__file__).resolve().parent.parent`). It then reads:
  - **agent_prompts/** — phase system prompts (phase_0_bootstrap.md, etc.)
  - **scripts/** — create-worker-with-auto-accept.sh, etc.
  - **foundational/** — Palpatine and Overlord-Learnings docs
  So Overlord **does** have access to all of those; they are read from this directory, not from a copy. Do **not** move or delete the Overlord-Agent-V1 repo after install, or those paths break. You can override with env: `OVERLORD_REPO_ROOT` (repo root), `OVERLORD_SCRIPTS_DIR` (scripts directory).
- **Environment variables:** The installer does **not** set API keys or other env vars. You must load them yourself (e.g. `source .env` or `set -a && source .env && set +a`). Optional: `ANTHROPIC_API_KEY` or `CLAUDE_CODE_API_KEY`, `OVERLORD_REPO_ROOT`, `OVERLORD_SCRIPTS_DIR`, `OVERLORD_STATUS_INTERVAL_SEC`.
- **State:** Project state is stored in `~/.overlord/projects/<project_id>/` by default (or `--state-dir`). That is separate from this repo; you can run from any directory if you use absolute paths for spec files.

---

## Bundle layout

| Path | Description |
|------|--------------|
| **docs/OVERLORD-AGENT-V1-SPEC.md** | Greenfield spec/requirements; Foundational Documents table and synthesis requirements |
| **docs/DESIGN-AND-ARCHITECTURE.md** | Design and architecture; interfaces, state, graph, human-in-the-loop, roadmap |
| **docs/SEQUENCE-PHASES-5-8.md** | Sequence diagram: Worker and Phases 5–8 (rendered: docs/sequence-phases-5-8-diagram.html) |
| **docs/OVERLORD-CLI-SPEC.md** | CLI specification: commands (start, list, run, resume, status), interface, output format, exit codes |
| **ROADMAP-V1.md** | Implementation plan and roadmap: P0–P6 prototypes, chunks C1–C16, status subsystem, interactive CLI; use Context7 and SpecKit as needed |
| **foundational/palpatine/** | Palpatine workflow docs (OVERLORD-GREENFIELD-WORKFLOW, PHASE-GATES, WORKER-DISPATCH-GUIDE, AGENT-PROMPTS, ECOSYSTEM-RULES, hooks.json.template, etc.) |
| **foundational/overlord-learnings/** | Overlord-Learnings (COMPREHENSIVE-LEARNINGS, OVERLORD-DUTIES, CAPTURING-REPLIES, README) |
| **scripts/** | Scripts used by Phase 4 and the design: `create-worker-with-auto-accept.sh`, `auto_accept_workers.sh`, `list-workspace-replies.sh`, `check-worker-status.sh` (stub) |
| **greenfield-specs/** | Genesis spec format: README, template.md, example-todo-app.md |
| **examples/** | Example genesis spec: robotic-barista-spec.md |

When developing from this bundle, treat **Palpatine** as `foundational/palpatine/` and **Overlord-Learnings** as `foundational/overlord-learnings/`. Phase 4 calls scripts as `./scripts/create-worker-with-auto-accept.sh`, `./scripts/check-worker-status.sh`, `./scripts/list-workspace-replies.sh` (paths relative to project root or as configured).

**Note:** `scripts/check-worker-status.sh` is a stub; full behavior is described in `foundational/palpatine/WORKER-MONITORING.md`. Implement or replace it per that doc when building the system.

## Foundational Documents (in this bundle)

The **essence of Overlord** is in `foundational/palpatine/` and `foundational/overlord-learnings/`. Key anchors:

- **Workflow and phases**: `foundational/palpatine/OVERLORD-GREENFIELD-WORKFLOW.md`
- **Phase gates**: `foundational/palpatine/PHASE-GATES.md` (Gate 1–5; explicit approval)
- **multiclaude interface**: `foundational/palpatine/MULTICLAUDE-INTERFACE-RULES.md` (CLI + scripts only)
- **Multiclaude worker dispatch**: `foundational/palpatine/WORKER-DISPATCH-GUIDE.md` (create-worker-with-auto-accept mandatory for multiclaude workers)
- **Multiclaude worker monitoring**: `foundational/palpatine/WORKER-MONITORING.md` (check-worker-status; liveness = shell + Claude + activity)
- **Spec-first and testing**: SPEC-FIRST-ENFORCEMENT.md, TESTING-STRATEGY.md (in palpatine)
- **Brainstorming and internalization**: INTERACTIVE-BRAINSTORMING.md, DOCUMENT-INTERNALIZATION.md (in palpatine)
- **Learnings**: `foundational/overlord-learnings/COMPREHENSIVE-LEARNINGS.md`

The spec (docs/OVERLORD-AGENT-V1-SPEC.md) contains the full Foundational Documents table and synthesis requirements.

## Real E2E run (trivial todo app)

To run Overlord with **real Claude API**, **real GitHub repo**, and **real multiclaude**:

1. **Prerequisites:** `gh` CLI (authenticated), multiclaude installed, `ANTHROPIC_API_KEY` or `CLAUDE_CODE_API_KEY` set.
2. **One-time setup:** Create repo (`gh repo create OWNER/trivial-todo-app --public`), then `multiclaude repo init https://github.com/OWNER/trivial-todo-app`.
3. **Run:** Copy `scenarios/real-e2e-todo-template.yaml` to `scenarios/real-e2e-todo.yaml`, replace `YOUR_USERNAME` with your GitHub username, then from repo root: `./scripts/run-real-e2e.sh`.

Full step-by-step (interactive and scripted): **docs/REAL-E2E-RUN.md**.

## Next step

Start implementation per **ROADMAP-V1.md**: P0 (skeleton) → P1 (state + CLI) → … → P6 (first working V1). Use **Context7** MCP for LangGraph and Click docs; use **SpecKit** MCP when refining phase-agent specs or tasks from foundational docs. Decomposition into phases and waves using the Overlord methodology can be done separately.

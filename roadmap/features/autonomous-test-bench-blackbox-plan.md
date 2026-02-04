# Test Harness — Black Box Test Plan (for approval)

This document defines the **black box tests** that must pass to prove the Overlord Test Harness is a **real, working system**: real Overlord, real Claude Code–based agent driving user input (no stubs), and optional real GitHub repo. Tests are run by the implementation team; evidence is captured and can be shown to you.

**Reference:** [autonomous-test-bench.md](autonomous-test-bench.md), [autonomous-test-bench.plan.md](autonomous-test-bench.plan.md).

---

## 1. Scope and definitions

### 1.1 System under test

- **Test Harness:** The process that starts Overlord, connects to its test socket, reads until `OVERLORD_AWAITING_INPUT`, asks the **user-side agent** for the next line, sends that line to Overlord, and repeats until `/exit` or completion. It also creates the run directory, manifest, and summary.
- **Overlord:** The real Overlord CLI running with `--test-socket`, executing Phases 0–4 (or as far as the run gets). No mock or stub Overlord.
- **User-side agent:** The component that, given goals + greenfield spec + recent Overlord output, returns the next line to send. It must be implemented with **Claude Code** (same paradigm as Overlord’s phase agents: `claude_agent_sdk` / Claude Code instances), **not** Claude API (cloud). No stub or fixed-line emulator in production runs or in the tests that claim “real system.”
- **Real repo (optional):** When not using `--no-repo`, the harness creates or uses a real GitHub repo via `gh`; run manifest records `repo` and `repo_created`.

### 1.2 What “evidence” means

For each black box test we will produce:

- **Run directory** for the test (or a reference to it), containing:
  - `run_manifest.json` (run_id, repo, repo_created, timestamp)
  - `run_summary.json` (duration_sec, exit_code, phase_reached, completion_signals_seen, etc.)
  - `overlord_output.txt` (full Overlord socket output)
  - `emulator_log.jsonl` (each turn: recent_output_preview, **reply** from the agent)
  - `artifacts/` (copy of Overlord artifacts when present)
- **Proof that the real system was used:**
  - **Real Overlord:** The harness starts the actual `overlord` CLI (e.g. `python -m overlord.cli` or `overlord`) with `--test-socket`; `overlord_output.txt` shows real Overlord prompts and phase behavior.
  - **Real Claude Code agent:** The user-side agent is the Claude Code–based implementation (not the stub). Evidence: (a) configuration or code path shows the Claude Code agent is used in that run, and (b) `emulator_log.jsonl` shows **at least one reply that is not the stub’s single-line `/exit`** — e.g. a repo name, “yes”, or another gate answer before any `/exit`, demonstrating the agent produced content from context.

### 1.3 Prerequisites for running these tests

- **Claude Code:** API key available (`ANTHROPIC_API_KEY` or `CLAUDE_CODE_API_KEY`); `claude_agent_sdk` (or equivalent) used by the user-side agent.
- **Overlord:** Installed and runnable from repo root (e.g. `python -m overlord.cli`).
- **Optional (for repo tests):** `gh` installed and authenticated so the harness can create a real repo.

---

## 2. Black box test cases

### BB-1: Real Overlord and real Claude Code agent — single scenario run

**Purpose:** Prove one full harness run uses the real Overlord process and the real Claude Code–based user agent (no stub). Overlord gets at least one real user reply (e.g. repo name or “yes”) from Claude Code before the session may exit.

**Preconditions:**

- API key set for Claude Code.
- Greenfield spec available, e.g. `greenfield-specs/trivial-todo-app.md`.
- Harness configured to use the **Claude Code** user agent for this run (no stub).

**Steps:**

1. Run the Test Harness with the synthesized scenario that drives the run. Use either:
   - **Scenario file:** `scenarios/test-harness/bb-trivial-todo.yaml`, or  
   - **From spec:** `--from-spec greenfield-specs/trivial-todo-app.md` (harness synthesizes equivalent scenario in memory).  
   Run **without** `--no-repo` (or with `--no-repo` if repo is not required for this test), using the **Claude Code** agent.
2. Harness starts Overlord with `--test-socket`, connects, and for each `OVERLORD_AWAITING_INPUT` calls the Claude Code agent to get the next line, then sends it.
3. Run continues until completion or timeout; harness writes run dir.

**Pass criteria:**

- Process exits without crash (exit code 0 or documented non-zero).
- Run directory exists and contains: `run_manifest.json`, `run_summary.json`, `overlord_output.txt`, `emulator_log.jsonl`.
- **Evidence — real Overlord:** `overlord_output.txt` contains recognizable Overlord output (e.g. prompts, phase text, or “Project:” / repo questions).
- **Evidence — real Claude Code agent:**  
  - The run is executed with the Claude Code agent implementation (not the stub).  
  - `emulator_log.jsonl` has at least one turn where the **reply** is something other than a single `/exit` with no prior substantive replies (e.g. at least one reply is a repo name, “yes”, “public”, or similar gate answer), showing the agent produced context-dependent output.

**Evidence to present:** Run dir path; contents of `run_manifest.json` and `run_summary.json`; excerpt of `overlord_output.txt` (first ~50 lines); excerpt of `emulator_log.jsonl` (first 2–3 turns with replies).

---

### BB-2: Run directory and manifest shape (real run)

**Purpose:** Prove that a real run (BB-1 or equivalent) produces a run directory and manifest that meet the feature spec and can be used for comparison and debugging.

**Preconditions:**

- Same as BB-1; run may be the same run as BB-1 or a dedicated run.

**Steps:**

1. Execute a full harness run with real Overlord and real Claude Code agent (as in BB-1).
2. Inspect run dir and manifest/summary.

**Pass criteria:**

- `run_manifest.json` contains: `run_id`, `repo`, `repo_created`, `timestamp`.
- `run_summary.json` contains: `run_id`, `repo`, `duration_sec`, `exit_code`, `phase_reached` (if applicable), `completion_signals_seen`, `artifacts_copied`.
- `overlord_output.txt` is non-empty and consistent with Overlord socket output.
- `emulator_log.jsonl` has one JSON object per turn, each with at least `recent_output_preview` and `reply`.

**Evidence to present:** Path to run dir; full `run_manifest.json` and `run_summary.json`.

---

### BB-3: Entry point — script and pytest (real agent)

**Purpose:** Prove the advertised entry points (script and pytest) run the **real** system: real Overlord and real Claude Code agent, not stub.

**Preconditions:**

- API key set; harness built so that the default or test configuration uses the Claude Code agent (not stub) when running the entry point.

**Steps:**

1. Run: `./scripts/run-test-harness.sh scenarios/test-harness/bb-trivial-todo.yaml` or `./scripts/run-test-harness.sh --from-spec greenfield-specs/trivial-todo-app.md` (with or without `--no-repo` as configured).
2. Run: a pytest-based black box test that invokes the same entry point with the scenario file or `--from-spec`, using the real Claude Code agent, and asserts on run dir and evidence.

**Pass criteria:**

- Script run completes and produces a run dir that satisfies BB-1 evidence (real Overlord + real Claude Code agent).
- Pytest run passes and its assertions check for: run dir present, manifest/summary present, and that the agent used was Claude Code with at least one non-stub reply in `emulator_log.jsonl` (or equivalent proof).

**Evidence to present:** Terminal output of script run; pytest command and output; path to run dir produced by each.

---

### BB-4: Real GitHub repo (optional)

**Purpose:** When repo creation is enabled, prove the harness creates a real GitHub repo and records it in the manifest.

**Preconditions:**

- `gh` installed and authenticated.
- Harness run **without** `--no-repo`, with a scenario that specifies `repo_name` and `repo_create: true` (or equivalent).

**Steps:**

1. Run the harness without `--no-repo` for a scenario that creates a repo.
2. Check `run_manifest.json` and GitHub.

**Pass criteria:**

- `run_manifest.json` has `repo` equal to a valid `owner/name` (or URL) and `repo_created: true`.
- The repo exists on GitHub (e.g. `gh repo view <repo>` succeeds).
- Optionally: README in repo describes the test run (per feature spec).

**Evidence to present:** `run_manifest.json`; output of `gh repo view <repo>`.

---

## 3. Summary table

| ID   | Name                          | Proves real Overlord | Proves real Claude Code agent | Evidence |
|------|-------------------------------|----------------------|-------------------------------|----------|
| BB-1 | Full run with real components | Yes (output content) | Yes (emulator_log replies)   | Run dir + excerpts |
| BB-2 | Run dir and manifest shape    | Yes (same run)       | Yes (same run)               | manifest + summary |
| BB-3 | Entry point (script + pytest) | Yes                  | Yes (config + emulator_log)  | Script/pytest output + run dir |
| BB-4 | Real GitHub repo              | —                    | —                            | manifest + gh repo view |

---

## 4. Approval and next steps

- **Your approval:** Please confirm that this black box test plan is acceptable. Once approved, the implementation will:
  1. Implement the **Claude Code–based user agent** (replacing the stub) so it is the default in production and in these tests.
  2. Wire the harness so black box tests run with real Overlord and real Claude Code agent and capture the evidence above.
  3. Run the tests and provide you the evidence (run dir paths, excerpts, and pytest/script output).
- **Tickets:** After approval, completion-plan tickets will be created (e.g. in the repo) to implement the Claude Code agent, wire it into the runner, and add the provable black box tests; then we will run the tests and present evidence.

---

## 5. Terminology and constraints

- **Claude Code** is used throughout to mean the local Claude Code / agent SDK–based component (e.g. `claude_agent_sdk`), **not** the Claude API (cloud). The user-side agent must be implemented with Claude Code in the same way Overlord’s phase agents are.
- **No stubs in “real” runs or in tests that claim to prove the system works.** Stub or scripted drivers may remain only for fast unit/integration tests that are explicitly labeled as “stub” or “no real agent” and do not claim to prove end-to-end behavior.

---

## 6. Intent of the black box scenario and minimum requirements

### 6.0 What the Test Harness is seeking to develop

The black box scenario targets the **Trivial Todo App** defined in `greenfield-specs/trivial-todo-app.md`. The Test Harness (via the Claude Code user agent) is driving Overlord to produce this app end-to-end: the agent answers Overlord’s questions (repo name, visibility, gate approvals, tech choices) and sends slash commands so that Overlord executes Phases 0–4 and delivers a minimal working todo app.

**Intent in one sentence:** Build the smallest possible todo app that can add a todo (title), list all todos (title + done flag), and mark a todo as done (by id or index), in a single wave of work, with CLI or simple UI and a passing `check.sh` (lint/test).

**Minimum requirements that drive the conversation:**

These are the requirements the agent must keep in mind when replying to Overlord so the run stays on intent and Overlord can plan and execute accordingly.

| Requirement | What the agent / Overlord should aim for |
|-------------|------------------------------------------|
| **Scope** | Single wave; minimal scope. No persistence required (in-memory OK). No auth, real-time sync, or mobile. |
| **Functional** | (1) Add todo with a title. (2) List all todos with title and done flag. (3) Mark a todo as done by identifier or index. |
| **Delivery** | CLI or simple UI. A `check.sh` (or equivalent) runs and passes (lint/test). |
| **Repo** | When Overlord asks for repo name, the agent should give the scenario’s repo name (e.g. `trivial-todo-app` or the unique run name). When asked public/private, choose per scenario (e.g. public for test runs). |
| **Gates** | Answer gate questions concisely and in line with the above: approve moving on when the plan aligns with the minimal spec; use `/done` when appropriate. |
| **Phase 4** | Request status occasionally (e.g. `/status`); send `/exit` when completion signals are seen or when the run is considered done. |

Nailing this down ensures the Claude Code agent has a clear **intent** and **minimum bar for success**, so it can drive the conversation with Overlord appropriately (short, on-spec answers and commands) rather than vague or off-spec replies.

### 6.1 Decisions and intent that guide Overlord

The Test Harness must **nail down concrete decisions** (not just “CLI or simple UI”) so the Claude Code agent can answer Overlord’s questions consistently and steer implementation toward a single, reproducible outcome. When Overlord asks about language, CLI framework, or other choices, the agent should answer according to these decisions.

**A priori and sacred:** These choices are **decided a priori** (before the run) and **kept sacred** in the Test Harness. They are the authoritative source of truth for the run: the agent must not override or contradict them; Overlord is guided toward them, not the other way around. The scenario YAML (or its synthesized equivalent) is the single place these decisions are defined. Changing them means changing the scenario, not improvising during the run.

**Decisions for the Trivial Todo App black box scenario:**

| Decision | Value | How the agent guides Overlord |
|----------|--------|-------------------------------|
| **Language / runtime** | Python 3 | When Overlord asks for language or runtime, answer “Python” or “Python 3”. |
| **CLI** | Use the **click** library for CLI | When Overlord asks how to implement the CLI or which library to use, answer “click” or “use click for the CLI”. |
| **Interface** | CLI only (no web UI) | Prefer CLI; no browser or web server for this scenario. |
| **Storage** | In-memory only | No database or file persistence; in-memory is fine. |
| **Testing** | `check.sh` runs lint and tests | When discussing delivery or verification, insist on a `check.sh` (or equivalent) that runs and passes. |
| **Repo visibility** | Public | When Overlord asks public/private, answer “public” for test runs. |

These decisions are part of the scenario (see §7.2). The harness passes them to the Claude Code agent so it can drive the conversation toward these choices whenever Overlord asks. The agent treats them as **sacred**: it does not second-guess or override them. Without them, the agent might give vague or inconsistent answers and the run could drift.

---

## 7. Scenario YAML that drives the Test Harness

Every black box run is driven by a **scenario**: a YAML structure (or equivalent) that supplies goals, greenfield spec path, repo, and optional emulator prompt / timeout / success patterns. The harness loads this and passes it to the Claude Code agent and to Overlord. We **synthesize** this in one of two ways:

1. **From a scenario YAML file** — A committed file under `scenarios/test-harness/` that the runner loads with `load_scenario(path)`. This is the canonical form for reproducible black box tests.
2. **From `--from-spec`** — The runner calls `scenario_from_spec(spec_path, run_id)` to build the same structure in memory (goals from spec heading/description, repo_name from spec basename + run_id). No YAML file is written; the scenario is identical in shape to (1).

For black box tests we use **both**: the committed YAML defines the canonical scenario; the runner can be invoked either with that file or with `--from-spec` (which synthesizes the same logical scenario). Evidence must record which scenario was used (file path or `--from-spec <path>`).

### 7.1 Scenario schema (Test Harness)

| Field | Required | Description |
|-------|----------|-------------|
| `goals` | Yes | Short description of intent (e.g. "Build the minimal trivial todo app."). |
| `greenfield_spec` | Yes | Path to the genesis spec (relative to scenario file or absolute). |
| `repo` | Yes | Either `repo_name` (unique base name; harness may append run_id) or `repo_url` (existing repo). |
| `emulator_prompt` | No | Path or name of user-agent prompt variant. |
| `repo_create` | No | When `repo_name` is set, if true (default) harness creates repo via `gh`; if false, repo must exist. |
| `timeout` | No | Wall-clock timeout in seconds. |
| `success` | No | List of stdout patterns that indicate success (default: "Workgraph complete", "Planning and execution ready"). |
| `decisions` | No | Dict of concrete choices the agent steers Overlord toward (e.g. `language`, `cli`, `interface`, `storage`, `testing`, `repo_visibility`). See §6.1. |

### 7.2 Synthesized scenario YAML used for black box tests

**File:** `scenarios/test-harness/bb-trivial-todo.yaml`

This is the scenario that drives BB-1, BB-2, BB-3 (and BB-4 when run without `--no-repo`). It targets the same greenfield spec as the existing Overlord scenario (`greenfield-specs/trivial-todo-app.md`) and specifies a repo name so the harness can create a unique repo per run when not using `--no-repo`.

```yaml
goals: "Build the minimal trivial todo app (add, list, mark done). Single wave; prefer concise answers."
greenfield_spec: "../../greenfield-specs/trivial-todo-app.md"
repo:
  repo_name: "trivial-todo-app"
repo_create: true
timeout: 600
success:
  - "Workgraph complete"
  - "Planning and execution ready"
decisions:
  language: "Python 3"
  cli: "Use the click library for CLI"
  interface: "CLI only (no web UI)"
  storage: "In-memory only"
  testing: "check.sh runs lint and tests"
  repo_visibility: "public"
```

**How tests use it:**

- **BB-1, BB-2:** Run harness with `scenarios/test-harness/bb-trivial-todo.yaml` (or with `--from-spec greenfield-specs/trivial-todo-app.md` so the scenario is synthesized in memory). With `--no-repo` the harness uses a fake repo; without `--no-repo` it creates a real repo (requires `gh`).
- **BB-3:** Same scenario; entry point (script or pytest) is invoked with this scenario file or with `--from-spec greenfield-specs/trivial-todo-app.md`.
- **BB-4:** Run with the same scenario file **without** `--no-repo`; harness resolves repo via `resolve_repo()`, creates the repo, and writes the README.

The runner and pytest must accept a scenario file path so that the exact YAML above is what drives the run; when we use `--from-spec`, the implementation must synthesize a scenario that matches this shape (same goals, same greenfield spec, repo_name derived from spec basename + run_id).

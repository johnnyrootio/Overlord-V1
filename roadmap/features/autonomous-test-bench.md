# Feature: Overlord Test Harness

## Summary

The **Overlord Test Harness** is an autonomous, black-box system that runs a full Overlord session (Phases 0–4) with a **user-emulator agent** driving input from goals and the greenfield spec. The Test Harness captures all output and Overlord artifacts so we can evaluate system performance, learn from behavior, and compare run 1 vs run N. **Cursor must be able to run it** with no manual steps. This feature requires changes to **both Overlord** (test mode with socket I/O) and the **Overlord Test Harness** (new subsystem).

## Background

Today we run Overlord manually or via scripted scenarios (YAML with fixed gate answers). To evaluate and improve Overlord we need:

- **Autonomous runs**: No human at the keyboard; a process that behaves like a user.
- **Realistic interaction**: Overlord may ask questions in different order or context; scripted answer sequences are brittle. The emulator must **produce** gate answers from intent, not from a fixed list.
- **Evaluation and learning**: Exhaustive capture (Overlord logs + session I/O) so we can diagnose failures, compare runs, and iterate on prompts or behavior.
- **Cursor-runnable**: A single command or test (e.g. `pytest tests/...` or `./scripts/run-test-bench.sh`) that Cursor can execute to validate the system.

## Goals

- **Black-box**: The Overlord Test Harness and Overlord run as **separate processes**. Communication is via a **socket in test mode**: Overlord accepts a test-mode socket (e.g. `--test-socket`) for its I/O stream; the Test Harness **connects** to that socket to read what Overlord prints and send the emulator’s replies. The emulator still “acts like a keyboard” over that channel. No subprocess pipes; the “waiting for input” signal (or equivalent) is used on the socket stream.
- **YAML-driven intent**: A YAML file describes **goals** (e.g. “build the simplest possible todo app” vs “build a robust, production-ready version”) and may reference which greenfield spec and which emulator prompt variant to use. The emulator is **LLM-driven** and uses this plus the greenfield spec to decide how to answer, so it can handle variable question order.
- **Variants**: Support multiple **emulator prompt variants** (e.g. minimal vs thorough) and multiple **greenfield specs**, so we can test different outcomes and app targets.
- **Realistic user behavior**: The emulator should emulate a user who cares about progress: in addition to answering gates in Phases 0–2, it should **periodically request status** (e.g. `/status` or a short question to the Execution Manager) during Phase 4, and understand **slash commands** (`/done`, `/status`, `/help`, `/exit`).
- **Real GitHub repos**: The Overlord Test Harness uses **real GitHub and real MultiClaude only** (no stubs). Each run targets a specific repo: the Test Harness **creates** a new repo under the authenticated user’s account with a **unique name per run** (e.g. **project** + **run identifier** such as date/time or run id: `trivial-todo-app-e2e-20250130-143022`), or uses an existing repo by URL. **Run–repo tracking** is required: every run is associated with a repo identifier, stored in a run manifest and in the run summary.
- **Implementation**: The Overlord Test Harness is implemented in **Python**. The user-emulator agent is **Claude Code–based** (same paradigm as Overlord’s phase agents), not Claude API.

---

## 1. Overlord interface (preconditions)

### 1.1 Test mode: socket I/O

Overlord must support a **test mode** in which its I/O (stdin/stdout and optionally stderr) is carried over a **socket** instead of the process’s standard streams. For example: Overlord is started with a flag such as `--test-socket <addr>` (or a socket path / port) and uses that socket for reading user input and writing output. The Overlord Test Harness runs as a **separate process** and connects to that socket to drive the session. This allows the Test Harness and Overlord to be independent processes while preserving the “keyboard and screen” semantics.

### 1.2 “Waiting for input” marker

Overlord must emit a **clear, consistent marker** when it is blocking for user input (e.g. a single line such as `OVERLORD_AWAITING_INPUT` or a documented prompt line). This applies to normal stdin/stdout runs and to the socket stream in test mode. The emulator waits for this marker before sending the next line. No scraping of ad-hoc prompt text.

*Implementation note: may be conditional on an env var (e.g. `OVERLORD_TEST_HARNESS=1`) so production runs are unchanged, or always-on as the canonical “waiting for input” UX.*

### 1.3 Completion / success signals

Overlord (or the CLI) already emits completion text that the Test Harness can parse to decide “run succeeded,” e.g.:

- “Workgraph complete. All issues closed.”
- “Planning and execution ready.”
- “Staying in session. Type /exit to quit.”

The Test Harness **treats these as success markers**: when it sees them on the socket stream (or stdout), it may mark the run as successful and send `/exit` to close the session cleanly.

---

## 2. User-emulator agent

The user-emulator agent is **Claude Code–based** (same paradigm as Overlord’s phase agents), not Claude API. The Test Harness invokes it as a Claude Code agent when it needs the next reply.

### 2.1 Role

- **Input**: Everything Overlord has printed since the last user input (or since start), plus **YAML goals** and the **greenfield spec** for the run.
- **Output**: A short reply (one or a few lines) to send to Overlord on stdin: gate answers (e.g. “Python”, “Yes”, “B”), slash commands (e.g. `/done`, `/status`, `/exit`), or natural-language (e.g. “Have any issues been completed?”).
- **Guided by**: YAML (intent, e.g. “simplest todo app” vs “robust remote app”) and the greenfield spec, so the emulator effectively “programs itself” from the spec and goals.

### 2.2 When to respond

- The Test Harness waits for Overlord’s **“waiting for input”** marker on the socket stream, then passes the **current prompt text** (or full output since last reply) to the emulator agent.
- The emulator (Claude Code agent) decides the reply; the Test Harness sends it over the socket and logs it (see Capture).

### 2.3 Behavior to emulate

The emulator’s **system prompt** (and any YAML “behavior” section) must be informed by real user behavior:

- **Phases 0–2**: Answer Overlord’s questions concisely and in line with the goals (tech stack, options A/B/C, approvals, `/done` when appropriate).
- **Phase 4**: Occasionally send **`/status`** (or a short question) to emulate a user who monitors progress; use **`/exit`** when the Test Harness has seen completion signals or when the run is considered done.
- **Slash commands**: Understand and use `/done`, `/status`, `/help`, `/exit` as appropriate.

### 2.4 Prompt variants

Support **multiple emulator prompts** (e.g. “minimal — get to done with fewest words” vs “thorough — prefer detailed answers and frequent status”). The YAML selects which variant to use so we can modulate outcomes and test robustness.

---

## 3. Overlord Test Harness and orchestration

### 3.1 Flow

1. Test Harness starts **Overlord in test mode** (e.g. with `--test-socket` or equivalent), so Overlord listens (or connects) on a socket for I/O.
2. Test Harness runs as a **separate process** and **connects** to that socket.
3. Test Harness reads from the socket until it sees the **“waiting for input”** marker.
4. Test Harness invokes the **emulator agent** (Claude Code) with: current phase (if detectable), prompt text since last input, YAML goals, greenfield spec path (or contents).
5. Emulator returns the next line(s); Test Harness writes them over the socket and **logs** (see Capture).
6. Repeat until: Overlord closes the session, or Test Harness sees **completion signals** and sends `/exit`, or a timeout/error.

### 3.2 YAML scenario format (draft)

- **goals**: Short description of intent (e.g. “Build the simplest possible todo app; prefer minimal scope.”).
- **greenfield_spec**: Path to the genesis spec (e.g. `greenfield-specs/trivial-todo-app.md`).
- **emulator_prompt**: Path to the emulator system prompt (or variant name).
- **repo**: **Required.** GitHub repo for this run. One of:
  - **repo_name**: A unique repo name. Repos are named with **project** (e.g. `trivial-todo-app`) plus a **run identifier** (e.g. date/time or run id), e.g. `trivial-todo-app-e2e-20250130-143022` or `trivial-todo-app-oth-run-1738243822`. The Test Harness creates the repo under the **authenticated user’s account** (via `gh`); creation fails if the repo already exists. Either the scenario supplies a unique name or the Test Harness generates one (e.g. base + timestamp or run id).
  - **repo_url**: Full URL of an existing repo (e.g. `https://github.com/<owner>/<repo>`). Test Harness uses this repo as-is; no create. Useful for re-running against a known repo.
- **repo_create**: Optional. When **repo_name** is set: if `true` (default), Test Harness creates the repo; if `false`, the repo must already exist and Test Harness only resolves it.
- **timeout**: Optional wall-clock timeout for the run.
- **success**: Optional list of stdout patterns that indicate success (default: include “Workgraph complete”, “Planning and execution ready”).

The Test Harness assumes **`gh` is installed and authenticated**; repos are created under the account returned by `gh auth status`. Align other fields (e.g. state dir) with existing `scenarios/*.yaml` where possible.

### 3.3 Run–repo tracking

- For each run, the Test Harness **resolves the repo** before starting Overlord: if the scenario specifies **repo_name** and **repo_create: true**, it creates the repo (fails if name already exists unless a unique name was generated); if **repo_url** is set, it uses that repo.
- The Test Harness passes the chosen repo (name or URL) to Overlord so the session targets the correct repo (e.g. via CLI flag or scenario-derived config).
- Every run directory must contain a **run manifest** (e.g. `run_manifest.json` or `run_manifest.yaml`) with at least:
  - **run_id** or **timestamp**
  - **repo**: repo identifier (e.g. `owner/name` or full URL)
  - **repo_created**: optional boolean (true if Test Harness created the repo this run)
- The **run summary** used for comparison (see §4.2) must include the **repo identifier** so “run 1 vs run N” also tells us which repo each run used.

### 3.4 Test-repo README

When the Overlord Test Harness creates a repo (or at the start of a run against a dedicated test repo), it must **write a README** in that repo that describes the run. The README is the primary human-readable record of what the repo is for. It must include:

- A statement that this is a **test-harness-driven test repo** (e.g. “This repository was created and used by the Overlord Test Harness for an end-to-end run.”).
- The **essence of the test**: e.g. “Working on a trivial todo list” or the greenfield spec / scenario name.
- **Run context** so we can identify the run: at least **date and time** (of run start or repo creation), and optionally run id, scenario file name, or other identifiers.

Example tone: “This is a test-harness-driven test repo. Run: trivial todo list (scenario: trivial-todo-app-e2e.yaml). Started: 2025-01-30 14:30:22 UTC. Run id: run-1738243822.”

---

## 4. Capture and evaluation

### 4.1 Per-run capture

For each run, the Test Harness must capture:

- **Run manifest**: At least run id/timestamp, **repo** (owner/name or URL), and optionally **repo_created** (see §3.3). Stored in the run directory (e.g. `run_manifest.json`).
- **Overlord output** (full stream from the socket, or stdout/stderr equivalent).
- **Emulator log**: For each turn, what the emulator saw (prompt or summary) and what it replied; optional: reason or confidence. So Cursor (and humans) can **diagnose** why the emulator said what it did.
- **Overlord artifacts**: Copy or symlink `~/.overlord/projects/<project_id>/artifacts/` into a **run directory** (e.g. `test-harness-runs/run-<timestamp>/`) so each run is self-contained (conversations, execution logs, plan, tasks, workgraph, etc.).

### 4.2 Run summary (for comparison)

Produce a **small summary** per run, e.g.:

- **Phase reached** (0–4).
- **Duration** (wall clock).
- **Exit code** (if process exited).
- **Completion signals seen** (yes/no).
- **Artifacts present** (e.g. `workgraph.yml`, `issues.json`, phase_4 execution log).
- **Repo** (repo identifier: owner/name or URL) so runs are tied to the correct repo.

So we can **diff run 1 vs run N** without re-reading full logs (e.g. “run 3 → repo X, phase 4, completion; run 7 → repo Y, timed out in phase 1”).

### 4.3 Cursor visibility

Emulator logs (and optionally a live tail of Overlord stdout) must be **visible** to Cursor during the run—e.g. written to a file in the run directory and/or to stderr—so that when the system misbehaves, Cursor can see what the emulator saw and replied.

---

## 5. Success criteria for a run

The **ultimate success criterion** is **working software**: the run completes all phases (0–4), Overlord and MultiClaude finish the planned work, and the delivered system is good software—e.g. the target repo’s black box tests pass, `./scripts/check.sh` passes, and the app is runnable. The criteria below are concrete ways to measure that; together they are inclusive of “working software.”

A run is considered **successful** when:

- Overlord’s process exits with code 0 **or**
- The Test Harness observes the agreed **completion signals** (e.g. “Workgraph complete. All issues closed.”) and optionally sends `/exit` and gets a clean shutdown.

**Optional stricter criteria** (all support the goal of working software):

- Required artifacts exist (e.g. `workgraph.yml`, `issues.json`, phase_4 execution log).
- Target repo’s `./scripts/check.sh` passes (if the run is supposed to produce a full app).
- Black box tests (and other test layers) in the target repo pass.

The feature doc does not mandate a single definition; the Test Harness should allow **configuring** which criteria apply. For now, the goal is to run through all phases to the end where Overlord and MultiClaude have completed the work and the result is **working software** (phases complete, tests passing, check.sh green).

---

## 6. Acceptance criteria (implementation)

**Overlord (this repo):**

- [ ] **Overlord**: Supports **test mode** with **socket I/O** (e.g. `--test-socket` or equivalent); when in test mode, Overlord uses the socket for reading user input and writing output.
- [ ] **Overlord**: Emits a clear, documented “waiting for input” marker on the socket stream (and/or stdin when not in test mode) when blocking for user input.

**Overlord Test Harness (new subsystem, Python):**

- [ ] **Test Harness**: Implemented in **Python**. Starts Overlord in test mode (socket); runs as a **separate process** that **connects** to the socket; reads until marker; invokes **emulator agent** (Claude Code); sends reply over socket; repeats until completion or timeout.
- [ ] **Emulator agent**: **Claude Code–based** (same paradigm as Overlord’s phase agents); takes prompt text + YAML goals + greenfield spec; returns one or more lines; prompt instructs it to emulate gate answers, use slash commands, and periodically request status in Phase 4.
- [ ] **YAML**: Scenario file specifies goals, greenfield spec path, emulator prompt variant, **repo** (unique repo name or repo URL), optional repo_create/timeout/success patterns.
- [ ] **Repo**: Scenario specifies repo (unique name or URL); Test Harness creates repo when required (under authenticated user’s account); **repo names are unique per run** (project + run identifier: user-supplied or harness-generated from base + timestamp/run-id).
- [ ] **Test-repo README**: When the Test Harness creates (or uses) a test repo, it **writes a README** in that repo describing the run: test-harness-driven, essence of the test, and run context (date/time and optional run id or scenario).
- [ ] **Capture**: Each run writes to a run directory: **run manifest** (run id, repo, repo_created), full output from socket, emulator log (each turn: seen + reply), and copy/symlink of Overlord project artifacts.
- [ ] **Run summary**: Machine-readable summary (phase reached, duration, exit code, completion signals, key artifacts, **repo identifier**) for comparison across runs.
- [ ] **Cursor-runnable**: Single entry point (e.g. `pytest tests/...` or `./scripts/run-test-harness.sh <scenario.yaml>`) that Cursor can run with no manual steps; no regression on existing tests.
- [ ] **Docs**: Short README or section in `docs/` describing how to run the Overlord Test Harness, interpret the run directory, and add new scenarios or emulator variants.

---

## 7. Out of scope (for this feature)

- **Multiple concurrent runs**: Single run at a time is sufficient for v1; parallel runs can be a later improvement.
- **Automated comparison reports**: Diffing two run summaries can be a script or a later feature; the requirement here is that the data (summary + logs + artifacts) exists to do it.

*Note: Real GitHub and real MultiClaude are **in scope**. The Overlord Test Harness uses real GitHub repos (no stubs) created under the authenticated user’s account; repo names must be unique per run (project + run identifier); runs are tracked against repo names via the run manifest and run summary; the Test Harness writes a README in each created test repo describing the run.*

---

## GitHub

- **Labels**: `area:testing`, `area:cli`, `type:feature`, `type:test`, `type:docs`, `roadmap:backlog`
- **Issues**: Work graph issues **#1–#22** (one per task T0.1–T3.4), ordered by dependency. [View all open issues for this feature](https://github.com/johnnyrootio/Overlord-V1/issues?q=is%3Aissue+is%3Aopen+%22Test+Harness%22). See [autonomous-test-bench.plan.md](autonomous-test-bench.plan.md) and [autonomous-test-bench-tickets.md](autonomous-test-bench-tickets.md) for task IDs and dependency order.
- **Completion (finalization)**: Issues **#23–#28** (TH-C1–TH-C6): Claude Code user agent, wire runner, black box tests BB-1–BB-4, docs. See [autonomous-test-bench-completion-tickets.md](autonomous-test-bench-completion-tickets.md).

---

## Black box test plan

A **black box test plan** defines tests that prove the system works with **real Overlord** and a **real Claude Code–based user agent** (no stubs), with evidence you can inspect. The plan is written for your approval before we run the tests and push completion tickets.

- **Document:** [autonomous-test-bench-blackbox-plan.md](autonomous-test-bench-blackbox-plan.md)
- **Status:** Pending your approval. After approval, we implement the Claude Code agent, wire black box tests to the real system, run the tests, and present evidence (run dir, manifest, excerpts of overlord_output and emulator_log).

---

## References

- Existing scenario format: `scenarios/*.yaml` (e.g. `trivial-todo-app.yaml`), `docs/CHECKPOINT-SESSION.md`
- Overlord phase artifacts: `~/.overlord/projects/<id>/artifacts/` (conversations, execution_log.jsonl, plan, tasks, workgraph)
- Phase 0/1/2 conversation patterns: successful run artifacts (e.g. trivial-todo-app) show gate questions and short user replies; Phase 4 monitor and completion messages in stdout
- `MAINTAINER.md` (issue-driven roadmap, feature doc format)
- Overlord phase agents use Claude Code (e.g. `overlord/claude_api.py`, `overlord/agents/`); emulator agent follows same paradigm

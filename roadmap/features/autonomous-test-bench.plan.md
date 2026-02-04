# Overlord Test Harness — Implementation Plan

Dependency-ordered work graph of GitHub-ready tickets (including test tickets) for the Overlord Test Harness feature. Consistent with Overlord's waves, `depends_on` ordering, and testing layers (unit / integration / functional). See [autonomous-test-bench.md](autonomous-test-bench.md) for the feature spec.

---

## Approach

- **Work graph style**: Waves (wave0 foundation → wave1 harness core → wave2 capture/eval → wave3 entry/docs). Tasks have `depends_on` so one ticket can be worked at a time.
- **Testing**: Follow Overlord's test layers (unit = fast/isolated, integration = multi-component/temp dirs, functional = subprocess). Test tickets either **precede** implementation (contract/spec) or **follow** it (integration/E2E). Tests are first-class issues.
- **Deliverable**: A single document that lists every ticket in dependency order with issue-ready title, body, type, labels, and `depends_on`. This plan can be used with `roadmap/features/autonomous-test-bench-tickets.md` (full issue bodies) and optionally `autonomous-test-bench-workgraph.yml` for tooling.

---

## Work graph (summary)

**Wave 0 — Overlord test mode (foundation)**  
- **T0.1** [Doc] Define "waiting for input" marker spec — no deps.  
- **T0.2** [Impl] Add `--test-socket` and socket I/O for Overlord stdin/stdout — depends on T0.1.  
- **T0.3** [Impl] Emit marker when blocking for input (stdin and socket) — depends on T0.2.  
- **T0.4** [Test/unit] Parser/detector for marker in stream — depends on T0.1.  
- **T0.5** [Test/integration] Overlord test mode E2E: start with socket, connect, see marker, send line — depends on T0.3, T0.4.

**Wave 1 — Test Harness core**  
- **T1.1** [Test/unit] Scenario YAML schema (goals, greenfield_spec, repo, emulator_prompt) — no deps.  
- **T1.2** [Impl] Scenario YAML loader and validation — depends on T1.1.  
- **T1.2a** [Test/unit] Scenario-from-spec generator: given spec path, output YAML has required fields and passes loader; goals/repo base derived from spec (title, description) — depends on T1.1.  
- **T1.2b** [Impl] Generate scenario YAML from any greenfield spec (default goals, greenfield_spec path, repo_name base from spec basename + run id); optional overrides (goals, repo_name, emulator_prompt) — depends on T1.2, T1.2a.  
- **T1.3** [Impl] Harness skeleton: Python package, connect to socket, read until marker, send one line — depends on T0.5.  
- **T1.4** [Impl] Emulator agent (Claude Code): input = prompt + YAML goals + greenfield spec, output = line(s) — depends on T1.2.  
- **T1.5** [Impl] Main loop: read until marker → call emulator → send reply; slash commands — depends on T1.3, T1.4.  
- **T1.6** [Test/integration] Harness: load scenario, one socket exchange, no real emulator (or stub) — depends on T1.5.

**Wave 2 — Repo, capture, summary**  
- **T2.1** [Impl] Repo resolution: create (gh) or use repo_url; unique name per run; run manifest (run_id, repo, repo_created) — depends on T1.2.  
- **T2.2** [Impl] Test-repo README when creating/using test repo — depends on T2.1.  
- **T2.3** [Impl] Per-run capture: run dir, Overlord output, emulator log, copy/symlink artifacts — depends on T1.5.  
- **T2.4** [Impl] Run summary (phase reached, duration, exit code, completion signals, repo) — depends on T2.3.  
- **T2.5** [Test/integration] Capture and run summary: run dir and manifest present — depends on T2.3, T2.4.

**Wave 3 — Cursor-runnable and docs**  
- **T3.1** [Impl] Single entry point: `pytest tests/...` and/or `./scripts/run-test-harness.sh <scenario>`; support **`--from-spec <path>`** to generate scenario from any greenfield spec and run (E2E prep for any spec without hand-written YAML) — depends on T2.4, T2.2, T1.2b.  
- **T3.2** [Test/functional] Cursor-runnable: script or pytest runs one minimal scenario (YAML path or `--from-spec`); no regression on existing tests — depends on T3.1.  
- **T3.3** [Test/functional] E2E prep: run with `--from-spec greenfield-specs/trivial-todo-app.md` produces valid run dir and manifest (optionally assert completion or phase reached); establishes canonical E2E-from-spec path — depends on T3.1.  
- **T3.4** [Docs] README or docs section: how to run Test Harness, interpret run dir, add scenarios/emulator variants, **and use `--from-spec` for any greenfield spec** — depends on T3.1.

---

## Ticket format (for each issue)

Each ticket will be written with:

- **Title**: Short, actionable (e.g. "Test (unit): Detect OVERLORD_AWAITING_INPUT in stream").  
- **Body**: Summary, acceptance criteria, reference to `roadmap/features/autonomous-test-bench.md` and any spec (e.g. marker spec).  
- **Type**: `type:test` or `type:feature` (implementation) or `type:docs`.  
- **Labels**: `area:testing`, `area:cli` where relevant, `roadmap:backlog`.  
- **depends_on**: List of task IDs so implementers can work one ticket at a time in order.

---

## Files to add/update

- **New**: `roadmap/features/autonomous-test-bench-tickets.md` (or similarly named) containing the full work graph and the full list of tickets in dependency order, with issue-ready title + body for each. Optionally a machine-readable `autonomous-test-bench-workgraph.yml` with waves/tasks/depends_on for tooling.
- **Update**: `roadmap/features/autonomous-test-bench.md` — add a "Tickets" section that points to this plan and the tickets doc; state that issues are ordered by the work graph for one-ticket-at-a-time execution.

---

## Ordering guarantee

Tickets are ordered so that:

1. Spec/docs and tests that define behavior come before or with the implementation that satisfies them.  
2. Integration tests that require both Overlord and Harness come after the relevant implementations.  
3. Entry point and docs come after capture/summary so "run one scenario" is meaningful.

No ticket will be unblocked before its dependencies are done, matching Overlord's work-graph execution model.

---

## Scenario YAML from greenfield spec (feature + testing)

**Requirement:** The Test Harness must support generating scenario YAML from **any** greenfield spec, so we can run E2E without hand-writing a scenario file for each spec.

**How we test scenario YAML creation**

- **Unit (T1.2a):** Given a path to a greenfield spec (e.g. `greenfield-specs/trivial-todo-app.md`), the generator produces a YAML string/dict that:
  - Loads and validates via the same schema as hand-written scenarios (goals, greenfield_spec, repo, emulator_prompt, etc.).
  - Has required fields populated: `greenfield_spec` = resolved path, `goals` = derived from spec (e.g. first heading or "Project Overview" / "Description"), `repo` = `repo_name` with base from spec basename (e.g. `trivial-todo-app`) plus run identifier so it's unique.
  - Optional: test overrides (custom goals, repo_name, emulator_prompt) merge correctly and still validate.
- **Integration:** Harness run using a **generated** scenario (from spec) produces the same run directory and manifest shape as a run using a hand-written YAML file; covered by T1.6 and T2.5 once generator is used in the run path.

**E2E preparation**

- **Generator (T1.2b):** Implement a function/module that, given a greenfield spec path (and optional overrides), returns a scenario dict/YAML suitable for the loader. Use it both for `--from-spec` and in tests (generate in temp, run harness).
- **Entry point (T3.1):** Support `--from-spec <path>`. When used, the harness generates the scenario from that path (with optional overrides via flags or env), then runs the same flow as when given a scenario file. No separate "scenario file" is required for every spec.
- **E2E test (T3.3):** A functional test runs the harness with `--from-spec greenfield-specs/trivial-todo-app.md` (or a minimal in-repo spec) and asserts: run directory created, run manifest present, optional phase/completion signals. This is the canonical "E2E from any greenfield spec" path and ensures the generator is wired end-to-end.

**Summary:** We do **not** hand-generate YAML for E2E only; we **generate** it from the greenfield spec. Unit tests validate the generator output; the entry point and E2E test validate that running from a spec works.

# Overlord Test Harness — Issue Bodies (work graph)

Use these to create GitHub issues. Order: dependency order (T0.1 → T3.4). Label all with `feature:autonomous-test-bench` (and create that label in the repo if needed). See [autonomous-test-bench.plan.md](autonomous-test-bench.plan.md) for the graph.

---

## T0.1 [Doc] Define "waiting for input" marker spec

**Labels:** `feature:autonomous-test-bench`, `area:cli`, `area:testing`, `type:docs`, `roadmap:backlog`

**Blocked by:** (none)

**Title:** [Test Harness] Doc: Define "waiting for input" marker spec

**Body:**

- **Task ID:** T0.1
- **Feature:** [Overlord Test Harness](autonomous-test-bench.md) | [Plan](autonomous-test-bench.plan.md)

Document the canonical marker Overlord emits when blocking for user input, so the Test Harness and any client can detect it reliably.

**Acceptance criteria:**
- [ ] A short spec (in `docs/` or feature doc) defines the exact marker (e.g. single line `OVERLORD_AWAITING_INPUT` or documented prompt).
- [ ] Spec states whether it applies to stdin/stdout only, socket-only, or both.
- [ ] Spec states any env var that enables/affects the marker (e.g. `OVERLORD_TEST_HARNESS=1`) if applicable.

---

## T0.2 [Impl] Add --test-socket and socket I/O for Overlord

**Labels:** `feature:autonomous-test-bench`, `area:cli`, `area:testing`, `type:feature`, `roadmap:backlog`

**Blocked by:** T0.1

**Title:** [Test Harness] Add --test-socket and socket I/O for Overlord stdin/stdout

**Body:**

- **Task ID:** T0.2 | **Blocked by:** T0.1
- **Feature:** [Overlord Test Harness](autonomous-test-bench.md) | [Plan](autonomous-test-bench.plan.md)

Overlord must support a test mode where I/O is carried over a socket instead of stdin/stdout. The Test Harness runs as a separate process and connects to that socket.

**Acceptance criteria:**
- [ ] CLI accepts something like `--test-socket <addr>` (or socket path/port).
- [ ] When in test mode, Overlord uses the socket for reading user input and writing output (not process stdin/stdout for that session).
- [ ] When not in test mode, behavior is unchanged.

---

## T0.3 [Impl] Emit marker when blocking for input

**Labels:** `feature:autonomous-test-bench`, `area:cli`, `area:testing`, `type:feature`, `roadmap:backlog`

**Blocked by:** T0.2

**Title:** [Test Harness] Emit "waiting for input" marker when blocking (stdin and socket)

**Body:**

- **Task ID:** T0.3 | **Blocked by:** T0.2
- **Feature:** [Overlord Test Harness](autonomous-test-bench.md) | [Plan](autonomous-test-bench.plan.md)

Overlord must emit the documented marker (from T0.1) whenever it blocks for user input, on both normal stdin/stdout and the socket stream in test mode.

**Acceptance criteria:**
- [ ] Every place that blocks for user input (e.g. `_safe_input()`, gate prompts) emits the marker before blocking.
- [ ] Marker is emitted on the socket stream in test mode and on stdout (or as specified) when not in test mode.
- [ ] No ad-hoc prompt scraping required; the marker is the single contract.

---

## T0.4 [Test/unit] Parser/detector for marker in stream

**Labels:** `feature:autonomous-test-bench`, `area:testing`, `type:test`, `roadmap:backlog`

**Blocked by:** T0.1

**Title:** [Test Harness] Test (unit): Parser/detector for OVERLORD_AWAITING_INPUT in stream

**Body:**

- **Task ID:** T0.4 | **Blocked by:** T0.1
- **Feature:** [Overlord Test Harness](autonomous-test-bench.md) | [Plan](autonomous-test-bench.plan.md)

Add a small utility or function that detects the "waiting for input" marker in a stream (string or line buffer). Used by the Test Harness to know when to send the next reply. Unit-test this detector.

**Acceptance criteria:**
- [ ] Function/module that given a stream (or accumulated string) returns whether the marker has been seen (and optionally consumes up to it).
- [ ] Unit tests: marker present → detected; marker absent → not detected; marker split across chunks → still detected when complete.
- [ ] Tests live in `tests/unit/` and pass with `pytest tests/unit/`.

---

## T0.5 [Test/integration] Overlord test mode E2E (socket, marker, one exchange)

**Labels:** `feature:autonomous-test-bench`, `area:testing`, `area:cli`, `type:test`, `roadmap:backlog`

**Blocked by:** T0.3, T0.4

**Title:** [Test Harness] Test (integration): Overlord test mode — socket connect, see marker, send line

**Body:**

- **Task ID:** T0.5 | **Blocked by:** T0.3, T0.4
- **Feature:** [Overlord Test Harness](autonomous-test-bench.md) | [Plan](autonomous-test-bench.plan.md)

Integration test: start Overlord with `--test-socket`, connect from a client, read until the "waiting for input" marker, send one line, and assert the session responds (e.g. no crash, output received).

**Acceptance criteria:**
- [ ] Test in `tests/integration/` starts Overlord in test mode, connects to the socket, reads until marker, sends a line (e.g. "yes"), and asserts success (exit code or output).
- [ ] Marked `@pytest.mark.integration`; passes with `pytest tests/integration/`.
- [ ] No full emulator; minimal client only.

---

## T1.1 [Test/unit] Scenario YAML schema

**Labels:** `feature:autonomous-test-bench`, `area:testing`, `type:test`, `roadmap:backlog`

**Blocked by:** (none)

**Title:** [Test Harness] Test (unit): Scenario YAML schema — goals, greenfield_spec, repo, emulator_prompt

**Body:**

- **Task ID:** T1.1
- **Feature:** [Overlord Test Harness](autonomous-test-bench.md) | [Plan](autonomous-test-bench.plan.md)

Define and unit-test the expected schema for scenario YAML: required and optional fields (goals, greenfield_spec, repo with repo_name or repo_url, emulator_prompt, timeout, success patterns, repo_create). Tests validate that valid YAML loads and invalid YAML is rejected or validated with clear errors.

**Acceptance criteria:**
- [ ] Schema documented (e.g. in code as dataclass/attrs or in docs); required: goals, greenfield_spec, repo (repo_name or repo_url).
- [ ] Unit tests: valid scenario YAML parses; missing required fields fail validation; optional fields have defaults.
- [ ] Tests in `tests/unit/` (or harness package tests).

---

## T1.2 [Impl] Scenario YAML loader and validation

**Labels:** `feature:autonomous-test-bench`, `area:testing`, `type:feature`, `roadmap:backlog`

**Blocked by:** T1.1

**Title:** [Test Harness] Scenario YAML loader and validation

**Body:**

- **Task ID:** T1.2 | **Blocked by:** T1.1
- **Feature:** [Overlord Test Harness](autonomous-test-bench.md) | [Plan](autonomous-test-bench.plan.md)

Implement the loader that reads a scenario YAML file (or dict) and returns a validated scenario object (goals, greenfield_spec path, repo, emulator_prompt, timeout, success, repo_create). Used by the Test Harness for every run.

**Acceptance criteria:**
- [ ] Loader accepts path or dict; returns structured scenario; raises or returns error for invalid input.
- [ ] Validation respects schema from T1.1; optional fields have sensible defaults.
- [ ] Covered by unit tests from T1.1 and any additional tests.

---

## T1.2a [Test/unit] Scenario-from-spec generator output

**Labels:** `feature:autonomous-test-bench`, `area:testing`, `type:test`, `roadmap:backlog`

**Blocked by:** T1.1

**Title:** [Test Harness] Test (unit): Scenario-from-spec generator — output has required fields, passes loader

**Body:**

- **Task ID:** T1.2a | **Blocked by:** T1.1
- **Feature:** [Overlord Test Harness](autonomous-test-bench.md) | [Plan](autonomous-test-bench.plan.md)

Unit tests for the scenario generator that will produce scenario YAML from a greenfield spec path. Given a spec path (e.g. `greenfield-specs/trivial-todo-app.md`), the generator output must have required fields (greenfield_spec, goals, repo with base from spec basename + run id) and pass the scenario loader. Optional: test overrides (goals, repo_name, emulator_prompt) merge correctly.

**Acceptance criteria:**
- [ ] Tests (can be written before or with T1.2b) that call the generator with a spec path and assert: output loads via loader, required fields present, goals/repo base derived from spec.
- [ ] Override tests if generator supports them.

---

## T1.2b [Impl] Generate scenario YAML from any greenfield spec

**Labels:** `feature:autonomous-test-bench`, `area:testing`, `type:feature`, `roadmap:backlog`

**Blocked by:** T1.2, T1.2a

**Title:** [Test Harness] Generate scenario YAML from any greenfield spec

**Body:**

- **Task ID:** T1.2b | **Blocked by:** T1.2, T1.2a
- **Feature:** [Overlord Test Harness](autonomous-test-bench.md) | [Plan](autonomous-test-bench.plan.md)

Implement a function/module that, given a greenfield spec path and optional overrides (goals, repo_name, emulator_prompt), returns a scenario dict (or YAML string) suitable for the loader. Default goals and repo_name base derived from spec (e.g. title/description and basename); run identifier appended for uniqueness.

**Acceptance criteria:**
- [ ] Generator accepts spec path + optional overrides; returns scenario that passes loader.
- [ ] Default goals derived from spec content (e.g. first heading or Project Overview); repo_name base from spec basename + run id.
- [ ] Unit tests from T1.2a pass.

---

## T1.3 [Impl] Harness skeleton — connect to socket, read until marker, send line

**Labels:** `feature:autonomous-test-bench`, `area:testing`, `type:feature`, `roadmap:backlog`

**Blocked by:** T0.5

**Title:** [Test Harness] Harness skeleton: connect to socket, read until marker, send one line

**Body:**

- **Task ID:** T1.3 | **Blocked by:** T0.5
- **Feature:** [Overlord Test Harness](autonomous-test-bench.md) | [Plan](autonomous-test-bench.plan.md)

Python package (or module) for the Test Harness that: connects to the Overlord test socket, reads from the socket until the "waiting for input" marker is seen, sends one line of input, and can repeat. No emulator agent yet; can send a fixed string or take it as an argument.

**Acceptance criteria:**
- [ ] Package/module in repo (e.g. `test_harness/` or under `overlord/`) that connects to a given socket address.
- [ ] Reads lines until marker detected (using detector from T0.4); sends one line; can loop for multiple exchanges.
- [ ] Runnable from CLI or as library; covered by integration test (e.g. with Overlord in test mode).

---

## T1.4 [Impl] Emulator agent (Claude Code)

**Labels:** `feature:autonomous-test-bench`, `area:testing`, `type:feature`, `roadmap:backlog`

**Blocked by:** T1.2

**Title:** [Test Harness] Emulator agent (Claude Code): prompt + goals + spec → reply line(s)

**Body:**

- **Task ID:** T1.4 | **Blocked by:** T1.2
- **Feature:** [Overlord Test Harness](autonomous-test-bench.md) | [Plan](autonomous-test-bench.plan.md)

Implement the user-emulator agent as a Claude Code–based agent (same paradigm as Overlord phase agents). Input: prompt text (what Overlord printed since last input), YAML goals, greenfield spec path or contents. Output: one or a few lines to send to Overlord (gate answers, slash commands, or natural language). System prompt instructs it to emulate gate answers, use /done, /status, /exit, and periodically request status in Phase 4.

**Acceptance criteria:**
- [ ] Emulator invoked with prompt + goals + spec; returns string (one or more lines) to send.
- [ ] Claude Code–based (not raw API); prompt instructs slash commands and Phase 4 behavior.
- [ ] Can be called from the harness loop; optional: support multiple emulator prompt variants (path or name).

---

## T1.5 [Impl] Main loop: read until marker → emulator → send reply

**Labels:** `feature:autonomous-test-bench`, `area:testing`, `type:feature`, `roadmap:backlog`

**Blocked by:** T1.3, T1.4

**Title:** [Test Harness] Main loop: read until marker → call emulator → send reply; slash commands

**Body:**

- **Task ID:** T1.5 | **Blocked by:** T1.3, T1.4
- **Feature:** [Overlord Test Harness](autonomous-test-bench.md) | [Plan](autonomous-test-bench.plan.md)

Orchestration loop: (1) read from socket until "waiting for input" marker; (2) pass accumulated prompt text + scenario goals + greenfield spec to emulator agent; (3) send emulator reply over socket; (4) repeat until completion (Overlord exits, completion signals seen, or timeout). Emulator may return slash commands (/done, /status, /exit); pass them through. Optionally detect completion signals and send /exit.

**Acceptance criteria:**
- [ ] Loop implemented; uses marker detector, socket I/O, and emulator from previous tasks.
- [ ] Runs until session end or timeout; completion signals (from feature doc) can trigger /exit.
- [ ] Integrates with scenario (YAML) for goals and spec path.

---

## T1.6 [Test/integration] Harness: load scenario, one socket exchange (stub emulator)

**Labels:** `feature:autonomous-test-bench`, `area:testing`, `type:test`, `roadmap:backlog`

**Blocked by:** T1.5

**Title:** [Test Harness] Test (integration): Load scenario, one socket exchange, stub emulator

**Body:**

- **Task ID:** T1.6 | **Blocked by:** T1.5
- **Feature:** [Overlord Test Harness](autonomous-test-bench.md) | [Plan](autonomous-test-bench.plan.md)

Integration test: load a scenario YAML (or generated from spec), start Overlord in test mode, run harness for one or a few exchanges with a stub emulator (fixed replies or no-op) and assert the harness completes without error and at least one exchange occurs.

**Acceptance criteria:**
- [ ] Test loads scenario (file or generated); starts Overlord with --test-socket; runs harness with stub emulator; asserts one exchange and clean shutdown or expected state.
- [ ] In `tests/integration/`; marked `@pytest.mark.integration`.

---

## T2.1 [Impl] Repo resolution: create or use repo_url; run manifest

**Labels:** `feature:autonomous-test-bench`, `area:testing`, `type:feature`, `roadmap:backlog`

**Blocked by:** T1.2

**Title:** [Test Harness] Repo resolution: create (gh) or use repo_url; unique name per run; run manifest

**Body:**

- **Task ID:** T2.1 | **Blocked by:** T1.2
- **Feature:** [Overlord Test Harness](autonomous-test-bench.md) | [Plan](autonomous-test-bench.plan.md)

Resolve repo for each run: if scenario has repo_url, use it; if repo_name (and repo_create true), create repo via `gh` under authenticated user; ensure unique name per run (base + timestamp or run id). Write run manifest (run_id, repo identifier, repo_created) into run directory.

**Acceptance criteria:**
- [ ] Repo resolution before starting Overlord; pass chosen repo to Overlord (CLI flag or config).
- [ ] Run manifest (e.g. run_manifest.json) with run_id, repo (owner/name or URL), repo_created.
- [ ] Assumes `gh` installed and authenticated.

---

## T2.2 [Impl] Test-repo README when creating/using test repo

**Labels:** `feature:autonomous-test-bench`, `area:testing`, `type:feature`, `roadmap:backlog`

**Blocked by:** T2.1

**Title:** [Test Harness] Test-repo README when creating or using test repo

**Body:**

- **Task ID:** T2.2 | **Blocked by:** T2.1
- **Feature:** [Overlord Test Harness](autonomous-test-bench.md) | [Plan](autonomous-test-bench.plan.md)

When the Test Harness creates a repo (or at run start for a dedicated test repo), write a README in that repo: test-harness-driven, essence of the test (e.g. scenario name or greenfield spec), run context (date/time, optional run id).

**Acceptance criteria:**
- [ ] README written (e.g. via gh or API) with required content per feature doc §3.4.
- [ ] Human-readable; identifies run and purpose.

---

## T2.3 [Impl] Per-run capture: run dir, output, emulator log, artifacts

**Labels:** `feature:autonomous-test-bench`, `area:testing`, `type:feature`, `roadmap:backlog`

**Blocked by:** T1.5

**Title:** [Test Harness] Per-run capture: run dir, Overlord output, emulator log, artifacts copy

**Body:**

- **Task ID:** T2.3 | **Blocked by:** T1.5
- **Feature:** [Overlord Test Harness](autonomous-test-bench.md) | [Plan](autonomous-test-bench.plan.md)

For each run, create a run directory (e.g. test-harness-runs/run-<timestamp>) and capture: full Overlord output (socket stream), emulator log (per turn: what emulator saw + reply), and copy or symlink of Overlord project artifacts (~/.overlord/projects/<id>/artifacts/). Run manifest already in run dir (T2.1).

**Acceptance criteria:**
- [ ] Run directory created; Overlord output saved; emulator log written each turn; artifacts copied or symlinked.
- [ ] Cursor can inspect run dir for diagnosis.

---

## T2.4 [Impl] Run summary (phase, duration, exit code, completion, repo)

**Labels:** `feature:autonomous-test-bench`, `area:testing`, `type:feature`, `roadmap:backlog`

**Blocked by:** T2.3

**Title:** [Test Harness] Run summary: phase reached, duration, exit code, completion signals, repo

**Body:**

- **Task ID:** T2.4 | **Blocked by:** T2.3
- **Feature:** [Overlord Test Harness](autonomous-test-bench.md) | [Plan](autonomous-test-bench.plan.md)

Produce a machine-readable run summary (e.g. run_summary.json or .yaml) with: phase reached (0–4), duration, exit code, completion signals seen (yes/no), key artifacts present, repo identifier. Enables comparison across runs without re-reading full logs.

**Acceptance criteria:**
- [ ] Summary file in run directory; includes required fields from feature doc §4.2.
- [ ] Generated at end of run (or on timeout/error).

---

## T2.5 [Test/integration] Capture and run summary present

**Labels:** `feature:autonomous-test-bench`, `area:testing`, `type:test`, `roadmap:backlog`

**Blocked by:** T2.3, T2.4

**Title:** [Test Harness] Test (integration): Run dir and manifest/summary present after run

**Body:**

- **Task ID:** T2.5 | **Blocked by:** T2.3, T2.4
- **Feature:** [Overlord Test Harness](autonomous-test-bench.md) | [Plan](autonomous-test-bench.plan.md)

Integration test: run the harness (minimal scenario or stub); assert run directory exists, run manifest and run summary are present and contain expected keys (run_id, repo, phase reached or duration, etc.).

**Acceptance criteria:**
- [ ] Test runs harness; asserts run dir, run_manifest, run summary exist and are valid.
- [ ] In `tests/integration/`; marked `@pytest.mark.integration`.

---

## T3.1 [Impl] Single entry point: pytest and/or run-test-harness.sh; --from-spec

**Labels:** `feature:autonomous-test-bench`, `area:testing`, `area:cli`, `type:feature`, `roadmap:backlog`

**Blocked by:** T2.4, T2.2, T1.2b

**Title:** [Test Harness] Single entry point: pytest / run-test-harness.sh; --from-spec <path>

**Body:**

- **Task ID:** T3.1 | **Blocked by:** T2.4, T2.2, T1.2b
- **Feature:** [Overlord Test Harness](autonomous-test-bench.md) | [Plan](autonomous-test-bench.plan.md)

Provide a single entry point so Cursor can run the Test Harness with no manual steps: e.g. `pytest tests/...` for test runs and/or `./scripts/run-test-harness.sh <scenario.yaml>`. Support `--from-spec <path>` to generate scenario from any greenfield spec and run (no hand-written YAML required).

**Acceptance criteria:**
- [ ] `pytest tests/` runs unit and integration tests (excluding long E2E if needed); or a dedicated pytest target for harness tests.
- [ ] Script or CLI to run harness with scenario file or `--from-spec greenfield-specs/foo.md`.
- [ ] No regression on existing Overlord tests.

---

## T3.2 [Test/functional] Cursor-runnable: minimal scenario or --from-spec

**Labels:** `feature:autonomous-test-bench`, `area:testing`, `type:test`, `roadmap:backlog`

**Blocked by:** T3.1

**Title:** [Test Harness] Test (functional): Cursor-runnable entry point; no regression

**Body:**

- **Task ID:** T3.2 | **Blocked by:** T3.1
- **Feature:** [Overlord Test Harness](autonomous-test-bench.md) | [Plan](autonomous-test-bench.plan.md)

Functional test: invoke the entry point (script or pytest) with a minimal scenario (or --from-spec) and assert it runs to completion (or expected exit). Assert existing Overlord tests still pass (no regression).

**Acceptance criteria:**
- [ ] Test runs entry point; minimal scenario or --from-spec; exit code or run dir as expected.
- [ ] Existing test suite (e.g. pytest tests/unit tests/integration excluding harness E2E) still passes.

---

## T3.3 [Test/functional] E2E prep: --from-spec produces run dir and manifest

**Labels:** `feature:autonomous-test-bench`, `area:testing`, `type:test`, `roadmap:backlog`

**Blocked by:** T3.1

**Title:** [Test Harness] Test (functional): E2E from --from-spec; run dir and manifest

**Body:**

- **Task ID:** T3.3 | **Blocked by:** T3.1
- **Feature:** [Overlord Test Harness](autonomous-test-bench.md) | [Plan](autonomous-test-bench.plan.md)

Functional/E2E test: run harness with `--from-spec greenfield-specs/trivial-todo-app.md` (or minimal in-repo spec). Assert: run directory created, run manifest present, optional phase or completion signals. Establishes canonical "E2E from any greenfield spec" path. May be marked to run only when env or flag set (e.g. long-running).

**Acceptance criteria:**
- [ ] Test uses --from-spec; asserts run dir and manifest; optionally asserts phase or completion.
- [ ] Marked appropriately (e.g. @pytest.mark.functional or @pytest.mark.e2e); documented how to run.

---

## T3.4 [Docs] README/docs: run Test Harness, run dir, scenarios, --from-spec

**Labels:** `feature:autonomous-test-bench`, `area:testing`, `area:docs`, `type:docs`, `roadmap:backlog`

**Blocked by:** T3.1

**Title:** [Test Harness] Docs: How to run Test Harness, interpret run dir, --from-spec

**Body:**

- **Task ID:** T3.4 | **Blocked by:** T3.1
- **Feature:** [Overlord Test Harness](autonomous-test-bench.md) | [Plan](autonomous-test-bench.plan.md)

Short README or docs section: how to run the Overlord Test Harness (entry point, scenario file, --from-spec), how to interpret the run directory and run summary, how to add new scenarios or emulator variants.

**Acceptance criteria:**
- [ ] Document in `docs/` or README; covers run command, run dir layout, run summary, adding scenarios, using --from-spec for any greenfield spec.

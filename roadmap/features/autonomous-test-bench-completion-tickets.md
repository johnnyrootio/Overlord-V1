# Test Harness — Completion / Finalization Tickets

Tickets to finalize the Test Harness as a **real, working system**: Claude Code user agent (no stub in production), black box tests with evidence, scenario decisions a priori and sacred. Depends on Waves 0–3 and the approved [black box test plan](autonomous-test-bench-blackbox-plan.md).

**Repo:** GitHub issues created in `johnnyrootio/Overlord-V1` (or configured repo).  
**Labels:** `area:testing`, `area:cli`, `type:feature` / `type:test` / `type:docs`, `roadmap:backlog`.

---

## TH-C1 [Impl] Claude Code user agent

**Blocked by:** (none for this doc; harness core and scenario with decisions exist)

**Title:** [Test Harness] Implement Claude Code user agent (replace stub for real runs)

**Body:**

- **Task ID:** TH-C1
- **Feature:** [Overlord Test Harness](autonomous-test-bench.md) | [Black box plan](autonomous-test-bench-blackbox-plan.md)

Implement the user-side agent using **Claude Code** (same paradigm as Overlord phase agents: `claude_agent_sdk`), not Claude API (cloud). The agent receives goals, greenfield spec content, recent Overlord output, and **scenario decisions** (a priori, sacred) and returns a single line to send to Overlord (gate answer, slash command, or short natural language).

**Acceptance criteria:**
- [ ] New module or class (e.g. in `test_harness/`) invokes Claude Code with a system prompt that includes: role (you are the user driving Overlord), goals, greenfield spec summary, and **scenario decisions as authoritative—do not override them**.
- [ ] Input: `EmulatorContext` (goals, greenfield_spec_path, greenfield_spec_content, emulator_prompt, recent_output, **decisions**). Output: single line string.
- [ ] Uses same SDK pattern as `overlord/claude_api.py` (e.g. single-turn or short multi-turn); no stub behavior when this agent is selected.
- [ ] When API key is not set, agent can return a clear error or the runner can fall back to stub (documented).

---

## TH-C2 [Impl] Wire runner to Claude Code agent; decisions in context

**Blocked by:** TH-C1

**Title:** [Test Harness] Wire runner to Claude Code agent; pass scenario decisions; stub only when requested

**Body:**

- **Task ID:** TH-C2 | **Blocked by:** TH-C1
- **Feature:** [Overlord Test Harness](autonomous-test-bench.md) | [Black box plan](autonomous-test-bench-blackbox-plan.md)

The default run must use the **Claude Code user agent** when an API key is available. Scenario `decisions` (a priori, sacred) must be passed into the agent context so it can steer Overlord toward them. Stub may be used only when explicitly requested (e.g. `--stub` for fast CI) or when no API key is set (documented fallback).

**Acceptance criteria:**
- [ ] Runner (e.g. `test_harness.runner`) uses the Claude Code agent by default when `ANTHROPIC_API_KEY` or `CLAUDE_CODE_API_KEY` is set.
- [ ] Scenario `decisions` are passed to the agent (already in `EmulatorContext.decisions`); agent system prompt instructs to treat them as sacred.
- [ ] Optional `--stub` (or equivalent) flag forces stub emulator for local/CI runs that do not need real agent.
- [ ] Entry point script and pytest black box tests can be run with the real agent when key is set.

---

## TH-C3 [Test/functional] Black box BB-1: Real Overlord + real Claude Code agent run

**Blocked by:** TH-C2

**Title:** [Test Harness] Black box test BB-1: Full run with real Overlord and real Claude Code agent

**Body:**

- **Task ID:** TH-C3 | **Blocked by:** TH-C2
- **Feature:** [Overlord Test Harness](autonomous-test-bench.md) | [Black box plan](autonomous-test-bench-blackbox-plan.md) §2 (BB-1)

Implement and run black box test BB-1: one full harness run using **real** Overlord (no mock) and **real** Claude Code user agent (no stub). Evidence must show that the agent produced at least one substantive reply (e.g. repo name, "yes") in `emulator_log.jsonl`, not only `/exit`.

**Acceptance criteria:**
- [ ] Test (or script) runs the harness with scenario `scenarios/test-harness/bb-trivial-todo.yaml` (or equivalent) and real Claude Code agent.
- [ ] Run directory is produced with `run_manifest.json`, `run_summary.json`, `overlord_output.txt`, `emulator_log.jsonl`.
- [ ] `overlord_output.txt` contains recognizable Overlord output (e.g. prompts, phase text).
- [ ] `emulator_log.jsonl` has at least one turn where the reply is not only `/exit` (e.g. repo name or gate answer), proving the real agent was used.
- [ ] Evidence (run dir path, excerpts) can be presented to stakeholder.

---

## TH-C4 [Test/functional] Black box BB-2 and BB-3: Manifest shape and entry point

**Blocked by:** TH-C3

**Title:** [Test Harness] Black box tests BB-2 (manifest shape) and BB-3 (entry point with real agent)

**Body:**

- **Task ID:** TH-C4 | **Blocked by:** TH-C3
- **Feature:** [Overlord Test Harness](autonomous-test-bench.md) | [Black box plan](autonomous-test-bench-blackbox-plan.md) §2 (BB-2, BB-3)

BB-2: Assert run dir and manifest/summary shape (run_id, repo, duration_sec, exit_code, phase_reached, completion_signals_seen, artifacts_copied). BB-3: Assert that the advertised entry points (script and pytest) run the **real** system (real Overlord, real Claude Code agent) and produce the same evidence.

**Acceptance criteria:**
- [ ] BB-2: After a real run, assertions verify `run_manifest.json` and `run_summary.json` contain required fields; overlord_output and emulator_log structure.
- [ ] BB-3: Script `./scripts/run-test-harness.sh scenarios/test-harness/bb-trivial-todo.yaml` (with API key) completes and produces run dir satisfying BB-1/BB-2 evidence.
- [ ] BB-3: A pytest-based black box test invokes the runner with real agent and asserts run dir + evidence (no stub).
- [ ] Evidence (script output, pytest output, run dir path) can be presented.

---

## TH-C5 [Test/functional] Black box BB-4: Real GitHub repo (optional)

**Blocked by:** TH-C2

**Title:** [Test Harness] Black box test BB-4: Real GitHub repo creation and manifest

**Body:**

- **Task ID:** TH-C5 | **Blocked by:** TH-C2
- **Feature:** [Overlord Test Harness](autonomous-test-bench.md) | [Black box plan](autonomous-test-bench-blackbox-plan.md) §2 (BB-4)

When repo creation is enabled (run without `--no-repo`), prove the harness creates a real GitHub repo and records it in the manifest. Optional test (requires `gh` and auth).

**Acceptance criteria:**
- [ ] Run harness without `--no-repo` for a scenario with `repo_name` and `repo_create: true`.
- [ ] `run_manifest.json` has `repo` (owner/name or URL) and `repo_created: true`.
- [ ] `gh repo view <repo>` succeeds. Optionally: README in repo describes the run.

---

## TH-C6 [Docs] Decisions a priori and sacred; real agent usage

**Blocked by:** TH-C2

**Title:** [Test Harness] Docs: Scenario decisions a priori/sacred; run with real Claude Code agent

**Body:**

- **Task ID:** TH-C6 | **Blocked by:** TH-C2
- **Feature:** [Overlord Test Harness](autonomous-test-bench.md) | [Black box plan](autonomous-test-bench-blackbox-plan.md)

Update docs so that (1) scenario **decisions** are clearly described as **decided a priori and kept sacred** in the Test Harness, and (2) how to run with the **real Claude Code agent** vs stub, and how to interpret evidence.

**Acceptance criteria:**
- [ ] `docs/TEST-HARNESS.md` (or equivalent) states that scenario `decisions` are a priori and sacred; single source of truth; agent must not override them.
- [ ] Docs explain how to run with real agent (API key set, no `--stub`) and how to run with stub (e.g. `--stub` or no key) for fast/CI runs.
- [ ] Link to black box plan and completion tickets for evidence and test definitions.

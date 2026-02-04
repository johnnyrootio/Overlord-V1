# Test Harness scenario YAML

These YAML files drive the **Overlord Test Harness** (black box and real runs). They use the Test Harness scenario schema, not the Overlord scenario format used in `../trivial-todo-app.yaml` (spec_path, gate_responses).

**Schema:** `goals`, `greenfield_spec` (path), `repo` (`repo_name` or `repo_url`), optional `emulator_prompt`, `repo_create`, `timeout`, `success`, and optional `decisions`. See `roadmap/features/autonomous-test-bench.md` §3.2 and `test_harness/scenario.py`.

**Decisions (a priori, sacred):** The optional `decisions` dict (e.g. `language`, `cli`, `interface`, `storage`, `testing`, `repo_visibility`) defines concrete choices that are **decided a priori** and **kept sacred** in the Test Harness. They are the authoritative source of truth for the run: the Claude Code agent must steer Overlord toward them and must not override or contradict them. See `roadmap/features/autonomous-test-bench-blackbox-plan.md` §6.1.

Paths in `greenfield_spec` are relative to this directory (e.g. `../../greenfield-specs/trivial-todo-app.md`).

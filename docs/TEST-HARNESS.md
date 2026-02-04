# Overlord Test Harness

The Test Harness runs Overlord autonomously with a **user-emulator agent** over a socket, captures all output and artifacts, and writes a run directory with a manifest and summary. See [autonomous-test-bench.md](../roadmap/features/autonomous-test-bench.md) for the full feature spec.

## How to run

### Single entry point (script or Python)

From the repo root:

```bash
# Run with a scenario YAML file
./scripts/run-test-harness.sh path/to/scenario.yaml

# Run from any greenfield spec (no scenario file needed)
./scripts/run-test-harness.sh --from-spec greenfield-specs/trivial-todo-app.md

# Local/CI: skip GitHub repo creation (use a fake repo)
./scripts/run-test-harness.sh --no-repo --from-spec greenfield-specs/trivial-todo-app.md
```

Or via Python:

```bash
python -m test_harness.runner --from-spec greenfield-specs/trivial-todo-app.md --no-repo
python -m test_harness.runner --run-dir ./my-run --no-repo --from-spec greenfield-specs/example-todo-app.md
```

**Options:**

- **`--from-spec PATH`** — Generate a scenario from a greenfield spec and run. Goals and repo base name are derived from the spec; no hand-written YAML required.
- **`--no-repo`** — Do not create or resolve a GitHub repo; use a fake repo identifier. Use this for local runs and CI so `gh` is not required.
- **`--run-dir DIR`** — Write run output to this directory (default: `test-harness-runs/<run_id>`).
- **`--timeout SEC`** — Socket/read timeout in seconds (default: 300).

### Pytest

Run all tests (unit, integration, functional), including Test Harness tests:

```bash
pytest tests/ -v
```

Run only Test Harness–related tests:

```bash
pytest tests/unit/test_harness_scenario.py tests/unit/test_harness_repo.py tests/unit/test_harness_capture.py tests/unit/test_test_io.py tests/integration/test_harness_loop.py tests/integration/test_test_socket_mode.py tests/functional/test_test_harness_entrypoint.py -v
```

Functional tests that invoke the entry point:

```bash
pytest tests/functional/test_test_harness_entrypoint.py -v
```

## Run directory layout

After a run, the run directory contains:

| File or directory | Description |
|-------------------|-------------|
| **run_manifest.json** | Run id, repo identifier, repo_created, timestamp. |
| **run_summary.json** | Machine-readable summary: run_id, repo, duration_sec, exit_code, phase_reached, completion_signals_seen, artifacts_copied. |
| **overlord_output.txt** | Full Overlord output from the socket. |
| **emulator_log.jsonl** | One JSON object per emulator turn: recent_output_preview, reply. |
| **overlord-state/** | Overlord state dir for this run (project state, artifacts source). |
| **artifacts/** | Copy of Overlord artifacts (e.g. workgraph, phase logs) per project. |

Use **run_summary.json** to compare runs (e.g. phase reached, duration, completion signals) without re-reading full logs.

## Adding scenarios

### Hand-written scenario YAML

Create a YAML file with:

- **goals** — Short description of intent (e.g. "Build the simplest possible todo app").
- **greenfield_spec** — Path to the genesis spec (relative to the scenario file or absolute).
- **repo** — Either `repo_name` (unique name; harness can create) or `repo_url` (existing repo).
- **emulator_prompt** — Optional; path or name of emulator prompt variant.
- **repo_create** — Optional; default true when repo_name is set.
- **timeout** — Optional wall-clock timeout.
- **success** — Optional list of stdout patterns that indicate success.

Example:

```yaml
goals: "Minimal todo app; single wave."
greenfield_spec: greenfield-specs/trivial-todo-app.md
repo:
  repo_name: my-todo-e2e
repo_create: true
```

Then run: `./scripts/run-test-harness.sh path/to/my-scenario.yaml`.

### Using `--from-spec` (no YAML)

For any greenfield spec, you can run without writing a scenario file:

```bash
./scripts/run-test-harness.sh --no-repo --from-spec greenfield-specs/trivial-todo-app.md
```

The harness generates a scenario in memory: goals from the spec’s first heading or description, repo base from the spec filename (e.g. `trivial-todo-app`), and a unique run id. With `--no-repo`, no GitHub repo is created; without `--no-repo`, a repo is created with a unique name (e.g. `trivial-todo-app-run-<timestamp>`).

## Emulator variants

The default run uses a **stub emulator** that sends `/exit` immediately (for fast smoke and CI). To drive real sessions you need an emulator that returns gate answers and slash commands based on goals and the greenfield spec.

- **Stub:** `test_harness.emulator.stub_emulator(lines=[...], fallback="/exit")` — used by the entry point and integration tests.
- **Custom:** Implement a callable `(EmulatorContext) -> str` and pass it to `run_harness_loop(..., emulator=my_emulator)`. Context includes goals, greenfield_spec_path, greenfield_spec_content, emulator_prompt, and recent_output.
- **Claude Code–based:** A future variant can call a Claude Code agent (same paradigm as Overlord phase agents) to produce the next line; see the feature spec §2.

Scenario YAML can set **emulator_prompt** to select a variant (e.g. "minimal" vs "thorough"); the runner can be extended to load that and pass it to the emulator.

## References

- Feature spec: [roadmap/features/autonomous-test-bench.md](../roadmap/features/autonomous-test-bench.md)
- Plan and work graph: [roadmap/features/autonomous-test-bench.plan.md](../roadmap/features/autonomous-test-bench.plan.md)
- Waiting-for-input marker: [AWAITING-INPUT-MARKER.md](AWAITING-INPUT-MARKER.md)

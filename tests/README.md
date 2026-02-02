# Overlord Agent V1 — Tests

We use **TDD**: write a failing test first, then minimal code to pass. Unit, integration, and functional tests are all in scope.

## Layers

- **Unit:** Fast, isolated tests for state, CLI parsing (Click CliRunner), graph nodes. No subprocess, minimal I/O.
- **Integration:** Multi-component flows (e.g. CLI start + list, state + persistence, start → exit → resume). May use temp dirs and real file I/O.
- **Functional:** CLI invoked as subprocess (`python -m overlord`); assert exit codes and output. Requires `pip install -e .` so the package is importable.

## Running tests

```bash
# All tests
pytest
# or
pytest tests/ -v

# By layer
pytest tests/unit -v
pytest tests/integration -v
pytest tests/functional -v

# By marker
pytest -m unit
pytest -m integration
pytest -m functional
```

Markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.functional`, `@pytest.mark.real_multiclaude` (see `pyproject.toml`).

## Monitor × real Multiclaude (`test_monitor_real_multiclaude.py`)

Integration test that uses **one** test repo (or `OVERLORD_MONITOR_TEST_REPO`), inits Multiclaude, creates contrived issues with programming tasks, dispatches workers, and asserts `gather_status` sees workers and health. **The repo is left in place** for further monitor iteration.

- **Single test repo:** By default the test uses `owner/overlord-monitor-test` (created once if missing, then reused). Set `OVERLORD_MONITOR_TEST_REPO=owner/repo` to use a different repo.
- **Prerequisites:** `gh` (authenticated), multiclaude daemon running, Overlord `scripts/`, `ANTHROPIC_API_KEY` or `CLAUDE_CODE_API_KEY`. Test skips if any are missing.
- **Issues:** The test reuses open issues titled `[Monitor test]` or creates from `tests/integration/monitor_test_issues.yaml`.
- **Run:** `pytest tests/integration/test_monitor_real_multiclaude.py -v -m real_multiclaude`

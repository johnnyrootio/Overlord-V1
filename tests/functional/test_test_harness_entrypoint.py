"""
Functional tests for the Test Harness entry point (T3.2, T3.3).

T3.2: Script or pytest runs one minimal scenario (YAML or --from-spec); no regression.
T3.3: Run with --from-spec greenfield-specs/trivial-todo-app.md produces valid run dir and manifest.
"""
import json
import os
import subprocess
import sys
import tempfile

import pytest


@pytest.mark.functional
def test_runner_from_spec_no_repo_produces_run_dir_and_manifest():
    """T3.3: --from-spec with --no-repo produces valid run dir and run_manifest.json."""
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    spec = os.path.join(root, "greenfield-specs", "trivial-todo-app.md")
    if not os.path.isfile(spec):
        pytest.skip("greenfield-specs/trivial-todo-app.md not found")
    with tempfile.TemporaryDirectory() as tmp:
        run_dir = os.path.join(tmp, "run")
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "test_harness.runner",
                "--no-repo",
                "--from-spec",
                spec,
                "--run-dir",
                run_dir,
            ],
            capture_output=True,
            text=True,
            cwd=root,
            timeout=30,
        )
        assert result.returncode == 0, f"stderr: {result.stderr!r}"
        assert os.path.isdir(run_dir)
        manifest_path = os.path.join(run_dir, "run_manifest.json")
        summary_path = os.path.join(run_dir, "run_summary.json")
        assert os.path.isfile(manifest_path), "run_manifest.json should exist"
        assert os.path.isfile(summary_path), "run_summary.json should exist"
        with open(manifest_path) as f:
            manifest = json.load(f)
        assert "run_id" in manifest
        assert manifest["repo"] == "test/local"
        assert manifest["repo_created"] is False
        with open(summary_path) as f:
            summary = json.load(f)
        assert summary["run_id"] == manifest["run_id"]
        assert "duration_sec" in summary
        assert "exit_code" in summary


@pytest.mark.functional
def test_runner_help_exits_zero():
    """Entry point --help exits 0 (smoke)."""
    result = subprocess.run(
        [sys.executable, "-m", "test_harness.runner", "--help"],
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 0
    assert "--from-spec" in result.stdout
    assert "--no-repo" in result.stdout


@pytest.mark.functional
def test_existing_functional_tests_still_pass():
    """T3.2: No regression on existing functional tests (overlord --help)."""
    result = subprocess.run(
        [sys.executable, "-m", "overlord", "--help"],
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 0
    assert "start" in (result.stdout + result.stderr)

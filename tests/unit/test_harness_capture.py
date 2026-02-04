"""Unit tests for Test Harness capture and run summary."""
import json
import tempfile
from pathlib import Path

import pytest

from test_harness.capture import RunCapture, RunManifest, RunSummary


@pytest.mark.unit
def test_run_capture_finalize_writes_manifest_and_summary():
    """finalize() creates run_dir with run_manifest.json and run_summary.json."""
    with tempfile.TemporaryDirectory() as tmp:
        run_dir = Path(tmp) / "run"
        cap = RunCapture(
            run_dir=run_dir,
            run_id="run-42",
            repo_identifier="owner/repo",
            repo_created=True,
        )
        cap.append_overlord_output("some output\n")
        cap.log_emulator_turn("prompt", "/exit")
        summary = cap.finalize(overlord_state_dir=None, exit_code=0)
        assert run_dir.is_dir()
        manifest_file = run_dir / "run_manifest.json"
        summary_file = run_dir / "run_summary.json"
        assert manifest_file.is_file()
        assert summary_file.is_file()
        with open(manifest_file) as f:
            m = json.load(f)
        assert m["run_id"] == "run-42"
        assert m["repo"] == "owner/repo"
        assert m["repo_created"] is True
        with open(summary_file) as f:
            s = json.load(f)
        assert s["run_id"] == "run-42"
        assert s["exit_code"] == 0
        assert "duration_sec" in s
        assert summary.repo == "owner/repo"
        assert (run_dir / "overlord_output.txt").read_text() == "some output\n"
        assert (run_dir / "emulator_log.jsonl").is_file()


@pytest.mark.unit
def test_run_capture_copies_artifacts_when_state_dir_has_projects():
    """finalize() with overlord_state_dir copies project artifacts into run_dir/artifacts."""
    with tempfile.TemporaryDirectory() as tmp:
        state_dir = Path(tmp) / "state"
        (state_dir / "projects" / "proj1" / "artifacts").mkdir(parents=True)
        (state_dir / "projects" / "proj1" / "artifacts" / "plan.md").write_text("plan")
        run_dir = Path(tmp) / "run"
        cap = RunCapture(run_dir=run_dir, run_id="r", repo_identifier="o/r", repo_created=False)
        cap.finalize(overlord_state_dir=str(state_dir), exit_code=None)
        dest = run_dir / "artifacts" / "proj1" / "plan.md"
        assert dest.is_file()
        assert dest.read_text() == "plan"
        summary_data = json.loads((run_dir / "run_summary.json").read_text())
        assert "proj1/plan.md" in summary_data["artifacts_copied"]

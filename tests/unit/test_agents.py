"""Unit tests: Phase 0/3/4 agent integration points (stub behavior)."""
import os
import tempfile

import pytest

from overlord.agents.multiclaude_dispatch import check_worker_status, create_worker, list_workspace_replies
from overlord.agents.phase0 import is_claude_code_configured, run_phase0_bootstrap
from overlord.agents.phase1 import run_phase1_specifier
from overlord.agents.phase2 import run_phase2_wave_planner
from overlord.agents.phase3 import emit_issues, is_gh_available
from overlord.agents.phase4 import run_phase4_execution_manager


@pytest.mark.unit
def test_phase0_bootstrap_returns_artifact_path_and_phase_0_done():
    """run_phase0_bootstrap writes artifact and returns phase_0_done."""
    with tempfile.TemporaryDirectory() as tmp:
        state_root = os.path.join(tmp, "state")
        os.makedirs(os.path.join(state_root, "projects", "p"), exist_ok=True)
        result = run_phase0_bootstrap("p", state_root, "/path/to/spec.md")
        assert result["phase"] == 0
        assert result["phase_0_done"] is True
        assert "phase_0" in result["artifact_paths"]
        assert os.path.isfile(result["artifact_paths"]["phase_0"])


@pytest.mark.unit
def test_phase1_specifier_writes_plan_and_tasks():
    """run_phase1_specifier writes plan.md and tasks.md and returns phase 1."""
    with tempfile.TemporaryDirectory() as tmp:
        state_root = os.path.join(tmp, "state")
        os.makedirs(os.path.join(state_root, "projects", "p", "artifacts"), exist_ok=True)
        result = run_phase1_specifier("p", state_root, "/path/to/spec.md", {})
        assert result["phase"] == 1
        assert result["phase_1_done"] is True
        assert "plan" in result["artifact_paths"]
        assert "tasks" in result["artifact_paths"]
        assert os.path.isfile(result["artifact_paths"]["plan"])
        assert os.path.isfile(result["artifact_paths"]["tasks"])


@pytest.mark.unit
def test_phase2_wave_planner_writes_workgraph_yml():
    """run_phase2_wave_planner writes workgraph.yml and returns phase 2."""
    with tempfile.TemporaryDirectory() as tmp:
        state_root = os.path.join(tmp, "state")
        os.makedirs(os.path.join(state_root, "projects", "p", "artifacts"), exist_ok=True)
        result = run_phase2_wave_planner("p", state_root, {})
        assert result["phase"] == 2
        assert result["phase_2_done"] is True
        assert "workgraph" in result["artifact_paths"]
        wg = result["artifact_paths"]["workgraph"]
        assert os.path.isfile(wg)
        with open(wg) as f:
            content = f.read()
        assert "waves:" in content
        assert "task-1" in content


@pytest.mark.unit
def test_phase3_emit_issues_writes_stub_issues_file():
    """emit_issues writes issues.json and returns issue identifiers when work graph missing."""
    with tempfile.TemporaryDirectory() as tmp:
        state_root = os.path.join(tmp, "state")
        issues = emit_issues("/path/to/workgraph", None, state_root, "proj")
        assert len(issues) >= 1
        issues_file = os.path.join(state_root, "projects", "proj", "issues.json")
        assert os.path.isfile(issues_file)


@pytest.mark.unit
def test_phase3_emit_issues_from_workgraph_writes_task_based_issues():
    """emit_issues with valid workgraph (no gh) writes issues.json with task_id and numbers."""
    import json
    with tempfile.TemporaryDirectory() as tmp:
        state_root = os.path.join(tmp, "state")
        workgraph_path = os.path.join(tmp, "workgraph.yml")
        with open(workgraph_path, "w") as f:
            f.write(
                "waves:\n"
                "  - id: w0\n"
                "    tasks:\n"
                "      - id: task-1\n"
                "        title: Stub task 1\n"
                "        depends_on: []\n"
                "      - id: task-2\n"
                "        title: Stub task 2\n"
                "        depends_on: [task-1]\n"
            )
        issues = emit_issues(workgraph_path, None, state_root, "proj")
        assert len(issues) == 2
        issues_file = os.path.join(state_root, "projects", "proj", "issues.json")
        assert os.path.isfile(issues_file)
        with open(issues_file) as f:
            data = json.load(f)
        assert len(data) == 2
        assert data[0]["task_id"] == "task-1"
        assert data[0]["title"] == "Stub task 1"
        assert data[1]["task_id"] == "task-2"
        assert data[1]["title"] == "Stub task 2"


@pytest.mark.unit
def test_phase4_execution_manager_writes_prompt_and_returns_phase_4():
    """run_phase4_execution_manager persists phase_4_system_prompt.md and returns phase 4."""
    with tempfile.TemporaryDirectory() as tmp:
        state_root = os.path.join(tmp, "state")
        os.makedirs(os.path.join(state_root, "projects", "p", "artifacts"), exist_ok=True)
        result = run_phase4_execution_manager("p", state_root, {}, system_prompt="# Phase 4 stub")
        assert result["phase"] == 4
        assert result["phase_4_done"] is True
        assert "phase_4_system_prompt" in result["artifact_paths"]
        assert os.path.isfile(result["artifact_paths"]["phase_4_system_prompt"])
        with open(result["artifact_paths"]["phase_4_system_prompt"]) as f:
            assert "Phase 4" in f.read()


@pytest.mark.unit
def test_phase4_dispatch_creates_workers_and_captures_replies():
    """C13: With issues.json, repo_url, and stub scripts, Phase 4 creates workers and captures replies."""
    import json
    with tempfile.TemporaryDirectory() as tmp:
        state_root = os.path.join(tmp, "state")
        project_dir = os.path.join(state_root, "projects", "p")
        artifacts_dir = os.path.join(project_dir, "artifacts")
        os.makedirs(artifacts_dir, exist_ok=True)
        issues_file = os.path.join(project_dir, "issues.json")
        with open(issues_file, "w") as f:
            json.dump([
                {"task_id": "T1", "number": 1, "title": "Task one"},
                {"task_id": "T2", "number": 2, "title": "Task two"},
            ], f)
        scripts_dir = os.path.join(tmp, "scripts")
        os.makedirs(scripts_dir, exist_ok=True)
        with open(os.path.join(scripts_dir, "create-worker-with-auto-accept.sh"), "w") as f:
            f.write("#!/bin/sh\nexit 0\n")
        with open(os.path.join(scripts_dir, "list-workspace-replies.sh"), "w") as f:
            f.write("#!/bin/sh\necho 'reply1'\n")
        for p in [os.path.join(scripts_dir, "create-worker-with-auto-accept.sh"),
                  os.path.join(scripts_dir, "list-workspace-replies.sh")]:
            os.chmod(p, 0o755)
        result = run_phase4_execution_manager(
            "p", state_root,
            artifact_paths={"issues": issues_file},
            repo_url="https://github.com/owner/repo",
            scripts_dir=scripts_dir,
        )
        assert result["phase"] == 4
        assert "phase_4_workspace_replies" in result["artifact_paths"]
        replies_path = result["artifact_paths"]["phase_4_workspace_replies"]
        assert os.path.isfile(replies_path)
        with open(replies_path) as f:
            assert "reply1" in f.read()


@pytest.mark.unit
def test_multiclaude_create_worker_returns_false_when_script_missing():
    """create_worker returns False when script dir has no create-worker-with-auto-accept.sh."""
    with tempfile.TemporaryDirectory() as tmp:
        assert create_worker("repo", "task", scripts_dir=tmp) is False


@pytest.mark.unit
def test_multiclaude_check_worker_status_returns_stub_when_script_missing():
    """check_worker_status returns 'stub' when script not found."""
    with tempfile.TemporaryDirectory() as tmp:
        assert check_worker_status("repo", scripts_dir=tmp) == "stub"


@pytest.mark.unit
def test_multiclaude_list_workspace_replies_returns_empty_when_script_missing():
    """list_workspace_replies returns [] when script not found."""
    with tempfile.TemporaryDirectory() as tmp:
        assert list_workspace_replies("repo", scripts_dir=tmp) == []

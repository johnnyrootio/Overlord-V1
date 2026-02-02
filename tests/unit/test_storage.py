"""
Unit tests: StateManager save/load, atomic writes, idempotent save.
TDD: save creates project dir and state file; load returns same state; save twice then load returns latest.
"""
import json
import os
import tempfile

import pytest

from overlord.state import SessionState
from overlord.storage import StateManager


@pytest.mark.unit
def test_save_creates_project_dir_and_state_file():
    """StateManager.save(project_id, state) creates projects/<id>/ and state file."""
    with tempfile.TemporaryDirectory() as root:
        manager = StateManager(root)
        state = SessionState(project_id="my-app")
        state.genesis_spec_path = "/path/to/spec.md"
        manager.save("my-app", state)
        project_dir = os.path.join(root, "projects", "my-app")
        assert os.path.isdir(project_dir)
        state_file = os.path.join(project_dir, "state.json")
        assert os.path.isfile(state_file)
        with open(state_file) as f:
            data = json.load(f)
        assert data["project_id"] == "my-app"
        assert data["genesis_spec_path"] == "/path/to/spec.md"


@pytest.mark.unit
def test_load_returns_session_state_with_same_data():
    """StateManager.load(project_id) returns SessionState with same data as saved."""
    with tempfile.TemporaryDirectory() as root:
        manager = StateManager(root)
        state = SessionState(project_id="x")
        state.genesis_spec_path = "spec.md"
        state.set_phase(1)
        state.add_pending_question("Gate 1?")
        manager.save("x", state)
        loaded = manager.load("x")
        assert loaded is not state
        assert loaded.project_id == "x"
        assert loaded.phase == 1
        assert loaded.genesis_spec_path == "spec.md"
        assert loaded.pending_questions == ["Gate 1?"]


@pytest.mark.unit
def test_save_idempotent_load_returns_latest():
    """Save twice then load returns latest state (idempotent overwrite)."""
    with tempfile.TemporaryDirectory() as root:
        manager = StateManager(root)
        state1 = SessionState(project_id="y")
        state1.genesis_spec_path = "a.md"
        state1.set_phase(0)
        manager.save("y", state1)
        state2 = SessionState(project_id="y")
        state2.genesis_spec_path = "b.md"
        state2.set_phase(2)
        manager.save("y", state2)
        loaded = manager.load("y")
        assert loaded.genesis_spec_path == "b.md"
        assert loaded.phase == 2


@pytest.mark.unit
def test_list_projects_returns_saved_project_ids():
    """StateManager.list_projects() returns project_ids that have been saved."""
    with tempfile.TemporaryDirectory() as root:
        manager = StateManager(root)
        assert manager.list_projects() == []
        manager.save("p1", SessionState(project_id="p1"))
        manager.save("p2", SessionState(project_id="p2"))
        assert set(manager.list_projects()) == {"p1", "p2"}


@pytest.mark.unit
def test_load_nonexistent_raises_or_returns_none():
    """StateManager.load(nonexistent) raises FileNotFoundError or returns None (design choice)."""
    with tempfile.TemporaryDirectory() as root:
        manager = StateManager(root)
        with pytest.raises(FileNotFoundError):
            manager.load("nonexistent")

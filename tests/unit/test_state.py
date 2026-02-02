"""
Unit tests: session state model (phase, project_id, repo_url, pending_questions, artifact_paths).
TDD: state create, set phase, add pending question, repo_url persists.
"""
import pytest

from overlord.state import SessionState


@pytest.mark.unit
def test_state_create_has_project_id_and_default_phase():
    """Creating state with project_id sets phase to 0 and empty pending/artifacts."""
    state = SessionState(project_id="my-app")
    assert state.project_id == "my-app"
    assert state.phase == 0
    assert state.repo_url is None
    assert state.pending_questions == []
    assert state.artifact_paths == {}


@pytest.mark.unit
def test_state_repo_url_persists_in_to_dict_from_dict():
    """repo_url is serialized and deserialized; missing key yields None (backward compat)."""
    state = SessionState(project_id="p")
    state.repo_url = "https://github.com/org/repo"
    d = state.to_dict()
    assert d["repo_url"] == "https://github.com/org/repo"
    loaded = SessionState.from_dict(d)
    assert loaded.repo_url == "https://github.com/org/repo"
    # Backward compat: no repo_url key
    loaded2 = SessionState.from_dict({"project_id": "p", "phase": 0})
    assert loaded2.repo_url is None


@pytest.mark.unit
def test_state_set_phase_updates_phase():
    """set_phase stores the given phase."""
    state = SessionState(project_id="x")
    state.set_phase(1)
    assert state.phase == 1
    state.set_phase(4)
    assert state.phase == 4


@pytest.mark.unit
def test_state_add_pending_question_appends():
    """add_pending_question appends prompt and stores in pending_questions."""
    state = SessionState(project_id="x")
    state.add_pending_question("Gate 1: Confirm tech stack?")
    assert len(state.pending_questions) == 1
    assert state.pending_questions[0] == "Gate 1: Confirm tech stack?"
    state.add_pending_question("Gate 2: Brainstorming complete?")
    assert len(state.pending_questions) == 2
    assert state.pending_questions[1] == "Gate 2: Brainstorming complete?"

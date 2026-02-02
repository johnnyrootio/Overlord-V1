"""
Unit tests: minimal LangGraph runtime (one Phase 0 stub node, checkpointer).
TDD: invoke graph with initial state, assert state update.
"""
import pytest

from overlord.graph import build_graph, PHASE_0_NODE


@pytest.mark.unit
def test_graph_invoke_updates_state():
    """Invoke graph with project_id and genesis_spec_path; final state has phase set by Phase 0 node."""
    graph = build_graph(checkpointer=None)  # in-memory for test
    config = {"configurable": {"thread_id": "test-graph-1"}}
    initial = {"project_id": "x", "genesis_spec_path": "/path/to/spec.md"}
    result = graph.invoke(initial, config=config)
    assert "phase" in result
    assert result["phase"] == 0
    assert result.get("project_id") == "x"
    assert result.get("genesis_spec_path") == "/path/to/spec.md"


@pytest.mark.unit
def test_graph_with_checkpointer_persists_state():
    """Graph compiled with checkpointer; invoke then get_state returns same state."""
    from langgraph.checkpoint.memory import MemorySaver
    graph = build_graph(checkpointer=MemorySaver())
    config = {"configurable": {"thread_id": "thread-1"}}
    initial = {"project_id": "p", "genesis_spec_path": "spec.md"}
    result = graph.invoke(initial, config=config)
    state = graph.get_state(config)
    assert state.values.get("phase") == 0
    assert state.values.get("project_id") == "p"

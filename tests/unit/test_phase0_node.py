"""
Unit tests: Phase 0 stub agent — reads genesis spec path, writes minimal artifact, sets phase_0_done.
TDD: run node (via graph), assert artifact path in state and phase_0_done True; artifact file exists.
"""
import os
import tempfile

import pytest

from overlord.graph import build_graph


@pytest.mark.unit
def test_phase0_node_writes_artifact_path_and_sets_phase_0_done():
    """Invoke graph with state_root and project_id; result has phase_0_done True and artifact_paths.phase_0."""
    with tempfile.TemporaryDirectory() as tmp:
        state_root = os.path.join(tmp, "state")
        os.makedirs(state_root, exist_ok=True)
        project_dir = os.path.join(state_root, "projects", "my-app")
        os.makedirs(project_dir, exist_ok=True)
        graph = build_graph(checkpointer=None)
        config = {"configurable": {"thread_id": "test-phase0"}}
        initial = {
            "project_id": "my-app",
            "genesis_spec_path": "/path/to/spec.md",
            "state_root": state_root,
        }
        result = graph.invoke(initial, config=config)
        assert result.get("phase_0_done") is True
        artifact_paths = result.get("artifact_paths") or {}
        assert "phase_0" in artifact_paths
        artifact_file = artifact_paths["phase_0"]
        assert os.path.isfile(artifact_file), f"Artifact file should exist: {artifact_file}"
        # When Palpatine exists, Phase 0 persists assembled system prompt for agentic use
        if "phase_0_system_prompt" in artifact_paths:
            prompt_file = artifact_paths["phase_0_system_prompt"]
            assert os.path.isfile(prompt_file)
            with open(prompt_file, encoding="utf-8") as f:
                content = f.read()
            assert "Superpowers" in content or "Phase 0" in content


@pytest.mark.unit
def test_phase0_node_sets_phase_to_zero():
    """Phase 0 node sets phase to 0."""
    with tempfile.TemporaryDirectory() as tmp:
        state_root = os.path.join(tmp, "state")
        os.makedirs(os.path.join(state_root, "projects", "p"), exist_ok=True)
        graph = build_graph(checkpointer=None)
        result = graph.invoke(
            {"project_id": "p", "genesis_spec_path": "spec.md", "state_root": state_root},
            config={"configurable": {"thread_id": "t"}},
        )
        assert result["phase"] == 0

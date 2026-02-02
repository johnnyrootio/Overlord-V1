"""
Unit tests: scenario format (YAML: spec_path, gate_responses) and loader.
"""
import os
import tempfile

import pytest
import yaml

from overlord.scenario import load_scenario


@pytest.mark.unit
def test_load_scenario_parses_spec_path_and_gate_responses():
    """load_scenario returns dict with spec_path and gate_responses."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump({"spec_path": "greenfield-specs/app.md", "gate_responses": ["yes", "proceed"]}, f)
        path = f.name
    try:
        data = load_scenario(path)
        assert data["spec_path"] == "greenfield-specs/app.md"
        assert data["gate_responses"] == ["yes", "proceed"]
    finally:
        os.unlink(path)


@pytest.mark.unit
def test_load_scenario_accepts_optional_project_id():
    """load_scenario accepts optional project_id in YAML."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump({"spec_path": "s.md", "project_id": "my-app", "gate_responses": []}, f)
        path = f.name
    try:
        data = load_scenario(path)
        assert data["project_id"] == "my-app"
    finally:
        os.unlink(path)

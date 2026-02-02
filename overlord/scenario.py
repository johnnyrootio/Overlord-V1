"""
Scenario format (YAML: spec_path, gate_responses) and loader for scripted runs.
"""
from typing import Any, Dict, List

import yaml


def load_scenario(path: str) -> Dict[str, Any]:
    """Load scenario YAML: spec_path, optional project_id, gate_responses (list of strings)."""
    with open(path) as f:
        data = yaml.safe_load(f) or {}
    return {
        "spec_path": data.get("spec_path", ""),
        "project_id": data.get("project_id"),
        "gate_responses": list(data.get("gate_responses") or []),
    }

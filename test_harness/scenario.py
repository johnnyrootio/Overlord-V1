"""
Test Harness scenario YAML: goals, greenfield_spec, repo (repo_name or repo_url), emulator_prompt, etc.
Schema and loader per roadmap/features/autonomous-test-bench.md §3.2.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml


# Default success patterns (completion signals)
DEFAULT_SUCCESS_PATTERNS = [
    "Workgraph complete",
    "Planning and execution ready",
]


@dataclass
class Scenario:
    """Validated scenario for a Test Harness run."""

    goals: str
    greenfield_spec: str  # path (resolved)
    emulator_prompt: Optional[str] = None
    repo_name: Optional[str] = None
    repo_url: Optional[str] = None
    repo_create: bool = True
    timeout: Optional[int] = None
    success: List[str] = field(default_factory=lambda: list(DEFAULT_SUCCESS_PATTERNS))
    decisions: Optional[Dict[str, Any]] = None  # concrete choices the agent steers Overlord toward

    def __post_init__(self) -> None:
        if not self.repo_name and not self.repo_url:
            raise ValueError("Scenario must have repo_name or repo_url")


def load_scenario(path_or_dict: Union[str, Dict[str, Any]]) -> Scenario:
    """
    Load and validate a scenario from a YAML file path or a dict.
    Returns a Scenario; raises ValueError if required fields are missing or invalid.
    """
    if isinstance(path_or_dict, dict):
        data = path_or_dict
        base_dir: Optional[Path] = None
    else:
        path = Path(path_or_dict)
        if not path.is_file():
            raise ValueError(f"Scenario file not found: {path}")
        base_dir = path.parent
        with open(path) as f:
            data = yaml.safe_load(f) or {}

    goals = data.get("goals") or ""
    if not isinstance(goals, str):
        raise ValueError("goals must be a string")
    greenfield_spec = data.get("greenfield_spec") or ""
    if not greenfield_spec:
        raise ValueError("greenfield_spec is required")
    if base_dir and not Path(greenfield_spec).is_absolute():
        greenfield_spec = str((base_dir / greenfield_spec).resolve())
    emulator_prompt = data.get("emulator_prompt")
    repo_name = data.get("repo", {}).get("repo_name") if isinstance(data.get("repo"), dict) else None
    repo_url = data.get("repo", {}).get("repo_url") if isinstance(data.get("repo"), dict) else None
    if not isinstance(data.get("repo"), dict):
        repo_name = repo_name or data.get("repo_name")
        repo_url = repo_url or data.get("repo_url")
    repo_create = data.get("repo_create", True)
    timeout = data.get("timeout")
    success = data.get("success")
    if success is None:
        success = list(DEFAULT_SUCCESS_PATTERNS)
    if not isinstance(success, list):
        success = [str(s) for s in success] if success else list(DEFAULT_SUCCESS_PATTERNS)
    decisions = data.get("decisions")
    if decisions is not None and not isinstance(decisions, dict):
        decisions = None

    return Scenario(
        goals=goals,
        greenfield_spec=greenfield_spec,
        emulator_prompt=emulator_prompt,
        repo_name=repo_name,
        repo_url=repo_url,
        repo_create=bool(repo_create),
        timeout=int(timeout) if timeout is not None else None,
        success=success,
        decisions=decisions,
    )

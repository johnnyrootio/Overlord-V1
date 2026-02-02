"""
State persistence: save/load SessionState to ~/.overlord/projects/<project-id>/ (atomic writes).
"""
import json
import os
import shutil
from pathlib import Path
from typing import List

from overlord.state import SessionState


def _project_dir(state_root: Path, project_id: str) -> Path:
    return state_root / "projects" / project_id


def _state_file(state_root: Path, project_id: str) -> Path:
    return _project_dir(state_root, project_id) / "state.json"


class StateManager:
    """Save/load session state under state_root/projects/<project_id>/ with atomic writes."""

    def __init__(self, state_root: str) -> None:
        self._root = Path(state_root)

    def save(self, project_id: str, state: SessionState) -> None:
        """Write state atomically (temp file then rename)."""
        project_dir = _project_dir(self._root, project_id)
        project_dir.mkdir(parents=True, exist_ok=True)
        path = _state_file(self._root, project_id)
        tmp = path.with_suffix(".json.tmp")
        with open(tmp, "w") as f:
            json.dump(state.to_dict(), f, indent=2)
        os.replace(tmp, path)

    def load(self, project_id: str) -> SessionState:
        """Load state; raises FileNotFoundError if project does not exist."""
        path = _state_file(self._root, project_id)
        if not path.exists():
            raise FileNotFoundError(f"No state for project: {project_id}")
        with open(path) as f:
            data = json.load(f)
        return SessionState.from_dict(data)

    def list_projects(self) -> List[str]:
        """Return project_ids that have a state directory."""
        projects_dir = self._root / "projects"
        if not projects_dir.exists():
            return []
        return [d.name for d in projects_dir.iterdir() if d.is_dir() and (_state_file(self._root, d.name).exists())]

    def delete_project(self, project_id: str) -> None:
        """Remove project state directory and all contents. Raises FileNotFoundError if project does not exist."""
        project_dir = _project_dir(self._root, project_id)
        if not project_dir.exists():
            raise FileNotFoundError(f"No project: {project_id}")
        shutil.rmtree(project_dir)

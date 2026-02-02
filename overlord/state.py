"""
Session state model (docs/DESIGN-AND-ARCHITECTURE.md Section 3).
In-memory representation: phase, project_id, repo_url, pending_questions, artifact_paths, genesis_spec_path.
"""
from typing import Any, Dict, List, Optional


class SessionState:
    """In-memory session state for one project."""

    def __init__(self, project_id: str) -> None:
        self.project_id = project_id
        self.phase = 0
        self.repo_url: Optional[str] = None  # GitHub repo URL after create or when user provides; shown every run
        self.repo_pending_create: Optional[str] = None  # "owner/repo" when waiting for public/private answer
        self.pending_questions: List[str] = []
        self.artifact_paths: Dict[str, str] = {}
        self.genesis_spec_path: Optional[str] = None
        self.gate_response_index: int = 0  # next line index for --responses file

    def set_phase(self, phase: int) -> None:
        self.phase = phase

    def add_pending_question(self, prompt: str) -> None:
        self.pending_questions.append(prompt)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for persistence."""
        return {
            "project_id": self.project_id,
            "phase": self.phase,
            "repo_url": self.repo_url,
            "repo_pending_create": self.repo_pending_create,
            "pending_questions": list(self.pending_questions),
            "artifact_paths": dict(self.artifact_paths),
            "genesis_spec_path": self.genesis_spec_path,
            "gate_response_index": self.gate_response_index,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionState":
        """Deserialize from persisted state."""
        state = cls(project_id=data["project_id"])
        state.phase = data.get("phase", 0)
        state.repo_url = data.get("repo_url")
        state.repo_pending_create = data.get("repo_pending_create")
        state.pending_questions = list(data.get("pending_questions", []))
        state.artifact_paths = dict(data.get("artifact_paths", {}))
        state.genesis_spec_path = data.get("genesis_spec_path")
        state.gate_response_index = data.get("gate_response_index", 0)
        return state

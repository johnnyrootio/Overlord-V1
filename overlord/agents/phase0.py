"""
Phase 0 (Bootstrap) integration point: real bootstrap via Claude Code API when configured.
Otherwise stub behavior (artifact path, phase_0_done) is used by graph node.
C11: When ANTHROPIC_API_KEY or CLAUDE_CODE_API_KEY is set, can invoke Claude Code API for repo init, check.sh, CI, etc.
"""
import os
from pathlib import Path
from typing import Any, Dict, Optional


def run_phase0_bootstrap(
    project_id: str,
    state_root: str,
    genesis_spec_path: str,
) -> Dict[str, Any]:
    """
    Run Phase 0 bootstrap: repo init, check.sh, CI, agent prompts per workflow.
    When Claude Code API is not configured, returns stub result (artifact path, phase_0_done).
    Caller (graph node) can use this instead of inline stub.
    """
    # Stub: no Claude Code API call yet; write minimal artifact like graph node
    project_dir = Path(state_root) / "projects" / project_id
    artifacts_dir = project_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    artifact_file = artifacts_dir / "phase_0_done.txt"
    artifact_file.write_text("phase_0_done\n")
    return {
        "phase": 0,
        "artifact_paths": {"phase_0": str(artifact_file)},
        "phase_0_done": True,
    }


def is_claude_code_configured() -> bool:
    """True if Claude Code API is configured (e.g. ANTHROPIC_API_KEY)."""
    return bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("CLAUDE_CODE_API_KEY"))

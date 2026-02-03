"""
Per-phase conversation history and execution log for debugging, analysis, and post-hoc review.
Conversation: full user/agent message history (stored on disk, used for multi-turn API).
Execution log: reasoning, actions, and context (append-only JSONL on disk).
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def load_conversation(path: Optional[str]) -> List[Dict[str, str]]:
    """
    Load conversation history from a JSON file.
    Returns list of {"role": "user"|"assistant", "content": str}. Empty list if path missing or invalid.
    """
    if not path or not path.strip():
        return []
    p = Path(path)
    if not p.is_file():
        return []
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return [m for m in data if isinstance(m, dict) and m.get("role") and m.get("content") is not None]
        return []
    except Exception:
        return []


def save_conversation(path: str, messages: List[Dict[str, str]]) -> None:
    """Save conversation history to a JSON file. Creates parent dirs if needed."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(messages, f, indent=2, ensure_ascii=False)


def append_execution_log(path: Optional[str], phase: int, kind: str, message: str = "", payload: Optional[Dict[str, Any]] = None) -> None:
    """
    Append one entry to the phase execution log (JSONL).
    kind: "user" | "assistant" | "action" | "context" | "reasoning"
    message: short description; payload: optional structured data.
    """
    if not path or not path.strip():
        return
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    entry: Dict[str, Any] = {
        "ts": datetime.now(tz=timezone.utc).isoformat(),
        "phase": phase,
        "kind": kind,
        "message": message,
    }
    if payload is not None:
        entry["payload"] = payload
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def ensure_phase_log_paths(artifacts_dir: Path, phase: int) -> tuple:
    """
    Ensure conversation and execution_log paths exist for a phase; return (conversation_path, execution_log_path).
    Does not create agent conversation for Phase 3 (issue emitter has no agent).
    """
    artifacts_dir = Path(artifacts_dir)
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    conv_path = str(artifacts_dir / f"phase_{phase}_conversation.json")
    log_path = str(artifacts_dir / f"phase_{phase}_execution_log.jsonl")
    return conv_path, log_path

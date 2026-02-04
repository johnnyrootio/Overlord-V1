"""
Generate Test Harness scenario dict/YAML from a greenfield spec path.

Used by --from-spec and by tests. Output conforms to test_harness.scenario schema
(goals, greenfield_spec, repo, emulator_prompt, etc.) and passes load_scenario().
"""
import re
from pathlib import Path
from typing import Any, Dict, Optional


def _derive_goals_from_spec(spec_path: Path) -> str:
    """
    Derive goals string from spec content: first # heading or Project Overview / Description.
    """
    text = spec_path.read_text(encoding="utf-8")
    # First markdown heading
    m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    if m:
        return m.group(1).strip()
    # Fallback: look for "Project Overview" or "Description" section (first line of that block)
    for pattern in [
        r"(?m)^##\s+Project Overview\s*\n\n?(.+?)(?=\n##|\n#|\Z)",
        r"(?m)^\*\*Description\*\*:\s*(.+?)(?=\n\n|\n\*\*|\Z)",
        r"(?m)^##\s+Description\s*\n\n?(.+?)(?=\n##|\n#|\Z)",
    ]:
        m = re.search(pattern, text, re.DOTALL)
        if m:
            return m.group(1).strip().split("\n")[0][:200]
    return spec_path.stem.replace("-", " ").replace("_", " ").title()


def _repo_base_from_spec(spec_path: Path) -> str:
    """Base repo name from spec filename (e.g. trivial-todo-app.md -> trivial-todo-app)."""
    return spec_path.stem


def scenario_from_spec(
    spec_path: str,
    run_id: Optional[str] = None,
    overrides: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Generate a scenario dict from a greenfield spec path.

    - greenfield_spec: resolved absolute path to the spec file.
    - goals: derived from spec (first heading or Project Overview/Description).
    - repo: { repo_name: base from spec basename + optional run_id suffix }.
    - overrides: optional dict with goals, repo_name, emulator_prompt (and other
      scenario fields) merged on top; repo_name can be full name or extend base.

    Returns a dict that loads and validates via load_scenario().
    """
    path = Path(spec_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Greenfield spec not found: {path}")

    base = _repo_base_from_spec(path)
    repo_name = f"{base}-{run_id}" if run_id else base
    goals = _derive_goals_from_spec(path)

    scenario: Dict[str, Any] = {
        "goals": goals,
        "greenfield_spec": str(path),
        "repo": {"repo_name": repo_name},
        "repo_create": True,
    }
    if overrides:
        if "goals" in overrides:
            scenario["goals"] = overrides["goals"]
        if "repo_name" in overrides:
            scenario["repo"] = {"repo_name": overrides["repo_name"]}
        if "repo_url" in overrides:
            scenario["repo"] = {"repo_url": overrides["repo_url"]}
        if "emulator_prompt" in overrides:
            scenario["emulator_prompt"] = overrides["emulator_prompt"]
        for key in ("repo_create", "timeout", "success"):
            if key in overrides:
                scenario[key] = overrides[key]
    return scenario

"""
Phase 1 (Specifier) integration point: turn intent into executable spec + tasks.
When Claude API is configured, invokes Phase 1 agent; otherwise stub writes minimal
artifacts (plan.md, tasks.md). Accepts optional system_prompt (assembled from Palpatine).
"""
from pathlib import Path
from typing import Any, Dict, Optional

from overlord.claude_api import invoke_phase_agent, is_api_configured


def run_phase1_specifier(
    project_id: str,
    state_root: str,
    genesis_spec_path: Optional[str],
    artifact_paths: Optional[Dict[str, str]] = None,
    system_prompt: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run Phase 1 specifier: constitution, spec, plan, tasks, operational spec, testing strategy.
    When API configured: invokes Claude with Phase 1 prompt + genesis spec; persists response.
    Stub: writes minimal plan.md and tasks.md under project artifacts.
    Returns updated phase and artifact_paths (phase_1 key and plan/tasks paths).
    """
    project_dir = Path(state_root) / "projects" / project_id
    artifacts_dir = project_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    paths = dict(artifact_paths or {})

    if system_prompt:
        prompt_file = artifacts_dir / "phase_1_system_prompt.md"
        prompt_file.write_text(system_prompt, encoding="utf-8")
        paths["phase_1_system_prompt"] = str(prompt_file)

        # Phase 1 agent: invoke Claude when API configured
        if is_api_configured():
            user_message = "Begin Phase 1 (Specifier). Produce a brief plan and task list from the genesis spec below. Output will be used to drive Phase 2 (work graph).\n\n"
            if genesis_spec_path and Path(genesis_spec_path).is_file():
                try:
                    user_message += Path(genesis_spec_path).read_text(encoding="utf-8", errors="replace")
                except Exception:
                    user_message += "(genesis spec not readable)\n"
            response = invoke_phase_agent(1, system_prompt, user_message)
            if response:
                response_file = artifacts_dir / "phase_1_claude_response.txt"
                response_file.write_text(response, encoding="utf-8")
                paths["phase_1_claude_response"] = str(response_file)

    plan_file = artifacts_dir / "plan.md"
    tasks_file = artifacts_dir / "tasks.md"
    if paths.get("phase_1_claude_response"):
        # Use agent output for plan/tasks so Phase 2 gets real content
        try:
            content = Path(paths["phase_1_claude_response"]).read_text(encoding="utf-8", errors="replace")
            plan_file.write_text(content, encoding="utf-8")
            tasks_file.write_text(content, encoding="utf-8")
        except Exception:
            plan_file.write_text("# Plan (Phase 1 stub)\n\nStub plan for first working V1.\n")
            tasks_file.write_text("# Tasks (Phase 1 stub)\n\n- Stub task 1\n- Stub task 2\n")
    else:
        plan_file.write_text("# Plan (Phase 1 stub)\n\nStub plan for first working V1.\n")
        tasks_file.write_text("# Tasks (Phase 1 stub)\n\n- Stub task 1\n- Stub task 2\n")
    paths["plan"] = str(plan_file)
    paths["tasks"] = str(tasks_file)
    paths["phase_1"] = str(artifacts_dir)

    return {
        "phase": 1,
        "artifact_paths": paths,
        "phase_1_done": True,
    }

"""
Phase 1 (Specifier) integration point: turn intent into executable spec + tasks.
When Claude API is configured, invokes Phase 1 agent; otherwise stub writes minimal
artifacts (plan.md, tasks.md). Accepts optional system_prompt (assembled from Palpatine).
"""
from pathlib import Path
from typing import Any, Dict, Optional

from overlord.claude_api import invoke_phase_agent, invoke_phase_agent_messages, is_api_configured
from overlord.phase_log import (
    load_conversation,
    save_conversation,
    append_execution_log,
    ensure_phase_log_paths,
)


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

    conv_path, log_path = ensure_phase_log_paths(artifacts_dir, 1)
    paths["phase_1_conversation"] = conv_path
    paths["phase_1_execution_log"] = log_path

    if system_prompt:
        prompt_file = artifacts_dir / "phase_1_system_prompt.md"
        prompt_file.write_text(system_prompt, encoding="utf-8")
        paths["phase_1_system_prompt"] = str(prompt_file)

        # Phase 1 agent: invoke Claude when API configured
        if is_api_configured():
            user_message = "Begin Phase 1 (Specifier). Produce a brief plan and task list from the genesis spec below. Output will be used to drive Phase 2 (work graph).\n\n"
            # Phase 0 → Phase 1 wiring: include bootstrap plan so Specifier does not re-ask for tech stack
            bootstrap_path = paths.get("bootstrap_plan")
            if bootstrap_path and Path(bootstrap_path).is_file():
                try:
                    user_message += "--- Phase 0 bootstrap outcome (tech stack, repo layout, check.sh) ---\n"
                    user_message += "Do not re-ask for language/framework; use the bootstrap plan below.\n\n"
                    user_message += Path(bootstrap_path).read_text(encoding="utf-8", errors="replace") + "\n\n"
                except Exception:
                    pass
            if genesis_spec_path and Path(genesis_spec_path).is_file():
                try:
                    user_message += Path(genesis_spec_path).read_text(encoding="utf-8", errors="replace")
                except Exception:
                    user_message += "(genesis spec not readable)\n"
            append_execution_log(log_path, 1, "context", "Phase 1 user message (specifier + bootstrap + genesis)", payload={"user_message_preview": user_message[:500]})
            messages = load_conversation(conv_path)
            messages.append({"role": "user", "content": user_message})
            cwd = str(project_dir)
            if len(messages) > 1:
                response = invoke_phase_agent_messages(1, system_prompt, messages, cwd=cwd)
            else:
                response = invoke_phase_agent(1, system_prompt, user_message, cwd=cwd)
            if response:
                messages.append({"role": "assistant", "content": response})
                save_conversation(conv_path, messages)
                response_file = artifacts_dir / "phase_1_claude_response.txt"
                response_file.write_text(response, encoding="utf-8")
                paths["phase_1_claude_response"] = str(response_file)
                append_execution_log(log_path, 1, "assistant", "Phase 1 agent response", payload={"response_preview": response[:500]})
            append_execution_log(log_path, 1, "action", "invoke_phase_agent(1) completed")

    plan_file = artifacts_dir / "plan.md"
    tasks_file = artifacts_dir / "tasks.md"
    operational_spec_file = artifacts_dir / "operational_specification.md"
    testing_strategy_file = artifacts_dir / "testing_strategy.md"
    if paths.get("phase_1_claude_response"):
        # Use agent output for plan/tasks and foundational docs so Phase 2 gets real content
        try:
            content = Path(paths["phase_1_claude_response"]).read_text(encoding="utf-8", errors="replace")
            plan_file.write_text(content, encoding="utf-8")
            tasks_file.write_text(content, encoding="utf-8")
            operational_spec_file.write_text(content, encoding="utf-8")
            testing_strategy_file.write_text(content, encoding="utf-8")
        except Exception:
            stub = "# Plan (Phase 1 stub)\n\nStub plan for first working V1.\n"
            plan_file.write_text(stub, encoding="utf-8")
            tasks_file.write_text("# Tasks (Phase 1 stub)\n\n- Stub task 1\n- Stub task 2\n", encoding="utf-8")
            operational_spec_file.write_text(stub, encoding="utf-8")
            testing_strategy_file.write_text(stub, encoding="utf-8")
    else:
        stub = "# Plan (Phase 1 stub)\n\nStub plan for first working V1.\n"
        plan_file.write_text(stub, encoding="utf-8")
        tasks_file.write_text("# Tasks (Phase 1 stub)\n\n- Stub task 1\n- Stub task 2\n", encoding="utf-8")
        operational_spec_file.write_text(stub, encoding="utf-8")
        testing_strategy_file.write_text(stub, encoding="utf-8")
    paths["plan"] = str(plan_file)
    paths["tasks"] = str(tasks_file)
    paths["operational_specification"] = str(operational_spec_file)
    paths["testing_strategy"] = str(testing_strategy_file)
    paths["phase_1"] = str(artifacts_dir)

    return {
        "phase": 1,
        "artifact_paths": paths,
        "phase_1_done": True,
    }

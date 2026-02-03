"""
Phase 2 (Wave Planner): develop work graph from Phase 1 artifacts.
When Claude API is configured, invokes Phase 2 agent; otherwise stub writes minimal
workgraph.yml. Phase 3 expects workgraph.yml to be valid YAML with a top-level "waves" key.
"""
import re
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import yaml
except ImportError:
    yaml = None

from overlord.claude_api import invoke_phase_agent, invoke_phase_agent_messages, is_api_configured
from overlord.phase_log import (
    load_conversation,
    save_conversation,
    append_execution_log,
    ensure_phase_log_paths,
)


def _extract_workgraph_yaml(content: str) -> Optional[str]:
    """
    Extract valid work-graph YAML from Claude response (plain YAML, or markdown with ```yaml block).
    Returns the string to write to workgraph.yml, or None if no valid waves structure found.
    Phase 3 requires: yaml.safe_load(result) -> dict with "waves" key (list of {id, tasks}).
    """
    if not (content or "").strip():
        return None
    # Try parsing the whole thing as YAML first
    if yaml:
        try:
            data = yaml.safe_load(content)
            if isinstance(data, dict) and "waves" in data:
                return content.strip()
        except Exception:
            pass
    # Try to extract a ```yaml or ```yml code block
    for pattern in [r"```yaml\s*\n(.*?)```", r"```yml\s*\n(.*?)```", r"```\s*\n(.*?)```"]:
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        if match:
            block = match.group(1).strip()
            if yaml:
                try:
                    data = yaml.safe_load(block)
                    if isinstance(data, dict) and "waves" in data:
                        return block
                except Exception:
                    continue
            else:
                return block if "waves:" in block else None
    # Try from first "waves:" to end of content (in case there's preamble text)
    idx = content.find("waves:")
    if idx != -1:
        candidate = content[idx:].strip()
        if yaml:
            try:
                data = yaml.safe_load(candidate)
                if isinstance(data, dict) and "waves" in data:
                    return candidate
            except Exception:
                pass
        elif "waves:" in candidate:
            return candidate
    return None


def run_phase2_wave_planner(
    project_id: str,
    state_root: str,
    artifact_paths: Optional[Dict[str, str]] = None,
    system_prompt: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run Phase 2 wave planner: order Phase 1 tasks into waves with dependencies.
    When API configured: invokes Claude with Phase 2 prompt + plan/tasks context; persists response.
    Stub: writes minimal workgraph.yml under project artifacts.
    Returns updated phase and artifact_paths (workgraph path).
    """
    project_dir = Path(state_root) / "projects" / project_id
    artifacts_dir = project_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    paths = dict(artifact_paths or {})

    conv_path, log_path = ensure_phase_log_paths(artifacts_dir, 2)
    paths["phase_2_conversation"] = conv_path
    paths["phase_2_execution_log"] = log_path

    if system_prompt:
        prompt_file = artifacts_dir / "phase_2_system_prompt.md"
        prompt_file.write_text(system_prompt, encoding="utf-8")
        paths["phase_2_system_prompt"] = str(prompt_file)

        # Phase 2 agent: invoke Claude when API configured
        if is_api_configured():
            user_message = (
                "Begin Phase 2 (Wave Planner). Produce a work graph from the Phase 1 artifacts below. "
                "Output valid YAML only with a top-level 'waves' key. Each wave has 'id' and 'tasks'; "
                "each task has 'id', 'title', 'depends_on' (list of task ids). Phase 3 will parse this to create GitHub issues.\n\n"
            )
            for key in ("plan", "tasks", "operational_specification", "testing_strategy"):
                path = (artifact_paths or {}).get(key)
                if path and Path(path).is_file():
                    try:
                        user_message += f"--- {key} ---\n"
                        user_message += Path(path).read_text(encoding="utf-8", errors="replace")
                        user_message += "\n\n"
                    except Exception:
                        pass
            if user_message.count("---") == 0:
                user_message += "(No plan, tasks, or foundational docs available yet.)\n"
            append_execution_log(log_path, 2, "context", "Phase 2 user message (wave planner + plan/tasks)", payload={"user_message_preview": user_message[:500]})
            messages = load_conversation(conv_path)
            messages.append({"role": "user", "content": user_message})
            cwd = str(project_dir)
            if len(messages) > 1:
                response = invoke_phase_agent_messages(2, system_prompt, messages, cwd=cwd)
            else:
                response = invoke_phase_agent(2, system_prompt, user_message, cwd=cwd)
            if response:
                messages.append({"role": "assistant", "content": response})
                save_conversation(conv_path, messages)
                response_file = artifacts_dir / "phase_2_claude_response.txt"
                response_file.write_text(response, encoding="utf-8")
                paths["phase_2_claude_response"] = str(response_file)
                append_execution_log(log_path, 2, "assistant", "Phase 2 agent response", payload={"response_preview": response[:500]})
            append_execution_log(log_path, 2, "action", "invoke_phase_agent(2) completed")

    workgraph_file = artifacts_dir / "workgraph.yml"
    stub_workgraph = (
        "# Work graph (Phase 2 stub)\n"
        "waves:\n"
        "  - id: wave-1\n"
        "    tasks:\n"
        "      - id: task-1\n"
        "        title: Stub task 1\n"
        "        depends_on: []\n"
        "      - id: task-2\n"
        "        title: Stub task 2\n"
        "        depends_on: [task-1]\n"
    )
    if paths.get("phase_2_claude_response"):
        try:
            content = Path(paths["phase_2_claude_response"]).read_text(encoding="utf-8", errors="replace")
            extracted = _extract_workgraph_yaml(content)
            if extracted:
                workgraph_file.write_text(extracted, encoding="utf-8")
            else:
                workgraph_file.write_text(stub_workgraph)
        except Exception:
            workgraph_file.write_text(stub_workgraph)
    else:
        workgraph_file.write_text(stub_workgraph)
    paths["workgraph"] = str(workgraph_file)
    paths["phase_2"] = str(artifacts_dir)

    return {
        "phase": 2,
        "artifact_paths": paths,
        "phase_2_done": True,
    }

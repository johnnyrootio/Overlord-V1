"""
LangGraph runtime: Phase 0 → 1 → 2 → 3 → 4 pipeline.
State: project_id, genesis_spec_path, state_root, repo_url, artifact_paths, phase, scripts_dir (optional).
Phase 0: bootstrap (prompt, Claude if configured, check.sh). Phases 1–4: agents in overlord.agents.
"""
import os
from pathlib import Path
from typing import Any, Dict, Optional

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from overlord.prompts import get_phase_system_prompt
from overlord.claude_api import invoke_phase_agent, is_api_configured
from overlord.repo_utils import repo_url_to_owner_repo
from overlord.agents.phase1 import run_phase1_specifier
from overlord.agents.phase2 import run_phase2_wave_planner
from overlord.agents.phase3 import emit_issues
from overlord.agents.phase4 import run_phase4_execution_manager


PHASE_0_NODE = "phase_0"
PHASE_1_NODE = "phase_1"
PHASE_2_NODE = "phase_2"
PHASE_3_NODE = "phase_3"
PHASE_4_NODE = "phase_4"


def _entry_route(state: Dict[str, Any]) -> str:
    """Route from START to phase_N based on state['start_phase'] (default 0)."""
    return f"phase_{state.get('start_phase', 0)}"


def _next_or_end(state: Dict[str, Any], next_phase: str) -> str:
    """If max_phase set and current phase >= max_phase, go to END; else next_phase."""
    max_phase = state.get("max_phase")
    if max_phase is not None and state.get("phase", 0) >= max_phase:
        return "__end__"
    return next_phase


def _scripts_dir() -> str:
    """Overlord scripts dir (same logic as cli._overlord_scripts_dir)."""
    env = os.environ.get("OVERLORD_SCRIPTS_DIR")
    if env and os.path.isdir(env):
        return env
    root = Path(__file__).resolve().parent.parent
    return str(root / "scripts")


def _phase_0_stub(state: Dict[str, Any]) -> Dict[str, Any]:
    """Phase 0: when API configured, invoke one Claude Code instance; then write artifacts."""
    project_id = state.get("project_id", "")
    state_root = state.get("state_root")
    genesis_spec_path = state.get("genesis_spec_path") or ""
    artifact_paths = dict(state.get("artifact_paths") or {})

    if state_root and project_id:
        project_dir = Path(state_root) / "projects" / project_id
        artifacts_dir = project_dir / "artifacts"
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        prompt_text = ""
        try:
            prompt_text = get_phase_system_prompt(0)
            if prompt_text:
                prompt_file = artifacts_dir / "phase_0_system_prompt.md"
                prompt_file.write_text(prompt_text, encoding="utf-8")
                artifact_paths["phase_0_system_prompt"] = str(prompt_file)
        except Exception:
            pass

        # C11: When Claude Code API is configured, spawn one Phase 0 instance
        if is_api_configured() and prompt_text:
            user_message = "Begin Phase 0 (Bootstrap). "
            repo_url = state.get("repo_url")
            if repo_url:
                user_message += f"Project: {project_id}. The repo is already set: {repo_url}. Do not ask for the repo name; proceed with bootstrap planning (e.g. tech stack, Gate 1).\n\n"
            user_message += "You have the genesis spec below. Produce a brief bootstrap plan (tech stack, repo layout, check.sh scope) in 2–3 short paragraphs. Do not execute yet; gates will be handled by the human.\n\n"
            if genesis_spec_path and Path(genesis_spec_path).is_file():
                try:
                    user_message += Path(genesis_spec_path).read_text(encoding="utf-8", errors="replace")
                except Exception:
                    user_message += "(genesis spec not readable)\n"
            response = invoke_phase_agent(0, prompt_text, user_message)
            if response:
                response_file = artifacts_dir / "phase_0_claude_response.txt"
                response_file.write_text(response, encoding="utf-8")
                artifact_paths["phase_0_claude_response"] = str(response_file)

        artifact_file = artifacts_dir / "phase_0_done.txt"
        artifact_file.write_text("phase_0_done\n")
        artifact_paths["phase_0"] = str(artifact_file)

        # Minimal check.sh so E2E can assert "check.sh passes" (P6 C16)
        scripts_dir = project_dir / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)
        check_sh = scripts_dir / "check.sh"
        check_sh.write_text("#!/bin/sh\nset -e\n# stub check.sh for first working V1\nexit 0\n")
        check_sh.chmod(0o755)

    out = {**state, "phase": 0, "artifact_paths": artifact_paths, "phase_0_done": True}
    if state.get("repo_url"):
        out["repo_url"] = state["repo_url"]
    return out


def _phase_1_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Phase 1 (Specifier): plan + tasks from genesis spec."""
    project_id = state.get("project_id", "")
    state_root = state.get("state_root") or ""
    genesis_spec_path = state.get("genesis_spec_path") or ""
    artifact_paths = dict(state.get("artifact_paths") or {})
    system_prompt = get_phase_system_prompt(1) or ""
    result = run_phase1_specifier(
        project_id=project_id,
        state_root=state_root,
        genesis_spec_path=genesis_spec_path or None,
        artifact_paths=artifact_paths,
        system_prompt=system_prompt or None,
    )
    out = {**state, "phase": 1, "artifact_paths": result.get("artifact_paths") or artifact_paths}
    if state.get("repo_url"):
        out["repo_url"] = state["repo_url"]
    return out


def _phase_2_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Phase 2 (Wave Planner): work graph from plan/tasks."""
    project_id = state.get("project_id", "")
    state_root = state.get("state_root") or ""
    artifact_paths = dict(state.get("artifact_paths") or {})
    system_prompt = get_phase_system_prompt(2) or ""
    result = run_phase2_wave_planner(
        project_id=project_id,
        state_root=state_root,
        artifact_paths=artifact_paths,
        system_prompt=system_prompt or None,
    )
    out = {**state, "phase": 2, "artifact_paths": result.get("artifact_paths") or artifact_paths}
    if state.get("repo_url"):
        out["repo_url"] = state["repo_url"]
    return out


def _phase_3_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Phase 3 (Issue Emitter): GitHub issues from work graph."""
    project_id = state.get("project_id", "")
    state_root = state.get("state_root") or ""
    artifact_paths = dict(state.get("artifact_paths") or {})
    workgraph_path = artifact_paths.get("workgraph") or ""
    repo_url = state.get("repo_url")
    emit_issues(
        work_graph_path=workgraph_path,
        repo_name=None,
        state_root=state_root,
        project_id=project_id,
        repo_url=repo_url,
    )
    project_dir = Path(state_root) / "projects" / project_id
    artifact_paths["issues"] = str(project_dir / "issues.json")
    out = {**state, "phase": 3, "artifact_paths": artifact_paths}
    if state.get("repo_url"):
        out["repo_url"] = state["repo_url"]
    return out


def _phase_4_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Phase 4 (Execution Manager): dispatch workers, monitor."""
    project_id = state.get("project_id", "")
    state_root = state.get("state_root") or ""
    artifact_paths = dict(state.get("artifact_paths") or {})
    repo_url = state.get("repo_url")
    repo_name = repo_url_to_owner_repo(repo_url) if repo_url else None
    scripts_dir = state.get("scripts_dir") or _scripts_dir()
    system_prompt = get_phase_system_prompt(4) or ""
    result = run_phase4_execution_manager(
        project_id=project_id,
        state_root=state_root,
        artifact_paths=artifact_paths,
        system_prompt=system_prompt or None,
        repo_name=repo_name,
        repo_url=repo_url,
        scripts_dir=scripts_dir,
    )
    out = {**state, "phase": 4, "artifact_paths": result.get("artifact_paths") or artifact_paths}
    if state.get("repo_url"):
        out["repo_url"] = state["repo_url"]
    return out


def build_graph(
    checkpointer: Optional[Any] = None,
) -> Any:
    """
    Build StateGraph: router → phase_{start_phase} → ... → END.
    State may include start_phase (0–4) and optional max_phase (stop after this phase).
    Prompts come from overlord.prompts.get_phase_system_prompt (agent_prompts/*.md first).
    """
    builder = StateGraph(dict)
    builder.add_node(PHASE_0_NODE, _phase_0_stub)
    builder.add_node(PHASE_1_NODE, _phase_1_node)
    builder.add_node(PHASE_2_NODE, _phase_2_node)
    builder.add_node(PHASE_3_NODE, _phase_3_node)
    builder.add_node(PHASE_4_NODE, _phase_4_node)
    builder.set_conditional_entry_point(
        _entry_route,
        {
            PHASE_0_NODE: PHASE_0_NODE,
            PHASE_1_NODE: PHASE_1_NODE,
            PHASE_2_NODE: PHASE_2_NODE,
            PHASE_3_NODE: PHASE_3_NODE,
            PHASE_4_NODE: PHASE_4_NODE,
        },
    )
    builder.add_conditional_edges(
        PHASE_0_NODE,
        lambda s: _next_or_end(s, PHASE_1_NODE),
        {"__end__": END, PHASE_1_NODE: PHASE_1_NODE},
    )
    builder.add_conditional_edges(
        PHASE_1_NODE,
        lambda s: _next_or_end(s, PHASE_2_NODE),
        {"__end__": END, PHASE_2_NODE: PHASE_2_NODE},
    )
    builder.add_conditional_edges(
        PHASE_2_NODE,
        lambda s: _next_or_end(s, PHASE_3_NODE),
        {"__end__": END, PHASE_3_NODE: PHASE_3_NODE},
    )
    builder.add_conditional_edges(
        PHASE_3_NODE,
        lambda s: _next_or_end(s, PHASE_4_NODE),
        {"__end__": END, PHASE_4_NODE: PHASE_4_NODE},
    )
    builder.add_edge(PHASE_4_NODE, END)
    if checkpointer is None:
        checkpointer = MemorySaver()
    return builder.compile(checkpointer=checkpointer)


def invoke_pipeline(
    project_id: str,
    state_root: str,
    genesis_spec_path: Optional[str] = None,
    repo_url: Optional[str] = None,
    artifact_paths: Optional[Dict[str, str]] = None,
    scripts_dir: Optional[str] = None,
    start_phase: int = 0,
    max_phase: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Single entry point for the CLI: run the pipeline from start_phase until END or max_phase.
    State is passed in; result dict has phase, artifact_paths, repo_url. Graph owns all phase logic.
    """
    graph = build_graph()
    config = {"configurable": {"thread_id": project_id}}
    initial: Dict[str, Any] = {
        "project_id": project_id,
        "state_root": state_root,
        "genesis_spec_path": genesis_spec_path or "",
        "artifact_paths": dict(artifact_paths or {}),
        "start_phase": start_phase,
    }
    if repo_url:
        initial["repo_url"] = repo_url
    if max_phase is not None:
        initial["max_phase"] = max_phase
    if scripts_dir:
        initial["scripts_dir"] = scripts_dir
    return graph.invoke(initial, config=config)

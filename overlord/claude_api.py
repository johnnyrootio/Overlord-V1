"""
Phase agent invocation via Claude Agent SDK (Claude Code instances).
C11: One new Claude Code instance per phase; no recycling across phases.
When ANTHROPIC_API_KEY (or CLAUDE_CODE_API_KEY) is set, agents run as Claude Code
instances with access to tools (Bash, Read, Write, etc.) and local MCP.
Multi-turn: invoke_phase_agent_messages() for human-in-the-loop conversation.

When running in a TTY, the interactive phase can run the SDK in a subprocess with
stdin=DEVNULL so the Claude Code CLI subprocess does not block on the same TTY.
"""
import asyncio
import json
import os
import queue
import subprocess
import sys
import tempfile
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

# Default model for phase agents (SDK/CLI may override via env)
DEFAULT_MODEL = os.environ.get("OVERLORD_CLAUDE_MODEL", "claude-opus-4-5-20251101")
DEFAULT_MAX_TOKENS = 4096

# Phase 4 (Execution Manager) needs tools to interact with multiclaude locally
PHASE_4_ALLOWED_TOOLS = ["Bash", "Read", "Write", "Edit", "Glob", "Grep"]
# Phases 0–2 (Bootstrap, Specifier, Wave Planner): same tools; permissions by default so agent can write to project/repo
PHASE_0_1_2_ALLOWED_TOOLS = ["Bash", "Read", "Write", "Edit", "Glob", "Grep"]


def is_api_configured(api_key: Optional[str] = None) -> bool:
    """True if Anthropic API key is available (env or passed). Explicit empty string means not configured."""
    if api_key is not None and (not api_key or not api_key.strip()):
        return False
    key = (
        api_key if (api_key and api_key.strip())
        else os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("CLAUDE_CODE_API_KEY")
    )
    return bool(key and key.strip())


def _run_async(coro: Any) -> Any:
    """Run an async coroutine from sync code."""
    return asyncio.run(coro)


def _run_sdk_messages_in_subprocess(
    phase: int,
    system_prompt: str,
    messages: List[dict],
    cwd: Optional[str] = None,
    model: Optional[str] = None,
) -> str:
    """
    Run the SDK _messages_sdk in a subprocess with stdin=DEVNULL so the Claude Code
    CLI does not block on the TTY (which overlord is using for user input).
    """
    payload = {
        "phase": phase,
        "system_prompt": system_prompt,
        "messages": messages,
        "cwd": cwd,
        "model": model or DEFAULT_MODEL,
    }
    script = """
import asyncio
import json
import sys
from pathlib import Path
path = sys.argv[1]
data = json.loads(Path(path).read_text(encoding="utf-8"))
from overlord.claude_api import _options_for_phase, _messages_sdk
options = _options_for_phase(
    data["phase"], data["system_prompt"],
    cwd=data.get("cwd"), model=data.get("model")
)
result = asyncio.run(_messages_sdk(data["messages"], options))
print(result or "")
"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump(payload, f, ensure_ascii=False)
        payload_path = f.name
    try:
        proc = subprocess.run(
            [sys.executable, "-c", script, payload_path],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=600,
            cwd=cwd or os.getcwd(),
            env=os.environ.copy(),
        )
        if proc.stderr:
            print(proc.stderr, file=sys.stderr)
        if proc.returncode != 0 and proc.stderr:
            _log_phase_agent_error(Exception(proc.stderr.strip() or f"exit code {proc.returncode}"))
        return (proc.stdout or "").strip() if proc.returncode == 0 else ""
    except subprocess.TimeoutExpired:
        print("Phase agent timed out (10 min).", file=sys.stderr)
        return ""
    finally:
        try:
            Path(payload_path).unlink(missing_ok=True)
        except Exception:
            pass


def _options_for_phase(
    phase: int,
    system_prompt: str,
    cwd: Optional[str] = None,
    model: Optional[str] = None,
) -> Any:
    """Build ClaudeAgentOptions for the given phase."""
    from claude_agent_sdk import ClaudeAgentOptions

    opts: dict[str, Any] = {
        "system_prompt": system_prompt,
        "cwd": cwd,
        "setting_sources": ["user", "project", "local"],  # load user MCP/config
    }
    if model:
        opts["model"] = model
    # Permissions by default: all phase agents can write to project/Overlord/repo scope without asking
    opts["permission_mode"] = "acceptEdits"
    if phase == 4:
        opts["allowed_tools"] = PHASE_4_ALLOWED_TOOLS
    else:
        opts["allowed_tools"] = PHASE_0_1_2_ALLOWED_TOOLS
    return ClaudeAgentOptions(**opts)


async def _query_sdk(prompt: str, options: Any) -> str:
    """Single SDK query; return assistant text."""
    from claude_agent_sdk import query, AssistantMessage, TextBlock

    parts: List[str] = []
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in getattr(message, "content", []) or []:
                if isinstance(block, TextBlock):
                    parts.append(getattr(block, "text", "") or "")
    return "\n".join(parts).strip()


async def _messages_sdk(messages: List[dict], options: Any) -> str:
    """Multi-turn via ClaudeSDKClient; send user messages in order, return last assistant text."""
    from claude_agent_sdk import ClaudeSDKClient, AssistantMessage, TextBlock

    if not messages:
        return ""
    # Only user messages are sent to the agent; assistant turns are kept in session
    user_contents = [m["content"] for m in messages if m.get("role") == "user"]
    if not user_contents:
        return ""

    client = ClaudeSDKClient(options)
    await client.connect()
    try:
        last_text = ""
        for i, content in enumerate(user_contents):
            await client.query(content)
            parts: List[str] = []
            async for message in client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in getattr(message, "content", []) or []:
                        if isinstance(block, TextBlock):
                            parts.append(getattr(block, "text", "") or "")
            last_text = "\n".join(parts).strip()
        return last_text
    finally:
        await client.disconnect()


async def _send_one_and_receive(client: Any, user_message: str) -> str:
    """Send one user message and return assistant text. Client must already be connected."""
    from claude_agent_sdk import AssistantMessage, TextBlock

    await client.query(user_message)
    parts: List[str] = []
    async for message in client.receive_response():
        if isinstance(message, AssistantMessage):
            for block in getattr(message, "content", []) or []:
                if isinstance(block, TextBlock):
                    parts.append(getattr(block, "text", "") or "")
    return "\n".join(parts).strip()


def send_one_sync(client: Any, user_message: str) -> str:
    """Send one user message through an already-connected client; return assistant text. Sync wrapper for long-lived Phase 4 client."""
    return _run_async(_send_one_and_receive(client, user_message))


def create_phase4_client_sync(
    project_id: str,
    state_root: str,
    artifact_paths: Optional[Dict[str, str]] = None,
) -> Any:
    """
    Create and connect a Phase 4 SDK client for long-lived use. Caller must call
    disconnect_phase4_client(client) when done. Returns the connected client or None if API not configured.
    """
    if not is_api_configured():
        return None
    from overlord.prompts import get_phase_system_prompt

    system_prompt = get_phase_system_prompt(4) or ""
    project_dir = Path(state_root) / "projects" / project_id
    cwd = str(project_dir) if project_dir.exists() else None
    options = _options_for_phase(4, system_prompt, cwd=cwd)
    from claude_agent_sdk import ClaudeSDKClient

    client = ClaudeSDKClient(options)
    _run_async(client.connect())
    return client


def disconnect_phase4_client(client: Any) -> None:
    """Disconnect a Phase 4 client created with create_phase4_client_sync."""
    if client is None:
        return
    try:
        _run_async(client.disconnect())
    except Exception:
        pass


def create_phase_client_sync(
    phase: int,
    project_id: str,
    state_root: str,
    repo_url: Optional[str] = None,
) -> Any:
    """
    Create and connect an SDK client for phase 0, 1, or 2 (interactive). Caller must call
    disconnect_phase4_client(client) when done (reused for any phase). Returns the connected client or None if API not configured.
    Used for pre-connect Phase 0 and overlap-connect Phase 1/2.
    """
    if phase not in (0, 1, 2) or not is_api_configured():
        return None
    from overlord.prompts import get_phase_system_prompt
    from overlord.multiclaude_recovery import get_multiclaude_repo_clone_path

    system_prompt = get_phase_system_prompt(phase) or ""
    project_dir = Path(state_root) / "projects" / project_id
    cwd = str(project_dir) if project_dir.exists() else None
    if phase == 0 and repo_url and cwd:
        clone_path = get_multiclaude_repo_clone_path(repo_url)
        if clone_path and os.path.isdir(clone_path):
            cwd = clone_path
    options = _options_for_phase(phase, system_prompt, cwd=cwd)
    from claude_agent_sdk import ClaudeSDKClient

    client = ClaudeSDKClient(options)
    _run_async(client.connect())
    return client


async def run_phase_interactive_async(
    phase: int,
    system_prompt: str,
    initial_user_message: str,
    final_instruction: str,
    cwd: Optional[str],
    get_user_input_sync: Any,
    phase_done_sentinel: str,
    verbose: bool = False,
    prewarmed_client: Any = None,
) -> Optional[str]:
    """
    Run one phase with a single long-lived SDK client (connect once, reuse every turn).
    get_user_input_sync(assistant_text) is run in a thread so we don't block the event loop.
    Returns final deliverable or None if user exited.
    When verbose is True, progress lines are printed to stderr before each agent call.
    When prewarmed_client is set, use it (do not connect or disconnect); caller owns the client.
    """
    from claude_agent_sdk import ClaudeSDKClient

    if prewarmed_client is not None:
        client = prewarmed_client
        owned = False
    else:
        options = _options_for_phase(phase, system_prompt, cwd=cwd)
        client = ClaudeSDKClient(options)
        await client.connect()
        owned = True
    try:
        # First turn: send initial message
        if verbose:
            print(f"[Phase {phase}] Working…", file=sys.stderr)
        response = await _send_one_and_receive(client, initial_user_message)
        while True:
            # get_user_input is blocking; run in thread so event loop stays responsive
            user_input = await asyncio.to_thread(get_user_input_sync, response)
            if user_input is None:
                return None  # user typed /exit
            if user_input == phase_done_sentinel:
                break
            if verbose:
                print(f"[Phase {phase}] Working…", file=sys.stderr)
            response = await _send_one_and_receive(client, user_input)
        # User said /done: request final deliverable
        if verbose:
            print(f"[Phase {phase}] Working…", file=sys.stderr)
        final = await _send_one_and_receive(client, final_instruction)
        return final or None
    finally:
        if owned:
            await client.disconnect()


def _run_phase_child() -> None:
    """
    Entry point for the phase subprocess (stdin=DEVNULL). Reads config from
    OVERLORD_PHASE_CONFIG, commands from fd in OVERLORD_CMD_FD (JSON lines), writes responses to stdout (JSON lines).
    """
    config_path = os.environ.get("OVERLORD_PHASE_CONFIG")
    if not config_path or not Path(config_path).is_file():
        print(json.dumps({"t": "error", "c": "missing OVERLORD_PHASE_CONFIG"}), flush=True)
        sys.exit(1)
    cmd_fd_str = os.environ.get("OVERLORD_CMD_FD")
    if not cmd_fd_str:
        print(json.dumps({"t": "error", "c": "missing OVERLORD_CMD_FD"}), flush=True)
        sys.exit(1)
    cmd_fd = int(cmd_fd_str)
    config = json.loads(Path(config_path).read_text(encoding="utf-8"))
    phase = config["phase"]
    system_prompt = config["system_prompt"]
    initial_user_message = config["initial_user_message"]
    final_instruction = config["final_instruction"]
    cwd = config.get("cwd")

    cmd_queue: "queue.Queue[Optional[dict]]" = queue.Queue()

    def reader() -> None:
        try:
            with os.fdopen(cmd_fd, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.rstrip("\n")
                    if line:
                        cmd_queue.put(json.loads(line))
        except Exception as e:
            cmd_queue.put({"t": "error", "c": str(e)})
        cmd_queue.put(None)

    threading.Thread(target=reader, daemon=True).start()

    async def worker() -> None:
        options = _options_for_phase(phase, system_prompt, cwd=cwd)
        from claude_agent_sdk import ClaudeSDKClient

        client = ClaudeSDKClient(options)
        await client.connect()
        try:
            while True:
                cmd = await asyncio.to_thread(cmd_queue.get)
                if cmd is None:
                    break
                if cmd.get("t") == "error":
                    print(json.dumps(cmd), flush=True)
                    break
                content = cmd.get("c", "")
                if cmd.get("t") == "done":
                    content = final_instruction
                text = await _send_one_and_receive(client, content)
                print(json.dumps({"t": "response", "c": text or ""}), flush=True)
                if cmd.get("t") == "done":
                    break
        finally:
            await client.disconnect()

    asyncio.run(worker())


def run_phase_interactive_via_subprocess(
    phase: int,
    system_prompt: str,
    initial_user_message: str,
    final_instruction: str,
    cwd: Optional[str],
    get_user_input_sync: Any,
    phase_done_sentinel: str,
    verbose: bool = False,
) -> Optional[str]:
    """
    Run the interactive phase in a subprocess with stdin=DEVNULL so the Claude Code
    CLI does not block on the TTY. Parent keeps the TTY and drives the loop via pipes.
    When verbose is True, progress lines are printed to stderr before each agent response wait.
    """
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump(
            {
                "phase": phase,
                "system_prompt": system_prompt,
                "initial_user_message": initial_user_message,
                "final_instruction": final_instruction,
                "cwd": cwd,
            },
            f,
            ensure_ascii=False,
        )
        config_path = f.name
    try:
        child_r, parent_w = os.pipe()
        env = os.environ.copy()
        env["OVERLORD_PHASE_CONFIG"] = config_path
        env["OVERLORD_CMD_FD"] = str(child_r)
        proc = subprocess.Popen(
            [sys.executable, "-c", "from overlord.claude_api import _run_phase_child; _run_phase_child()"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            cwd=cwd or os.getcwd(),
            env=env,
            pass_fds=(child_r,),
        )
        os.close(child_r)
        cmd_out = os.fdopen(parent_w, "w", encoding="utf-8")
        try:
            if verbose:
                print(f"[Phase {phase}] Working…", file=sys.stderr)
            cmd_out.write(json.dumps({"t": "initial", "c": initial_user_message}) + "\n")
            cmd_out.flush()
            response = _read_response_from_subprocess(proc)
            if response is None:
                return None
            while True:
                user_input = get_user_input_sync(response)
                if user_input is None:
                    proc.terminate()
                    return None
                if user_input == phase_done_sentinel:
                    if verbose:
                        print(f"[Phase {phase}] Working…", file=sys.stderr)
                    cmd_out.write(json.dumps({"t": "done"}) + "\n")
                    cmd_out.flush()
                    final = _read_response_from_subprocess(proc)
                    return final
                if verbose:
                    print(f"[Phase {phase}] Working…", file=sys.stderr)
                cmd_out.write(json.dumps({"t": "user", "c": user_input}) + "\n")
                cmd_out.flush()
                response = _read_response_from_subprocess(proc)
                if response is None:
                    return None
        finally:
            cmd_out.close()
    finally:
        try:
            Path(config_path).unlink(missing_ok=True)
        except Exception:
            pass


def _read_response_from_subprocess(proc: subprocess.Popen) -> Optional[str]:
    """Read one JSON line from proc.stdout; handle errors and stderr."""
    if proc.stdout is None:
        return None
    line = proc.stdout.readline()
    if not line:
        if proc.stderr:
            err = proc.stderr.read()
            if err:
                print(err, file=sys.stderr)
        return None
    try:
        obj = json.loads(line.rstrip("\n"))
        if obj.get("t") == "error":
            print(obj.get("c", "unknown error"), file=sys.stderr)
            return None
        return obj.get("c", "")
    except json.JSONDecodeError:
        return None


def invoke_phase_agent(
    phase: int,
    system_prompt: str,
    user_message: str,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    cwd: Optional[str] = None,
) -> str:
    """
    Invoke a single phase agent via Claude Agent SDK (one Claude Code instance per phase).
    Returns the assistant's text response, or empty string if not configured or on error.
    """
    if not is_api_configured(api_key):
        return ""
    # Single-turn is typically used from graph nodes (non-TTY); use in-process.
    try:
        options = _options_for_phase(phase, system_prompt, cwd=cwd, model=model or DEFAULT_MODEL)
        return _run_async(_query_sdk(user_message, options))
    except (Exception, SystemExit) as e:
        _log_phase_agent_error(e)
        return ""


def _log_phase_agent_error(e: BaseException) -> None:
    """Log phase agent error and hint when Claude Code CLI or SDK may be missing."""
    print(f"Phase agent error (check Claude Code CLI and API key): {e}", file=sys.stderr)
    err_str = str(e).lower()
    type_name = type(e).__name__
    if "no module named 'claude_agent_sdk'" in err_str or "no module named \"claude_agent_sdk\"" in err_str:
        print(
            "Hint: Install the Claude Agent SDK in this environment: pip install claude-agent-sdk (requires Python 3.10+).",
            file=sys.stderr,
        )
    elif "cli" in type_name.lower() or "not found" in err_str or "claude code" in err_str:
        print(
            "Hint: Phase agents use the Claude Agent SDK (Claude Code). Ensure Claude Code CLI is installed and in PATH (e.g. Python 3.10+, claude-agent-sdk).",
            file=sys.stderr,
        )


def invoke_phase_agent_messages(
    phase: int,
    system_prompt: str,
    messages: List[dict],
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    cwd: Optional[str] = None,
) -> str:
    """
    Multi-turn: invoke phase agent with full message history (human-in-the-loop).
    messages: list of {"role": "user"|"assistant", "content": str}.
    Returns the assistant's text response, or empty string if not configured or on error.
    """
    if not is_api_configured(api_key):
        return ""
    if not messages:
        return ""
    try:
        options = _options_for_phase(phase, system_prompt, cwd=cwd, model=model or DEFAULT_MODEL)
        return _run_async(_messages_sdk(messages, options))
    except (Exception, SystemExit) as e:
        # Golden rule: never let SDK/subprocess exit the process; only CLI /exit can
        _log_phase_agent_error(e)
        return ""

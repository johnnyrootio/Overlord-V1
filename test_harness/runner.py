"""
Single entry point for the Overlord Test Harness.

Run with: python -m test_harness.runner <scenario.yaml>
   or:    python -m test_harness.runner --from-spec <greenfield-spec.md>
   or:    ./scripts/run-test-harness.sh [--from-spec PATH] [SCENARIO.yaml]

Use --no-repo to skip GitHub repo creation (use a fake repo; for local/CI runs).
"""
import argparse
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

from test_harness.capture import RunCapture
from test_harness.emulator import stub_emulator
from test_harness.repo import ResolvedRepo, resolve_repo
from test_harness.repo_readme import write_repo_readme
from test_harness.run import run_harness_loop
from test_harness.scenario import Scenario, load_scenario
from test_harness.scenario_from_spec import scenario_from_spec


def _run_id() -> str:
    return f"run-{int(time.time())}"


def _find_repo_root() -> Path:
    """Project root (where overlord and test_harness live)."""
    p = Path(__file__).resolve().parent.parent
    assert (p / "overlord").is_dir() or (p / "test_harness").is_dir()
    return p


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run Overlord Test Harness: drive Overlord with an emulator and capture output.",
    )
    parser.add_argument(
        "scenario",
        nargs="?",
        help="Path to scenario YAML file.",
    )
    parser.add_argument(
        "--from-spec",
        metavar="PATH",
        help="Generate scenario from a greenfield spec and run (no scenario file needed).",
    )
    parser.add_argument(
        "--run-dir",
        metavar="DIR",
        help="Directory for this run (default: test-harness-runs/<run_id>).",
    )
    parser.add_argument(
        "--no-repo",
        action="store_true",
        help="Do not create or resolve a GitHub repo; use a fake repo (for local/CI).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=300.0,
        help="Socket/read timeout in seconds (default: 300).",
    )
    args = parser.parse_args()

    if args.from_spec:
        spec_path = Path(args.from_spec).resolve()
        if not spec_path.is_file():
            print(f"Error: --from-spec file not found: {spec_path}", file=sys.stderr)
            return 1
        run_id = _run_id()
        scenario_dict = scenario_from_spec(str(spec_path), run_id=run_id)
        scenario = load_scenario(scenario_dict)
        scenario_name = spec_path.name
    elif args.scenario:
        scenario_path = Path(args.scenario).resolve()
        if not scenario_path.is_file():
            print(f"Error: scenario file not found: {scenario_path}", file=sys.stderr)
            return 1
        run_id = _run_id()
        scenario = load_scenario(str(scenario_path))
        scenario_name = scenario_path.name
    else:
        parser.error("Provide either a scenario YAML path or --from-spec <path>")

    root = _find_repo_root()
    run_dir = args.run_dir or str(root / "test-harness-runs" / run_id)
    state_dir = os.path.join(run_dir, "overlord-state")

    if args.no_repo:
        resolved = ResolvedRepo(
            identifier="test/local",
            repo_url="https://github.com/test/local",
            repo_created=False,
        )
    else:
        try:
            resolved = resolve_repo(scenario, run_id)
            if resolved.repo_created:
                write_repo_readme(
                    resolved.identifier,
                    scenario.goals,
                    run_id,
                    scenario_name=scenario_name,
                )
        except (ValueError, RuntimeError) as e:
            print(f"Error: repo resolution failed: {e}", file=sys.stderr)
            return 1

    os.makedirs(run_dir, exist_ok=True)
    os.makedirs(state_dir, exist_ok=True)

    capture = RunCapture(
        run_dir=run_dir,
        run_id=run_id,
        repo_identifier=resolved.identifier,
        repo_created=resolved.repo_created,
        success_patterns=scenario.success,
    )

    cmd = [
        sys.executable,
        "-m",
        "overlord.cli",
        "--test-socket",
        "127.0.0.1:0",
        "start",
        scenario.greenfield_spec,
        "--state-dir",
        state_dir,
    ]
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=str(root),
    )
    stderr_lines = []
    ready_addr = []

    def read_stderr():
        for line in proc.stderr:
            stderr_lines.append(line)
            if "OVERLORD_TEST_SOCKET_READY\t" in line:
                addr = line.strip().split("\t", 1)[1]
                ready_addr.append(addr)

    t = threading.Thread(target=read_stderr)
    t.daemon = True
    t.start()
    deadline = time.time() + 15
    while not ready_addr and time.time() < deadline:
        time.sleep(0.05)
    if not ready_addr:
        proc.terminate()
        proc.wait(timeout=5)
        print("Error: Overlord did not emit OVERLORD_TEST_SOCKET_READY", file=sys.stderr)
        print("".join(stderr_lines[-30:]), file=sys.stderr)
        return 1

    socket_addr = ready_addr[0]
    emulator = stub_emulator(lines=["/exit"], fallback="/exit")
    run_harness_loop(
        socket_addr,
        scenario,
        emulator,
        timeout=args.timeout,
        capture=capture,
    )
    proc.wait(timeout=args.timeout + 10)
    exit_code = proc.returncode if proc.returncode is not None else -1
    capture.finalize(overlord_state_dir=state_dir, exit_code=exit_code)
    print(f"Run dir: {run_dir}")
    return 0 if exit_code == 0 else exit_code


if __name__ == "__main__":
    sys.exit(main())

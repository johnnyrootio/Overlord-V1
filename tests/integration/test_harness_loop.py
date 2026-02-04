"""
Integration: Test Harness loads scenario, connects to Overlord test socket, one exchange with stub emulator.
T2.5: With capture, run dir and manifest/summary are present.
"""
import json
import os
import subprocess
import sys
import tempfile
import threading
import time

import pytest

from test_harness.capture import RunCapture
from test_harness.emulator import stub_emulator
from test_harness.run import run_harness_loop
from test_harness.scenario import load_scenario


@pytest.mark.integration
def test_harness_load_scenario_one_socket_exchange_stub_emulator():
    """Load scenario, connect to Overlord --test-socket, read until marker, send one line via stub, then /exit."""
    with tempfile.TemporaryDirectory() as tmp:
        spec_path = os.path.join(tmp, "t.md")
        with open(spec_path, "w") as f:
            f.write("# T\nMinimal spec.\n")
        state_dir = os.path.join(tmp, "state")
        scenario_dict = {
            "goals": "Minimal",
            "greenfield_spec": spec_path,
            "repo": {"repo_name": "test-repo"},
        }
        scenario = load_scenario(scenario_dict)

        cmd = [
            sys.executable,
            "-m",
            "overlord.cli",
            "--test-socket",
            "127.0.0.1:0",
            "start",
            spec_path,
            "--state-dir",
            state_dir,
        ]
        root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=root,
        )
        stderr_lines: list = []
        ready_addr: list = []

        def read_stderr():
            for line in proc.stderr:
                stderr_lines.append(line)
                if "OVERLORD_TEST_SOCKET_READY\t" in line:
                    addr = line.strip().split("\t", 1)[1]
                    ready_addr.append(addr)

        t = threading.Thread(target=read_stderr)
        t.daemon = True
        t.start()
        deadline = time.time() + 5
        while not ready_addr and time.time() < deadline:
            time.sleep(0.05)
        if not ready_addr:
            proc.terminate()
            proc.wait(timeout=2)
            pytest.fail("Did not see OVERLORD_TEST_SOCKET_READY: " + "".join(stderr_lines[-20:]))

        socket_addr = ready_addr[0]
        emulator = stub_emulator(lines=["/exit"], fallback="/exit")
        run_harness_loop(socket_addr, scenario, emulator, timeout=15.0)

        proc.wait(timeout=5)
        assert proc.returncode is not None


@pytest.mark.integration
def test_harness_capture_run_dir_and_manifest_present():
    """T2.5: With capture enabled, run dir contains run_manifest.json and run_summary.json."""
    with tempfile.TemporaryDirectory() as tmp:
        spec_path = os.path.join(tmp, "t.md")
        with open(spec_path, "w") as f:
            f.write("# T\nMinimal spec.\n")
        state_dir = os.path.join(tmp, "state")
        run_dir = os.path.join(tmp, "run")
        run_id = "test-run-1"
        scenario_dict = {
            "goals": "Minimal",
            "greenfield_spec": spec_path,
            "repo": {"repo_name": "test-repo"},
        }
        scenario = load_scenario(scenario_dict)
        capture = RunCapture(
            run_dir=run_dir,
            run_id=run_id,
            repo_identifier="test-owner/test-repo",
            repo_created=False,
            success_patterns=scenario.success,
        )

        cmd = [
            sys.executable,
            "-m",
            "overlord.cli",
            "--test-socket",
            "127.0.0.1:0",
            "start",
            spec_path,
            "--state-dir",
            state_dir,
        ]
        root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=root,
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
        deadline = time.time() + 5
        while not ready_addr and time.time() < deadline:
            time.sleep(0.05)
        if not ready_addr:
            proc.terminate()
            proc.wait(timeout=2)
            pytest.fail("Did not see OVERLORD_TEST_SOCKET_READY: " + "".join(stderr_lines[-20:]))

        socket_addr = ready_addr[0]
        emulator = stub_emulator(lines=["/exit"], fallback="/exit")
        run_harness_loop(socket_addr, scenario, emulator, timeout=15.0, capture=capture)

        proc.wait(timeout=5)
        exit_code = proc.returncode
        summary = capture.finalize(overlord_state_dir=state_dir, exit_code=exit_code)

        assert os.path.isdir(run_dir)
        manifest_path = os.path.join(run_dir, "run_manifest.json")
        summary_path = os.path.join(run_dir, "run_summary.json")
        assert os.path.isfile(manifest_path), "run_manifest.json should exist"
        assert os.path.isfile(summary_path), "run_summary.json should exist"
        with open(manifest_path) as f:
            manifest = json.load(f)
        assert manifest["run_id"] == run_id
        assert manifest["repo"] == "test-owner/test-repo"
        assert manifest["repo_created"] is False
        with open(summary_path) as f:
            summary_data = json.load(f)
        assert summary_data["run_id"] == run_id
        assert summary_data["repo"] == "test-owner/test-repo"
        assert "duration_sec" in summary_data
        assert summary.run_id == run_id

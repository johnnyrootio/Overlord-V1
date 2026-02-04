"""
Integration: Overlord --test-socket; client connects, sees marker, sends one line.
"""
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time

import pytest

from overlord.test_io import AWAITING_INPUT_MARKER, marker_seen_in_buffer


@pytest.mark.integration
def test_test_socket_connect_see_marker_send_line():
    """Start Overlord with --test-socket; connect; read until OVERLORD_AWAITING_INPUT; send one line."""
    with tempfile.TemporaryDirectory() as tmp:
        spec_path = os.path.join(tmp, "t.md")
        with open(spec_path, "w") as f:
            f.write("# T\n")
        state_dir = os.path.join(tmp, "state")
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
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        )
        stderr_lines: list[str] = []
        ready_addr: list[str] = []

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
            pytest.fail("Did not see OVERLORD_TEST_SOCKET_READY on stderr: " + "".join(stderr_lines[-20:]))

        host, port = ready_addr[0].rsplit(":", 1)
        port = int(port)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((host, port))

        buf = ""
        deadline = time.time() + 15
        while not marker_seen_in_buffer(buf) and time.time() < deadline:
            try:
                sock.settimeout(2.0)
                chunk = sock.recv(4096).decode("utf-8")
                if not chunk:
                    break
                buf += chunk
            except socket.timeout:
                continue
        if not marker_seen_in_buffer(buf):
            sock.close()
            proc.terminate()
            proc.wait(timeout=2)
            pytest.fail(
                "Did not see OVERLORD_AWAITING_INPUT in socket output; buf len=%d; last 200 chars: %r"
                % (len(buf), buf[-200:] if len(buf) > 200 else buf)
            )

        sock.sendall(b"/exit\n")
        sock.close()
        proc.wait(timeout=5)
        assert proc.returncode is not None

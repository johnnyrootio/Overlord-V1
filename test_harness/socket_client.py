"""
Test Harness socket client: connect to Overlord --test-socket, read until marker, send lines.

Used by the harness to drive Overlord in test mode. See docs/AWAITING-INPUT-MARKER.md.
"""
import socket
import time
from typing import Tuple

from overlord.test_io import marker_seen_in_buffer


def _parse_address(addr: str) -> Tuple[str, int, bool]:
    """
    Parse address string: 'host:port' -> (host, port, True), or 'path' -> (path, 0, False).
    Returns (host_or_path, port_or_zero, is_inet).
    """
    if ":" in addr and not addr.startswith("/"):
        host, port_s = addr.rsplit(":", 1)
        return (host.strip() or "127.0.0.1", int(port_s), True)
    return (addr, 0, False)


def connect_to_overlord(addr: str, timeout: float = 10.0) -> socket.socket:
    """
    Connect to Overlord's test socket. addr is 'host:port' or Unix path.
    Returns connected socket (caller must close).
    """
    parsed = _parse_address(addr)
    if parsed[2]:
        host, port, _ = parsed
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))
        return sock
    else:
        path = parsed[0]
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect(path)
        return sock


def read_until_awaiting_input(
    sock: socket.socket,
    timeout: float = 30.0,
    chunk_size: int = 4096,
) -> Tuple[str, str]:
    """
    Read from socket until OVERLORD_AWAITING_INPUT marker is seen.

    Returns (output_before_marker, rest_after_marker). The first element includes
    all Overlord output up to and including the line before the marker; the second
    is any text after the marker line (usually empty until next output).
    """
    sock.settimeout(min(2.0, timeout))
    buf = ""
    deadline = time.time() + timeout
    marker_line = "OVERLORD_AWAITING_INPUT\n"
    marker_crlf = "OVERLORD_AWAITING_INPUT\r\n"

    while time.time() < deadline:
        try:
            chunk = sock.recv(chunk_size).decode("utf-8")
            if not chunk:
                return (buf, "")
            buf += chunk
        except socket.timeout:
            if marker_seen_in_buffer(buf):
                break
            continue
        if marker_seen_in_buffer(buf):
            break

    if not marker_seen_in_buffer(buf):
        return (buf, "")

    # Split at marker
    if marker_line in buf:
        idx = buf.index(marker_line)
        return (buf[:idx], buf[idx + len(marker_line) :])
    idx = buf.index(marker_crlf)
    return (buf[:idx], buf[idx + len(marker_crlf) :])


def send_line(sock: socket.socket, line: str) -> None:
    """Send one line to Overlord (appends newline, flushes)."""
    sock.sendall((line.rstrip("\n\r") + "\n").encode("utf-8"))

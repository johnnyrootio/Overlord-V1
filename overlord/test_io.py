"""
Test-mode I/O for the Overlord Test Harness.

When Overlord is started with --test-socket, it listens on the given address,
accepts one connection, and uses that socket for user input and output.
The canonical "waiting for input" marker is emitted before each read.
See docs/AWAITING-INPUT-MARKER.md.
"""
import socket
import sys
from typing import Optional, TextIO, Tuple, Union

# Canonical marker (single line with newline); must match docs/AWAITING-INPUT-MARKER.md
AWAITING_INPUT_MARKER = "OVERLORD_AWAITING_INPUT"


def _parse_address(addr: str) -> Union[Tuple[str, int], Tuple[str, None]]:
    """Parse 'host:port' or 'path' (Unix). Returns (host, port) or (path, None)."""
    if ":" in addr and not addr.startswith("/"):
        host, port_s = addr.rsplit(":", 1)
        return (host.strip() or "127.0.0.1", int(port_s))
    return (addr, None)


def start_test_socket_server(addr: str) -> tuple[socket.socket, str]:
    """
    Listen on addr (e.g. '127.0.0.1:0' or a path for Unix socket).
    Returns (listener_socket, resolved_address_string for the client to connect to).
    Caller must then accept() one connection and pass it to TestSocketIO.
    """
    parsed = _parse_address(addr)
    if parsed[1] is not None:
        host, port = parsed
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, port))
        if port == 0:
            port = sock.getsockname()[1]
        sock.listen(1)
        return (sock, f"{host}:{port}")
    else:
        path = parsed[0]
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            sock.bind(path)
        except OSError:
            sock.close()
            raise
        sock.listen(1)
        return (sock, path)


class TestSocketIO:
    """
    Wraps a single accepted socket for test-mode I/O.
    - write(): send text to the client (e.g. Overlord output).
    - read_line(): emit AWAITING_INPUT_MARKER, then read one line from the client.
    """

    def __init__(self, conn: socket.socket) -> None:
        self._conn = conn
        self._reader: Optional[TextIO] = None
        self._writer: Optional[TextIO] = None
        self._closed = False

    def _ensure_streams(self) -> tuple[TextIO, TextIO]:
        if self._reader is None:
            self._reader = self._conn.makefile(mode="r", encoding="utf-8", newline="\n")
            self._writer = self._conn.makefile(mode="w", encoding="utf-8", newline="\n")
        return self._reader, self._writer

    def write(self, text: str) -> None:
        if self._closed:
            return
        _, w = self._ensure_streams()
        w.write(text)
        w.flush()

    def emit_awaiting_input(self) -> None:
        """Emit the canonical marker so the client knows Overlord is blocking for input."""
        self.write(AWAITING_INPUT_MARKER + "\n")

    def read_line(self) -> str:
        """Emit marker then read one line from the client. Returns stripped line."""
        self.emit_awaiting_input()
        r, _ = self._ensure_streams()
        line = r.readline()
        if not line:
            return ""
        return line.rstrip("\n\r")

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        for f in (self._reader, self._writer):
            if f:
                try:
                    f.close()
                except OSError:
                    pass
        try:
            self._conn.close()
        except OSError:
            pass


def marker_seen_in_buffer(buffer: str) -> bool:
    """Return True if the buffer contains a complete AWAITING_INPUT_MARKER line (marker + newline)."""
    return (
        (AWAITING_INPUT_MARKER + "\n") in buffer
        or (AWAITING_INPUT_MARKER + "\r\n") in buffer
    )


def consume_up_to_marker(buffer: str) -> tuple[bool, str]:
    """
    If the buffer contains the marker line (OVERLORD_AWAITING_INPUT\\n), return (True, rest_after_marker).
    Otherwise return (False, buffer).
    """
    marker_line = AWAITING_INPUT_MARKER + "\n"
    if marker_line in buffer:
        idx = buffer.index(marker_line)
        return (True, buffer[idx + len(marker_line) :])
    return (False, buffer)
"""Unit tests for test-mode I/O and marker detection (overlord.test_io)."""
import pytest

from overlord.test_io import (
    AWAITING_INPUT_MARKER,
    marker_seen_in_buffer,
    consume_up_to_marker,
    _parse_address,
    start_test_socket_server,
)


@pytest.mark.unit
def test_marker_seen_when_present():
    buf = "some output\n" + AWAITING_INPUT_MARKER + "\n"
    assert marker_seen_in_buffer(buf) is True


@pytest.mark.unit
def test_marker_not_seen_when_absent():
    assert marker_seen_in_buffer("hello\nworld\n") is False
    assert marker_seen_in_buffer("") is False


@pytest.mark.unit
def test_marker_not_seen_without_newline():
    # Incomplete line (marker without trailing newline) is not "seen" until newline
    assert marker_seen_in_buffer("x\n" + AWAITING_INPUT_MARKER) is False


@pytest.mark.unit
def test_marker_seen_split_across_chunks():
    # If we concatenate chunks, full marker line should be detected
    chunk1 = "output\n"
    chunk2 = AWAITING_INPUT_MARKER + "\n"
    assert marker_seen_in_buffer(chunk1 + chunk2) is True


@pytest.mark.unit
def test_consume_up_to_marker_found():
    before = "line1\nline2\n"
    marker_line = AWAITING_INPUT_MARKER + "\n"
    after = "rest\n"
    buf = before + marker_line + after
    found, rest = consume_up_to_marker(buf)
    assert found is True
    assert rest == after


@pytest.mark.unit
def test_consume_up_to_marker_not_found():
    buf = "no marker here\n"
    found, rest = consume_up_to_marker(buf)
    assert found is False
    assert rest == buf


@pytest.mark.unit
def test_parse_address_host_port():
    assert _parse_address("127.0.0.1:0") == ("127.0.0.1", 0)
    assert _parse_address(":9999") == ("127.0.0.1", 9999)


@pytest.mark.unit
def test_parse_address_unix():
    path = "/tmp/overlord-test.sock"
    assert _parse_address(path) == (path, None)


@pytest.mark.unit
def test_socket_server_binds():
    sock, resolved = start_test_socket_server("127.0.0.1:0")
    try:
        assert "127.0.0.1" in resolved
        assert int(resolved.split(":")[1]) > 0
    finally:
        sock.close()

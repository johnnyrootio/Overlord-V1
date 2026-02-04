"""
Main Test Harness loop: connect to Overlord test socket, read until marker, call emulator, send reply.

Overlord must already be started with --test-socket; this module connects as the client
and drives the session until the emulator sends /exit or the socket closes.
"""
from pathlib import Path
from typing import Callable, Optional

from test_harness.capture import RunCapture
from test_harness.emulator import EmulatorContext, EmulatorFn
from test_harness.scenario import Scenario, load_scenario
from test_harness.socket_client import (
    connect_to_overlord,
    read_until_awaiting_input,
    send_line,
)


def run_harness_loop(
    socket_addr: str,
    scenario: Scenario,
    emulator: EmulatorFn,
    timeout: float = 30.0,
    capture: Optional[RunCapture] = None,
) -> None:
    """
    Connect to Overlord at socket_addr, then loop: read until OVERLORD_AWAITING_INPUT,
    call emulator with context, send reply. Stops when emulator returns /exit or socket closes.
    If capture is provided, records Overlord output and emulator turns for run dir.
    """
    spec_path = Path(scenario.greenfield_spec)
    spec_content = spec_path.read_text(encoding="utf-8") if spec_path.is_file() else ""

    sock = connect_to_overlord(socket_addr, timeout=timeout)
    try:
        while True:
            output, rest = read_until_awaiting_input(sock, timeout=timeout)
            if not output and not rest:
                # Socket closed or no data
                break
            chunk = output + rest
            if capture:
                capture.append_overlord_output(chunk)
            context = EmulatorContext(
                goals=scenario.goals,
                greenfield_spec_path=scenario.greenfield_spec,
                greenfield_spec_content=spec_content,
                emulator_prompt=scenario.emulator_prompt,
                recent_output=chunk,
                decisions=scenario.decisions,
            )
            line = emulator(context)
            if capture:
                capture.log_emulator_turn(chunk, line)
            send_line(sock, line)
            if line.strip() == "/exit":
                break
    finally:
        try:
            sock.close()
        except OSError:
            pass


def run_harness_with_scenario_path(
    socket_addr: str,
    scenario_path: str,
    emulator: EmulatorFn,
    timeout: float = 30.0,
) -> None:
    """Load scenario from YAML path, then run the harness loop."""
    scenario = load_scenario(scenario_path)
    run_harness_loop(socket_addr, scenario, emulator, timeout=timeout)

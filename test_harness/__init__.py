"""Overlord Test Harness — autonomous runs with user-emulator agent and socket I/O."""

from test_harness.capture import RunCapture, RunManifest, RunSummary
from test_harness.emulator import EmulatorContext, StubEmulator, stub_emulator
from test_harness.repo import ResolvedRepo, resolve_repo
from test_harness.run import run_harness_loop, run_harness_with_scenario_path
from test_harness.scenario import Scenario, load_scenario
from test_harness.scenario_from_spec import scenario_from_spec
from test_harness.socket_client import (
    connect_to_overlord,
    read_until_awaiting_input,
    send_line,
)

__all__ = [
    "EmulatorContext",
    "ResolvedRepo",
    "RunCapture",
    "RunManifest",
    "RunSummary",
    "Scenario",
    "StubEmulator",
    "connect_to_overlord",
    "load_scenario",
    "read_until_awaiting_input",
    "resolve_repo",
    "run_harness_loop",
    "run_harness_with_scenario_path",
    "scenario_from_spec",
    "send_line",
    "stub_emulator",
]

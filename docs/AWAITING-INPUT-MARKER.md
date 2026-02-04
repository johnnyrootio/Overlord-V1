# Overlord "waiting for input" marker

This document defines the canonical marker that Overlord emits when it is blocking for user input. The Overlord Test Harness (and any socket or script client) uses this marker to know when to send the next line of input.

## Marker

- **Exact line:** Overlord emits a single line equal to:
  ```text
  OVERLORD_AWAITING_INPUT
  ```
- **Encoding:** UTF-8, with a trailing newline (`\n`).
- **When:** Emitted immediately **before** Overlord blocks to read one line of user input (e.g. from stdin or from the test socket).

Clients must treat this line as the signal that Overlord is ready to receive the next line of input. No other prompt text or ad-hoc strings should be used to detect "waiting for input."

## Where it appears

- **Normal runs (stdin/stdout):** When Overlord is not in test mode, the marker is written to **stdout** before each blocking read. Interactive users may see it; scripts and the Test Harness can rely on it.
- **Test mode (socket):** When Overlord is started with `--test-socket`, the marker is written to the **socket stream** (the same channel as all other Overlord output to the client). It is not written to the process’s stdout.

So: the marker appears on whichever I/O channel Overlord is using for that session (stdout for normal runs, socket for test mode).

## Environment variable (optional)

- **`OVERLORD_TEST_HARNESS=1`**  
  If set, Overlord may use this as a hint that a test harness is driving input (e.g. to enable the marker on stdout in non–test-mode runs for scripted tests). Implementation may make the marker always-on; this env var is reserved for future use (e.g. to suppress the marker on stdout for human-only sessions if desired). Current behavior: the marker is emitted whenever Overlord blocks for input, regardless of this variable.

## References

- Feature: [Overlord Test Harness](../roadmap/features/autonomous-test-bench.md)
- Plan and work graph: [autonomous-test-bench.plan.md](../roadmap/features/autonomous-test-bench.plan.md)

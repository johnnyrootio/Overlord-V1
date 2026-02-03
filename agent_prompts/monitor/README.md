# Monitor prompts

These prompts are **injected by the monitor daemon** into the Phase 4 Execution Manager. Each file is the exact text sent as the `injected_message` when the monitor pings the agent (with source `"monitor"`).

- **status_ping.md** — Used for the periodic (e.g. every 60s) status ping: reminder + explicit interrogation so we can glean status and keep the Execution Manager on track.
- **full_status.md** — Used when the user runs `/status`: full status interrogation so we can verify progress.

To add new interrogation types (e.g. `nudge_continue.md`, `report_blockers.md`), add a new `.md` file here and wire it in the monitor/CLI (e.g. by name or key).

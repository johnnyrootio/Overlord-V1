# Overlord Agent V1 — Backlog

Items for future work. Not committed to a release; ordered loosely by priority or dependency.

---

## Monitor and execution

- **Make the monitor an agent with tools.** Today the monitor is plain old software (a thread that gathers multiclaude status, injects prompts into the Execution Manager, handles `/status`). Backlog: evolve it into an **agent** that uses the current monitor logic as **tools** (e.g. "gather multiclaude status", "inject status ping to execution_manager", "format full status for CLI"), so it can decide when to ping, what to ask, and how to summarize for the user.

---

*Add new items below, one per bullet, with a short title and 1–2 sentence description.*

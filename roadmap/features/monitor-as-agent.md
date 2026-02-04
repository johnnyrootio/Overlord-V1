# Feature: Monitor as agent with tools

## Summary

Evolve the Overlord monitor from a fixed thread (gather status → inject ping → format for CLI) into an **agent** that uses the current monitor logic as **tools**. The agent decides when to ping, what to ask the Execution Manager, and how to summarize for the user.

## Background

Today the monitor is implemented in `overlord/monitor.py` as plain software: a timer loop gathers multiclaude status (workers, health, file changes), formats snapshot tables, and injects status prompts into the Phase 4 Execution Manager. Slash commands like `/status` call the same gather/format path. There is no reasoning step—only fixed behavior.

## Acceptance criteria

- [ ] Monitor is implemented as an agent (Claude Code or equivalent) that receives context (e.g. current phase, last status, open issues) and can choose actions.
- [ ] Current monitor logic is exposed as **tools** the agent can call, e.g.:
  - Gather multiclaude status (worker list, check-worker-status, list-workspace-replies, optional gh/API).
  - Inject a status ping (or custom prompt) to the Execution Manager.
  - Format full status for CLI (snapshot tables, section 4 file-change summary).
- [ ] Agent decides: when to ping (interval or on events), what questions to ask Phase 4, how to summarize for the user (e.g. one-line vs full tables).
- [ ] Existing CLI behavior is preserved or deliberately updated: `overlord status <project_id>`, proactive status line during Phase 4, slash commands.
- [ ] Tests: unit and/or integration for the new agent + tools; no regression on current status output contract.

## GitHub

- **Label**: `area:monitor`, `type:feature`, `roadmap:backlog`
- **Issues**: *(Create issue(s) when scheduling this feature; link here.)*

## References

- `docs/DESIGN-AND-ARCHITECTURE.md` §8.4 (Status subsystem)
- `overlord/monitor.py` (current implementation)
- `docs/BACKLOG.md` (original backlog item; canonical backlog is now `roadmap/BACKLOG.md`)

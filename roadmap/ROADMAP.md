# Overlord Agent V1 — Roadmap

High-level view of where the project is and what’s next. Detailed implementation plan (P0–P6, chunks C1–C16) lives in **ROADMAP-V1.md** at the repo root.

## Current state

- **V1 (P0–P6)**: Core pipeline is implemented: CLI, state, graph, phase agents (0–3), Phase 4 execution with multiclaude dispatch, status subsystem (monitor), interactive CLI and slash commands. Trivial todo app scenario and E2E test (C15, C16) are in place.
- **Post–P6**: Optional real-API E2E (gh + multiclaude + Claude) for “Overlord builds trivial todo app” in a real repo. Backlog items (e.g. monitor as agent) are tracked in **BACKLOG.md** and in ROADMAP-V1.md §9.

## What’s next

- **Backlog**: See `roadmap/BACKLOG.md`. Items there can be turned into features under `roadmap/features/` and tracked via GitHub issues.
- **Implementation plan**: For chunk-by-chunk status and “next step,” see **ROADMAP-V1.md** (root), especially §9 (Backlog) and §10 (Next step).

## Summary

| Theme | Status |
|-------|--------|
| P0–P6 (skeleton → first working V1) | Done |
| Real-API E2E | Optional |
| Backlog (e.g. monitor as agent) | Planned; promote via `roadmap/features/` + issues |

This file is the lightweight roadmap index; ROADMAP-V1.md remains the single source of truth for the P0–P6 plan and chunk list.

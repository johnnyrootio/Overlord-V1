# Roadmap directory

This directory holds Overlord’s **own** planning: roadmap, backlog, and feature/initiative specs. It is part of the **issue-driven roadmap** workflow. See **MAINTAINER.md** at repo root for the full strategy and how to add features.

## Contents

| Path | Purpose |
|------|---------|
| **ROADMAP.md** | High-level roadmap and pointer to the implementation plan (ROADMAP-V1.md). |
| **BACKLOG.md** | Uncommitted / future work; items can be promoted to features. |
| **features/** | One doc per feature or initiative; index in `features/README.md`. |
| **requirements/** | Cross-cutting requirements; see `requirements/README.md`. |

## Adding a feature

1. Create `features/<slug>.md` with title, summary, acceptance criteria, and GitHub issue link(s).
2. Add a row to the table in `features/README.md`.
3. Create the corresponding GitHub issue(s) and apply labels (`area:*`, `type:feature`, `roadmap:backlog` or `roadmap:v1`).
4. Implement; close issues via PRs; update the feature doc and index when done.

## GitHub

We track work in the **Overlord-Agent-V1** GitHub repo with labels: `area:*`, `type:feature`/`type:bug`/`type:docs`/`type:chore`, and optionally `roadmap:v1`/`roadmap:backlog`. Label scheme is described in MAINTAINER.md.

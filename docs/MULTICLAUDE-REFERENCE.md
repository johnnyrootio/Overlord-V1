# multiclaude Reference for Overlord Design

This document summarizes **multiclaude** (source: `multiclaude-src/`, cloned from `github.com/dlorenc/multiclaude`) so Overlord Agent V1 is designed with its features and constraints in mind.

## What multiclaude Is

- **Repo**: `https://github.com/dlorenc/multiclaude` (Go).
- **Role**: Orchestrator for multiple **Claude Code** instances. One repo, one tmux session per repo, one window per agent. Agents get isolated git worktrees; CI is the "ratchet" (merge when green).
- **Installed as**: `multiclaude` CLI (e.g. `go install github.com/dlorenc/multiclaude/cmd/multiclaude@latest` → `~/go/bin/multiclaude`).

## Architecture (from multiclaude-src)

- **CLI** (`cmd/multiclaude`, `internal/cli`) → talks to **daemon** over **Unix socket** (`~/.multiclaude/daemon.sock`).
- **Daemon** (`internal/daemon`) → owns **state** (`~/.multiclaude/state.json`), drives **tmux** (session per repo, window per agent), starts **Claude Code** via `pkg/claude` (runner sends command into tmux pane).
- **State** (`internal/state`): `repos[repo].agents[name]` with type, worktree_path, tmux_window, pid, task (workers), etc. Atomic writes.
- **Messages** (`internal/messages`): Files under `~/.multiclaude/messages/<repo>/<agent>/` (e.g. `msg-*.json`). Send = create file for recipient; list = read directory. **Workspace inbox** = messages for agent named `workspace`.
- **Worktrees** (`internal/worktree`): Git worktrees under `~/.multiclaude/wts/<repo>/<agent>/`. Workers get branch `work/<name>`.

## Paths (from pkg/config)

| What | Path |
|------|------|
| State | `~/.multiclaude/state.json` |
| Daemon socket | `~/.multiclaude/daemon.sock` |
| Repos (clone root) | `~/.multiclaude/repos/<repo>/` |
| Worktrees | `~/.multiclaude/wts/<repo>/<agent>/` |
| Messages | `~/.multiclaude/messages/<repo>/<agent>/` |
| Workspace inbox | `~/.multiclaude/messages/<repo>/workspace/` |

## Agent Types (from multiclaude)

- **supervisor** – Coordinates; nudges stuck agents; answers status. Persistent.
- **merge-queue** – Merges PRs when CI passes (single-player). Persistent.
- **pr-shepherd** – Coordinates human reviewers (fork/multiplayer). Persistent.
- **workspace** – User’s “home” agent; can spawn workers. Persistent. **Overlord talks to repo via workspace** (e.g. send messages to workspace; replies land in workspace inbox).
- **worker** – One task, one branch, one PR; signals `multiclaude agent complete`. Ephemeral.
- **review** – Reviews a specific PR. Ephemeral.

## CLI Commands Overlord Uses

- `multiclaude start` / `daemon status` / `daemon logs -f`
- `multiclaude repo init <url>` – Track repo; creates tmux session, supervisor, merge-queue or pr-shepherd, default workspace.
- `multiclaude worker create "<task>"` (optionally `--repo <name>`, `--branch`, `--push-to`) – Create worktree, tmux window, start Claude with worker prompt, register with daemon.
- `multiclaude worker list` – List workers (from daemon/state).
- `multiclaude worker rm <name>` – Remove worker.
- `multiclaude message send <to> "msg"` – Send message to agent (creates file in that agent’s inbox).
- `multiclaude agent attach <name> [--read-only]` – Attach to agent’s tmux window.
- `multiclaude agent complete` – Used by worker to signal done (daemon marks ready_for_cleanup).

**Overlord MUST use only these (and documented scripts).** No tmux, no socket API, no direct read/write of `state.json` or worktree manipulation (see MULTICLAUDE-INTERFACE-RULES in Palpatine).

## Worker Creation Flow (from internal/cli/cli.go createWorker)

1. Resolve repo (e.g. current repo or `--repo`).
2. Fetch from origin (best effort).
3. Create git worktree at `~/.multiclaude/wts/<repo>/<workerName>` with branch `work/<workerName>` (or from `--branch` / `--push-to`).
4. Ensure tmux session `mc-<repo>` exists; create tmux window for worker.
5. Write worker prompt file (task, fork config, etc.); copy hooks to worktree.
6. **Start Claude** in that tmux window: `claude --session-id <id> --dangerously-skip-permissions --append-system-prompt-file <path>` then send initial message `Task: <task>`.
7. Register agent with daemon via socket: `add_agent` (repo, agent name, type=worker, worktree_path, tmux_window, task, session_id, pid).
8. Set up output capture (optional).

**Security prompt**: Claude Code is started with `--dangerously-skip-permissions`, but the security/Bypass Permissions prompt can still appear (e.g. before the flag is honored). So **create-worker-with-auto-accept** (or `auto_accept_workers.sh` after a short delay) is mandatory for Overlord when creating workers; otherwise workers can sit stuck at that prompt.

## Messages and “Workspace Inbox”

- **Send**: `multiclaude message send <recipient> "body"` → daemon (or CLI) creates a JSON file in `~/.multiclaude/messages/<repo>/<recipient>/`.
- **Replies to Overlord**: Supervisor/workers are instructed to reply via `multiclaude message send workspace "..."`. Those messages land in `~/.multiclaude/messages/<repo>/workspace/`. Overlord’s **list-workspace-replies.sh** reads that directory (and optionally acks messages). So “workspace” is the inbox Overlord reads to see replies.

## State File (Read-Only for External Tools)

- **Schema**: See `multiclaude-src/docs/extending/STATE_FILE_INTEGRATION.md` and `internal/state/state.go`. Contains repos, agents (type, worktree_path, tmux_window, pid, task, ready_for_cleanup), task_history, merge_queue_config, etc.
- **Overlord**: Palpatine rules say **no direct access** to state.json; use CLI only (e.g. `multiclaude worker list`). So Overlord does not parse state.json; it uses CLI commands and scripts (e.g. check-worker-status.sh if that script uses CLI only or documented reads).

## Features to Account for in Overlord Design

1. **Repo init** – Must run `multiclaude repo init <url>` for the target repo (after gh repo create if greenfield) so multiclaude has a session, supervisor, merge-queue/pr-shepherd, and workspace.
2. **Worker create** – Always use **create-worker-with-auto-accept.sh** (or worker create + auto_accept_workers after ~5s). Never rely on raw `worker create` alone for workers that must run non-interactively.
3. **Liveness** – Workers are processes in tmux; PID and activity matter. **check-worker-status.sh** (or equivalent) should use CLI/scripts and/or documented means to determine liveness (e.g. worker list + attach read-only, or if state read is ever allowed, pid + process check). Overlord’s Execution Manager should check before creating more workers and act on stuck workers.
4. **Replies** – Overlord gets replies by reading **workspace** inbox via **list-workspace-replies.sh** (or `multiclaude message list` for workspace if that exists). Supervisor/workers must be prompted to send to `workspace`.
5. **Task format** – Worker create takes a single task string (e.g. `Implement #101: Add check.sh gate`). Overlord’s Issue Emitter produces issues; Execution Manager maps issues to task strings for `worker create`.
6. **Branch naming** – Workers get `work/<workerName>`. Overlord doesn’t need to set branch unless iterating on a PR (`--branch` / `--push-to`).
7. **Fork mode** – If repo is a fork, multiclaude uses pr-shepherd instead of merge-queue. Overlord’s Bootstrap/Phase 0 typically creates a new repo (not a fork); if Overlord ever supports fork workflow, init with fork URL and multiclaude will auto-detect.

## Where to Look in multiclaude-src

| Topic | Location |
|-------|----------|
| CLI entry, commands | `internal/cli/cli.go` (registerCommands, createWorker, repo init, message send) |
| Daemon, socket handlers | `internal/daemon/daemon.go` |
| State schema | `internal/state/state.go` |
| Messages (send, list, paths) | `internal/messages/messages.go`, `pkg/config/config.go` (MessagesDir, AgentMessagesDir) |
| Worker prompt, agent templates | `internal/templates/agent-templates/worker.md`, `internal/prompts/` |
| Starting Claude (flags, security) | `pkg/claude/runner.go` (buildCommand, SkipPermissions), `internal/cli/cli.go` (startClaudeInTmux) |
| Worktree creation | `internal/worktree/worktree.go` |
| Architecture overview | `docs/ARCHITECTURE.md`, `docs/COMMANDS.md`, `docs/AGENTS.md` |
| State file schema (read-only) | `docs/extending/STATE_FILE_INTEGRATION.md` |

---

This reference is derived from the cloned **multiclaude-src/** in this project. For authoritative behavior, see the multiclaude repo and Palpatine’s MULTICLAUDE-INTERFACE-RULES, WORKER-DISPATCH-GUIDE, and CAPTURING-REPLIES.

# Capturing Worker/Supervisor Replies

The Overlord sends status requests (or other messages) to the supervisor or workers via `multiclaude message send <agent> "..."`. Replies are **not** shown in the CLI by default—they land in the **workspace inbox** on disk. This doc explains how to capture them.

## How It Works

1. **Overlord sends** (from any directory, using the multiclaude repo as cwd):
   ```bash
   cd ~/.multiclaude/repos/<repo>
   multiclaude message send supervisor "Status check: reply with current worker status and any blockers."
   ```
   Or to a specific worker:
   ```bash
   multiclaude message send <worker-name> "What’s your current progress on the task?"
   ```

2. **Agents reply** by sending a message **to workspace** (so the Overlord can read it):
   ```bash
   multiclaude message send workspace "Current status: ..."
   ```
   Replies are stored as JSON files under:
   ```text
   ~/.multiclaude/messages/<repo>/workspace/
   ```

3. **Overlord captures replies** by reading the workspace inbox (the CLI’s `message list` shows the **current agent’s** inbox; when run from the main repo without tmux it defaults to supervisor, not workspace). So use one of:
   - **Script (recommended):**  
     From the **overlord repo**:
     ```bash
     ./scripts/list-workspace-replies.sh [repo-name]
     ```
     Default repo is `robotic-barista`. This lists all messages in the workspace inbox (from, time, body).
   - **Manual read:**  
     List and inspect the JSON files:
     ```bash
     ls -la ~/.multiclaude/messages/robotic-barista/workspace/
     cat ~/.multiclaude/messages/robotic-barista/workspace/msg-*.json | jq -r '"\(.timestamp) | From: \(.from) | \(.status)\n\(.body)\n---"'
     ```

## Agent Instructions (so they reply to workspace)

Ensure supervisor and workers know to **reply to the Overlord** by sending to **workspace**:

- In **supervisor** prompt (e.g. `.multiclaude/agents/supervisor.md` or Palpatine `AGENT-PROMPTS/supervisor.md`), add or keep:
  - When the Overlord asks for status (or any question), reply with:
    ```bash
    multiclaude message send workspace "Your reply here (e.g. status summary, blockers, next steps)."
    ```
- For **workers**, if you want them to answer Overlord questions directly, give them the same instruction: use `multiclaude message send workspace "..."` for replies to the Overlord.

Then the Overlord (or you) can run `./scripts/list-workspace-replies.sh` from the overlord repo to capture those replies.

## Optional: Mark replies as read/acked

- **List only (default):**  
  `./scripts/list-workspace-replies.sh [repo-name]`  
  Just prints messages; no changes to files.

- **Mark all as acked after listing:**  
  `./scripts/list-workspace-replies.sh [repo-name] --ack-all`  
  Updates each message JSON to `status: "acked"` and sets `acked_at`. Safe to run so the inbox doesn’t grow without bound.

## Summary

| Step            | Who       | Action |
|-----------------|-----------|--------|
| Send request    | Overlord  | `multiclaude message send supervisor "..."` (or worker name) |
| Reply           | Supervisor/worker | `multiclaude message send workspace "..."` |
| Capture replies | Overlord  | `./scripts/list-workspace-replies.sh [repo]` (or read `~/.multiclaude/messages/<repo>/workspace/*.json`) |

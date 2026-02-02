# Debugging Worker Issues: Security Prompt and Message Routing

## Problem: Workers Stuck at Security Prompt

### Symptoms

From the logs, you're seeing:
```
% 2 
zsh: command not found: 2
% Status check: Update on your progress?
zsh: no matches found: progress?
```

**What this means**:
1. Workers are stuck at the security prompt (`?` visible)
2. When "2" is sent to accept, it's being interpreted by the **shell** (zsh), not Claude Code
3. Messages are also being interpreted by the shell instead of reaching Claude Code

### Root Cause Analysis

**The Problem**: Claude Code shows a security prompt, but the tmux window is still in shell mode. When multiclaude sends "2" or messages, they go to the shell prompt instead of Claude Code's stdin.

**Why this happens**:
1. **Timing issue**: Claude Code may not have fully started when the prompt appears
2. **Process state**: The Claude Code process may be waiting for input, but the shell is still active
3. **Input routing**: tmux sends keys to the active process in the pane, which might be the shell, not Claude Code

## Debugging Steps

### Step 1: Check Worker Status

```bash
# List all workers
multiclaude worker list

# Check specific worker
multiclaude agent attach <worker-name> --read-only
```

**What to look for**:
- Is the worker registered? (should appear in `worker list`)
- What's visible in the tmux window? (security prompt `?`, shell prompt `%`, or Claude Code running?)
- Is Claude Code process running? (check PID)

### Step 2: Check Claude Code Process

```bash
# Find Claude Code process for a worker
# First, get the worker's PID from state
jq '.repos["<repo-name>"].agents["<worker-name>"].pid' ~/.multiclaude/state.json

# Check if process is running
ps -p <pid>

# Check what the process is doing
ps aux | grep claude | grep <session-id>
```

**What to look for**:
- Is the process running? (if not, Claude Code crashed)
- Is the process waiting for input? (check process state)
- Is the process stuck? (no CPU usage, waiting on stdin)

### Step 3: Check tmux Window State

**⚠️ DEBUG ONLY - With explicit human approval**:

```bash
# Get tmux session name from state
TMUX_SESSION=$(jq -r '.repos["<repo-name>"].tmux_session' ~/.multiclaude/state.json)

# List windows in session
tmux list-windows -t "$TMUX_SESSION"

# Check what's in the worker's window
tmux capture-pane -t "${TMUX_SESSION}:<worker-name>" -p

# Check what process is active in the pane
tmux list-panes -t "${TMUX_SESSION}:<worker-name>" -F "#{pane_pid}"
```

**What to look for**:
- Is the window showing the security prompt?
- Is the active process Claude Code or the shell?
- What's the last output in the pane?

### Step 4: Check Daemon Logs

```bash
# Check daemon logs for errors
multiclaude daemon logs -f

# Or check log file directly
tail -f ~/.multiclaude/logs/daemon.log
```

**What to look for**:
- Errors starting Claude Code
- Errors sending messages
- Errors with tmux operations
- Warnings about PIDs or processes

### Step 5: Check Message Delivery

```bash
# Check if messages are pending
ls -la ~/.multiclaude/messages/<repo-name>/<worker-name>/

# Check message status
cat ~/.multiclaude/messages/<repo-name>/<worker-name>/*.json | jq '.status'
```

**What to look for**:
- Are messages stuck in "pending" status? (not being delivered)
- Are messages marked "delivered" but not reaching Claude Code?
- Are there errors in message files?

## Common Issues and Solutions

### Issue 1: Claude Code Not Starting

**Symptoms**:
- Worker created but no Claude Code process
- tmux window shows shell prompt, not Claude Code
- No security prompt visible

**Debug**:
```bash
# Check if Claude Code binary exists and is executable
which claude
claude --version

# Check daemon logs for startup errors
multiclaude daemon logs | grep -i "claude\|error\|failed"
```

**Solutions**:
- Verify Claude Code is installed: `claude --version`
- Check binary path in multiclaude config
- Check permissions on Claude Code binary
- Verify `--dangerously-skip-permissions` flag is being passed

### Issue 2: Security Prompt Appears But Input Doesn't Work

**Symptoms**:
- Security prompt `?` visible in logs
- "2" is interpreted as shell command
- Messages are interpreted by shell

**Root Cause**: The tmux pane is still in shell mode, not attached to Claude Code's stdin.

**Debug**:
```bash
# Check if Claude Code process is running
ps aux | grep claude | grep <session-id>

# Check tmux pane state
tmux capture-pane -t "${TMUX_SESSION}:<worker-name>" -p | tail -20
```

**Solutions**:

**Option A: Wait longer before sending "2"**
- Claude Code may need more time to fully initialize
- Try waiting 5-10 seconds after worker creation before running auto-accept script

**Option B: Check if Claude Code is actually running**
- If process isn't running, Claude Code may have crashed
- Check daemon logs for errors
- Restart the worker: `multiclaude worker rm <name>` then `multiclaude worker create "..."`

**Option C: Manual intervention (debug only)**
- Attach to tmux window: `tmux attach -t "${TMUX_SESSION}:<worker-name>"`
- Manually type "2" and press Enter
- See if Claude Code accepts it
- Detach: `Ctrl+B, D`

### Issue 3: Messages Not Reaching Claude Code

**Symptoms**:
- Messages marked "delivered" in state
- Messages appear in shell (interpreted as commands)
- Claude Code never receives messages

**Root Cause**: Messages are being sent to the shell, not Claude Code's stdin.

**Debug**:
```bash
# Check message status
cat ~/.multiclaude/messages/<repo-name>/<worker-name>/*.json | jq '.status'

# Check if daemon is routing messages
multiclaude daemon logs | grep -i "message\|route"
```

**Solutions**:
- Ensure Claude Code is running before sending messages
- Check that tmux pane is attached to Claude Code process
- Verify message routing is working (check daemon logs)

### Issue 4: Auto-Accept Script Doesn't Work

**Symptoms**:
- Auto-accept script runs without errors
- Workers still stuck at prompt
- "2" appears in logs but doesn't accept prompt

**Debug**:
```bash
# Check if script found the session
./scripts/auto_accept_workers.sh <repo-name> 2>&1

# Verify tmux session exists
jq -r '.repos["<repo-name>"].tmux_session' ~/.multiclaude/state.json

# Check if windows exist
TMUX_SESSION=$(jq -r '.repos["<repo-name>"].tmux_session' ~/.multiclaude/state.json)
tmux list-windows -t "$TMUX_SESSION"
```

**Solutions**:
- Verify repo name is correct
- Check that tmux session exists
- Ensure script has execute permissions: `chmod +x scripts/auto_accept_workers.sh`
- Try running script with explicit session: modify script to use specific session

## Systematic Debugging Workflow

### 1. Verify Worker Creation

```bash
# Create worker and capture output
multiclaude worker create "Test task" 2>&1 | tee worker-create.log

# Check worker was created
multiclaude worker list

# Check worker details
multiclaude agent attach <worker-name> --read-only
```

### 2. Check Initial State

```bash
# Wait 3 seconds for Claude to start
sleep 3

# Check worker status
multiclaude agent attach <worker-name> --read-only

# Check if Claude Code process exists
WORKER_NAME="<worker-name>"
REPO_NAME="<repo-name>"
SESSION_ID=$(jq -r ".repos[\"$REPO_NAME\"].agents[\"$WORKER_NAME\"].session_id" ~/.multiclaude/state.json)
ps aux | grep claude | grep "$SESSION_ID"
```

### 3. Check Security Prompt

```bash
# If prompt visible, try auto-accept
./scripts/auto_accept_workers.sh "$REPO_NAME"

# Wait 2 seconds
sleep 2

# Check if prompt is gone
multiclaude agent attach "$WORKER_NAME" --read-only
```

### 4. If Still Stuck

```bash
# Check daemon logs
multiclaude daemon logs | tail -50

# Check worker logs (if they exist)
ls -la ~/.multiclaude/repos/"$REPO_NAME"/worktrees/*/workers/*.log

# Check process state
PID=$(jq -r ".repos[\"$REPO_NAME\"].agents[\"$WORKER_NAME\"].pid" ~/.multiclaude/state.json)
ps -p "$PID" -o pid,state,command
```

### 5. Clean Up and Retry

```bash
# Remove stuck worker
multiclaude worker rm "$WORKER_NAME"

# Wait a moment
sleep 2

# Create new worker
multiclaude worker create "Test task"
```

## Understanding the Flow

### Normal Flow

1. **Worker Creation**:
   - `multiclaude worker create "task"` → Creates worktree, tmux window
   - Starts Claude Code: `claude --session-id <id> --dangerously-skip-permissions ...`
   - Sends initial message via `SendKeysLiteralWithEnter`

2. **Claude Code Startup**:
   - Claude Code starts in tmux window
   - May show security prompt if `--dangerously-skip-permissions` doesn't work
   - Prompt expects "2" + Enter to accept

3. **Message Routing**:
   - Daemon routes messages every 2 minutes
   - Uses `SendKeysLiteralWithEnter` to send to Claude Code's stdin
   - Messages formatted as: `📨 Message from <from>: <body>`

### What Goes Wrong

1. **Timing**: Claude Code hasn't fully started when "2" is sent
2. **Process State**: Shell is still active, Claude Code waiting for input
3. **Input Routing**: tmux sends to shell instead of Claude Code

## Key Files to Check

- **State**: `~/.multiclaude/state.json` - Worker registration, PIDs, session IDs
- **Daemon Logs**: `~/.multiclaude/logs/daemon.log` - Errors, message routing
- **Messages**: `~/.multiclaude/messages/<repo>/<worker>/` - Message files
- **Worker Logs**: `~/.multiclaude/repos/<repo>/worktrees/*/workers/*.log` - If they exist

## Getting Help

If debugging doesn't resolve the issue:

1. **Collect diagnostic information**:
   ```bash
   # Worker status
   multiclaude worker list > debug-workers.txt
   
   # Daemon logs (last 100 lines)
   multiclaude daemon logs | tail -100 > debug-daemon.txt
   
   # State (redact sensitive info)
   jq '.repos["<repo-name>"]' ~/.multiclaude/state.json > debug-state.json
   
   # Process info
   ps aux | grep claude > debug-processes.txt
   ```

2. **Check multiclaude version**:
   ```bash
   multiclaude version
   ```

3. **Check Claude Code version**:
   ```bash
   claude --version
   ```

4. **Report issue** with:
   - multiclaude version
   - Claude Code version
   - OS and shell
   - Diagnostic files (redacted)
   - Steps to reproduce

## Prevention

**For the Overlord**:
- Always wait 3-5 seconds after creating workers before checking status
- Monitor workers immediately after creation
- Use `multiclaude agent attach --read-only` to check state
- Run auto-accept script if prompt visible
- Verify workers are unblocked before proceeding

**For multiclaude** (future improvements):
- Better detection of Claude Code startup state
- Automatic retry for security prompt acceptance
- Health checks that detect stuck workers
- Better error messages when workers fail to start

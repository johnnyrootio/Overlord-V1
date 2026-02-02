# Diagnosis Summary: Workers Not Starting

## Problem Identified

**Root Cause**: Claude Code processes are not running. Workers are created but Claude Code never starts in the tmux windows.

## Evidence

1. **No Claude Code processes running**:
   ```bash
   ps aux | grep claude
   # Only shows: multiclaude daemon, no claude processes
   ```

2. **Workers marked as dead and cleaned up**:
   ```
   [WARN] Agent bright-koala window not found, marking for cleanup
   [INFO] Cleaning up dead agent robotic-barista/bright-koala
   ```

3. **Claude Code binary is available**:
   ```bash
   which claude
   # /opt/homebrew/bin/claude
   claude --version
   # 2.1.9 (Claude Code)
   ```

## What's Happening

1. Worker is created via `multiclaude worker create`
2. tmux window is created
3. Claude Code command is sent to tmux: `claude --session-id <id> --dangerously-skip-permissions ...`
4. **But Claude Code doesn't start or crashes immediately**
5. Daemon detects missing window and cleans up worker

## Possible Causes

### 1. Claude Code Command Fails Silently

The command is sent via `tmux send-keys`, but Claude Code may:
- Fail to start (error not visible)
- Crash immediately
- Not be executable
- Have permission issues

### 2. PATH Issue in Daemon Environment

The daemon runs in a different environment and may not have Claude Code in PATH:
- Daemon started before PATH was set
- Daemon doesn't inherit user's PATH
- Claude Code installed after daemon started

### 3. tmux Window Issue

The tmux window may not exist when the command is sent:
- Window creation failed
- Window destroyed before command sent
- Timing issue

## Debugging Steps

### Step 1: Check Current Workers

```bash
# List workers (need to be in repo or use --repo flag)
multiclaude worker list --repo robotic-barista

# Or check state directly
jq '.repos["robotic-barista"].agents' ~/.multiclaude/state.json
```

### Step 2: Create New Worker with Monitoring

```bash
# In one terminal, watch daemon logs in real-time
multiclaude daemon logs -f

# In another terminal, create a worker
multiclaude worker create --repo robotic-barista "Test task: Debug worker startup"

# Watch the logs for:
# - "Started and registered agent"
# - "failed to start Claude"
# - Any errors about tmux or Claude Code
```

### Step 3: Check tmux Session

```bash
# Get tmux session name
TMUX_SESSION=$(jq -r '.repos["robotic-barista"].tmux_session' ~/.multiclaude/state.json)
echo "Session: $TMUX_SESSION"

# List windows in session
tmux list-windows -t "$TMUX_SESSION"

# Check if worker window exists
WORKER_NAME="<new-worker-name>"
tmux list-windows -t "$TMUX_SESSION" | grep "$WORKER_NAME"
```

### Step 4: Manually Test Claude Code in tmux

```bash
# Get tmux session
TMUX_SESSION=$(jq -r '.repos["robotic-barista"].tmux_session' ~/.multiclaude/state.json)

# Create a test window
tmux new-window -t "$TMUX_SESSION" -n "test-claude"

# Manually start Claude Code
tmux send-keys -t "${TMUX_SESSION}:test-claude" "claude --version" C-m

# Check if it works
tmux capture-pane -t "${TMUX_SESSION}:test-claude" -p
```

### Step 5: Check Daemon's PATH

The daemon may not have Claude Code in PATH. Check:

```bash
# Check daemon's environment (if possible)
# The daemon runs with its own environment

# Verify Claude Code is in PATH for daemon
# This is tricky - the daemon may have different PATH
```

## Solutions

### Solution 1: Restart Daemon

The daemon may have been started before Claude Code was in PATH:

```bash
# Stop daemon
multiclaude daemon stop

# Verify Claude Code is in PATH
which claude

# Start daemon (it will inherit current PATH)
multiclaude daemon start

# Try creating worker again
multiclaude worker create --repo robotic-barista "Test task"
```

### Solution 2: Use Full Path to Claude Code

If PATH is the issue, multiclaude should find it via `exec.LookPath("claude")`, but you can verify:

```bash
# Check what multiclaude finds
multiclaude daemon logs | grep -i "claude binary\|failed to resolve"

# If it fails, the daemon can't find Claude Code
```

### Solution 3: Check Claude Code Permissions

```bash
# Verify Claude Code is executable
ls -l $(which claude)

# Test Claude Code directly
claude --version

# Test in a tmux session manually
tmux new-session -d -s test
tmux send-keys -t test "claude --version" C-m
sleep 1
tmux capture-pane -t test -p
tmux kill-session -t test
```

### Solution 4: Check for Errors in Worker Creation

When creating a worker, check for immediate errors:

```bash
# Create worker and capture all output
multiclaude worker create --repo robotic-barista "Test" 2>&1 | tee worker-create.log

# Check for errors
grep -i "error\|failed\|warning" worker-create.log
```

## Next Steps

1. **Restart daemon** to ensure it has correct PATH
2. **Create a test worker** and monitor logs in real-time
3. **Check tmux windows** to see if they're created
4. **Manually test Claude Code** in tmux to verify it works
5. **Check daemon logs** for any startup errors

## Prevention

For the Overlord:
- Always check `multiclaude worker list` after creating workers
- Monitor `multiclaude daemon logs -f` when creating workers
- Verify workers are actually running (not just created)
- Check for Claude Code processes: `ps aux | grep claude | grep -v grep`

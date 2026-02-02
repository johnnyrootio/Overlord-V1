# Worker Monitoring and Status Checking

## Overview

The Overlord needs robust monitoring to ensure workers are actively making progress. Workers should be:
- **Consuming CPU resources** (Claude Code actively processing)
- **Modifying files** (writing code, making changes)
- **Making commits** (progressing toward completion)
- **Not stuck or wedged** for extended periods

## Status Checking Script

### Basic Usage

```bash
# Check all workers for a repository
./scripts/check-worker-status.sh <repo-name>

# Verbose output (shows recent files)
./scripts/check-worker-status.sh <repo-name> --verbose

# JSON output (for automation)
./scripts/check-worker-status.sh <repo-name> --json
```

### What It Checks

1. **Process Status**:
   - Shell process running (PID, CPU, memory, state)
   - Claude Code process running (by session ID)
   - Process states (running, stopped, zombie)

2. **Activity Indicators**:
   - **CPU Usage**: Claude Code should be using > 0.1% CPU when active
   - **File Modifications**: Files modified in last 5 minutes
   - **Git Activity**: Commits in last 10 minutes
   - **Active Writes**: Files currently being written (lsof)
   - **Staged/Unstaged Changes**: Git working directory status

3. **Stuck Detection**:
   - No Claude Code process after 3+ minutes
   - Low activity score for 10+ minutes
   - No file/git activity for 15+ minutes
   - Very low CPU usage for 10+ minutes
   - Process in stopped/zombie state
   - Worker running 2+ hours without completion

### Activity Score

The script calculates an **activity score** (0-10) based on:
- Claude Code CPU usage > 0.1%: +2 points
- Files modified in last 2 minutes: +3 points
- Active file writes (lsof): +2 points
- Git commits in last 5 minutes: +2 points
- Staged/unstaged changes: +1 point
- I/O activity: +1 point

**Interpretation**:
- **5-10**: Worker is actively working ✅
- **3-4**: Worker may be thinking/planning ⚠️
- **0-2**: Worker likely stuck ❌

### Stuck Score

Workers get a **stuck score** based on severity:
- No Claude Code after 3+ min: +5
- No file/git activity for 15+ min: +4
- Low activity for 10+ min: +3
- Very low CPU for 10+ min: +2
- Process stopped/zombie: +10
- Running 2+ hours: +1

**Interpretation**:
- **≥5**: Worker is STUCK - requires intervention
- **1-4**: Warning signs - monitor closely
- **0**: No issues detected

## Continuous Monitoring

### Start Monitor Daemon

```bash
# Start monitoring (checks every 60 seconds)
./scripts/monitor-workers.sh <repo-name>

# Custom interval (check every 30 seconds)
./scripts/monitor-workers.sh <repo-name> --interval 30

# Custom alert threshold (alert after 20 minutes stuck)
./scripts/monitor-workers.sh <repo-name> --alert-threshold 20
```

### Monitor Output

The monitor logs to: `~/.multiclaude/worker-monitor-<repo>.log`

**Log entries**:
- When workers become stuck
- When stuck workers are resolved
- Critical alerts after threshold exceeded
- Recommended actions for stuck workers

### Stop Monitor

```bash
./scripts/monitor-workers.sh <repo-name> --stop
```

## Overlord Integration

### Periodic Status Checks

The Overlord should run status checks regularly:

```bash
# Every 5 minutes during active execution
while true; do
  ./scripts/check-worker-status.sh <repo-name>
  sleep 300
done
```

### Before Creating New Workers

**CRITICAL**: Always check status before creating new workers:

```bash
# 1. Check current worker status
./scripts/check-worker-status.sh <repo-name>

# 2. If stuck workers exist, address them first
# 3. Only then create new workers
```

### When Workers Appear Stuck

1. **Investigate**:
   ```bash
   # Check detailed status
   ./scripts/check-worker-status.sh <repo-name> --verbose
   
   # Attach to worker (read-only)
   multiclaude agent attach --repo <repo-name> <worker-name> --read-only
   ```

2. **Check Worktree**:
   ```bash
   # View recent changes
   cd ~/.multiclaude/wts/<repo-name>/<worker-name>
   git status
   git log --oneline -5
   find . -type f -mmin -10
   ```

3. **Take Action**:
   - If worker is truly stuck: `multiclaude worker kill --repo <repo-name> <worker-name>`
   - If worker needs help: Send message via `multiclaude message send`
   - If issue is unclear: Review worker logs and worktree

## Supervisor Role

The supervisor agent should also monitor workers, but the Overlord must verify:

1. **Supervisor is checking workers**:
   ```bash
   multiclaude message send supervisor "Status check: Are all workers making progress?"
   ```

2. **Supervisor is taking action**:
   - If supervisor isn't detecting stuck workers, Overlord must intervene
   - Overlord should nudge stuck workers directly if supervisor isn't

3. **Supervisor effectiveness**:
   - If supervisor consistently misses stuck workers, consider:
     - Updating supervisor prompt
     - Adding automated monitoring (this script)
     - Overlord taking more active role

## Best Practices

### 1. Regular Monitoring

- Check status **before** creating new workers
- Check status **every 5-10 minutes** during active execution
- Use continuous monitor for long-running sessions

### 2. Act on Stuck Workers

- Don't let workers stay stuck > 15 minutes
- Investigate immediately when stuck score ≥ 5
- Kill and recreate if worker is truly wedged

### 3. Track Activity Patterns

- Workers should show activity within 2-3 minutes of creation
- Activity should be consistent (not long gaps)
- File modifications should align with task progress

### 4. Use Activity Scores

- Activity score < 3 for 10+ minutes = investigate
- Activity score = 0 for 5+ minutes = likely stuck
- Activity score ≥ 5 = worker is active

## Troubleshooting

### Worker Shows as Running But No Activity

1. Check Claude Code process:
   ```bash
   ps aux | grep "session-id <session-id>"
   ```

2. Check CPU usage:
   - Should be > 0.1% when active
   - If 0%, Claude Code may be idle/waiting

3. Check worktree:
   ```bash
   cd ~/.multiclaude/wts/<repo>/<worker>
   git status
   ls -la
   ```

4. Attach to worker:
   ```bash
   multiclaude agent attach --repo <repo> <worker> --read-only
   ```

### False Positives

If workers show as stuck but are actually working:
- Adjust stuck detection thresholds
- Check if activity patterns are different than expected
- Verify file modification detection is working

### Monitor Not Detecting Issues

- Verify monitor is running: `ps aux | grep monitor-workers`
- Check log file for entries
- Manually run status check to compare

## Summary

**Key Points**:
- ✅ Workers must show **active CPU usage** and **file modifications**
- ✅ Use `check-worker-status.sh` before creating new workers
- ✅ Run continuous monitor during active execution
- ✅ Act on stuck workers within 15 minutes
- ✅ Supervisor should monitor, but Overlord must verify
- ✅ Activity score ≥ 5 = active, < 3 for 10+ min = investigate

**Scripts**:
- `check-worker-status.sh`: One-time status check
- `monitor-workers.sh`: Continuous monitoring daemon

Both scripts are in `scripts/` directory and should be available in the Overlord repository.

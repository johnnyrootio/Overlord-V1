# Supervisor Enhancement: Robust Worker Monitoring

## Problem

The supervisor is **not doing its job**. Workers get stuck and the supervisor doesn't detect or fix them:

- Workers stuck at Settings Error prompts
- Claude Code processes not running
- Workers idle with no CPU usage or file activity
- No proactive monitoring or recovery

**Result**: All monitoring falls to the Overlord, defeating the purpose of having a supervisor.

## Root Cause Analysis

### 1. Supervisor Prompt is Too Vague

**Current prompt says:**
- "Monitor workers and merge-queue"
- "Nudge stuck agents"

**But doesn't specify:**
- HOW to detect stuck workers
- WHAT constitutes "stuck"
- WHEN to check worker health
- HOW to fix stuck workers
- WHAT commands to use

### 2. No Actionable Monitoring Instructions

The supervisor has no specific instructions to:
- Check if Claude Code process is running
- Monitor CPU usage
- Check file activity in worktrees
- Verify git commits
- Use diagnostic scripts
- Restart stuck workers

### 3. Daemon Health Checks Are Basic

The daemon only checks:
- ✅ tmux window exists
- ✅ Process PID exists

**But doesn't check:**
- ❌ Claude Code process actually running
- ❌ CPU usage (could be wedged at 0%)
- ❌ File activity
- ❌ Git commits
- ❌ Actual progress

## Solution

### 1. Enhanced Supervisor Prompt

Added comprehensive customizations that specify:

- **Worker Health Monitoring** section with specific check process
- **Stuck Worker Detection** criteria (Claude Code not running, 0% CPU, no file activity, etc.)
- **Automatic Recovery Actions** (restart, nudge, fix config)
- **Monitoring Schedule** (every 5-10 minutes)
- **Recovery Protocol** for different stuck scenarios

### 2. Worker Status Script

The existing `check-worker-status.sh` script provides:
- Process status (shell and Claude Code)
- CPU and memory usage
- File activity in worktree
- Git commit activity
- Stuck detection with scoring

**The supervisor should use this script regularly.**

### 3. Actionable Commands

The enhanced prompt includes specific commands for:
- Checking worker status
- Verifying Claude Code is running
- Checking CPU usage
- Monitoring file activity
- Checking git commits
- Restarting workers

## Implementation

### Customization File

Created: `palpatine/AGENT-PROMPTS/CUSTOMIZATIONS/supervisor.md`

This adds:
1. **Worker Health Monitoring** section (new)
2. **Stuck Worker Detection** criteria
3. **Automatic Recovery Actions**
4. **When Workers Get Stuck** section (new)
5. Enhanced **Communication** section

### Apply Customizations

Run the update script to generate enhanced supervisor prompt:

```bash
./scripts/update-agent-prompts.sh
```

This will create `AGENT-PROMPTS/GENERATED/supervisor.md` with all enhancements.

### Deploy to Repository

Copy the generated prompt to your repository:

```bash
cp palpatine/AGENT-PROMPTS/GENERATED/supervisor.md <repo>/.multiclaude/agents/supervisor.md
```

The supervisor will automatically use the enhanced prompt on next restart.

## Expected Behavior

### Before Enhancement

- Supervisor: "I'll monitor workers" (but doesn't)
- Workers get stuck → Overlord has to fix
- No proactive detection
- No automatic recovery

### After Enhancement

- Supervisor: **Checks workers every 5-10 minutes**
- **Detects stuck workers** using specific criteria
- **Automatically attempts recovery** (restart, nudge, fix)
- **Creates blocker issues** if recovery fails
- **Documents issues** for prevention

## Monitoring Checklist

The supervisor should now:

- [ ] Check all workers every 5-10 minutes
- [ ] Verify Claude Code process is running
- [ ] Check CPU usage (not 0% for extended periods)
- [ ] Monitor file activity in worktrees
- [ ] Check git commit activity
- [ ] Detect stuck workers using criteria
- [ ] Attempt automatic recovery
- [ ] Create blocker issues if recovery fails
- [ ] Use `check-worker-status.sh` script when available

## Verification

After deploying the enhanced supervisor:

1. **Check supervisor prompt**:
   ```bash
   cat <repo>/.multiclaude/agents/supervisor.md | grep -A 5 "Worker Health Monitoring"
   ```

2. **Monitor supervisor behavior**:
   ```bash
   multiclaude agent attach supervisor --read-only
   # Should see regular worker status checks
   ```

3. **Test stuck worker detection**:
   - Create a worker
   - Kill Claude Code process
   - Wait 5-10 minutes
   - Supervisor should detect and attempt recovery

## Summary

**The supervisor was weak because:**
- Prompt was too vague
- No specific monitoring instructions
- No actionable recovery steps

**Now the supervisor:**
- ✅ Has specific monitoring instructions
- ✅ Knows how to detect stuck workers
- ✅ Has actionable recovery steps
- ✅ Will proactively monitor and fix issues

**This should significantly reduce the burden on the Overlord.**

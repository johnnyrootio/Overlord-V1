# Supervisor Customizations

> **Type**: Customization overlay
> **Purpose**: Add robust worker monitoring, stuck detection, and automatic recovery
> **Created**: 2026-01-28

## Customization Instructions

### Section: "Your Job"

**Action**: Enhance existing section

**Insert after**: "- Nudge stuck agents"

**Content**:
```markdown
- **Proactively monitor worker health** (CRITICAL - see Worker Health Monitoring below)
- **Detect and fix stuck workers** automatically
- **Restart workers** that are wedged or not making progress
```

### Section: "Worker Health Monitoring"

**Action**: Insert new section

**Insert after**: "Your Job" section

**Content**:
```markdown
## Worker Health Monitoring (CRITICAL RESPONSIBILITY)

**You MUST actively monitor all workers and ensure they're making progress. This is your primary job.**

### Health Check Process

**Every 5-10 minutes, check each worker:**

1. **Check worker status**:
   ```bash
   multiclaude worker list --repo <repo-name>
   ```

2. **For each worker, verify**:
   - ✅ Claude Code process is running (`ps aux | grep "session-id <session-id>" | grep -v grep`)
   - ✅ Claude Code is using CPU (not idle/wedged)
   - ✅ Files are being modified in worktree (recent activity)
   - ✅ Git commits are being made (progress indicators)

3. **Use worker status script** (if available):
   ```bash
   ./scripts/check-worker-status.sh <repo-name>
   ```

### Stuck Worker Detection

**A worker is STUCK if ANY of these are true:**

- ❌ Claude Code process NOT running (but worker exists)
- ❌ Claude Code CPU usage is 0% for 5+ minutes
- ❌ No file modifications in worktree for 10+ minutes
- ❌ No git commits for 15+ minutes
- ❌ Worker age > 30 minutes with no progress
- ❌ Worker shows "Settings Error" or other startup failures

### Automatic Recovery Actions

**When you detect a stuck worker:**

1. **Diagnose the issue**:
   ```bash
   # Check worker details
   multiclaude agent attach <worker-name> --read-only
   
   # Check process status
   ps aux | grep claude | grep <session-id>
   
   # Check worktree activity
   find ~/.multiclaude/wts/<repo>/<worker> -type f -mmin -10
   ```

2. **Try to unstick** (in order):
   
   a. **If Claude Code not running**:
      - Check if stuck at security prompt (use auto-accept script)
      - Check if stuck at settings error (fix hooks.json)
      - Restart Claude Code: `multiclaude agent restart <worker-name>`
   
   b. **If Claude Code running but idle**:
      - Send nudge message: `multiclaude message send <worker-name> "Status check: Update on your progress?"`
      - Wait 2 minutes
      - If still no activity, restart worker
   
   c. **If worker is wedged**:
      - Kill and recreate: `multiclaude worker kill <worker-name>` then recreate with same task

3. **If recovery fails**:
   - Create blocker issue: `blocker:worker-stuck`
   - Document the issue
   - Escalate to Overlord if needed

### Worker Status Monitoring Commands

**Essential commands for monitoring:**

```bash
# List all workers with status
multiclaude worker list --repo <repo-name>

# Check specific worker details
multiclaude agent attach <worker-name> --read-only

# Check Claude Code process
ps aux | grep claude | grep <session-id>

# Check worktree activity
find ~/.multiclaude/wts/<repo>/<worker> -type f -mmin -10 | wc -l

# Check git activity
git -C ~/.multiclaude/wts/<repo>/<worker> log --oneline --since="15 minutes ago"

# Check CPU usage
ps aux | grep "session-id <session-id>" | awk '{print $3}'
```

### Monitoring Schedule

**You MUST check worker health:**
- **Every 5-10 minutes** during active work periods
- **Immediately** when notified of worker completion
- **Immediately** when you notice no progress in your status checks
- **Before** creating new workers (check existing ones first)

**Don't wait for workers to ask for help - proactively monitor and fix issues.**
```

### Section: "When Workers Get Stuck"

**Action**: Insert new section

**Insert after**: "Worker Health Monitoring" section

**Content**:
```markdown
## When Workers Get Stuck

### Common Stuck Scenarios

1. **Claude Code not starting** (Settings Error, Security Prompt):
   - **Symptom**: Worker exists but no Claude Code process
   - **Fix**: Run `./scripts/auto_accept_workers.sh <repo-name>` or fix hooks.json
   - **Prevention**: Ensure hooks.json uses valid format (no "type: require")

2. **Claude Code wedged** (no CPU usage, no activity):
   - **Symptom**: Process running but 0% CPU, no file changes
   - **Fix**: Restart worker or send nudge message
   - **Prevention**: Monitor CPU usage regularly

3. **Worker idle** (no progress, no commits):
   - **Symptom**: Files exist but no recent changes or commits
   - **Fix**: Send nudge message, check for blockers
   - **Prevention**: Monitor file activity and git commits

4. **Worker crashed** (process dead):
   - **Symptom**: Worker in state but process doesn't exist
   - **Fix**: Daemon should auto-restart, but verify
   - **Prevention**: Health checks should catch this

### Recovery Protocol

**For each stuck worker:**

1. **Identify root cause** (use diagnostic commands above)
2. **Attempt automatic recovery** (restart, nudge, fix config)
3. **If recovery fails after 2 attempts**: Create blocker issue
4. **Document the issue** for future prevention
5. **Escalate to Overlord** if issue is systemic

**Never leave a worker stuck for more than 15 minutes without action.**
```

### Section: "Communication"

**Action**: Enhance existing section

**Insert after**: "multiclaude message ack <id>"

**Content**:
```markdown
**Proactive worker status checks**:
```bash
# Check all workers
multiclaude worker list --repo <repo-name>

# Ask a specific worker for status
multiclaude message send <worker-name> "Status check: What's your current progress?"
```
```

# Worker Dispatch Guide: Using multiclaude CLI

## Overview

**CRITICAL**: The Overlord must work through multiclaude's CLI interface, not around it. 

**STRICT PROHIBITION**: 
- ❌ **NEVER use tmux commands directly** (except in explicitly approved debug scenarios with human approval)
- ❌ **NEVER use socket API commands directly**
- ❌ **NEVER access multiclaude's internal state directly** (`~/.multiclaude/state.json`, worktrees, etc.)
- ✅ **ALWAYS use `multiclaude` CLI commands**

**See**: [MULTICLAUDE-INTERFACE-RULES.md](./MULTICLAUDE-INTERFACE-RULES.md) for complete prohibition details and enforcement.

## Proper Worker Dispatch Flow

### Step 1: Create Worker (multiclaude CLI)

```bash
# Create worker using multiclaude CLI
multiclaude worker create "Implement #101: Add authentication module"
```

**What this does**:
- Creates a git worktree for the worker
- Creates a tmux window for the worker
- Starts Claude Code with `--dangerously-skip-permissions` flag
- Registers worker with multiclaude daemon
- Sends initial task message to Claude

**Output**: Worker name (e.g., "witty-rabbit"), branch name, worktree path

### Step 2: Monitor Worker Status

```bash
# Check worker status
multiclaude worker list

# Or attach in read-only mode to see what's happening
multiclaude agent attach <worker-name> --read-only
```

**What to check**:
- Is worker running?
- Is Claude Code started?
- Is worker stuck at a prompt?
- Has worker started working on the task?

### Step 3: Handle Security Prompt (if needed)

**The Problem**: Sometimes Claude Code shows a security prompt asking to accept "Bypass Permissions mode" even though multiclaude passes `--dangerously-skip-permissions`. This blocks the worker.

**Why it happens**:
- Claude Code version may not fully honor the flag
- Prompt appears before flag is processed
- Configuration issue

**The Solution**: Use the auto-accept script (documented workaround)

```bash
# After creating workers, if they're stuck at prompt:
./scripts/auto_accept_workers.sh <repo-name>
```

**What the script does**:
- Reads tmux session from `~/.multiclaude/state.json`
- Sends "2" + Enter to all worker windows
- Accepts the security prompt

**When to run it**:
- After creating workers
- If `multiclaude worker list` shows workers but they're not making progress
- If `multiclaude agent attach <name> --read-only` shows prompt

### Step 4: Verify Worker is Unblocked

```bash
# Check worker is now working
multiclaude agent attach <worker-name> --read-only

# Should see Claude Code running and processing the task
# Should NOT see the security prompt anymore
```

## Complete Dispatch Workflow

### MANDATORY: Use the Combined Script for ALL Workers

**CRITICAL: You MUST use the combined script for EVERY worker you create. This is not optional.**

**The script is located at**: `scripts/create-worker-with-auto-accept.sh` in the repository root.

**For EVERY ready issue, use this command:**

```bash
./scripts/create-worker-with-auto-accept.sh <repo-name> "Implement #<issue>: <title>"
```

**Why this script is mandatory:**
- Workers will be **stuck at the security prompt** without the auto-accept step
- The script **automatically unsticks workers** by handling the security prompt
- It creates the worker, waits for the prompt, accepts it, and verifies Claude Code is running
- This is the **only reliable way** to ensure workers start properly

**What the script does:**
1. Creates the worker using multiclaude CLI
2. Waits 5 seconds for the security prompt to appear
3. Automatically runs the auto-accept script (sends Down arrow + Enter to accept)
4. Waits for Claude Code to start
5. Verifies Claude Code process is running
6. Reports success/failure

**If the script is not in your repository**, you need to get it from the `project-overlord` repository:
- Location: `scripts/create-worker-with-auto-accept.sh`
- Repository: `https://github.com/johnnyrootio/project-overlord`
- The script must be in the `scripts/` folder at the root of your Overlord directory

### Manual Workflow (NOT RECOMMENDED - Use the script instead)

**WARNING**: Only use this if the script is unavailable. The script is the standard approach.

If you absolutely must create workers manually:

```bash
# For each ready issue in the wave:

# 1. Create worker
multiclaude worker create --repo <repo-name> "Implement #<issue>: <title>"

# 2. Wait for security prompt to appear (4-5 seconds is optimal)
sleep 5

# 3. Run auto-accept script (MANDATORY - workers will be stuck without this)
./scripts/auto_accept_workers.sh <repo-name>

# 4. Wait for Claude Code to start
sleep 3

# 5. Verify worker is unblocked
multiclaude agent attach --repo <repo-name> <worker-name> --read-only
# Should see Claude working on the task

# 6. Continue monitoring
multiclaude worker list --repo <repo-name>
multiclaude daemon logs -f
```

**CRITICAL**: The auto-accept script is **mandatory** - workers will be stuck at the security prompt without it.

## Key Principles

### ✅ DO: Work Through multiclaude CLI

- Use `multiclaude worker create` to spawn workers
- Use `multiclaude worker list` to check status
- Use `multiclaude agent attach` to monitor
- Use `multiclaude message send` for agent communication
- Use auto-accept script (it's a documented workaround, part of the workflow)

### ❌ DON'T: Go Around multiclaude

**STRICT PROHIBITION** (except explicitly approved debug scenarios with human approval):
- ❌ **NEVER use `tmux send-keys` directly**
- ❌ **NEVER use socket API commands**
- ❌ **NEVER manually interact with tmux sessions**
- ❌ **NEVER access `~/.multiclaude/state.json` directly**
- ❌ **NEVER manipulate worktrees directly**
- ❌ **NEVER bypass multiclaude's abstraction**

**If you find yourself wanting to use tmux/socket/state commands, you're doing something wrong. Stop and use multiclaude CLI instead.**

**See**: [MULTICLAUDE-INTERFACE-RULES.md](./MULTICLAUDE-INTERFACE-RULES.md) for complete prohibition details.

## Why multiclaude Abstracts tmux

multiclaude provides:
- **State management**: Tracks workers, repos, agents
- **Message routing**: Agent-to-agent communication
- **Worktree management**: Isolated git worktrees
- **Process monitoring**: Health checks, recovery
- **Abstraction**: You don't need to know about tmux

**The Overlord should use multiclaude's interface, not tmux directly.**

## Security Prompt Handling Plan

### Detection

The Overlord should detect stuck workers:

```bash
# After creating workers, check status
multiclaude worker list

# If workers exist but aren't making progress:
multiclaude agent attach <worker-name> --read-only

# Look for:
# - Security prompt visible
# - No activity after 10+ seconds
# - Worker registered but Claude not responding
```

### Resolution

**Option 1: Auto-accept script (recommended)**
```bash
./scripts/auto_accept_workers.sh <repo-name>
```

**Option 2: Manual acceptance (if script doesn't work)**
```bash
# Attach to worker
multiclaude agent attach <worker-name>

# Manually type "2" and press Enter
# Then detach (Ctrl+B, D)
```

**Option 3: Restart worker (if stuck)**
```bash
# Remove stuck worker
multiclaude worker rm <worker-name>

# Create new worker
multiclaude worker create "Implement #<issue>: <title>"
```

### Prevention

**Long-term solution**: Ensure `--dangerously-skip-permissions` works correctly:
- Verify Claude Code version supports the flag
- Report bug if flag doesn't work
- Update Claude Code if needed

**For now**: Use auto-accept script as documented workaround

## Integration with Phase 4

In Phase 4 (Dispatch), the Overlord should:

1. **Create workers** using `multiclaude worker create`
2. **Monitor immediately** using `multiclaude worker list` and `multiclaude agent attach --read-only`
3. **Detect stuck workers** (security prompt visible)
4. **Run auto-accept script** if needed: `./scripts/auto_accept_workers.sh <repo-name>`
5. **Verify unblocked** by checking worker activity
6. **Continue monitoring** worker progress and PR creation

## Example: Complete Dispatch Sequence

```bash
# Overlord creates workers for wave 0
multiclaude worker create "Implement #101: Add check.sh gate"
multiclaude worker create "Implement #102: Add CI to run check.sh"

# Wait for Claude to start
sleep 3

# Check worker status
multiclaude worker list
# Output shows: witty-rabbit, calm-deer

# Check if any are stuck
multiclaude agent attach witty-rabbit --read-only
# If prompt visible → run auto-accept script

# Accept prompts if needed
./scripts/auto_accept_workers.sh <repo-name>

# Verify workers are unblocked
multiclaude agent attach witty-rabbit --read-only
# Should see Claude working on task

# Continue monitoring
multiclaude worker list
multiclaude daemon logs -f

# Monitor for PRs
gh pr list --repo <repo>
```

## Troubleshooting

### Worker Created But Not Working

**Symptoms**:
- `multiclaude worker list` shows worker
- `multiclaude agent attach` shows security prompt
- No activity after 10+ seconds

**Solution**:
```bash
./scripts/auto_accept_workers.sh <repo-name>
```

### Auto-Accept Script Doesn't Work

**Check**:
1. Script exists: `ls scripts/auto_accept_workers.sh`
2. Script is executable: `chmod +x scripts/auto_accept_workers.sh`
3. Repo name is correct: Check `~/.multiclaude/state.json`

**Alternative**: Manually attach and accept:
```bash
multiclaude agent attach <worker-name>
# Type "2" and press Enter
```

### Worker Still Stuck After Accepting

**Check**:
1. Is Claude Code running? `multiclaude agent attach <name> --read-only`
2. Are there errors? `multiclaude daemon logs -f`
3. Is worktree valid? Check `~/.multiclaude/repos/<repo>/worktrees/`

**Solution**: Remove and recreate worker:
```bash
multiclaude worker rm <worker-name>
multiclaude worker create "Implement #<issue>: <title>"
```

## Remember

**The Overlord works through multiclaude's CLI interface.**
- Use `multiclaude` commands, not tmux directly
- Use auto-accept script as documented workaround
- Monitor workers actively
- Handle stuck workers promptly

**multiclaude abstracts tmux for you - use that abstraction.**

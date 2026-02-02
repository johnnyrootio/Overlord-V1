# multiclaude Interface Rules: CRITICAL PROHIBITIONS

## ⚠️ CRITICAL: NEVER BYPASS multiclaude's INTERFACE

**The Overlord MUST work through multiclaude's CLI interface. Direct interaction with tmux, socket APIs, or other multiclaude internals is STRICTLY PROHIBITED except in explicitly approved debug scenarios.**

## What is PROHIBITED

### ❌ NEVER DO THESE:

1. **NEVER use tmux commands directly**:
   ```bash
   # ❌ FORBIDDEN - Never do this:
   tmux send-keys -t "session:window" "command"
   tmux attach -t "session"
   tmux list-windows -t "session"
   tmux list-sessions
   ```

2. **NEVER use socket API commands directly**:
   ```bash
   # ❌ FORBIDDEN - Never do this:
   echo '{"command": "..."}' | nc localhost 12345
   curl -X POST http://localhost:12345/...
   ```

3. **NEVER access multiclaude's internal state directly**:
   ```bash
   # ❌ FORBIDDEN - Never do this:
   cat ~/.multiclaude/state.json
   jq '.repos' ~/.multiclaude/state.json
   ls ~/.multiclaude/repos/...
   ```

4. **NEVER manipulate worktrees directly**:
   ```bash
   # ❌ FORBIDDEN - Never do this:
   git worktree add ...
   git worktree remove ...
   ```

5. **NEVER interact with Claude Code processes directly**:
   ```bash
   # ❌ FORBIDDEN - Never do this:
   ps aux | grep claude
   kill -9 <claude-pid>
   ```

## What is REQUIRED

### ✅ ALWAYS DO THESE:

1. **ALWAYS use multiclaude CLI commands**:
   ```bash
   # ✅ CORRECT - Always use multiclaude CLI:
   multiclaude worker create "Implement #101: Add feature"
   multiclaude worker list
   multiclaude agent attach <name> --read-only
   multiclaude message send <name> "message"
   multiclaude worker rm <name>
   multiclaude daemon logs -f
   ```

2. **ALWAYS use documented scripts** (if they exist):
   ```bash
   # ✅ CORRECT - Use documented workaround scripts:
   ./scripts/auto_accept_workers.sh <repo-name>
   ```

3. **ALWAYS work through multiclaude's abstraction**:
   - multiclaude manages tmux sessions for you
   - multiclaude manages worktrees for you
   - multiclaude manages state for you
   - multiclaude routes messages for you
   - **You don't need to know about the internals**

## Exception: Debug Scenarios (Human Approval Required)

**The ONLY exception** is when:
1. **Explicitly debugging** a multiclaude issue
2. **Human has explicitly approved** the debug action
3. **Action is clearly documented** as a debug step
4. **Action is temporary** and will be removed after debugging

**Example of approved debug scenario**:
```
Human: "I'm debugging why workers aren't starting. You can check the tmux session directly to see what's happening."

Overlord: "I'll check the tmux session as you've approved for debugging purposes."
# Then can use: tmux list-sessions, tmux attach, etc.
```

**Without explicit human approval, even debug actions are FORBIDDEN.**

## Why This Matters

### multiclaude Provides Abstraction

multiclaude abstracts away:
- **tmux session management** - You don't need to know session names
- **Worktree management** - You don't need to manage git worktrees
- **State management** - You don't need to parse JSON state files
- **Message routing** - You don't need to know about sockets
- **Process management** - You don't need to manage Claude processes

### Bypassing Breaks Things

When you bypass multiclaude's interface:
- **State becomes inconsistent** - multiclaude doesn't know what you did
- **Worktrees get orphaned** - multiclaude can't track them
- **Messages get lost** - multiclaude can't route them properly
- **Workers get confused** - multiclaude can't manage them
- **Debugging becomes impossible** - multiclaude can't help you

### The Right Way

**Use multiclaude's CLI**:
- State stays consistent
- Worktrees are tracked
- Messages are routed properly
- Workers are managed correctly
- Debugging is possible

## Detection and Enforcement

### How to Detect Violations

**Red flags** (if you see these, you're violating the rules):
- Using `tmux` commands
- Using `jq` on `~/.multiclaude/state.json`
- Using `git worktree` commands
- Using `ps`, `kill`, or process management
- Using `nc`, `curl`, or socket commands
- Accessing `~/.multiclaude/` directories directly

### Self-Check Before Any Action

**Before running any command, ask yourself**:
1. "Am I using a `multiclaude` CLI command?"
2. "Is this a documented script/workaround?"
3. "Do I have explicit human approval for this debug action?"
4. "Am I bypassing multiclaude's interface?"

**If the answer to #4 is "yes" and #3 is "no", STOP. Don't do it.**

## Examples

### ❌ WRONG: Direct tmux Access

```bash
# ❌ FORBIDDEN - Don't do this:
TMUX_SESSION=$(jq -r '.repos["my-repo"].tmux_session' ~/.multiclaude/state.json)
tmux send-keys -t "${TMUX_SESSION}:0" "2" C-m
```

**Why it's wrong**: Bypasses multiclaude's interface, manipulates tmux directly.

**Right way**:
```bash
# ✅ CORRECT - Use documented script:
./scripts/auto_accept_workers.sh my-repo
```

### ❌ WRONG: Direct State Access

```bash
# ❌ FORBIDDEN - Don't do this:
WORKERS=$(jq -r '.repos["my-repo"].workers[]' ~/.multiclaude/state.json)
for worker in $WORKERS; do
  echo "Worker: $worker"
done
```

**Why it's wrong**: Bypasses multiclaude's interface, reads state directly.

**Right way**:
```bash
# ✅ CORRECT - Use multiclaude CLI:
multiclaude worker list
```

### ❌ WRONG: Direct Worktree Manipulation

```bash
# ❌ FORBIDDEN - Don't do this:
git worktree add ../my-repo-worker-1 -b worker-1
cd ../my-repo-worker-1
claude -p "Implement feature"
```

**Why it's wrong**: Bypasses multiclaude's interface, creates worktrees manually.

**Right way**:
```bash
# ✅ CORRECT - Use multiclaude CLI:
multiclaude worker create "Implement feature"
```

### ✅ CORRECT: Using multiclaude CLI

```bash
# ✅ CORRECT - All of these use multiclaude's interface:
multiclaude worker create "Implement #101: Add feature"
multiclaude worker list
multiclaude agent attach worker-1 --read-only
multiclaude message send worker-1 "Please focus on tests"
multiclaude worker rm worker-1
multiclaude daemon logs -f
```

## Integration with Workflow

### Phase 0 (Bootstrap)

**When creating the auto-accept script**:
- Script is created as a **documented workaround**
- Script is **part of the workflow**, not a bypass
- Script is **explicitly documented** in WORKER-DISPATCH-GUIDE.md
- **This is the ONLY approved way to handle security prompts**

### Phase 4 (Dispatch)

**When dispatching workers**:
- Use `multiclaude worker create` - ✅ CORRECT
- Use `multiclaude worker list` - ✅ CORRECT
- Use `multiclaude agent attach` - ✅ CORRECT
- Use `./scripts/auto_accept_workers.sh` - ✅ CORRECT (documented workaround)
- Use `tmux send-keys` directly - ❌ FORBIDDEN
- Use `jq` on state.json - ❌ FORBIDDEN

### Debugging

**When debugging issues**:
- First, try multiclaude CLI commands
- Check `multiclaude daemon logs -f`
- Use `multiclaude agent attach --read-only`
- **Only if human explicitly approves**: Can use tmux/socket commands for debugging
- **Document what you did** and why
- **Remove debug commands** after debugging

## Remember

**multiclaude abstracts complexity for you. Use that abstraction.**

**If you find yourself wanting to use tmux/socket/state commands, ask:**
1. "Is there a multiclaude CLI command for this?"
2. "Is there a documented workaround/script?"
3. "Do I have explicit human approval for this debug action?"

**If the answer to all three is "no", you're doing something wrong. Stop and reconsider.**

## Violation Consequences

**If you bypass multiclaude's interface**:
- State becomes inconsistent
- Workers may become orphaned
- Messages may not be routed correctly
- multiclaude may not be able to manage workers
- Debugging becomes impossible
- **The workflow breaks**

**Don't break the workflow. Use multiclaude's interface.**

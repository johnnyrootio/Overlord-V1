# Fixing hooks.json Format Issues

## Problem

Workers fail to start with error: **"Settings Error from invalid hooks.json format"**

**Root cause**: The `hooks.json` file uses an invalid format. Claude Code has updated its hook schema, and `"type": "require"` is no longer valid.

## Solution

### Option 1: Use validate-bash.sh Format (Recommended)

Replace your `.multiclaude/hooks.json` with this format (calls a script for validation):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/validate-bash.sh"
          }
        ]
      }
    ]
  }
}
```

Create `.claude/hooks/validate-bash.sh` in the repo so it exists in each worktree. In that script you can enforce `./scripts/check.sh` before PR commands, deny destructive commands (`rm -rf`, `git reset --hard`, etc.), and prevent CI weakening.

### Option 2: Temporarily Disable Hooks

If you need workers to start immediately:

```bash
# Rename hooks.json to disable it
mv <repo>/.multiclaude/hooks.json <repo>/.multiclaude/hooks.json.disabled

# Restart workers
multiclaude worker list --repo <repo-name>
# Kill stuck workers and recreate
```

**Note**: This removes protection, so only use temporarily.

### Option 3: Remove Hooks Entirely

If hooks aren't critical right now:

```bash
rm <repo>/.multiclaude/hooks.json
```

## Format Requirements

### Valid Hook Structure

Claude Code hooks must use **arrays** for hook definitions, not objects:

**✅ CORRECT** (array format):
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": { ... },
        "hooks": [ ... ]
      }
    ]
  }
}
```

**❌ INCORRECT** (object format):
```json
{
  "hooks": {
    "PreToolUse": {
      "type": "require",  // INVALID
      ...
    }
  }
}
```

### Common Hook Types

- `"type": "deny"` - Block command/action
- `"type": "log"` - Log command/action
- `"type": "allow"` - Explicitly allow (rarely needed)

**Note**: `"type": "require"` is **not valid** in current Claude Code versions.

## Overlord Instructions

When creating `hooks.json` during Phase 0:

1. **Start minimal**: Use the template above (deny destructive commands only)
2. **Test**: Create one worker and verify it starts
3. **Expand gradually**: Add more hooks only after confirming they work

**Template location**: `palpatine/hooks.json.template`

## Verification

After fixing hooks.json:

1. **Check format**:
   ```bash
   cat <repo>/.multiclaude/hooks.json | jq .
   # Should parse without errors
   ```

2. **Test worker creation**:
   ```bash
   ./scripts/create-worker-with-auto-accept.sh <repo-name> "Test: Verify hooks"
   ```

3. **Check Claude Code starts**:
   ```bash
   ps aux | grep claude | grep -v grep
   # Should show Claude Code process
   ```

## References

- Claude Code hooks documentation: https://code.claude.com/docs/en/hooks
- Use `/doctor` command in Claude Code to diagnose hook format issues

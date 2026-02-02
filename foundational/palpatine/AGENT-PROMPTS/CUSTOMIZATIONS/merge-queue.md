# Merge Queue Customizations

> **Type**: Customization overlay
> **Purpose**: Add merge conflict detection and resolution to merge-queue
> **Created**: 2026-01-28

## Customization Instructions

This file defines how to augment the base merge-queue prompt. The Overlord will automatically apply these customizations when the base template changes.

### Section: "Before Merging Any PR"

**Action**: Enhance existing checklist

**Add after line**: `- [ ] Aligns with ROADMAP.md? (no out-of-scope features)`

**Insert**:
```markdown
- [ ] **PR is mergeable?** (`gh pr view <number> --json mergeable` - must be `true`)

**CRITICAL: Check mergeability before attempting merge:**
```bash
# Check if PR can be merged (no conflicts)
MERGEABLE=$(gh pr view <number> --json mergeable -q .mergeable)
if [[ "$MERGEABLE" != "true" ]]; then
  # PR has conflicts - handle them (see Merge Conflict Handling below)
  # DO NOT attempt merge
fi
```
```

### Section: "Merge Conflict Handling"

**Action**: Insert new section

**Insert after**: "Before Merging Any PR" section

**Content**:
```markdown
## Merge Conflict Handling

**CRITICAL: You MUST detect and handle merge conflicts before attempting merge.**

### Detection

Before attempting any merge, check if the PR is mergeable:
```bash
gh pr view <number> --json mergeable,mergeableState
```

**If `mergeable` is `false` or `mergeableState` is `"BLOCKED"` or `"DIRTY"`:**
- The PR has merge conflicts
- **DO NOT attempt merge** - it will fail
- Proceed to conflict resolution workflow

### Conflict Resolution Workflow

**When a PR has merge conflicts:**

1. **Create blocker issue:**
   ```bash
   gh issue create \
     --title "Resolve merge conflict in PR #<number>" \
     --label "blocker:merge-conflict" \
     --label "wave:<X>" \
     --body "PR #<number> has merge conflicts with main after recent merges. Needs conflict resolution."
   ```

2. **Spawn conflict-resolver worker:**
   ```bash
   # Get PR branch name
   PR_BRANCH=$(gh pr view <number> --json headRefName -q .headRefName)
   
   # Spawn worker to resolve conflicts
   ./scripts/create-worker-with-auto-accept.sh <repo-name> "Resolve merge conflict in PR #<number>" --branch $PR_BRANCH
   ```

3. **Conflict-resolver worker should:**
   - Merge main into PR branch: `git fetch origin main && git merge origin/main`
   - Resolve conflicts manually
   - Run gate: `./scripts/check.sh`
   - Update PR: `git push origin <branch>`
   - Signal completion: `multiclaude agent complete`

4. **After conflict resolution:**
   - Re-check mergeability: `gh pr view <number> --json mergeable`
   - If `mergeable` is now `true`, proceed with normal merge workflow
   - If still conflicts, the conflict-resolver may need another iteration

### Error Handling

**If `gh pr merge` fails with conflict error:**
```bash
# Check the error message
if [[ $? != 0 ]]; then
  ERROR=$(gh pr merge <number> --squash 2>&1)
  if echo "$ERROR" | grep -i "conflict\|cannot merge\|mergeable"; then
    # This is a conflict - handle it via conflict resolution workflow above
    # DO NOT retry merge - it will fail again
  fi
fi
```

**Never retry a merge that failed due to conflicts** - always resolve conflicts first.
```

### Section: "When Things Fail"

**Action**: Enhance existing section

**Add after**: "Review feedback:" subsection

**Insert**:
```markdown
**Merge conflicts:**
- Follow "Merge Conflict Handling" workflow above
- Create blocker issue and spawn conflict-resolver worker
```

### Section: "Labels"

**Action**: Enhance existing table

**Add row**:
```markdown
| `blocker:merge-conflict` | Has merge conflicts, needs resolution |
```

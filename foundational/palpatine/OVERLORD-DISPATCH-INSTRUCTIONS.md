# Overlord Dispatch Instructions: Cut and Paste

## CRITICAL: Use Script for Every Worker

**For EVERY new worker you create, you MUST use the combined script:**

```bash
./scripts/create-worker-with-auto-accept.sh <repo-name> "Implement #<issue>: <title>"
```

**Script location**: `scripts/create-worker-with-auto-accept.sh` in the repository root.

**If the script is not in your repository**, you need to get it from the `project-overlord` repository:
- Location: `scripts/create-worker-with-auto-accept.sh`
- Repository: `https://github.com/johnnyrootio/project-overlord`
- The script must be in the `scripts/` folder at the root of your Overlord directory

**Why this is mandatory:**
- Workers will be **stuck at the security prompt** without the auto-accept step
- The script **automatically unsticks workers** by handling the security prompt
- The script handles worker creation + security prompt acceptance automatically
- It verifies Claude Code is running before reporting success
- This is the proven, tested approach

**Example:**
```bash
./scripts/create-worker-with-auto-accept.sh robotic-barista "Implement #3: Add feature X"
```

**DO NOT use `multiclaude worker create` directly** - always use the script. The script automatically unsticks workers by handling the security prompt.

## Check Status Before Creating New Workers

**BEFORE creating any new worker, you MUST check the status of all existing work:**

```bash
# 1. Check all workers and their status
multiclaude worker list --repo <repo-name>

# 2. Check all open PRs and their status
gh pr list --repo <repo-name> --state open

# 3. Check all open issues and their status
gh issue list --repo <repo-name> --state open

# 4. Verify which issues are completed/merged
gh pr list --repo <repo-name> --state merged | grep -E "#<issue-number>"

# 5. Check if any workers are stuck or need attention
multiclaude worker list --repo <repo-name> | grep -E "running|stuck|error"
```

**Only after checking status should you:**
- Identify which issues are ready for work
- Determine which issues have been completed
- Create new workers for ready issues

## Current Status Update

**Issue #2 Status: COMPLETED**

Issue #2 (Data Schema Interface Contract) has been completed. The worker `eager-eagle` successfully:
- Created the JSON schema file (`contracts/data-schema.json`)
- Created interface contract tests (`tests/interfaces/data-schema-contract.test.py`)
- Updated `scripts/check.sh` to run interface tests
- All work is ready for PR creation and review

**Before creating the next worker, verify:**
1. Check if PR for Issue #2 exists: `gh pr list --repo <repo-name> --head work/eager-eagle`
2. Check current worker status: `multiclaude worker list --repo <repo-name>`
3. Check all open issues: `gh issue list --repo <repo-name> --state open`
4. Identify the next ready issue to work on

## Complete Dispatch Sequence

**For each new worker, follow this sequence:**

```bash
# Step 1: Check status of all existing work
multiclaude worker list --repo <repo-name>
gh pr list --repo <repo-name> --state open
gh issue list --repo <repo-name> --state open

# Step 2: Identify the next ready issue
# (Check dependencies, wave labels, etc.)

# Step 3: Create worker using the script
./scripts/create-worker-with-auto-accept.sh <repo-name> "Implement #<issue>: <title>"

# Step 4: Verify worker is running
multiclaude worker list --repo <repo-name>
ps aux | grep claude | grep -v grep | grep -v multiclaude

# Step 5: Monitor worker progress
multiclaude agent attach --repo <repo-name> <worker-name> --read-only
```

## Remember

- **ALWAYS use the script** - never use `multiclaude worker create` directly
- **ALWAYS check status first** - know what's happening before creating new workers
- **ALWAYS verify workers are running** - check that Claude Code processes exist
- **The script is at**: `scripts/create-worker-with-auto-accept.sh` in the repository root

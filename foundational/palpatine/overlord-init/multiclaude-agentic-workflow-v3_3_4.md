# Agentic Workflow v3.3 — Multiclaude + Claude Code + Spec Kit (Project‑Agnostic)

This is a **project‑agnostic**, **LLM‑consumable** workflow for building software using:

- **Claude Code CLI** (local, repo‑aware coding agent)
- **multiclaude** (daemon + tmux orchestration of multiple Claude Code agents)
- **Spec Kit** (turns ideas into structured specs/tasks)
- Optional: **Claude Superpowers** (brainstorming + planning helpers)

It is written so that **an LLM (Cursor / Claude Code / other)** can follow it step‑by‑step, and so a human can audit/override at any point.

---

## 0. Tooling

Keep this list in the doc so an LLM can plan installs and decide when to use what.

### Tier 0 — Core loop (required)
1. **Claude Code CLI**
2. **multiclaude**
3. **Spec Kit**
4. **Hookify‑style lifecycle guardrails** (or equivalent; must exist)

### Tier 1 — Always available (no extra API keys)
5. **Claude Superpowers**
6. **Episodic Memory**
7. **Context7 MCP**

### Tier 2 — Capability‑gated (API keys / infra)
8. **SuperClaude framework**
9. **Firecrawl**
10. **Browserbase**
11. **Playwright**
12. **typescript-language-server (+ typescript)**

---

## 1. Terms and mental model

### Roles

**Two operating modes (multiclaude built-in):**
- **Single-player:** `merge-queue` auto-merges PRs when CI + review requirements are satisfied.
- **Multiplayer:** `pr-shepherd` coordinates with human reviewers and respects your team’s review process (often used when PRs require manual human review).

- **Operator**: a person (or automation) that kicks off runs, approves policy escalations, and can pause/stop.
- **Worker**: implements exactly one task/issue and opens a PR; then signals completion so multiclaude can clean up. 
- **Review agent**: reviews a PR and reports to merge‑queue; signals completion. 
- **Merge‑queue**: merges only when CI is green + no blocking review; spawns fixups; handles conflicts.
- **Supervisor**: optional; manages wave scheduling, dedupe, and deadlock protocols.

### The ratchet
multiclaude is designed so “chaos is okay” **as long as progress is captured**:
- Many agents run in parallel.
- CI + merge policy capture forward progress.
- Failed attempts are discarded; green PRs are merged.

This workflow adds:
1) **Wave scheduling** (foundation → core → features) to reduce semantic conflicts (“roof before walls”).
2) **Deadlock breakers** (merge conflicts, duplicate work, manual prompts) so the system can run longer without human babysitting.
3) A **controller loop** that can repeat from Phase 1 (brainstorm → plan → spec → issues → workers), with stop conditions.

---

## 2. Non‑negotiable invariants

### I1 — One gate to rule them all
There must be one local gate script:

- `./scripts/check.sh`

It is the single definition of “safe to merge.” **CI must run this exact script** (not a duplicated list of commands).

### I2 — CI is sacred
- Never weaken CI to “get green.”
- Any CI change requires explicit escalation.

### I3 — Small diffs by default
Workers must keep PRs small and focused:
- No drive‑by refactors
- No formatting sweeps
- No dependency upgrades unless the issue is specifically about that
- If more work is discovered: open a follow‑up issue

**Why:** small diffs reduce merge conflicts, reduce semantic drift, and make deadlocks cheaper to resolve.

### I4 — One issue/task → one worker → one PR
Default unit:
- One issue/task is implemented by one worker and ends with a PR.
- Overlap can happen across issues, but you should not intentionally “race” multiple workers on one issue unless explicitly requested.

### I5 — Every blocker becomes a work item
If something blocks:
- Create a new issue labeled `blocker:*`
- Dispatch a worker to resolve it
- Continue the wave

---

## 3. Repo control surfaces

Create these in the target repo:

```txt
scripts/check.sh
.github/workflows/ci.yml

CLAUDE.md

.multiclaude/
  hooks.json
  agents/
    worker.md
    reviewer.md
    merge-queue.md
    supervisor.md   (optional)

(spec-kit outputs)
  specs/ or spec/ or .specs/   # use Spec Kit defaults
```

Notes:
- New multiclaude versions support per‑repo prompt overrides under `.multiclaude/agents/…` and deprecate old root‑level files. 
- If `.multiclaude/hooks.json` exists, multiclaude copies it into each worktree’s `.claude/settings.json` to integrate Claude Code hooks. 

---

## 4. Phase 0 — Bootstrap (determinism + autonomy)

### Goal
Make the repo “agent‑ready”:
- deterministic checks
- CI ratchet
- safe defaults
- **no unattended stalls** (manual prompts addressed)

### Outputs
- Single gate: `./scripts/check.sh`
- CI runs `./scripts/check.sh`
- `CLAUDE.md` with repo rules
- `.multiclaude/agents/*` overrides (minimal)
- `.multiclaude/hooks.json` (hooks copied to worktrees)
- Optional: `scripts/auto_accept_workers.sh` (for unattended mode)

---

### 0.1 Tooling config (LLM‑assisted)
The LLM (Cursor/Claude Code) should:
1) Detect stack (package manager, test runner, type checker)
2) Create/update tooling configs
3) Produce a `check.sh` that runs lint/typecheck/tests deterministically

Operator note: keep the initial gate minimal; add expensive tests later.

#### `scripts/check.sh` template (edit to your stack)
```bash
#!/usr/bin/env bash
set -euo pipefail

echo "==> Running repo gate"

# Examples (pick what exists in your repo):
# Python:
#   python -m ruff check .
#   python -m ruff format --check .
#   python -m mypy src tests
#   python -m pytest -q
#
# Node/TS:
#   npm run lint
#   npm run typecheck
#   npm test

echo "TODO: edit scripts/check.sh to match this repo"
exit 1
```

Exit: `./scripts/check.sh` passes locally.

---

### 0.2 CI integration (must run the gate)
Create `.github/workflows/ci.yml` that:
1) checks out code
2) installs deps
3) runs `./scripts/check.sh`

Rule: do not re‑list lint/typecheck/test commands in YAML — call the gate.

Exit: a PR runs CI and CI runs `./scripts/check.sh`.

---

### 0.3 `CLAUDE.md` (repo rules for all agents)
Create `CLAUDE.md` with:
- “small diffs” rule
- “run `./scripts/check.sh` before PR”
- “no CI weakening”
- “when blocked, create a blocker issue”
- “link PRs to issues”

Template:
```md
# Repo rules for AI agents

## Non-negotiables
- Keep PRs small and focused.
- Never weaken CI.
- Run ./scripts/check.sh before opening a PR.
- If blocked: create a new issue labeled blocker:* and stop.

## PR hygiene
- Link PR to issue: "Closes #123" in the PR description.
- Include verification output (CI link or gate output).
```

---

### 0.4 multiclaude agent prompts (defaults + minimal overrides)

## Prompt override semantics

multiclaude ships embedded default prompts. Repo files under `.multiclaude/agents/` are **overrides**. To make this unambiguous for humans and LLMs, use one of the two modes below.

### Mode A — ADDITIVE override (recommended)
Use this when you simply want to add repo-specific constraints (gate command, small diffs, stop conditions, labeling policy).

- Put **only the delta** in the override file.
- Keep it short (ideally < 30 lines).
- Do **not** restate the full upstream prompt.
- Treat the override as “policy + constraints + endpoints”, not a full role description.

Add this header at the top of the file:

```md
MODE: ADDITIVE (recommended)
```

### Mode B — FULL REPLACE override (rare)
Use this only if you intentionally want to replace upstream defaults (accepting drift risk when multiclaude updates).

- Paste the **entire** prompt you want the agent to use (role + process + outputs).
- Include all safety constraints and endpoints explicitly.

Add this header at the top of the file:

```md
MODE: REPLACE_DEFAULT_PROMPT (drift risk accepted)
```

> Note: multiclaude does not need to parse these headers; they are for operator/LLM clarity so the workflow remains deterministic.
Newer multiclaude versions embed default prompts, and repos can add overrides at:
- `.multiclaude/agents/worker.md`
- `.multiclaude/agents/merge-queue.md`
- `.multiclaude/agents/reviewer.md` 

Rule: override only to add repo‑specific constraints (gate, small diffs, stop conditions). Keep overrides short so you don’t fight upstream prompt improvements.

Minimum content:

#### `.multiclaude/agents/worker.md`
- follow the assigned task/issue exactly
- keep diffs small
- run `./scripts/check.sh`
- open PR and link issue
- **after PR creation, signal completion**: `multiclaude agent complete` so the daemon can mark cleanup. 

#### `.multiclaude/agents/reviewer.md`
- verify scope matches issue
- check “small diff” compliance
- check tests/gate evidence
- mark blocking issues clearly and report to merge‑queue, then `multiclaude agent complete`. 

#### `.multiclaude/agents/merge-queue.md`
- merge only when CI green and reviewer summary has no blocking items
- if CI fails, spawn fixup worker on that branch
- if merge conflict, create a blocker issue and dispatch a conflict‑resolver worker

#### `.multiclaude/agents/supervisor.md` (optional but recommended)
- wave scheduling rules
- dedupe detection
- deadlock breaker protocol

---

### 0.5 hooks.json (avoid config drift + enforce the gate)

What multiclaude does:
- If `.multiclaude/hooks.json` exists, multiclaude copies it into each worktree’s `.claude/settings.json`, so Claude Code hooks apply to workers. 

Hook goals:
- Log tool usage (optional)
- Block destructive commands (`rm -rf`, `git reset --hard`, `git clean -fdx`)
- Require `./scripts/check.sh` before “open PR / create PR”
- Prevent weakening CI

Because Claude Code hook schemas vary, use this process:
1) Start with minimal denylist + log
2) Run one worker and verify hooks fire
3) Expand gradually

Starter (pseudo‑structure; adapt to your installed Claude Code hook schema):
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "deny", "pattern": "rm -rf" },
          { "type": "deny", "pattern": "git reset --hard" },
          { "type": "deny", "pattern": "git clean -fdx" },
          { "type": "log", "target": "~/.claude/tool-log.txt" }
        ]
      }
    ]
  }
}
```

Exit: hooks trigger at least once during a worker run.

---

### 0.6 Autonomy blocker: bypass-permissions prompt (unattended mode)

Observed problem:
- Each worker session may prompt to acknowledge “Bypass Permissions mode,” blocking unattended operation.

If your environment still prompts even with `--dangerously-skip-permissions`, you need unattended keystroke injection.

#### What keys must be pressed
For the prompt shown in your screenshots, the sequence is:
- type: `2`
- press: `Enter`

multiclaude itself uses `tmux send-keys ...` for message delivery.  You can do the same for auto‑accept.

#### Where the tmux session name comes from
- Convention: `mc-<repo-name>` (repo name parsed from URL; separators sanitized). The **actual** session name is recorded in state:
- `~/.multiclaude/state.json` → `repos[<repo>].tmux_session` 

Rule for future‑proofing:
- Prefer reading session name from `~/.multiclaude/state.json` instead of guessing.

#### Example script excerpt (LLM‑reproducible)
Add this to your repo as `scripts/auto_accept_workers.sh` (or keep outside repo if you prefer). It:
1) finds the tmux session for a repo from `~/.multiclaude/state.json`
2) iterates windows
3) sends `2` then `Enter` to each

```bash
#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./scripts/auto_accept_workers.sh <repo-name>
# Example:
#   ./scripts/auto_accept_workers.sh open-source-credit-scoring-system

REPO_NAME="${1:-}"
if [[ -z "$REPO_NAME" ]]; then
  echo "usage: $0 <repo-name>" >&2
  exit 2
fi

STATE_FILE="${HOME}/.multiclaude/state.json"
if [[ ! -f "$STATE_FILE" ]]; then
  echo "state file not found: $STATE_FILE" >&2
  exit 2
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "jq is required" >&2
  exit 2
fi

TMUX_SESSION=$(jq -r --arg repo "$REPO_NAME" '.repos[$repo].tmux_session // empty' "$STATE_FILE")
if [[ -z "$TMUX_SESSION" ]]; then
  echo "repo not found in state.json: $REPO_NAME" >&2
  exit 2
fi

# Send keystrokes to every window. This is intentionally blunt: it unblocks the permissions prompt.
# The prompt expects: "2" then Enter.
WINDOWS=$(tmux list-windows -t "$TMUX_SESSION" -F '#{window_index}')
for w in $WINDOWS; do
  tmux send-keys -t "${TMUX_SESSION}:${w}" '2' C-m
done

echo "Sent auto-accept to session ${TMUX_SESSION} windows: ${WINDOWS}" >&2
```

Exit: after spawning N workers, none are stuck waiting on the bypass‑permissions prompt.

---

## 5. Phase 1 — Brainstorm and converge

Goal: turn fuzzy intent into an executable spec + task list.

Tools:
- Superpowers: brainstorm + plan
- Spec Kit: specification + tasks

Outputs:
- Spec: goals, non‑goals, constraints, acceptance criteria
- Plan: architecture decisions, risks, milestones
- Tasks: small units with dependencies and verification steps

---

## 6. Phase 2 — Compile tasks into an ordered work graph

Why: prevents “roof before walls.”

Output artifact: `workgraph.yml` (LLM‑friendly + machine‑parseable).

Minimal schema:
```yaml
waves:
  - id: wave0
    name: foundation
    tasks:
      - id: T1
        issue: 101
        title: Add check.sh gate
        depends_on: []
      - id: T2
        issue: 102
        title: Add CI to run check.sh
        depends_on: [T1]
  - id: wave1
    name: core
    tasks: []
  - id: wave2
    name: features
    tasks: []
```

Rules:
- A task is runnable only if all `depends_on` tasks are merged.
- Within a wave, run tasks in parallel if file overlap is low.
- Use labels: `wave:*`, `area:*`, `risk:*`, `parallel`.

---

## 7. Phase 3 — Emit GitHub issues from the work graph

For each task, create a GitHub issue with:
- Goal
- Files to touch (best guess)
- Acceptance checks
- Verification: `./scripts/check.sh`
- Dependencies: links to prerequisite issues
- Labels: `wave:0|1|2`, `area:*`, `risk:*`, `parallel` if safe

Exit: each issue can be done by one worker and is labeled for wave scheduling.

---

## 8. Phase 4 — Dispatch: run multiclaude in waves

### Command format
multiclaude is moving to noun‑verb commands; older forms are aliases. 

Core commands used in this workflow:
- `multiclaude repo init <github-url> [name]` 
- `multiclaude worker create "task description"` 
- `multiclaude worker rm <name>` 
- `multiclaude agent complete` (signals done + triggers cleanup) 
- `multiclaude message send <agent> "..."` (review → merge‑queue reporting) 

### Dispatcher algorithm (LLM‑consumable)
Repeat for each wave:

1) Query issues with label `wave:X` and status open
2) Filter to those whose dependencies are merged/closed
3) Spawn up to `N` workers for ready issues
4) If unattended mode: run `./scripts/auto_accept_workers.sh <repo-name>`
5) Wait until:
   - PRs opened + reviewed + merged OR blocked
6) Convert blocks into blocker issues
7) Continue until no ready issues remain

Within a wave:
- Allow chaos, but cap concurrency per `area:*` to reduce conflicts.

Exit per wave:
- `main` CI is green
- all wave issues merged or explicitly deferred

---

## 9. Phase 5 — Review + fix loop

Default loop (automated):

For each PR:
1) Run review agent on the PR

```bash
multiclaude review <pr-url>
```
2) If review finds **blocking** items:
   - comment with explicit tasks
   - spawn a fix worker on the same branch
   - re‑run review
3) If no blocking items and CI is green:
   - merge‑queue merges

Review reporting pattern:
- Review agent posts comments and then sends a summary to merge‑queue using `multiclaude message send …`, then signals completion. 

---

## 10. Phase 6 — Deadlock breakers (continuous operation)

A deadlock is when agents cannot make forward progress **without an external action** (human keystroke, conflict resolution, decision).

### How to detect deadlocks (LLM‑checkable)
Use multiclaude state as the source of truth:
- `~/.multiclaude/state.json` tracks agent PIDs, last_nudge, and `ready_for_cleanup`. 

Heuristic detector:
- **Prompt stall:** tmux pane shows interactive prompt; PID alive but no output for > X minutes.
- **Supervisor waiting on you:** supervisor messages repeatedly asking for decision; no progress.
- **Merge conflict loop:** merge‑queue reports conflicts across multiple PRs; workers idle.
- **Duplicate overlap:** supervisor flags “issue overlaps with PR …” and no closure occurs.

Deterministic responses (no “human checkpoint” required by default):

### Deadlock A: merge conflicts between PRs
Response:
1) Create issue: “Resolve merge conflict between PR A and PR B”
2) Label: `blocker:merge-conflict`, `wave:X`
3) Spawn conflict‑resolver worker:
   - merges main into PR branch
   - resolves conflicts
   - runs gate
   - updates PR
   - `multiclaude agent complete`

### Deadlock B: duplicate work overlap
Response:
1) Supervisor chooses winner PR (by CI green + scope match)
2) Close/abandon duplicates with links
3) If reconciliation needed:
   - create `blocker:reconcile`
   - spawn reconciliation worker

### Deadlock C: manual prompt stall
Response:
- If unattended mode: run auto‑accept script
- Else: operator acknowledges prompt(s)
- If prompts recur unexpectedly: file `blocker:autonomy` issue so the system adds/updates automation

---

## 11. Phase 7 — Stop conditions (token safety)

Stop conditions prevent infinite token burn.

### S1: wave complete
- No open issues with `wave:X`
- No open PRs linked to `wave:X`
- `main` is green

### S2: milestone complete (optional)
- `main` green
- All waves up to Y complete
- Release notes summary emitted

### S3: budget guard
- Token/cost threshold reached
- System pauses and emits summary:
  - what merged
  - what is blocked
  - recommended next issues

---

## 12. Phase 8 — Controller loop (repeat from Phase 1)

To reduce human involvement, run the workflow as a loop:

1) **Brainstorm** (Superpowers) → candidate improvements or next features
2) **Plan** → architecture + milestones
3) **Spec** (Spec Kit) → tasks with acceptance criteria
4) **Work graph** → waves + dependencies
5) **Issues** → GitHub issues + labels
6) **Dispatch** (multiclaude) → workers in waves
7) **Deadlock breakers** + **fix loop**
8) Check stop condition; if not met, repeat

Rule: the loop must always produce concrete artifacts (specs/issues/PRs) so progress is inspectable.

---

## 13. Execution cookbook (commands)

### Start multiclaude daemon
```bash
multiclaude start
```

### Initialize a repo
```bash
multiclaude repo init https://github.com/<org>/<repo>
```

### Create a worker
```bash
multiclaude worker create "Implement #123: <short title>"
```

### Remove a worker (cleanup)
```bash
multiclaude worker rm <worker-name>
```

### Review reporting to merge‑queue (from review agent)
```bash
multiclaude message send merge-queue "Review complete for PR #123. Found 0 blocking issues. Safe to merge."
multiclaude agent complete
```

### Unattended-mode auto‑accept
```bash
./scripts/auto_accept_workers.sh <repo-name>
```

---

## 14. Variables section (for reuse across projects)

When instantiating this workflow for a new project, fill these in:

- `REPO_URL`: https://github.com/<org>/<repo>
- `REPO_NAME`: last path segment (used to find `repos[REPO_NAME]` in state.json)
- `STACK`: python | node | go | rust | mixed
- `GATE_CMD`: ./scripts/check.sh
- `CI_PROVIDER`: GitHub Actions | other
- `WAVES`: foundation | core | features (+ optional hardening)
- `CONCURRENCY`: N workers, max 1 per area label (default)
- `UNATTENDED_MODE`: true/false
- `BUDGET_GUARD`: token/cost/time threshold

---

## Appendix A — Minimal worker override (starter)

`.multiclaude/agents/worker.md`:

```md
MODE: ADDITIVE (recommended)

You are a Worker. Implement exactly one GitHub issue.

Rules:
- Keep the diff small and focused on the issue.
- Do not do drive-by refactors or formatting sweeps.
- Run ./scripts/check.sh before opening a PR.
- Open a PR and include "Closes #<issue>" in the PR description.
- If blocked by merge conflicts or prompts: create a blocker issue and stop.
- Never weaken CI.

IMPORTANT:
- After creating/updating the PR, signal completion with: multiclaude agent complete

Deliverables:
- PR link
- Summary of changes
- Verification evidence (CI link or gate output)
```

---

## Appendix B — Minimal review override (starter)

`.multiclaude/agents/reviewer.md`:

```md
MODE: ADDITIVE (recommended)

You are a Review agent. Review a PR against its linked issue.

Check:
- Scope matches issue; no unrelated changes.
- Diff is reasonably small; no drive-by refactors.
- Gate/CI evidence present.
- Tests updated where needed.

Output:
- Summary
- [BLOCKING] items (must be fixed before merge)
- [NON-BLOCKING] suggestions

After review:
- Send a summary to merge-queue using multiclaude message send
- Then signal completion with: multiclaude agent complete
```

---

## Appendix C — Minimal merge‑queue override (starter)

`.multiclaude/agents/merge-queue.md`:

```md
MODE: ADDITIVE (recommended)

You are the Merge Queue.

Rules:
- Merge only when CI is green AND review summary has no [BLOCKING] items.
- If CI fails: spawn a fixup worker on the same branch.
- If merge conflicts: create blocker issue and spawn conflict-resolver worker.
- Never weaken CI to merge.
```


## Debugging and extras (optional but useful)

- See whether multiclaude is running: `multiclaude daemon status`
- Follow logs: `multiclaude daemon logs -f`
- See which agent definitions (including overrides) are in use: `multiclaude agents list`
- Reset agent templates after upgrading multiclaude: `multiclaude agents reset`
- Spawn a custom agent type: `multiclaude agents spawn --name <n> --class <c> --prompt-file <f>`

Notes:
- `multiclaude repo init <url>` creates a **default workspace**; attach via `multiclaude workspace connect`.
- To run without a merge queue (single-player mode): `multiclaude repo init <url> [name] --no-merge-queue`

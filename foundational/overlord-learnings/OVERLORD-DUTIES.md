# Overlord Duties (Check Status & Dispatch Work)

**When acting as the Overlord for a multiclaude project (e.g. robotic-barista), do the following routinely.**

## 1. Check status

- **Workers:** `cd ~/.multiclaude/repos/<repo> && multiclaude work list`
- **PRs:** `gh pr list --state open` and recent merged
- **Health (if workers exist):** `./scripts/check-worker-status.sh <repo>`

## 2. Keep the pipeline moving

- **If no workers and open issues:** Dispatch workers for the next ready issues (check workgraph dependencies).
- **If open PRs with green CI:** Nudge reviewer and/or merge-queue:  
  `multiclaude message send reviewer "..."` and/or `multiclaude message send merge-queue "..."`
- **If workers are stuck:** See CAPTURING-REPLIES.md and supervisor messages; nudge or reassign as needed.

## 3. Brief the supervisor (optional but useful)

After dispatching or when a wave completes:  
`multiclaude message send supervisor "Overlord: <short status>. Dispatched X (Issue #N). ..."`

---

**Remember:** Check status regularly and automatically dispatch work when the pipeline is idle. Run from `~/.multiclaude/repos/<repo>` for multiclaude commands.

#!/usr/bin/env bash
set -euo pipefail

# Check multiclaude worker liveness: active workers, Claude Code processes, CPU/memory, worktree activity.
# Usage: ./scripts/check-worker-status.sh <repo-name> [--verbose|--json]
# Output: parseable key=value lines (ACTIVE_WORKERS=, PROCESS_COUNT=, CPU_PCT=, MEM_MB=, DISK_MB=, REPO_CHANGES=)
#         plus human-readable summary. See foundational/palpatine/WORKER-MONITORING.md.

REPO_NAME="${1:-}"
VERBOSE=""
JSON=""
if [[ "${2:-}" == "--verbose" ]]; then VERBOSE=1; fi
if [[ "${2:-}" == "--json" ]]; then JSON=1; fi
if [[ "${1:-}" == "--verbose" ]] || [[ "${1:-}" == "--json" ]]; then
  REPO_NAME="${2:-}"
  VERBOSE="${VERBOSE:-$([[ \"$1\" == \"--verbose\" ]] && echo 1)}"
  JSON="${JSON:-$([[ \"$1\" == \"--json\" ]] && echo 1)}"
fi

if [[ -z "$REPO_NAME" ]]; then
  echo "usage: $0 <repo-name> [--verbose|--json]" >&2
  exit 2
fi

# Conventional paths (multiclaude: ~/.multiclaude/wts/<repo>/<agent>)
ROOT="${MULTICLAUDE_ROOT:-$HOME/.multiclaude}"
WTS_DIR="$ROOT/wts/$REPO_NAME"
RECENT_MINS="${RECENT_MINS:-10}"
# Tmux session: mc-<repo> with / replaced by -
TMUX_SESSION="mc-${REPO_NAME//\//-}"
TMUX_SESSION="${TMUX_SESSION//./-}"

# 0) Default agents (supervisor, merge-queue, default) from tmux windows
DEFAULT_AGENTS=()
if tmux has-session -t "$TMUX_SESSION" 2>/dev/null; then
  while IFS= read -r win; do
    [[ -n "$win" ]] && DEFAULT_AGENTS+=("$win")
  done < <(tmux list-windows -t "$TMUX_SESSION" -F "#{window_name}" 2>/dev/null || true)
fi

# 1) List workers via CLI only (parse human output: only agent names and status, e.g. "workspace ● running" -> workspace,running)
WORKERS=()
WORKER_STATUSES=()
while IFS= read -r line; do
  line=$(echo "$line" | sed 's/^#.*//' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
  [[ -z "$line" ]] && continue
  # Skip header/footer/separator lines
  [[ "$line" == *"Workspace in"* ]] && continue
  [[ "$line" == *"No workers"* ]] && continue
  [[ "$line" == *"Create a worker"* ]] && continue
  [[ "$line" == *"repository '"* ]] && continue
  [[ "$line" =~ ^-+$ ]] && continue
  [[ "$line" == *"NAME "*"STATUS"* ]] && continue
  # "  workspace ● running" or "nice-dolphin  ● running    work/..." -> name, running
  if [[ "$line" == *"●"* ]] && [[ "$line" == *"running"* ]]; then
    name=$(echo "$line" | awk '{print $1}')
    [[ -n "$name" ]] && WORKERS+=("$name") && WORKER_STATUSES+=("running")
  # Table row when worker finished: "nice-dolphin  ○ done" or similar (name in first column, no ● running)
  elif [[ "$line" =~ ^[a-zA-Z0-9_-]+[[:space:]] ]] && [[ ! "$line" == *"●"* ]]; then
    name=$(echo "$line" | awk '{print $1}')
    status="finished"
    [[ "$line" == *"running"* ]] && status="running"
    [[ -n "$name" ]] && WORKERS+=("$name") && WORKER_STATUSES+=("$status")
  elif [[ "$line" =~ ^[a-zA-Z0-9_-]+$ ]]; then
    WORKERS+=("$line")
    WORKER_STATUSES+=("unknown")
  fi
done < <(multiclaude worker list --repo "$REPO_NAME" 2>/dev/null || true)

# 2) Active workers: worktree exists and has files modified in last RECENT_MINS minutes
ACTIVE=()
REPO_CHANGES=()
for w in "${WORKERS[@]}"; do
  wt="$WTS_DIR/$w"
  if [[ -d "$wt" ]]; then
    count=$(find "$wt" -type f -mmin "-$RECENT_MINS" 2>/dev/null | wc -l | tr -d ' ')
    if [[ "${count:-0}" -gt 0 ]]; then
      ACTIVE+=("$w")
      while IFS= read -r f; do
        [[ -z "$f" ]] && continue
        rel="${f#$wt/}"
        REPO_CHANGES+=("$rel")
      done < <(find "$wt" -type f -mmin "-$RECENT_MINS" 2>/dev/null | head -50)
    fi
  fi
done

# 3) Claude Code / multiclaude processes: only known ones (daemon, claude sessions, log capture)
PROCESS_COUNT=0
CLAUDE_PROCESS_LINES=()
CPU_TOTAL=0.0
MEM_MB=0.0
while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  pid=$(echo "$line" | awk '{ print $2 }')
  cpu=$(echo "$line" | awk '{ print $3 }')
  mem=$(echo "$line" | awk '{ print $4 }')
  agent=""
  # multiclaude daemon
  if [[ "$line" == *"multiclaude"* ]] && [[ "$line" == *"daemon"* ]]; then
    agent="daemon"
  # claude --session-id ... --append-system-prompt-file X.md (supervisor, merge-queue, default, or named worker e.g. nice-dolphin.md)
  elif [[ "$line" == *"supervisor.md"* ]]; then agent="supervisor"
  elif [[ "$line" == *"merge-queue.md"* ]]; then agent="merge-queue"
  elif [[ "$line" == *"default.md"* ]]; then agent="default"
  elif [[ "$line" == *".multiclaude/prompts/"* ]] && [[ "$line" == *".md"* ]]; then
    agent=$(echo "$line" | sed -n 's|.*/prompts/\([^/]*\)\.md.*|\1|p')
    [[ -z "$agent" ]] && agent="worker"
  elif [[ "$line" == *"worker"* ]] && [[ "$line" != *"merge-queue"* ]]; then agent="worker"
  # sh -c cat >> .../X.log (output capture)
  elif [[ "$line" == *"cat >>"* ]] && [[ "$line" == *".multiclaude/output"* ]]; then
    [[ "$line" == *"default.log"* ]] && agent="default (log)"
    [[ "$line" == *"merge-queue.log"* ]] && agent="merge-queue (log)"
    [[ "$line" == *"supervisor.log"* ]] && agent="supervisor (log)"
  fi
  if [[ -n "$agent" ]]; then
    # Only include real processes: default agents (by name), daemon, and named task workers. Exclude log processes and generic "worker".
    real=0
    case "$agent" in
      daemon|supervisor|merge-queue|default) real=1 ;;
      *" (log)"*) real=0 ;;
      worker) real=0 ;;
      *) [[ "$agent" != *"("* ]] && real=1 ;;  # named worker from prompts/NAME.md
    esac
    if [[ "$real" -eq 1 ]]; then
      PROCESS_COUNT=$((PROCESS_COUNT + 1))
      CPU_TOTAL=$(awk "BEGIN { print $CPU_TOTAL + ${cpu:-0} }" 2>/dev/null || echo "$CPU_TOTAL")
      MEM_MB=$(awk "BEGIN { print $MEM_MB + ${mem:-0} }" 2>/dev/null || echo "$MEM_MB")
      CLAUDE_PROCESS_LINES+=("${pid},${cpu},${mem},${agent}")
    fi
  fi
done < <(ps aux 2>/dev/null | grep -E '[Cc]laude|multiclaude' | grep -v grep || true)

# 4) Disk usage of worktrees for this repo
DISK_MB=0
if [[ -d "$WTS_DIR" ]]; then
  DISK_KB=$(du -sk "$WTS_DIR" 2>/dev/null | cut -f1)
  DISK_MB=$((DISK_KB / 1024))
fi

# Output parseable lines for monitor (comma-separated lists)
echo "DEFAULT_AGENTS=$(IFS=,; echo "${DEFAULT_AGENTS[*]:-}")"
echo "WORKERS=$(IFS=,; echo "${WORKERS[*]:-}")"
echo "ACTIVE_WORKERS=$(IFS=,; echo "${ACTIVE[*]:-}")"
for i in "${!WORKERS[@]}"; do
  echo "WORKER_STATUS=${WORKERS[$i]},${WORKER_STATUSES[$i]:-unknown}"
done
echo "PROCESS_COUNT=$PROCESS_COUNT"
echo "CPU_PCT=$CPU_TOTAL"
echo "MEM_PCT=$MEM_MB"
echo "DISK_MB=$DISK_MB"
CHANGES_CSV=$(IFS=,; echo "${REPO_CHANGES[*]:-}")
echo "REPO_CHANGES=$CHANGES_CSV"
for pline in "${CLAUDE_PROCESS_LINES[@]}"; do
  echo "CLAUDE_PROCESS=$pline"
done

# Human-readable liveness summary (first line = legacy "liveness" field)
echo "LIVENESS: ${#ACTIVE[@]} active of ${#WORKERS[@]} workers; $PROCESS_COUNT Claude process(es); CPU ${CPU_TOTAL}% MEM ${MEM_MB}%; disk ${DISK_MB}MB"

if [[ -n "$VERBOSE" ]]; then
  echo "Worktrees: $WTS_DIR"
  for w in "${WORKERS[@]}"; do
    wt="$WTS_DIR/$w"
    if [[ -d "$wt" ]]; then
      recent=$(find "$wt" -type f -mmin "-$RECENT_MINS" 2>/dev/null | wc -l)
      echo "  $w: $recent file(s) modified in last ${RECENT_MINS}min"
    else
      echo "  $w: (no worktree)"
    fi
  done
fi

exit 0

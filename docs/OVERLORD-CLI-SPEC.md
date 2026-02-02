# Overlord CLI Specification

This document specifies the **command-line interface** for Overlord Agent V1: entry point, commands, arguments, options, output format, and interaction behavior. It aligns with **DESIGN-AND-ARCHITECTURE.md** and **OVERLORD-AGENT-V1-SPEC.md**.

---

## 1. Overview

- **Primary interface (V1)**: The human interacts with Overlord only via the CLI.
- **One project per run**: A single Overlord process actively manages one target project at a time. The **list** command is used to choose which project to re-enter.
- **Proactive pending**: When the user runs Overlord for a project that has **pending questions** (e.g. blocked at a phase gate), the CLI **automatically** surfaces those questions, asks them, and reminds the user which phase they are in. The user does not need to remember to "resume."
- **Exit when blocked**: When Overlord needs human input (phase gate, unstick, optional review), it persists state, prints the prompt and phase reminder, then **exits**. The user answers later by running Overlord again for that project (e.g. `overlord run <project-id>` or `overlord resume <project-id>`).
- **Interactive mode**: The CLI is not only commands—it also supports **ad hoc interactions**. During **planning phases** (Phase 0, Phase 1), the session is **chat-like**: the CLI acts like a chat window where the agent asks questions (one at a time, Socratic) and the user answers; agents can **push questions** to the CLI and the user can type free-form replies. During **execution phase** (Phase 4+), the CLI provides a **proactive status stream** (from the multiclaude monitor, e.g. every minute) so the user sees progress (workers, issues, liveness) and can **interrogate** status at any time; Q&A (unstick, arbitration) also flows through the same interface. This **intercontextual chat**—agents and CLI sharing one conversational context—is a first-class part of the interface.

---

## 2. Entry Point

| Item | Specification |
|------|----------------|
| **Command name** | `overlord` |
| **Alternative** | `python -m overlord` (when run from source) |
| **Installation** | Provided by the Overlord package (e.g. `pip install` or `pip install -e .`). Entry point configured in `pyproject.toml` under `[project.scripts]` so `overlord` is available on PATH after install. |

**Examples:**

```bash
overlord --help
overlord start greenfield-specs/example-todo-app.md
overlord list
overlord run my-todo-app
```

---

## 3. Global Behavior

- **State directory**: Local state is stored under `~/.overlord/projects/<project-id>/` (or path given by `--state-dir` if supported in V1). The CLI reads and writes this directory; the graph runtime and state manager perform actual persistence. State includes **project_id** and **repo_url** (GitHub URL after repo creation or when the user provides a URL); the CLI uses these so the user **never has to remind the system** which project they are in.
- **Project context (always show)**: On every **run**, **resume**, **status**, and when blocking at a prompt, the CLI **must** output project identity: **"Project: &lt;project-id&gt;"** and, when **repo_url** is set, **"Repo: &lt;repo_url&gt;"**. This ensures the user always sees which project is active and where the repo lives; the system remembers and does not re-ask.
- **Status echo (repo creation or URL)**: When a new GitHub repo is created (e.g. via `gh repo create` in Phase 0), the CLI or Phase 0 agent **must** echo back clear status: **"Repo created. Project is here: &lt;url&gt;"** and store the URL in state (**repo_url**). When the user provides a **full GitHub URL** (existing repo) as the answer to the first question, the CLI **must** echo **"Using existing repo: &lt;url&gt;"** and store the URL in state. Good status feedback is required so the user sees confirmation and the project URL in one place.
- **First question: name or GitHub URL**: The first question in Phase 0 is: **"What's the name of this repo? (Or provide a full GitHub URL for an existing repo.)"** The user may answer with a **repo name** (e.g. `my-app`) for a new repo, or a **full GitHub URL** (e.g. `https://github.com/org/my-app`) for an existing repo. If the answer is a URL, the system uses it for `multiclaude repo init` and does **not** run `gh repo create`; it stores **repo_url** and echoes "Using existing repo: &lt;url&gt;." If the answer is a name, the system creates the repo (when Phase 0 is fully implemented), then echoes "Repo created. Project is here: &lt;url&gt;" and stores **repo_url**.
- **Step names in UI**: Phases (0–4) are an **internal abstraction** in the software. The **UI uses colloquial step names** so the user never sees "Phase N". Human-readable output shows **step=** with one of: **setup**, **planning**, **work graph**, **issues**, **execution**. JSON output may still include numeric `phase` for API/script consumers. The **issues** step is a **programmatic process** (creating GitHub issues from the work graph); no agent is invoked for that step.
- **Working directory**: Unless specified otherwise, paths (e.g. spec path for `start`) are relative to the **current working directory**.
- **Stdio**: Normal output goes to **stdout**; prompts and progress may go to stdout or stderr as specified per command. User input is read from **stdin** when interactive.
- **Non-interactive / scripted mode**: For tests and scenario runs, input may be supplied via a file (e.g. `--responses <file>`) or environment (e.g. `OVERLORD_RESPONSES_FILE`). When in non-interactive mode, the CLI does not block on stdin for gate answers; it reads from the supplied source. Exact mechanism is implementation-defined (see scenarios in plan/ROADMAP).

---

## 4. Interactive Mode, Chat-Like Behavior, and Slash Commands

### 4a. Modes

- **Planning phases (Phase 0, Phase 1)**: The session is **chat-like**. The CLI presents agent questions (e.g. gate prompts, Socratic brainstorming) and the user types answers. It behaves like a **chat window**: back-and-forth Q&A, one question at a time. All phase agents in these phases can **communicate with the CLI** and ask questions; the CLI is the single channel between the user and the agents (intercontextual chat).
- **Execution phase (Phase 4+)**: The CLI still handles Q&A (unstick, arbitration, human decisions), but in addition it shows a **proactive status stream** (see Section 6): multiclaude status (workers, issues, liveness, CPU, file activity) is pushed to the CLI on an interval (e.g. every minute) so the user sees progress without asking. The user can type **slash commands** (see below) or free-form input to interrogate status or answer prompts.

### 4b. Slash Commands

During an active session (`run` or `start`), the user can type **slash commands** to control or query the CLI without leaving the session. Commands are prefixed with `/`.

| Slash command | Purpose |
|---------------|---------|
| `/status` | Show current multiclaude status snapshot (workers, issues in progress, liveness, optional CPU/file activity). Same data as the status loop; on-demand. |
| `/phase` | Show current Overlord phase and short reminder. |
| `/help` | List slash commands and short usage. |
| `/quiet` | Toggle: reduce or suppress proactive status lines (e.g. only show on `/status`). |
| `/verbose` | Toggle: show more detail in status stream. |

Additional slash commands (e.g. `/pending`, `/checkpoint`) may be added per design. Slash commands are **in-session** only; they do not replace top-level commands like `overlord status <project-id>` (which is for when no session is active).

### 4c. Intercontextual Chat

- **Agents → CLI**: Any phase agent (Phase 0, 1, 4, …) can push a **question** or **prompt** to the CLI. The CLI displays it and reads the user's answer (stdin or responses file), then passes the answer back to the runtime/agent. This is the normal flow for phase gates, Socratic questions, and "human decision needed" during execution.
- **User → CLI**: The user can type free-form text (answer to a question, or a slash command). The CLI interprets slash commands; otherwise it treats input as the answer to the current pending question, if any, or as a passthrough to the agent/runtime if the design supports it (e.g. "clarify X").
- **One context**: Planning and execution share the same **intercontextual** channel: one stream of prompts, answers, and status so the user has a single place to see what's happening and respond.

### 4d. Human Talking to the Active Agent (Routing)

- **Yes — the human effectively communicates with each phase agent.** As the workflow moves through phases (0 → 1 → 2 → …), the **active** agent is whichever phase the graph is in. That agent’s questions are **routed to the CLI** (e.g. as pending questions or in-session prompts); the **user’s response is passed back to that same agent** (via the graph runtime), so the human is directly talking to that agent.
- **Single channel, different agents over time:** The human always uses the same CLI (one stream of Q&A). Who they’re “talking to” changes with the phase: Phase 0 (Bootstrap) at gates, Phase 1 (Specifier) during spec refinement, Phase 4 (Execution Manager) for unstick/arbitration, etc. The runtime ensures the **current** agent’s prompt is shown and the **answer is delivered to that agent** so it can continue (e.g. advance the graph, update state).
- **Direct communication:** The user’s reply is not reinterpreted by Overlord; it is the **input to the agent** that asked. So the human does directly communicate with the agents—through the CLI, with the runtime handling routing (which agent asked, deliver answer to that agent).

---

## 5. Commands (Top-Level)

### 5.1 `overlord start` (Greenfield)

Start a **new** greenfield project from a genesis spec.

**Usage:**

```text
overlord start <spec-path> [options]
```

| Argument / Option | Required | Description |
|------------------|----------|-------------|
| `<spec-path>` | Yes | Path to the genesis spec file (e.g. `greenfield-specs/example-todo-app.md`). Relative to CWD or absolute. |
| `--project-id <id>` | No | Project identifier. If omitted, derived from spec (e.g. basename minus extension) or generated. Must be unique under `~/.overlord/projects/`. |
| `--state-dir <dir>` | No (V1) | Override state root. Default: `~/.overlord`. |

**Behavior:**

1. Validate spec path (file exists, readable).
2. Resolve or generate project-id; ensure it does not already exist under state dir.
3. Create project state directory and initial state (phase = Phase 0, entry = greenfield).
4. Invoke graph runtime starting at **Phase 0** with the spec path in state.
5. When a phase gate (or pending question) is reached: persist state, print the prompt and phase reminder to the user, then **exit** with code 0 (blocked waiting for input). On next run with this project (`run` or `resume`), pending questions are surfaced first.

**Output:** Progress and phase reminders to stdout/stderr; prompt text for the user when blocking.

**Exit codes:** 0 (success or blocked waiting for user); non-zero on error (e.g. spec not found, project-id collision, state write failure).

---

### 5.2 `overlord list` (Projects)

List known projects and indicate which have **pending questions**.

**Usage:**

```text
overlord list [options]
```

| Option | Description |
|--------|-------------|
| `--state-dir <dir>` | Override state root. Default: `~/.overlord`. |
| `--format <fmt>` | Output format: `human` (default), `json`. See Section 7. |

**Behavior:**

1. Scan `~/.overlord/projects/` (or state-dir) for project directories.
2. For each project, read state (or summary) and determine: project-id, current phase, whether there are pending questions, last checkpoint if available.
3. Print table (human) or JSON (machine).

**Output:** One line per project (human) or a single JSON object (machine). Must include at least: `project_id`, `phase`, `pending_questions` (count or boolean). Optional: `last_checkpoint`, `summary`.

**Exit codes:** 0 on success; non-zero on state-dir read error.

---

### 5.3 `overlord run` (Attach and Continue)

Attach to an **existing** project and continue execution. This is the primary way to "resume" after the process has exited (e.g. after a phase gate).

**Usage:**

```text
overlord run <project-id> [options]
```

| Argument / Option | Required | Description |
|------------------|----------|-------------|
| `<project-id>` | Yes | Project identifier (as in `~/.overlord/projects/<project-id>/`). |
| `--state-dir <dir>` | No | Override state root. |
| `--responses <file>` | No (V1) | Path to file containing canned responses for gates/questions (one per line or structured). Used for scripted runs and tests. |

**Behavior:**

1. Load state for `<project-id>`. If no state exists, exit with error (use `start` for new projects).
2. **Proactive pending**: If state contains **pending questions**, present them **first** (in order), read answers from stdin (or from `--responses` file), update state, then continue.
3. Remind the user which **step** they are in (e.g. "Setup – answer to continue."); step names are colloquial (setup, planning, work graph, issues, execution).
4. Invoke graph runtime from the node indicated by state; continue until next block or completion.
5. When blocked again: persist state, print prompt and phase reminder, exit 0.

**Output:** Step reminder, then progress; when blocking, prompt and reminder.

**Exit codes:** 0 (success or blocked); non-zero if project not found or state invalid.

---

### 5.4 `overlord resume` (Alias for Run)

**Usage:** `overlord resume <project-id> [options]`

**Behavior:** Same as `overlord run <project-id>`. Provided for clarity in user mental model ("resume" after exit). Implementation may implement `resume` as an alias of `run`.

---

### 5.5 `overlord status` (Project Status)

Show detailed status for a project: current step (colloquial name), pending questions count, last checkpoint, optional progress summary.

**Usage:**

```text
overlord status <project-id> [options]
```

| Argument / Option | Required | Description |
|------------------|----------|-------------|
| `<project-id>` | Yes | Project identifier. |
| `--state-dir <dir>` | No | Override state root. |
| `--format <fmt>` | No | `human` (default) or `json`. |

**Behavior:**

1. Load state for `<project-id>`.
2. Output: step (colloquial name), pending_questions (count and/or list), last_checkpoint, optional short progress summary (e.g. "Setup – Gate 1 pending.").

**Output:** Human-readable summary or JSON. No prompts; read-only.

**Exit codes:** 0 on success; non-zero if project not found.

**Note:** Status is a first-class concept (DESIGN-AND-ARCHITECTURE Section 10.1). V1 should implement this command; exact fields may be refined.

---

### 5.6 `overlord --help` and `overlord <command> --help`

- **overlord --help**: Print short description and list of commands.
- **overlord <command> --help**: Print usage and options for that command.

**Exit code:** 0.

---

## 6. Status Stream and Multiclaude Monitor Integration

During **execution phase** (Phase 4+), when the user has an active session (`overlord run <project-id>`), the CLI receives **proactive status** from the **multiclaude monitor** (see DESIGN-AND-ARCHITECTURE.md Section 8.4).

- **Status loop**: A **timer-driven** loop (e.g. every minute) in the Overlord process (or a small daemon) gathers multiclaude status via CLI and documented scripts only: worker list, check-worker-status (liveness, CPU, file activity), list-workspace-replies, and optionally PR/issue state. The result is a **status snapshot** (workers, issues being worked on, liveness, CPU/file activity).
- **Proactive display**: The CLI **proactively** prints a short status line (or block) to the user at each interval, e.g.:  
  `[12:34] 3 workers | #101 #102 in progress | 2 PRs open | multiclaude healthy`  
  so the user sees progress without typing anything. Frequency and verbosity may be configurable (e.g. `/quiet` to suppress, `/verbose` for more detail).
- **Interrogation**: The user can **interrogate** status at any time by typing `/status` (slash command) or by running `overlord status <project-id>` in another terminal. The same snapshot is available; the status loop keeps it fresh.
- **Health**: If the monitor detects multiclaude daemon down or repo not inited, the CLI surfaces a clear error (e.g. "multiclaude daemon not running") so the operator knows why status is missing.

This gives the execution phase "very good status" (learnings) and **ownership by the system**: the system remembers to refresh and display status on a schedule, rather than relying on agents to do recurring status updates.

---

## 7. Output Formats

### 7.1 Human (default)

- **list**: Table with columns e.g. `PROJECT_ID`, `PHASE`, `PENDING`, `LAST_CHECKPOINT`. Rows sorted by project-id. Projects with pending questions may be highlighted or listed first (implementation choice).
- **status**: Short paragraphs or bullet list: Phase, Wave, Pending questions (count), Last checkpoint, Summary.
- **start / run / resume**: Progress lines and prompts to stdout/stderr; prompts clearly delimited (e.g. "--- Gate 1 ---" or "Pending: ...") so the user knows when to answer.

### 7.2 JSON (machine)

- **list**: `{ "projects": [ { "project_id": "...", "phase": "...", "pending_questions": N, "last_checkpoint": "..." } ] }`
- **status**: `{ "project_id": "...", "phase": "...", "wave": "..." | null, "pending_questions": N, "pending_prompts": [ "..." ], "last_checkpoint": "...", "summary": "..." }`

When `--format json` is used, **only** the JSON object is printed to stdout (no extra banners or progress), so output is parseable.

---

## 8. Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success; or blocked waiting for user input (state persisted; user should run `overlord run <project-id>` later with their answer). |
| 1 | General error (e.g. invalid arguments, file not found). |
| 2 | Project not found or state invalid. |
| 3 | State or persistence error (e.g. could not write checkpoint). |

Implementations may use additional codes for specific errors; 0 for "blocked waiting for input" is required so scripted runners can distinguish "done for now" from "failure."

---

## 9. Interaction Flow (Proactive Pending)

1. User runs `overlord run my-app` (or `resume my-app`).
2. CLI loads state for `my-app`. State indicates: phase = Phase 0, pending_questions = [ … ], repo_url = … (if set).
3. CLI **before** invoking the graph:
   - Prints **project context**: "Project: my-app" and, if set, "Repo: &lt;url&gt;" (so the user never has to remind the system).
   - Prints the pending question and reads the user's answer (stdin or responses file).
   - If the question was "repo name or URL" and the answer is a GitHub URL: stores repo_url, echoes "Using existing repo: &lt;url&gt;."
   - Updates state (clear that pending question, store answer).
   - If more pending questions, repeat.
4. When no pending questions remain, invoke graph runtime; continue until next block or completion.
5. If the graph blocks again (e.g. Gate 2): persist state with the new pending question, print the prompt and "Overlord is paused. Run 'overlord run my-app' when ready to continue.", exit 0.

---

## 10. Brownfield (V1 Scope)

Brownfield is **out of scope** for the first working V1 per the plan; the CLI may reserve a future command, e.g.:

- **overlord ingest <repo-path>** (future): Run Project Ingester; create project state; next step is `overlord run <project-id>` which enters at Phase 1.

No implementation required for V1; the spec table in DESIGN-AND-ARCHITECTURE and OVERLORD-AGENT-V1-SPEC remains the source for entry scenarios.

---

## 11. Roadmap: Additional Commands (Later)

Planned for **later** (DESIGN-AND-ARCHITECTURE Section 10.2):

- **overlord inspect <project-id>**: Detailed inspect of state, artifacts, and history (read-only).
- **overlord checkpoint [project-id]**: Trigger checkpoint and optionally sync to repo.
- **overlord clean [project-id]**: Remove local state (with confirmation or --force).
- **overlord config**: Get/set config (e.g. state-dir, repo checkpoint on/off).
- **Diagnostics**: A command or subcommand that reports Overlord + multiclaude state (phase, pending, workers, PRs, last checkpoint, suggestions). May be part of `status` or a separate `overlord diagnostics`.

These are not part of the V1 CLI contract; they are listed here for coherence with the design doc.

---

## 12. Summary Table

| Command | Purpose | Key arguments |
|---------|---------|----------------|
| `overlord start <spec-path>` | New greenfield project | spec-path; optional --project-id |
| `overlord list` | List projects; show pending | — |
| `overlord run <project-id>` | Attach and continue; proactive pending | project-id; optional --responses |
| `overlord resume <project-id>` | Alias for run | same as run |
| `overlord status <project-id>` | Project status (phase, pending, checkpoint) | project-id; optional --format json |
| `overlord --help` / `overlord <cmd> --help` | Help | — |
| **In-session** | **Interactive** | |
| Slash commands (`/status`, `/phase`, `/help`, `/quiet`, `/verbose`) | On-demand status, phase, help; toggle status verbosity | During `run` / `start` |
| Proactive status stream | Multiclaude monitor pushes status every minute (Phase 4+); user can interrogate via `/status` | See Section 6 |

---

This document is the **CLI specification** for Overlord Agent V1. Implementation must follow DESIGN-AND-ARCHITECTURE.md and OVERLORD-AGENT-V1-SPEC.md; this spec defines the command surface and interaction behavior for the human operator.

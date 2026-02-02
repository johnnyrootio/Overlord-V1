# Real end-to-end run: trivial todo app

This guide walks you through running Overlord with **real Claude API**, **real GitHub repo**, and **real multiclaude** to build the trivial todo app (add, list, mark done). Human input is only at phase gates.

---

## 0. Convention: where Overlord stores state

- **State root:** Overlord uses **`~/.overlord`** (your home directory) by default. That directory is **not** “installed” there—Overlord just **writes project state there** when you run commands. It is created automatically on first save.
- **Override:** You can pass `--state-dir /some/path` to any command to use a different state root.
- **One subfolder per project:** Under the state root, each project gets its own directory:
  - `~/.overlord/projects/trivial-todo-app/`  (state, artifacts, scripts for that project)
  - `~/.overlord/projects/other-project/`     (another project)
  You **do not** create a separate “Overlord directory” for the todo app—use one **project id** (e.g. `trivial-todo-app`); Overlord creates `~/.overlord/projects/<project_id>/` for you.
- **What’s stored:** Under `~/.overlord/projects/<project_id>/`: `state.json`, `artifacts/` (plan.md, workgraph, etc.), `scripts/check.sh` (stub from Phase 0).
- **Run from anywhere?** You can run the `overlord` command from **any** directory (the CLI is on your PATH after `pip install -e .`). **But:** paths like `greenfield-specs/trivial-todo-app.md` or `scenarios/real-e2e-todo.yaml` are resolved **relative to your current working directory**. So run from the **Overlord repo root** when using those relative paths, or use **absolute paths** for spec and scenario files to run from anywhere.

---

## 1. Prerequisites

- **Python 3.9+** (3.11+ recommended).
- **Overlord installed:** From repo root run `./overlordinstall.sh` (creates a `.venv` and installs Overlord there), or `pip install -e .` in your own venv.
- **GitHub CLI** (`gh`) installed and authenticated: `gh auth status` shows “Logged in”.
- **Claude API**: set one of:
  - `ANTHROPIC_API_KEY` (for phase agents), or
  - `CLAUDE_CODE_API_KEY`
- **multiclaude** installed (Go): `multiclaude --help` works.  
  Used in Phase 4 to dispatch workers. [multiclaude](https://github.com/dlorenc/multiclaude) — install e.g. `go install github.com/dlorenc/multiclaude/cmd/multiclaude@latest`.

---

## 2. One-time setup: repo + multiclaude

Create the target repo and tell multiclaude about it. Do this **once** before using Overlord for this project.

### 2.1 Create the GitHub repo

```bash
# Replace YOUR_USERNAME with your GitHub username or org
gh repo create YOUR_USERNAME/trivial-todo-app --public --description "Trivial todo app (Overlord E2E)"
```

Or create an empty repo on GitHub and note the URL.

### 2.2 Initialize multiclaude for that repo

Workers (Phase 4) need multiclaude to know the repo. Run:

```bash
multiclaude repo init https://github.com/YOUR_USERNAME/trivial-todo-app
```

If multiclaude uses a daemon, start it (if not already running):

```bash
multiclaude start
# or: overlord multiclaude daemon start
```

---

## 3. Run Overlord: two options

### Option A — Interactive (type answers at the CLI)

From the **Overlord repo root**:

**Step 1 — Start the project**

```bash
overlord start greenfield-specs/trivial-todo-app.md --project-id trivial-todo-app
```

You’ll see the first prompt (repo name or URL).

**Step 2 — Answer the first question (repo)**

When prompted: **“What’s the name of this repo? (Or provide a full GitHub URL…)”**

Answer with either:

- Full URL: `https://github.com/YOUR_USERNAME/trivial-todo-app`
- Or owner/repo: `YOUR_USERNAME/trivial-todo-app`

Overlord will echo “Using existing repo: …” and save it. Then it will exit (one question per run when interactive).

**Step 3 — Resume and answer the five gates**

You’ll be prompted once per gate. Each time, run:

```bash
overlord run trivial-todo-app
```

When asked for approval at each gate, answer **yes** (or the exact answer the prompt expects). Repeat until there are no more pending questions.

After the last gate, Overlord will run Phase 1 (Specifier) → Phase 2 (Wave Planner) → Phase 3 (Issue Emitter, creates GitHub issues) → Phase 4 (Execution Manager, dispatches multiclaude workers). You’ll see “Planning complete.”, “Work graph ready.”, “GitHub issues created.”, “Execution ready.” and a final status line.

**Step 4 — Check status**

```bash
overlord status trivial-todo-app
overlord worker list YOUR_USERNAME/trivial-todo-app   # if Phase 4 dispatched workers
```

---

### Option B — Scripted (responses in a file)

Use a responses file so you don’t type each answer. First line = repo (URL or `owner/repo`), next 5 lines = gate answers (e.g. `yes`).

**Step 1 — Create the responses file**

```bash
# Replace YOUR_USERNAME with your GitHub username
cat > /tmp/e2e-responses.txt << 'EOF'
https://github.com/YOUR_USERNAME/trivial-todo-app
yes
yes
yes
yes
yes
EOF
```

Or use `YOUR_USERNAME/trivial-todo-app` on the first line instead of the full URL.

**Step 2 — Start the project**

```bash
overlord start greenfield-specs/trivial-todo-app.md --project-id trivial-todo-app
```

When prompted for the repo, type the URL (or owner/repo) and press Enter — or run once with `--responses` (see below).

**Step 3 — Resume with the responses file (all 6 answers)**

```bash
overlord run trivial-todo-app --responses /tmp/e2e-responses.txt
```

If the CLI only consumes one response per `run`, run it **6 times** (once per line in the file), or use the scenario command with a YAML that lists all gate responses (see “Scenario YAML” below).

**Scenario YAML (one-shot scripted run)**

From repo root you can use the scenario runner with a **real** repo URL in `gate_responses`:

```yaml
# real-e2e-todo.yaml (replace YOUR_USERNAME)
spec_path: greenfield-specs/trivial-todo-app.md
project_id: trivial-todo-app
gate_responses:
  - "https://github.com/YOUR_USERNAME/trivial-todo-app"
  - "yes"
  - "yes"
  - "yes"
  - "yes"
  - "yes"
```

Then run:

```bash
overlord scenario real-e2e-todo.yaml
```

Use an absolute path for `spec_path` if needed, e.g.:

```yaml
spec_path: /full/path/to/Overlord-Agent-V1/greenfield-specs/trivial-todo-app.md
```

---

## 4. What happens in each phase

| Phase | What runs | What you need |
|-------|-----------|----------------|
| 0 | Graph: stub Phase 0, writes artifacts + `scripts/check.sh` under project state. | (none) |
| 1 | **Specifier**: Claude produces plan + tasks; stub writes `plan.md`, `tasks.md`. | `ANTHROPIC_API_KEY` or `CLAUDE_CODE_API_KEY` |
| 2 | **Wave planner**: stub writes `workgraph.yml`. | (none) |
| 3 | **Issue emitter**: reads work graph, creates **real GitHub issues** via `gh`. | `gh auth status` OK, repo exists |
| 4 | **Execution manager**: Claude plan; **multiclaude workers** created per issue. | multiclaude inited for repo, daemon if required |

After Phase 4, workers run in multiclaude; you can watch with:

```bash
overlord status trivial-todo-app
overlord worker list YOUR_USERNAME/trivial-todo-app
overlord reconcile trivial-todo-app
```

---

## 5. Quick reference: CLI commands

| Command | Purpose |
|---------|--------|
| `overlord start greenfield-specs/trivial-todo-app.md --project-id trivial-todo-app` | Start project from spec. |
| `overlord run trivial-todo-app` | Resume; answer next pending question (or use `--responses`). |
| `overlord run trivial-todo-app --responses /path/to/file.txt` | Resume using lines from file as answers. |
| `overlord list` | List projects and pending count. |
| `overlord status trivial-todo-app` | Show phase, workers, health, liveness. |
| `overlord worker list OWNER/REPO` | List multiclaude workers for repo. |
| `overlord worker rm OWNER/REPO WORKER_NAME --yes` | Remove a worker (e.g. stuck). |
| `overlord reconcile trivial-todo-app` | Reconcile GitHub issues + workers; optional `--dispatch` / `--cleanup-stuck`. |
| `overlord multiclaude daemon status \| start \| stop \| restart` | Control multiclaude daemon. |
| `overlord scenario path/to/scenario.yaml` | Run start + N resumes from YAML (spec_path + gate_responses). |

---

## 6. Troubleshooting

- **“Project not found”**  
  Use the same `--project-id` you passed to `start` (e.g. `trivial-todo-app`). Default comes from the spec filename.

- **Repo URL not saved**  
  First answer must be a full URL (`https://github.com/owner/repo`) or `owner/repo`. Overlord normalizes `owner/repo` to `https://github.com/owner/repo`.

- **Phase 3: issues not created**  
  Run `gh auth status` and fix login. Repo must exist; use the same repo URL (or owner/repo) you gave at the first prompt.

- **Phase 4: no workers**  
  Run `multiclaude repo init https://github.com/OWNER/REPO` for that repo. If multiclaude uses a daemon, run `multiclaude start` (or `overlord multiclaude daemon start`).

- **Workers stuck or finished but still listed**  
  `overlord worker rm OWNER/REPO WORKER_NAME --yes` then optionally `overlord reconcile trivial-todo-app --cleanup-stuck --yes`.

- **Slow or timeout**  
  Phase 1 and 4 call Claude; ensure API key is set and network is reachable. For scripted runs, use the scenario YAML so all 6 answers are consumed in one go.

---

## 7. Running a real E2E “test” (manual)

There is no fully automated real E2E test (it would need real API keys, repo, and multiclaude). To **run a real E2E** yourself:

1. Finish **§2** (create repo, `multiclaude repo init`, daemon if needed).
2. Use **Option B** with a scenario YAML where the first `gate_responses` entry is your repo URL (or `owner/repo`).
3. Run:  
   `overlord scenario path/to/real-e2e-todo.yaml`
4. When it finishes, check:
   - `overlord status trivial-todo-app`
   - GitHub repo: issues and (if Phase 4 ran) worker activity
   - `overlord worker list OWNER/REPO`
   - In the project state dir: `~/.overlord/projects/trivial-todo-app/` has artifacts and `projects/trivial-todo-app/scripts/check.sh` (stub from Phase 0). A full “check.sh passes” E2E would require workers to have implemented the app and updated `check.sh` in the **target** repo.

This gives you a repeatable, scripted real E2E run with real Claude, real repo, and real multiclaude, with instructions you can follow step-by-step.

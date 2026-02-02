# Functional Test Plan: Overlord Stages 0–3 (Trivial Todo App)

**Purpose:** Define a structured, realistic functional test plan so that stages 0–3 are validated from the “UI” (CLI) and the system is proven to work as required. No reliance on manual testing for the happy path.

**Scope:** Trivial todo app (`greenfield-specs/trivial-todo-app.md`). Stages: **0 (Bootstrap)**, **1 (Specifier)**, **2 (Wave Planner)**, **3 (Issue Emitter)**. Stage 4 (Execution Manager) is out of scope for this plan.

**UI under test:** Overlord CLI (`overlord start`, `overlord run` / `overlord resume`, `overlord list`, `overlord status`, `overlord scenario`).

---

## 1. Test tiers

| Tier | Description | GH | Claude API | Use |
|------|-------------|----|------------|-----|
| **Stub** | Fast, deterministic; no real GH or Claude | No | No | CI, regression |
| **Realistic** | Real GitHub (create/reuse repo); optional real Claude | Yes | Optional | Pre-merge, release; proves real flow |

Stub tests use scripted scenarios and env that disables API keys. Realistic tests require `gh auth login` and optionally `ANTHROPIC_API_KEY` / `CLAUDE_CODE_API_KEY`; they prove that “create repo → multiclaude init → phases 0–3” works against real services.

---

## 2. Known failure this plan must prevent

**Observed:** User ran `overlord start` with trivial-todo-app, accepted default repo (e.g. `johnnyrootio/trivial-todo-app`). Overlord created the repo via `gh repo create` (empty). Then `multiclaude repo init <url>` ran; multiclaude cloned the repo and tried to create the default workspace worktree → **failure: `fatal: invalid reference: HEAD`** (empty repo has no branch).

**Implication:** Any test that uses real GH and runs through “create repo then multiclaude init” must either (a) ensure the repo has at least one commit before `multiclaude repo init`, or (b) use an existing repo that already has commits. Realistic Stage 0 tests must assert “multiclaude repo init succeeds after repo is ready.”

---

## 3. Stage 0 (Bootstrap) — functional test cases

**Goal:** Project is created from spec; repo is resolved or created; multiclaude init succeeds; Phase 0 runs and produces bootstrap artifacts; state advances.

| ID | Tier | Test case | Preconditions | Steps | Pass criteria |
|----|------|-----------|---------------|------|----------------|
| **0-S1** | Stub | Start from spec, scripted repo answer | Isolated state dir, no API keys | `overlord start <spec>` then `overlord run <pid> --responses <file>` with one line: repo name or URL | Project exists; `state.repo_url` set; no crash |
| **0-S2** | Stub | Start + resume with scripted responses (scenario) | Same | `overlord scenario trivial-todo-app.yaml --state-dir <tmp>` | Exit 0; project exists; phase ≥ 0; repo_url set; when stub Phase 0 runs, no multiclaude call in stub path |
| **0-R1** | Realistic | Create new repo via default (Enter) then init | `gh auth login`, unique project_id | `overlord start trivial-todo-app.md`, Enter for repo; **repo must get initial commit before multiclaude_repo_init** | Repo exists on GitHub; `multiclaude repo init` succeeds; no “invalid reference: HEAD” |
| **0-R2** | Realistic | Use existing repo (owner/repo or URL) then init | `gh auth`, repo exists and has ≥1 commit | `overlord start trivial-todo-app.md`, provide existing owner/repo or URL | Repo URL stored; multiclaude init succeeds; Phase 0 can run (stub or real) |
| **0-R3** | Realistic | List and status after Stage 0 | Project from 0-R1 or 0-R2 | `overlord list`, `overlord status <pid>` | List shows project; status shows phase and repo |

**Artifacts / state (Stage 0):** `~/.overlord/projects/<id>/state.json`, `artifacts/` (e.g. Phase 0 outputs if implemented). Repo on GitHub with at least one commit if newly created.

---

## 4. Stage 1 (Specifier) — functional test cases

**Goal:** After Stage 0, Phase 1 runs (interactive or scripted); plan and tasks artifacts are written; state advances to phase 1.

| ID | Tier | Test case | Preconditions | Steps | Pass criteria |
|----|------|-----------|---------------|------|----------------|
| **1-S1** | Stub | Scenario runs through Phase 1 | Scenario YAML with enough gate_responses | `overlord scenario trivial-todo-app.yaml --state-dir <tmp>` | Exit 0; `state.phase >= 1`; `artifacts/plan.md` and `artifacts/tasks.md` exist and are non-empty (or stub content as defined) |
| **1-S2** | Stub | Resume until no pending, then Phase 1 | Project in phase 0, repo set, no pending | `overlord run <pid> --state-dir <tmp> --responses <file>` (empty or no more prompts) | Phase 1 run; plan.md, tasks.md present |
| **1-R1** | Realistic | Full start → run (real GH, optional Claude) through Phase 1 | gh auth; optional API keys | Start with real repo (existing or created with initial commit); run/resume until Phase 1 complete | Phase 1 artifacts exist; content reflects trivial todo app (add/list/mark done) if Claude used |
| **1-R2** | Realistic | List shows phase and pending | Project at phase 1 | `overlord list` | Project listed with step indicating phase 1 |

---

## 5. Stage 2 (Wave Planner) — functional test cases

**Goal:** After Phase 1, Phase 2 runs; workgraph (waves, tasks) is written; state advances to phase 2.

| ID | Tier | Test case | Preconditions | Steps | Pass criteria |
|----|------|-----------|---------------|------|----------------|
| **2-S1** | Stub | Scenario runs through Phase 2 | Same scenario as 1-S1 | `overlord scenario trivial-todo-app.yaml --state-dir <tmp>` | Exit 0; `state.phase >= 2`; `artifacts/workgraph.yml` exists and is valid YAML |
| **2-S2** | Stub | workgraph.yml structure | Project at phase 2 | Parse `artifacts/workgraph.yml` | Has waves/tasks structure consistent with spec (e.g. trivial todo) |
| **2-R1** | Realistic | Start through Phase 2 with real GH (optional Claude) | As 1-R1 | Run through Phase 2 | workgraph.yml present; state.phase == 2 |
| **2-R2** | Realistic | Status after Phase 2 | Project at phase 2 | `overlord status <pid>` | Status shows phase 2 |

---

## 6. Stage 3 (Issue Emitter) — functional test cases

**Goal:** After Phase 2, Phase 3 runs; GitHub issues (and optionally labels) are created from workgraph; state advances to phase 3; issues.json persisted.

| ID | Tier | Test case | Preconditions | Steps | Pass criteria |
|----|------|-----------|---------------|------|----------------|
| **3-S1** | Stub | Scenario runs through Phase 3 (no real GH) | Stub: Phase 3 must not call `gh` or must use mock | `overlord scenario` to phase 3 with mocked gh / no GH | Exit 0; `state.phase >= 3`; `issues.json` exists; structure has issue-like entries |
| **3-S2** | Stub | issues.json structure | Project at phase 3, stub Phase 3 | Read `issues.json` | Valid structure (e.g. list of {title, body?, labels?}) |
| **3-R1** | Realistic | Phase 3 creates real issues on GitHub | gh auth; repo exists with commits | Run through Phase 3 against real repo | `issues.json` exists; `gh issue list --repo <repo>` shows the created issues |
| **3-R2** | Realistic | List and status at phase 3 | Project at phase 3 | `overlord list`, `overlord status <pid>` | Phase 3 shown; status consistent |

---

## 7. Cross-stage and CLI behavior

| ID | Tier | Test case | Steps | Pass criteria |
|----|------|-----------|------|----------------|
| **X-S1** | Stub | Full scenario 0→3 (stub only) | Single `overlord scenario` run | Exit 0; phase == 3; plan.md, tasks.md, workgraph.yml, issues.json present; no unhandled exceptions |
| **X-R1** | Realistic | Full flow 0→3 with real GH | Start (create or use repo with initial commit), run/resume until phase 3 | All Stage 0–3 artifacts present; repo has issues; multiclaude init never sees empty repo |
| **X-C1** | Both | Slash commands during run | During interactive run: `/help`, `/status`, `/phase` | Commands are recognized and produce expected output |
| **X-C2** | Both | list/rm by name | `overlord list`, `overlord rm <pid> --yes` | List shows project; rm removes project and state dir |

---

## 8. Implementation notes (for when tests are implemented)

1. **Empty-repo fix:** Before calling `multiclaude_repo_init`, if the repo was just created via `gh repo create`, push an initial commit (e.g. README or .gitkeep) so the repo has HEAD. Alternatively, use `gh repo create --source <dir>` with a pre-initialized local repo.
2. **Stub Phase 3:** For 3-S1/3-S2, Phase 3 must be runnable without real `gh` (e.g. mock subprocess or “dry-run” that only writes issues.json).
3. **Realistic test isolation:** Use a unique project_id (e.g. `trivial-todo-app-<timestamp>`) and optionally a dedicated test repo to avoid clashing with user repos.
4. **CI:** Run stub tier in CI; realistic tier can be opt-in (e.g. `pytest -m realistic` with gh + env configured).

---

## 9. Summary checklist (stages 0–3)

- [ ] **0-S1, 0-S2** — Stub start and scenario through repo setup / Phase 0
- [ ] **0-R1** — Real GH: create repo with initial commit, multiclaude init succeeds
- [ ] **0-R2** — Real GH: existing repo, multiclaude init succeeds
- [ ] **0-R3** — List/status after Stage 0
- [ ] **1-S1, 1-S2** — Stub through Phase 1; plan.md, tasks.md
- [ ] **1-R1, 1-R2** — Realistic Phase 1; list shows phase 1
- [ ] **2-S1, 2-S2** — Stub through Phase 2; workgraph.yml valid
- [ ] **2-R1, 2-R2** — Realistic Phase 2; status
- [ ] **3-S1, 3-S2** — Stub Phase 3; issues.json structure
- [ ] **3-R1, 3-R2** — Realistic Phase 3; real issues on GH; list/status
- [ ] **X-S1** — Full stub scenario 0→3
- [ ] **X-R1** — Full realistic 0→3 (empty-repo bug prevented)
- [ ] **X-C1, X-C2** — Slash commands; list/rm

---

*Document version: 1.0. Pending your review and feedback before implementing tests.*

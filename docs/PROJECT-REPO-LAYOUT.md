# Project / Target Repo Layout

Overlord prescribes a **standard layout** for the **target project repository** (the repo that Overlord plans and that workers implement). This layout ensures specs, contracts, and work graph live in well-known locations and that **all interfaces have contracts** and **all planning artifacts are mandatory**.

**Reference implementation:** [johnnyrootio/robotic-barista](https://github.com/johnnyrootio/robotic-barista).

---

## 0. Initial condition and sequence (Phase 0)

When starting a **new project**, the **first question** is: **What's the name of this repo? (Or provide a full GitHub URL for an existing repo.)** The user may answer with a **repo name** (e.g. `robotic-barista`) for a new repo or a **full GitHub URL** (e.g. `https://github.com/org/robotic-barista`) for an existing repo. Phase 0 must ask this **before** any other gate or theme. **The system remembers the project** (state has project_id and repo_url); the CLI shows "Project:" and "Repo:" every run so the user never has to remind the system.

**Sequence:**

1. **Get repo name or URL** — First question: "What's the name of this repo? (Or provide a full GitHub URL for an existing repo.)" (one question; wait for answer.) If the answer is a **URL**: use it for multiclaude init; do **not** create a repo; **echo back** "Using existing repo: &lt;url&gt;" and store **repo_url** in state. If the answer is a **name**: optionally next "Should it be public or private?" and "Which GitHub org/user should own it?"
2. **Create the repo** (only if user gave a name) — `gh repo create <repo-name> [--public|--private] [--org <org>]`. **Echo back:** "Repo created. Project is here: &lt;url&gt;" and store **repo_url** in state. If user gave a URL, skip this step.
3. **Multiclaude initializes the repo** — `multiclaude repo init <url>` (URL from step 1 or 2). Multiclaude sets up its own layout. Do **not** skip this; workers and Overlord depend on multiclaude being inited for this repo.
4. **Overlord adds its parts** — On top of what multiclaude provides, Phase 0 creates the **Overlord-prescribed layout**: directory skeleton (**specs/**, **contracts/**, **docs/**), **scripts/check.sh**, CI config, agent prompts, and any initial placeholder files so Phase 1 can write directly into the prescribed paths.

**Initial condition (after Phase 0):**

- **From multiclaude:** Repo inited; multiclaude can create workers and manage worktrees for this repo.
- **From Overlord:** Repo root contains (at least): **specs/** (empty or placeholder), **contracts/** (empty), **docs/** (empty or placeholder), **scripts/check.sh**, **workgraph.yml** (added by Phase 2 later), and optionally **.overlord/**; agent prompts and hooks as required. No planning content yet in specs/ or docs/—Phase 1 fills those.

There is **no** separate "repo layout file" that lists only initial condition; this document defines both the initial skeleton (above) and the full prescribed structure (below). Phase 0 bootstrap prompt and REPOSITORY-SETUP must follow this sequence and first-question rule.

---

## 1. Prescribed directory structure

```
<target-repo>/
├── specs/                    # Mandatory: Overlord planning outputs (Phase 1)
│   ├── constitution.md       # High-level goals, principles
│   ├── plan.md               # Implementation plan
│   ├── specify.md            # Refined spec (from genesis + brainstorming)
│   └── tasks.md              # Task list for work graph
├── contracts/                # Mandatory: Interface contracts (Wave 0 + spec)
│   ├── cli-commands.yaml     # CLI interface contract (commands, args, exit codes)
│   ├── data-schema.json     # Data / API schema contract (JSON Schema or equivalent)
│   └── ...                   # One contract per interface (API, events, etc.)
├── docs/                     # Operational and user-facing docs
│   ├── operational-specification.md   # Source of truth for behavior (from Phase 1)
│   ├── testing-strategy.md           # Four layers, wave mapping, definition of done
│   └── user-manual.md                # User-facing guide (optional, from tasks)
├── workgraph.yml             # Work graph (Phase 2 output); repo root or .overlord/
├── scripts/
│   └── check.sh             # Gate: "working software" = this script passes
├── src/                      # Application source (structure per stack)
├── tests/                    # Test code (interfaces/, unit/, integration/, system/)
│   ├── interfaces/           # Interface contract tests (reference contracts/)
│   ├── unit/
│   ├── integration/
│   └── system/               # Black box tests
└── .overlord/                # Optional: Overlord section (decisions, context)
```

---

## 2. Mandatory Overlord planning outputs (specs/)

The following artifacts are **mandatory outputs** of Overlord planning (Phase 1) and must be written into the target repo (or Overlord state) so that Phase 2 and Phase 3 consume them.

| Artifact | Path | Owner | Description |
|----------|------|--------|-------------|
| **Constitution** | `specs/constitution.md` | Phase 1 | High-level goals, principles, non-negotiables. |
| **Plan** | `specs/plan.md` | Phase 1 | Implementation plan (phases, milestones). |
| **Specify** | `specs/specify.md` | Phase 1 | Refined specification (from genesis + brainstorming). |
| **Tasks** | `specs/tasks.md` | Phase 1 | Task list used by Phase 2 to build the work graph. |
| **Operational specification** | `docs/operational-specification.md` | Phase 1 | **Source of truth** for behavior: CLI/API, workflows, I/O, runnability. |
| **Testing strategy** | `docs/testing-strategy.md` | Phase 1 | Four layers, wave mapping, definition of done, test arbitration. |

Phase 1 must produce these files. Phase 2 reads from `specs/` and `docs/` (plan, tasks, operational-spec, testing-strategy) to produce `workgraph.yml`. When Overlord bootstraps the target repo (Phase 0), it may create the directory skeleton (`specs/`, `contracts/`, `docs/`) so that Phase 1 can write directly into the prescribed layout.

---

## 3. Mandatory interface contracts (contracts/)

**All interfaces must be defined and have contracts.** Interface contract tests (Wave 0) define and verify these contracts **before** implementation.

- **contracts/** holds machine-parseable contract files.
- Each **user-facing or component interface** has a contract:
  - **CLI:** `contracts/cli-commands.yaml` (commands, arguments, options, exit codes, output format).
  - **Data / API:** `contracts/data-schema.json` (or equivalent: JSON Schema, OpenAPI fragment, etc.).
  - **Events / messages:** optional `contracts/events.yaml` or similar, as needed.
- **Wave 0 tasks** in the work graph include "Test: X Interface Contract" tasks that:
  - Create or update the contract file in `contracts/`.
  - Create interface tests in `tests/interfaces/` that verify behavior against the contract.
- Implementers **do not** see test implementation code; they implement to **operational spec** and **contracts**. Tests validate.

Reference: robotic-barista uses `contracts/cli-commands.yaml` and `contracts/data-schema.json`; work graph tasks T0.1 and T0.2 reference them.

---

## 4. Work graph (workgraph.yml)

- **Location:** Repo root `workgraph.yml` (or, if Overlord keeps artifacts in state first, `artifacts/workgraph.yml`; copy or sync to repo root when persisting to target repo).
- **Format:** YAML. Schema: `waves` (id, name, tasks); each task: `id`, `title`, `type`, `depends_on`, `area`, `risk`, and where applicable `layer`, `tdd_required`, `description`, `test_specification`, `access_restriction`, `primary_goal`, `implementation_guidance`, `validation`.
- **Content:** Phase 2 produces this from Phase 1 artifacts. Tasks must reference `specs/` and `contracts/` where relevant (e.g. "CLI command interfaces in contracts/cli-commands.yaml").
- **Example:** See `docs/WORKGRAPH-EXAMPLE.md` (and [robotic-barista/workgraph.yml](https://github.com/johnnyrootio/robotic-barista/blob/main/workgraph.yml)).

---

## 5. Scripts and gate

- **scripts/check.sh** — The gate for "working software" (per ECOSYSTEM-RULES). Must exist and pass before the system is considered done. Phase 0 bootstrap ensures it exists; Phase 1 testing strategy and Phase 3 issues require it in definition of done.

---

## 6. Summary of requirements

| Requirement | Where enforced |
|-------------|----------------|
| **specs/** with constitution, plan, specify, tasks | Phase 1 outputs; DESIGN; AGENT-IO-SPEC |
| **docs/operational-specification.md**, **docs/testing-strategy.md** | Phase 1 outputs; Phase 2/3 inputs |
| **contracts/** with at least CLI and data/API contracts | Phase 1 (task list); Phase 2 (work graph Wave 0 tasks); Phase 3 (issue bodies) |
| **All interfaces have contracts** | Phase 1, Phase 2 prompts; PROJECT-REPO-LAYOUT |
| **workgraph.yml** at repo root or known path | Phase 2 output; Phase 3 input |
| **scripts/check.sh** | Phase 0; Phase 1 testing strategy; Phase 3 definition of done |

---

*Source: [johnnyrootio/robotic-barista](https://github.com/johnnyrootio/robotic-barista) (specs/, contracts/, docs/, workgraph.yml). Use this layout as the prescribed target repo structure for all Overlord greenfield projects.*

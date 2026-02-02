# Phase 3 Issue Emitter — Technical Specification

This document specifies the **Issue Emitter**: the component that turns the Phase 2 work graph into GitHub issues in the target repository. The emitter is implemented as deterministic code in `overlord/agents/phase3.py` (no LLM). It reads `workgraph.yml`, builds one issue per task with the required format, and creates issues via the GitHub CLI (`gh`) when available, or writes a local manifest when not.

**Related docs:** Format details and examples are in **docs/GITHUB-ISSUE-FORMAT-GUIDANCE.md**. Target repo layout is in **docs/PROJECT-REPO-LAYOUT.md**.

---

## 1. Purpose

- **Input:** Work graph (`workgraph.yml`) from Phase 2 — waves, tasks, dependencies, and metadata (area, risk, type, layer, etc.).
- **Output:** One GitHub issue per task in the target repo (when `gh` and repo are available), plus a local manifest `issues.json` mapping task IDs to issue numbers. When `gh` or repo is not available, the emitter writes only the manifest with placeholder numbers for testing.
- **Contract:** Issues must follow the format in GITHUB-ISSUE-FORMAT-GUIDANCE.md so they are consistent, worker-friendly, and enforce spec-first and testing strategy.

---

## 2. Inputs

| Name        | Source / path                          | Format |
|------------|-----------------------------------------|--------|
| work graph | `artifact_paths["workgraph"]` (e.g. `artifacts/workgraph.yml`) | YAML   |
| repo       | `repo_url` (GitHub URL) or `repo_name` (owner/repo) from session state | —      |
| state_root | Overlord state root                     | —      |
| project_id | Current project ID                      | —      |

The work graph schema is summarized in **docs/WORKGRAPH-EXAMPLE.md**: `waves` (list of waves), each wave has `id`, `tasks`; each task has `id`, `title`, `type`, `depends_on`, `area`, `risk`, and optionally `layer`, `tdd_required`, `description`, `test_specification`, `access_restriction`, `primary_goal`, `implementation_guidance`, `validation`.

---

## 3. Outputs

| Name            | Path / target                                    | Format |
|-----------------|---------------------------------------------------|--------|
| GitHub issues   | Target repository (when `gh` available and repo set) | One issue per task |
| issues manifest | `state_root/projects/<project_id>/issues.json`    | JSON array of `{ task_id, number, title }` |

The manifest is always written. When using `gh`, issue numbers are real; otherwise they are placeholders (1, 2, …) for downstream phases and tests.

---

## 4. Behavior

### 4.1 Task order

Tasks are taken from the work graph in **wave order**, then task order within each wave. The emitter creates issues in that order so that when a task has `depends_on`, the referenced tasks already have issue numbers; the body can use **Depends on: #N** with the correct N.

### 4.2 One issue per task

For each task the emitter produces:

- **Title:** From the task’s `title` (e.g. `Test: CLI Commands Interface Contract`, `Implement: Order Placement`). Clear, actionable; prefix by kind when appropriate.
- **Labels:** Derived from the work graph and GITHUB-ISSUE-FORMAT-GUIDANCE:
  - **wave:N** — from the wave index.
  - **area:** — from task `area` (e.g. `area:testing`, `area:services`).
  - **risk:** — from task `risk` (e.g. `risk:low`, `risk:medium`).
  - **type:** — from task `type` (e.g. `type:test`, `type:implementation`).
  - For test tasks: **layer:** (e.g. `layer:interface`) when present.
  - For implementation tasks with TDD: **tdd:required** when set.
- **Body:** Markdown with:
  - **Header block:** Type, Wave, and Depends on #N (when the task has dependencies). For test issues, Layer when applicable.
  - **Goal / Primary Goal** (from task `primary_goal` or `description`).
  - **Implementation guidance** or **Test specification / Access restrictions** from task fields.
  - **Files to Touch** when specified.
  - **Definition of Done** with checkboxes, always including `./scripts/check.sh` passes.

Exact body structure and examples are in **docs/GITHUB-ISSUE-FORMAT-GUIDANCE.md**.

### 4.3 Spec-first and testing strategy in issue text

Issue bodies must carry through:

- **Spec-first:** Implementation issues state that the primary goal is implementing the operational specification and that tests validate.
- **Testing layers:** Test issues reference the layer (interface, unit, integration, black box) per TESTING-STRATEGY.
- **Access restrictions:** Test issues state that test implementation code is NOT visible to implementation workers; they implement to spec and contracts; tests validate.
- **Escalation:** Implementation guidance includes that if the implementer believes a test is wrong, they create an issue with label **blocker:test-arbitration**.

### 4.4 Creation path

- **When `gh` is available and repo is set:** The emitter ensures labels exist (e.g. `gh label create … --force`), then creates each issue with `gh issue create --repo <owner/repo> --title … --body … --label …`. It parses the command output for the issue number and records it in the manifest and uses it for subsequent “Depends on” references.
- **When `gh` or repo is not available:** The emitter does not call GitHub. It still builds title, body, and labels for each task and writes the manifest with placeholder numbers (1, 2, …) so Phase 4 and tests can run.

---

## 5. Target repo layout references

The work graph is produced from **specs/** and **docs/** (see PROJECT-REPO-LAYOUT). Issue bodies should reference **contracts/** where applicable (e.g. `contracts/cli-commands.yaml`, `contracts/data-schema.json`) in Files to Touch and test specification. Interface contract tasks (Wave 0) create or verify files in **contracts/** and tests in **tests/interfaces/**.

---

## 6. Exit criteria (definition of done for the emitter)

- [ ] Every work graph task has a corresponding GitHub issue (or a manifest entry with placeholder number when not using `gh`).
- [ ] Issues have the correct labels (wave:N, area:, risk:, type:, and layer:/tdd:required where applicable).
- [ ] Dependencies are linked in issue bodies (**Depends on: #N** in the header block).
- [ ] Body structure matches GITHUB-ISSUE-FORMAT-GUIDANCE (header block, Goal, Guidance/Spec, Files to Touch, Definition of Done).
- [ ] Implementation issues state spec-first and test-access restrictions.
- [ ] Definition of Done includes `./scripts/check.sh` passes (and testing layer where applicable).

---

## 7. Implementation

- **Module:** `overlord/agents/phase3.py`
- **Entry point:** `emit_issues(work_graph_path, repo_name, state_root, project_id, repo_url=None)` — returns a list of issue number strings.
- **Helpers:** `is_gh_available()`, work graph loading (YAML), body/label construction from task fields, `gh issue create` / `gh label create` when available.

Phase 3 is **not** an LLM agent; it is plain old software that implements this spec. The format and behavior above are the single source of truth for what the emitter must produce.

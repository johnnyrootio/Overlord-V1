# Agent I/O Specification

Formal inputs and outputs for each Overlord phase agent. Used for wiring, validation, and machine-readable contracts (e.g. `agent-io-spec.json`).

**Conventions:**

- **Input** = artifact or state key the agent reads (path relative to project dir or state).
- **Output** = artifact the agent must produce (path, format).
- **Format** = MD (Markdown), YAML, JSON, or text as noted.

---

## Phase 0 — Bootstrap

| Kind   | Name / Key           | Source path / state                    | Format |
|--------|----------------------|----------------------------------------|--------|
| Input  | Genesis spec         | `state.genesis_spec_path`               | MD or YAML |
| Input  | Session state        | `state_root/projects/<project_id>/`     | (state) |
| Output | phase_0_done         | `artifacts/phase_0_done.txt`           | Text (sentinel) |
| Output | Phase 0 system prompt| `artifacts/phase_0_system_prompt.md`   | MD (copy for agentic use) |
| Output | check.sh             | `scripts/check.sh`                      | Shell script (executable) |
| Output | CI config            | (target repo) e.g. `.github/workflows/` | YAML |
| Output | Agent prompts        | (target repo) per AGENT-PROMPTS         | MD |

---

## Phase 1 — Specifier

| Kind   | Name / Key           | Source path / state                    | Format |
|--------|----------------------|----------------------------------------|--------|
| Input  | Genesis spec         | `state.genesis_spec_path`               | MD or YAML |
| Input  | Phase 0 artifacts    | `artifact_paths["phase_0"]`, `artifact_paths["phase_0_system_prompt"]` | — |
| Input  | Gate responses       | (implicit; gates 1–5 cleared)          | — |
| Output | constitution         | `specs/constitution.md`                | MD |
| Output | plan                 | `specs/plan.md`                        | MD |
| Output | specify              | `specs/specify.md`                     | MD |
| Output | tasks                | `specs/tasks.md`                       | MD |
| Output | operational specification | `docs/operational-specification.md` | MD |
| Output | testing strategy     | `docs/testing-strategy.md`            | MD |
| Output | Phase 1 system prompt| `artifacts/phase_1_system_prompt.md`   | MD |

*Prescribed layout per docs/PROJECT-REPO-LAYOUT. Phase 1 must prescribe interface contracts in **contracts/** (at least cli-commands.yaml, data-schema.json); Wave 0 tasks create/verify them. Current stub may still write to artifacts/ until target repo is created.*

---

## Phase 2 — Wave Planner

| Kind   | Name / Key            | Source path / state                    | Format |
|--------|-----------------------|----------------------------------------|--------|
| Input  | plan                  | `specs/plan.md`                        | MD |
| Input  | tasks                 | `specs/tasks.md`                       | MD |
| Input  | operational specification | `docs/operational-specification.md` | MD |
| Input  | testing strategy      | `docs/testing-strategy.md`            | MD |
| Output | workgraph             | `workgraph.yml` (repo root) or `artifacts/workgraph.yml` | YAML |
| Output | Phase 2 system prompt | `artifacts/phase_2_system_prompt.md`   | MD |

*Prescribed layout per docs/PROJECT-REPO-LAYOUT. Work graph schema and example: docs/WORKGRAPH-EXAMPLE. Tasks reference **contracts/** paths (e.g. contracts/cli-commands.yaml, contracts/data-schema.json) in Wave 0 interface contract tasks.*

---

## Phase 3 — Issue Emitter

| Kind   | Name / Key            | Source path / state                    | Format |
|--------|-----------------------|----------------------------------------|--------|
| Input  | workgraph             | `artifact_paths["workgraph"]` → `artifacts/workgraph.yml` | YAML |
| Input  | (optional) Repo name  | `repo_name` / state                    | — |
| Output | issues                | GitHub issues (one per work graph task) | — |
| Output | issues manifest       | `state_root/projects/<project_id>/issues.json` | JSON |
| Output | Phase 3 system prompt  | `artifacts/phase_3_system_prompt.md`   | MD |

*Current implementation writes `issues.json` locally; GitHub issue creation is stub/future. Issue format (labels, body structure) is defined in `docs/GITHUB-ISSUE-FORMAT-GUIDANCE.md` (reference: [johnnyrootio/robotic-barista](https://github.com/johnnyrootio/robotic-barista)).*

---

## Phase 4 — Execution Manager

| Kind   | Name / Key            | Source path / state                    | Format |
|--------|-----------------------|----------------------------------------|--------|
| Input  | issues / workgraph    | `issues.json`, workgraph, open issues  | JSON / YAML / API |
| Input  | Operational spec      | (in repo or artifacts)                 | MD |
| Input  | Repo name             | multiclaude repo                       | — |
| Output | (no persistent files) | Worker dispatch, status, messages      | — |

*Phase 4 is reactive: dispatches workers, monitors status, captures replies. Outputs are actions and user-facing status, not new artifact files.*

---

## Summary table (machine-oriented)

| Phase | Input artifacts | Output artifacts |
|-------|-----------------|------------------|
| 0     | genesis_spec_path | phase_0_done.txt, phase_0_system_prompt.md, scripts/check.sh, CI, agent prompts |
| 1     | genesis_spec_path, phase_0 artifacts | plan.md, tasks.md, phase_1_system_prompt.md |
| 2     | plan.md, tasks.md | workgraph.yml, phase_2_system_prompt.md |
| 3     | workgraph.yml   | issues (GitHub), issues.json, phase_3_system_prompt.md |
| 4     | issues.json, workgraph, operational spec | (none; status and dispatch actions) |

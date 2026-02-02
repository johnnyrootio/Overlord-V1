# Overlord Orchestration Guide: Greenfield Development with Multiclaude

## Overview

This document describes how an **Overlord** (typically Cursor acting as an orchestrating AI assistant) drives the complete agentic workflow for **greenfield projects**—projects starting from Phase 0 with no existing codebase. The Overlord coordinates with multiclaude's workspace agent to transform initial ideas into a fully functional software system through structured phases.

**Related Documents**:
- [GETTING-STARTED.md](./GETTING-STARTED.md) - **START HERE** - Practical guide to kick off a new project
- [MULTICLAUDE-INTERFACE-RULES.md](./MULTICLAUDE-INTERFACE-RULES.md) - **CRITICAL: Read this first!** Strict prohibitions against bypassing multiclaude's interface
- [WORKER-DISPATCH-GUIDE.md](./WORKER-DISPATCH-GUIDE.md) - **CRITICAL** - How to properly dispatch workers using multiclaude CLI
- [EXECUTION-PHASE-PROMPT.md](./EXECUTION-PHASE-PROMPT.md) - **CRITICAL** - Prompt template for active facilitation during execution phases
- [MCP-TOOLS-INTEGRATION.md](./MCP-TOOLS-INTEGRATION.md) - **CRITICAL** - How to use MCP tools (Reflection, Context7, SpecKit, etc.)
- [PHASE-GATES.md](./PHASE-GATES.md) - **CRITICAL** - Explicit phase gates requiring human approval
- [DOCUMENT-INTERNALIZATION.md](./DOCUMENT-INTERNALIZATION.md) - **CRITICAL** - How to properly internalize and follow workflow documents
- [INTERACTIVE-BRAINSTORMING.md](./INTERACTIVE-BRAINSTORMING.md) - **CRITICAL** - How to conduct interactive brainstorming sessions
- [MULTICLAUDE-SETUP.md](./MULTICLAUDE-SETUP.md) - multiclaude installation and usage on your system
- [GITHUB-PERMISSIONS.md](./GITHUB-PERMISSIONS.md) - GitHub CLI permissions and authentication requirements
- [INITIAL-OVERLORD-PROMPT.md](./INITIAL-OVERLORD-PROMPT.md) - Template prompt to give Cursor to start
- [REPOSITORY-SETUP.md](./REPOSITORY-SETUP.md) - Repository setup options (existing vs. create new)
- [PHASE-0-PLANNING.md](./PHASE-0-PLANNING.md) - **Phase 0 Planning Guide** - Using Claude Code superpowers and Context7
- [TESTING-STRATEGY.md](./TESTING-STRATEGY.md) - Comprehensive testing philosophy and methodology
- [SPEC-FIRST-ENFORCEMENT.md](./SPEC-FIRST-ENFORCEMENT.md) - How spec-first development is enforced
- [ECOSYSTEM-RULES/](./ECOSYSTEM-RULES/) - Ecosystem-specific rules, cursor rules, and best practices
- [AGENT-PROMPTS/](./AGENT-PROMPTS/) - Agent prompt templates (worker.md, supervisor.md, reviewer.md)
- [CAPTURING-REPLIES.md](./CAPTURING-REPLIES.md) - How to capture worker/supervisor replies (workspace inbox, `list-workspace-replies.sh`)
- [EVOLUTION-NOTES.md](./EVOLUTION-NOTES.md) - Tracked items for evolving the system (e.g. reliable capture of status stream)
- [multiclaude-agentic-workflow-v3_3_4.md](./multiclaude-agentic-workflow-v3_3_4.md) - Original workflow specification

## The Overlord Role

The **Overlord** is an external orchestrator (Cursor, Claude Code, or another AI assistant) that:

- **Communicates with multiclaude's workspace agent** via the workspace interface
- **Drives the workflow phases** from brainstorming through continuous operation
- **Takes initial ideas, specifications, or planning documents** from humans (e.g., "Palpatine")
- **Transforms them into executable work** (specs, tasks, issues, PRs)
- **Orchestrates wave-based execution** using multiclaude's agent system
- **Monitors progress and breaks deadlocks** to maintain forward momentum

The Overlord is **not** a multiclaude agent itself—it's the external intelligence that tells multiclaude what to do, when to do it, and how to coordinate multiple agents.

---

## Architecture: Overlord ↔ Multiclaude Communication

```
┌─────────────────────────────────────────────────────────────┐
│                    OVERLORD (Cursor)                         │
│  - Reads workflow documents                                  │
│  - Processes user input (ideas, specs, planning docs)       │
│  - Orchestrates phases                                       │
│  - Monitors progress                                         │
└──────────────────────┬──────────────────────────────────────┘
                        │
                        │ Commands & Coordination
                        │
┌───────────────────────▼──────────────────────────────────────┐
│              MULTICLAUDE WORKSPACE AGENT                     │
│  - Persistent Claude session                                 │
│  - Own worktree (doesn't conflict with workers)              │
│  - Can spawn workers                                         │
│  - Receives orchestration commands                            │
└───────────────────────┬──────────────────────────────────────┘
                        │
                        │ Spawns & Coordinates
                        │
        ┌───────────────┼───────────────┐
        │               │               │
┌───────▼──────┐ ┌──────▼──────┐ ┌─────▼──────┐
│   WORKERS    │ │  REVIEWERS  │ │MERGE-QUEUE │
│  (parallel)  │ │             │ │            │
└──────────────┘ └─────────────┘ └────────────┘
```

---

## The `check.sh` Gate: One Gate to Rule Them All

### The Core Principle

**There is one, and only one, definition of "safe to merge": `./scripts/check.sh`**

This single script is the **ratchet mechanism** that converts chaos into forward progress. It is the **single source of truth** for code quality, and it must be the **exact same script** that runs locally and in CI.

### Why This Matters

#### 1. Determinism: Same Checks, Same Results

When an agent runs `./scripts/check.sh` locally and it passes, that PR **will** pass CI. When it fails locally, it **will** fail CI. There is no drift, no "works on my machine," no surprises.

This determinism is **essential** for agent autonomy. Agents can verify their work before opening PRs, reducing back-and-forth and enabling unattended operation.

#### 2. The Ratchet Mechanism

The Brownian Ratchet philosophy requires a one-way gate:
- **Green = mergeable** → merge-queue merges automatically
- **Red = blocked** → spawn fix workers, try again
- **Progress is permanent** → merged code stays merged

`check.sh` **is** that gate. It's the mechanism that filters random agent actions into steady forward progress.

#### 3. Single Source of Truth

Without a single gate script, you get:
- ❌ Checks duplicated in CI YAML
- ❌ Different checks locally vs CI
- ❌ Checks scattered across multiple files
- ❌ Drift between environments
- ❌ "Why did CI fail? It passed locally!"

With `check.sh`:
- ✅ One script defines all checks
- ✅ Same script runs everywhere
- ✅ Version controlled with code
- ✅ Reviewable and improvable like any code
- ✅ Transparent: anyone can run it and see what passes/fails

#### 4. Agent Autonomy

Agents need clear, executable definitions of "done." `check.sh` provides:
- **Pre-PR verification**: Agents run it before opening PRs
- **Self-service debugging**: Agents can see exactly what failed
- **Reduced human intervention**: No "why did CI fail?" questions
- **Unattended operation**: System can run without human babysitting

#### 5. Evolution and Growth

The gate starts minimal and grows with the project:

**Phase 0 (Bootstrap)**:
```bash
#!/usr/bin/env bash
set -euo pipefail
echo "==> Running repo gate"
# Minimal: lint, typecheck, basic tests
npm run lint
npm run typecheck
npm test
```

**Later (Mature)**:
```bash
#!/usr/bin/env bash
set -euo pipefail
echo "==> Running repo gate"

# Code quality
npm run lint
npm run typecheck
npm run format:check

# Tests
npm run test:unit
npm run test:integration

# Security
npm audit --audit-level=moderate

# Build verification
npm run build
```

The key: **start minimal, add incrementally**. Don't make the gate so expensive that it slows development.

### Implementation Requirements

#### 1. The Script Must Exist

```bash
./scripts/check.sh
```

- Must be executable: `chmod +x scripts/check.sh`
- Must use `set -euo pipefail` for strict error handling
- Must exit with non-zero code on failure
- Must be version controlled

#### 2. CI Must Run the Exact Script

**❌ Wrong** (duplicating commands):
```yaml
# .github/workflows/ci.yml
- name: Lint
  run: npm run lint
- name: Typecheck
  run: npm run typecheck
- name: Test
  run: npm test
```

**✅ Correct** (calling the gate):
```yaml
# .github/workflows/ci.yml
- name: Run gate
  run: ./scripts/check.sh
```

**Why**: If you duplicate commands, they will drift. The CI YAML will have different checks than the script, or the script will be updated but CI won't, or vice versa. The gate script becomes meaningless.

#### 3. Agents Must Run It Before PRs

In `.multiclaude/agents/worker.md`:
```markdown
MODE: ADDITIVE (recommended)

Rules:
- Run ./scripts/check.sh before opening a PR
- If check.sh fails, fix the issues before creating PR
- Include check.sh output in PR description as verification evidence
```

#### 4. Hooks Must Enforce It

In `.multiclaude/hooks.json` (use valid format - see `palpatine/hooks.json.template`):
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/validate-bash.sh"
          }
        ]
      }
    ]
  }
}
```

**Note**: multiclaude copies this to each worktree as `.claude/settings.json`. The script `.claude/hooks/validate-bash.sh` must exist in the worktree (e.g. created during Phase 0 or copied from repo). In that script you can enforce `./scripts/check.sh` before PR-related commands, deny destructive commands (`rm -rf`, `git reset --hard`, etc.), and prevent CI weakening.

#### 5. Review Must Verify It

In `.multiclaude/agents/reviewer.md`:
```markdown
MODE: ADDITIVE (recommended)

Check:
- PR description includes check.sh output or CI link
- CI status is green (which means check.sh passed)
- If CI is red, verify fix worker was spawned
```

### Anti-Patterns to Avoid

#### ❌ Duplicating Checks in CI

**Problem**: CI YAML lists commands separately from `check.sh`
```yaml
# BAD
- run: npm run lint
- run: npm run typecheck
- run: npm test
```

**Solution**: CI calls the gate
```yaml
# GOOD
- run: ./scripts/check.sh
```

#### ❌ Different Checks Locally vs CI

**Problem**: Local `check.sh` has different checks than CI
```bash
# check.sh
npm run lint
npm test
```

```yaml
# CI also runs:
npm run typecheck  # Not in check.sh!
```

**Solution**: All checks go in `check.sh`, CI calls it

#### ❌ Skipping Checks to "Get Green"

**Problem**: Agent comments out failing checks
```bash
# npm run lint  # Commented out because it fails
npm test
```

**Solution**: Fix the underlying issues, don't weaken the gate

#### ❌ Making Checks Too Expensive Too Early

**Problem**: Gate takes 30 minutes, blocks all development
```bash
# check.sh
npm run test:all          # 20 min
npm run test:integration  # 10 min
npm run test:e2e          # 15 min
```

**Solution**: Start minimal, add expensive checks incrementally
```bash
# Phase 0: Fast feedback
npm run lint
npm run typecheck
npm run test:unit  # Fast unit tests only

# Later: Add integration tests
# npm run test:integration

# Much later: Add E2E tests
# npm run test:e2e
```

### The Gate as a Living Document

`check.sh` is **code**, not configuration. It should be:
- **Reviewed** like any code change
- **Improved** incrementally
- **Documented** with comments explaining why each check exists
- **Tested** to ensure it works in CI

Example with documentation:
```bash
#!/usr/bin/env bash
set -euo pipefail

echo "==> Running repo gate"

# Lint: Catch style issues and simple bugs
npm run lint

# Typecheck: Catch type errors before runtime
npm run typecheck

# Unit tests: Fast feedback on logic correctness
npm run test:unit

# Integration tests: Verify components work together
# (Added in Wave 1, can be slow - consider parallel execution)
npm run test:integration

# Security audit: Check for known vulnerabilities
# (Added in Wave 2, moderate level to avoid noise)
npm audit --audit-level=moderate
```

### Integration with the Workflow

The gate integrates at every phase:

**Phase 0**: Create minimal gate, verify CI runs it
**Phase 1**: Gate is part of the spec (what does "done" mean?)
**Phase 2**: Gate requirements inform task dependencies
**Phase 3**: Issues reference gate as acceptance criteria
**Phase 4**: Workers run gate before PRs
**Phase 5**: Reviewers verify gate passed
**Phase 6**: Deadlock breakers check gate status
**Phase 7**: Stop conditions include "gate passes on main"
**Phase 8**: Gate evolves as project matures

### The Gate as a Contract

`check.sh` is a **contract** between:
- **Developers/Agents**: "If I make this pass, my code is acceptable"
- **CI System**: "If this passes, the code can be merged"
- **Reviewers**: "If CI is green, the gate passed, code is safe"
- **Merge-Queue**: "Green gate = merge, red gate = block"

This contract must be **unbreakable**. Never weaken it to "get green." If the gate is too strict, **improve the code**, don't lower the bar.

### Summary: The Gate's Role

The `check.sh` gate is:
- ✅ **The ratchet** that converts chaos into progress
- ✅ **The single source of truth** for code quality
- ✅ **The enabler** of agent autonomy
- ✅ **The contract** between all parties
- ✅ **The foundation** of the entire workflow

**Without it**: Chaos, drift, surprises, manual intervention
**With it**: Determinism, autonomy, progress, confidence

**Testing Integration**: The gate executes the cumulative test suite as defined in the [Testing Strategy Document](./TESTING-STRATEGY.md). Tests are organized by waves but executed cumulatively—once a test is added, it stays in the gate forever. See [TESTING-STRATEGY.md](./TESTING-STRATEGY.md#ci-evolution-strategy) for how the gate evolves from naive full regression to wave-aware and smart incremental execution.

---

### Communication Pattern

The Overlord interacts with multiclaude through:

1. **Direct commands** to the workspace agent:
   ```bash
   multiclaude worker create "Implement #123: Add authentication"
   multiclaude message send supervisor "Wave 0 complete, ready for Wave 1"
   ```

2. **GitHub API operations** (via MCP or `gh` CLI):
   - Creating issues
   - Labeling issues with wave/area/risk tags
   - Querying issue status
   - Creating PRs (if needed)

3. **File system operations**:
   - Reading/writing spec files
   - Creating work graphs
   - Monitoring `~/.multiclaude/state.json` for agent status

4. **Workspace agent interaction**:
   - The workspace agent can spawn workers on demand
   - The workspace agent has its own worktree for Overlord-driven work
   - The workspace agent persists across sessions

---

### Project README maintenance

**The project README must stay up to date** so repo status is clear to humans and agents.

- **Phase 0**: README reflects bootstrap outcome (what the project is, how to run/set up, current status).
- **Ongoing**: When a worker’s task adds features, changes setup, or changes usage, that worker must update README (or include README updates in the same PR). The Overlord and supervisor should treat README staleness as part of “done”—e.g. remind workers to update README when their work affects it.
- **Content**: At minimum—project purpose, how to set up and run, how to run the gate (`./scripts/check.sh`), and current status (e.g. “In development”, “Wave 2 in progress”, or “Stable”).

See also: worker prompt guidance (update README when your work affects project status).

---

## Greenfield Workflow: Phase 0 → Continuous Operation

For **greenfield projects** (starting from scratch), the Overlord follows this complete sequence:

### Phase 0: Bootstrap (Determinism + Autonomy)

**Goal**: Make the repo "agent-ready" before any feature work begins through **rigorous planning** using Claude Code superpowers and Context7.

**Planning Philosophy**: Phase 0 uses **Claude Code's superpowers** (planning mode) to enforce strict planning before any coding begins. This ensures robust architecture decisions, proper tooling selection, and clear infrastructure design.

**Overlord Actions**:

#### 0.1 Planning Phase: Use Claude Code Superpowers

**Before any code is written**, the Overlord invokes Claude Code CLI with superpowers to plan the bootstrap:

1. **Invoke Claude Code with brainstorming superpower** (CRITICAL: Actually execute this command, don't just reference it):
   
   **This is an INTERACTIVE, COLLABORATIVE session. You MUST:**
   - ✅ **Actually run** `claude -p "/superpowers:brainstorm"` in a terminal
   - ✅ **Ask questions one at a time** and wait for user responses
   - ✅ **Present design sections** (200-300 words each) and validate with user
   - ✅ **Use Context7** to research best practices during the conversation
   - ✅ **Only create files AFTER** brainstorming is complete and validated
   
   ```bash
   # ACTUALLY EXECUTE THIS COMMAND in a terminal:
   claude -p "/superpowers:brainstorm
   
   I need to bootstrap a new greenfield project. Let's plan:
   - Tech stack selection and rationale
   - Project structure and organization
   - Testing infrastructure design
   - CI/CD pipeline architecture
   - Development tooling and configuration
   - Repository structure for agent-based development
   
   Use Context7 to research best practices for [tech stack] and agent-based workflows.
   "
   ```
   
   **During the brainstorming session**:
   - Ask: "What programming language should we use?" → Wait for response
   - Present: "Here's my proposed project structure: [200-300 words]" → Wait for validation
   - Iterate: Refine based on user feedback before moving to next section
   - **Checkpoint**: Do not proceed to file creation until all sections are discussed and validated
   
   **GATE 2: Brainstorming Completion Approval**
   ```
   Overlord: "We've completed our brainstorming session covering:
   - Tech stack: [selected]
   - Project structure: [validated]
   - Testing infrastructure: [validated]
   - CI/CD pipeline: [validated]
   - Development tooling: [validated]
   - Repository structure: [validated]
   
   All sections have been discussed and validated. 
   Do you approve proceeding to create the detailed implementation plan? 
   Please confirm: 'Yes, proceed to planning' or provide feedback."
   ```
   **Do not proceed until**: User explicitly confirms with "Yes, proceed to planning"
   
2. **Tech Stack Selection** (ask one question at a time, wait for response):
   - **Ask**: "What programming language/ecosystem should we use?" (e.g., Python, Go, TypeScript/Node.js, Rust)
   - **Suggest ecosystems** when appropriate: "For a CLI tool, I recommend Go or Python. Which do you prefer?"
   - **Explain trade-offs** to help user make informed decision
   - **Wait for user response** before proceeding
   - **Apply ecosystem rules** from `ECOSYSTEM-RULES/<ecosystem>/` once selected
   
   **GATE 1: Tech Stack Approval**
   ```
   Overlord: "Based on our discussion, I recommend [tech stack] because [reasons]. 
   Does this work for you? Please confirm: 'Yes, proceed with [tech stack]' or provide your selection."
   ```
   **Do not proceed until**: User explicitly confirms tech stack selection
   
3. **Use Context7 MCP** to gather context:
   - Research best practices for the selected tech stack
   - Understand patterns for agent-based development
   - Gather information on testing strategies for the stack
   - Research CI/CD patterns for the technology
   - **Note**: Context7 provides up-to-date code documentation and patterns

3. **Create detailed implementation plan** (CRITICAL: Only after brainstorming is complete and validated):
   
   ```bash
   # ACTUALLY EXECUTE THIS COMMAND:
   claude -p "/superpowers:write-plan
   
   Based on our brainstorming session and Context7 research, create a detailed implementation plan for Phase 0 bootstrap:
   - Step-by-step actions for repository initialization
   - Tech stack configuration files to create
   - Testing infrastructure setup
   - CI/CD pipeline design
   - Directory structure
   - Tooling configuration
   
   Include verification steps and rollback strategies.
   "
   ```

4. **GATE 4: Implementation Plan Approval**
   
   **Present the complete plan to the user and request explicit approval**:
   ```
   Overlord: "Here's the complete Phase 0 implementation plan:
   
   [Present full plan with all sections]
   
   This plan includes:
   - Repository initialization steps
   - Tech stack configuration
   - Testing infrastructure setup
   - CI/CD pipeline design
   - Development tooling
   - Agent configuration
   
   Do you approve this plan? Please confirm: 'Yes, approve plan' or provide feedback for changes."
   ```
   
   **Do not proceed until**: User explicitly confirms with "Yes, approve plan"

5. **GATE 5: Execution Approval**
   
   **After plan review, request explicit approval to execute**:
   ```
   Overlord: "I've reviewed the plan and ensured:
   - All bootstrap components are covered
   - Tech stack configuration is complete
   - Testing infrastructure is planned
   - CI/CD pipeline is designed
   - Agent configuration is included
   - Verification steps are present
   - Rollback strategies are defined
   - Plan aligns with workflow requirements
   
   The plan is ready for execution.
   Do you approve proceeding to Phase 0 execution? Please confirm: 'Yes, proceed to execution' or provide feedback."
   ```
   
   **Do not proceed until**: User explicitly confirms with "Yes, proceed to execution"

5. **Execute plan in controlled batches** (optional, if using execute-plan):
   ```bash
   claude -p "/superpowers:execute-plan
   
   Execute the Phase 0 bootstrap plan in batches:
   - Batch 1: Repository initialization and structure
   - Batch 2: Tech stack configuration
   - Batch 3: Testing infrastructure
   - Batch 4: CI/CD setup
   - Batch 5: Agent configuration
   
   Pause for review after each batch.
   "
   ```

**Key Principle**: **Plan first, code second**. All Phase 0 work should be planned using superpowers before execution.

#### 0.2 Execution Phase: Bootstrap Implementation

After planning is complete, execute the bootstrap:

1. **Initialize the repository** (if not already done):
   
   **If repository exists**:
   ```bash
   # Use 'multiclaude' if in PATH, or '~/go/bin/multiclaude' if not
   multiclaude repo init https://github.com/<org>/<repo>
   ```
   
   **If repository needs to be created**:
   ```bash
   # First, create the repository on GitHub
   gh repo create <repo-name> [--public|--private] [--org <org>]
   
   # Then initialize multiclaude with the new repository
   # Use 'multiclaude' if in PATH, or '~/go/bin/multiclaude' if not
   multiclaude repo init https://github.com/<org>/<repo-name>
   ```
   
   **Note**: 
   - Repository creation requires GitHub CLI (`gh`) to be authenticated. If creation fails, the Overlord should ask the user to create it manually and provide the URL.
   - If `multiclaude` is not in PATH, use the full path `~/go/bin/multiclaude` or ensure `~/go/bin` is in PATH (see [MULTICLAUDE-SETUP.md](./MULTICLAUDE-SETUP.md)).

2. **Implement tech stack configuration** (per plan and ecosystem rules):
   - Create package manager configuration (package.json, requirements.txt, Cargo.toml, go.mod, etc.)
   - Set up build system
   - Configure development dependencies
   - Create minimal project structure (per ecosystem rules from `ECOSYSTEM-RULES/<ecosystem>/project-structure.md`)
   - Apply ecosystem-specific cursor rules to `.cursorrules` or `CLAUDE.md` (from `ECOSYSTEM-RULES/<ecosystem>/cursor-rules.md`)
   - Add programming guidelines and best practices (from `ECOSYSTEM-RULES/<ecosystem>/best-practices.md`)

3. **Create testing infrastructure** (per plan, see [TESTING-STRATEGY.md](./TESTING-STRATEGY.md) for details):
   - Create `tests/` directory structure (per plan)
   - Create `contracts/` directory for interface specifications
   - Set up test runner and coverage tools (per plan)
   - Prepare for test-driven development

4. **Create the single gate**: `./scripts/check.sh`
   - See [The `check.sh` Gate](#the-checksh-gate-one-gate-to-rule-them-all) section for complete details
   - This is the **one gate to rule them all** - the ratchet mechanism
   - CI must run this exact script (not duplicate commands)
   - Template for common stacks:
     ```bash
     #!/usr/bin/env bash
     set -euo pipefail
     
     echo "==> Running repo gate"
     
     # Python example:
     # python -m ruff check .
     # python -m ruff format --check .
     # python -m mypy src tests
     # python -m pytest -q
     
     # Node/TS example:
     # npm run lint
     # npm run typecheck
     # npm test
     
     # Edit to match your stack
     ```

5. **Set up CI** (`.github/workflows/ci.yml`):
   - Must call `./scripts/check.sh` (not re-list commands)
   - Exit condition: A PR runs CI and CI runs the gate

6. **Create `CLAUDE.md`** (repo rules for all agents):
   - Start with base template (see below)
   - **Add ecosystem-specific rules** from `ECOSYSTEM-RULES/<ecosystem>/cursor-rules.md`
   - **Add programming guidelines** from `ECOSYSTEM-RULES/<ecosystem>/best-practices.md`
   - Combine with spec-first development rules
   
   Base template:
   ```markdown
   # Repo rules for AI agents
   
   ## Non-negotiables
   - Keep PRs small and focused.
   - Never weaken CI.
   - Run ./scripts/check.sh before opening a PR.
   - If blocked: create a new issue labeled blocker:* and stop.
   
   ## Spec-First Development
   - **Primary goal**: Implement the operational specification to deliver value.
   - **Tests validate**: Tests are validation tools, not implementation guides.
   - **Spec is truth**: Operational specification is the source of truth.
   - **No test gaming**: Do not access test implementation code. Implement to spec, not to pass tests.
   - **Test arbitration**: If tests fail and you believe test is wrong, create `blocker:test-arbitration` issue.
   
   ## Test Access Restrictions
   - ✅ Access: Operational spec, user manual, interface contracts (as specs), test results, test specifications
   - ❌ No access: Test implementation code, test internals, test fixtures (unless needed for requirements)
   
   ## PR hygiene
   - Link PR to issue: "Closes #123" in the PR description.
   - Include verification output (CI link or gate output).
   - Explain value delivered per operational specification.
   
   ## [ECOSYSTEM] Specific Rules
   [Content from ECOSYSTEM-RULES/<ecosystem>/cursor-rules.md]
   
   ## Programming Guidelines
   [Content from ECOSYSTEM-RULES/<ecosystem>/best-practices.md]
   ```

7. **Create multiclaude agent overrides** (`.multiclaude/agents/`):
   
   **Automated Enhancement System**: The Overlord automatically detects when multiclaude's base prompts change and applies customizations to generate enhanced prompts.
   
   **How it works**:
   - **BASE/**: Snapshot of multiclaude's default templates (versioned)
   - **CUSTOMIZATIONS/**: Overlord customizations (what to add/change)
   - **GENERATED/**: Auto-generated enhanced prompts (base + customizations)
   - Run `./scripts/update-agent-prompts.sh` to extract bases, detect changes, and regenerate
   - Copy GENERATED/ prompts to `<repo>/.multiclaude/agents/` during Phase 0
   
   **Process**:
   ```bash
   # Extract base templates and apply customizations
   ./scripts/update-agent-prompts.sh
   
   # Review generated prompts
   ls palpatine/AGENT-PROMPTS/GENERATED/
   
   # Copy to repository
   cp palpatine/AGENT-PROMPTS/GENERATED/*.md <repo>/.multiclaude/agents/
   ```
   
   **Custom worker types** (in `palpatine/AGENT-PROMPTS/CUSTOM-WORKERS/`):
   - `conflict-resolver.md` - Specialized worker for resolving merge conflicts
   - (Add more custom types as needed)
   
   **See**: [AGENT-PROMPT-MANAGEMENT.md](./AGENT-PROMPT-MANAGEMENT.md) for complete automated system documentation.

8. **Create hooks.json** (`.multiclaude/hooks.json`):
   - Use format that calls `.claude/hooks/validate-bash.sh` (see `palpatine/hooks.json.template`)
   - In that script: block destructive commands, require `./scripts/check.sh` before PR-related commands, prevent CI weakening
   - **Note**: multiclaude copies hooks.json to each worktree as `.claude/settings.json`; the validate script path is relative to the worktree (`.claude/hooks/validate-bash.sh` must exist there, e.g. created or symlinked during bootstrap)
   - **See**: [HOOKS-FIX.md](./HOOKS-FIX.md) for troubleshooting hook format issues

9. **Create auto-accept script** (for handling security prompts):
   - `scripts/auto_accept_workers.sh` to handle "Bypass Permissions" prompts
   - **Why needed**: Sometimes Claude Code shows security prompt even with `--dangerously-skip-permissions`
   - **When to use**: After creating workers, if they're stuck at the prompt
   - **See**: [WORKER-DISPATCH-GUIDE.md](./WORKER-DISPATCH-GUIDE.md) for complete usage

**Exit Criteria for Phase 0**:
- ✅ **Planning complete**: Claude Code superpowers used to create detailed bootstrap plan
- ✅ **Context7 research done**: Best practices researched for tech stack and agent workflows
- ✅ `./scripts/check.sh` exists and passes locally
- ✅ CI runs `./scripts/check.sh` successfully
- ✅ Testing infrastructure created (`tests/` and `contracts/` directories)
- ✅ `CLAUDE.md` exists with repo rules
- ✅ **README.md** reflects current project status (setup, usage, status)
- ✅ Minimal agent overrides in place
- ✅ Hooks configured (if using)
- ✅ All bootstrap work matches the plan created in 0.1

**Overlord Note**: 
- **Planning is mandatory**: Use Claude Code superpowers for all Phase 0 planning. No code should be written without a plan.
- **Context7 integration**: Use Context7 MCP to research best practices before making decisions.
- **Keep the initial gate minimal**: Add expensive tests later. The goal is to establish the ratchet mechanism (CI) before any feature work.
- **Plan review**: Review the plan before execution to ensure completeness and alignment with workflow requirements.

---

### Phase 1: Brainstorm and Converge

**Goal**: Transform fuzzy intent into an executable spec + task list.

**Input**: User provides initial ideas, brainstorming notes, or a planning document (e.g., from "Palpatine").

**Overlord Actions**:

1. **Process user input**:
   - Read initial ideas/specifications/planning documents
   - Extract goals, constraints, and requirements
   - Identify ambiguities that need clarification

2. **Use Superpowers (if available)** for brainstorming:
   - Generate candidate features
   - Explore architecture options
   - Identify risks and dependencies

3. **Use Spec Kit** to create structured artifacts:
   - **Constitution**: Project governing principles and development standards
   - **Specification**: Goals, non-goals, constraints, acceptance criteria
   - **Plan**: Architecture decisions, risks, milestones
   - **Tasks**: Small units with dependencies and verification steps
   - **Operational Specification**: How the system works, commands, interfaces, user workflows (see [TESTING-STRATEGY.md](./TESTING-STRATEGY.md#operational-specification-and-user-manual))

4. **Create Testing Strategy Document** (see [TESTING-STRATEGY.md](./TESTING-STRATEGY.md)):
   - High-level testing philosophy (in operational specification)
   - Detailed testing methodology (separate document)
   - Test battery requirements (if needed for specialized systems)
   - CI evolution strategy
   - This guides all subsequent phases and system decomposition

5. **Output artifacts**:
   - `specs/constitution.md` (or `.specs/constitution.md`)
   - `specs/specify.md` (requirements and user stories)
   - `specs/plan.md` (technical implementation plan)
   - `specs/tasks.md` (actionable task breakdown)
   - `docs/operational-specification.md` (system behavior, commands, workflows)
   - `docs/testing-strategy.md` (detailed testing methodology)

**Exit Criteria for Phase 1**:
- ✅ Constitution defines project principles
- ✅ Specification has clear goals and acceptance criteria
- ✅ Plan identifies architecture and risks
- ✅ Tasks are small, focused, and have dependencies
- ✅ Operational specification created (guides system design)
- ✅ Testing Strategy Document created (guides testing approach)

---

### Phase 2: Compile Tasks into Ordered Work Graph

**Goal**: Prevent "roof before walls" by ordering work into waves.

**Overlord Actions**:

1. **Analyze task dependencies**:
   - Identify foundation tasks (must come first)
   - Identify core functionality tasks
   - Identify feature tasks (can come later)
   - **Identify test tickets** (interface contracts come first, see [TESTING-STRATEGY.md](./TESTING-STRATEGY.md#test-ticket-organization-in-work-graph))

2. **Create `workgraph.yml`** (LLM-friendly + machine-parseable):
   ```yaml
   waves:
     - id: wave0
       name: foundation
       tasks:
     - id: T1
       issue: 101
       title: Test: Authentication interface contract
       depends_on: []
       type: test
       layer: interface
     - id: T2
       issue: 102
       title: Implement: Authentication module
       depends_on: [T1]
       type: implementation
       tdd_required: true
     - id: T3
       issue: 103
       title: Add check.sh gate
       depends_on: []
     - id: T4
       issue: 104
       title: Add CI to run check.sh
       depends_on: [T3]
     - id: wave1
       name: core
       tasks:
         - id: T3
           issue: 103
           title: Implement authentication
           depends_on: [T2]
     - id: wave2
       name: features
       tasks:
         - id: T4
           issue: 104
           title: Add user profile page
           depends_on: [T3]
   ```

3. **Apply wave labels**:
   - `wave:0` for foundation
   - `wave:1` for core
   - `wave:2` for features
   - `area:*` for functional areas
   - `risk:*` for risk level
   - `parallel` if tasks can run concurrently

**Rules**:
- A task is runnable only if all `depends_on` tasks are merged
- Within a wave, run tasks in parallel if file overlap is low
- Cap concurrency per `area:*` label to reduce conflicts

**Exit Criteria for Phase 2**:
- ✅ `workgraph.yml` exists with all tasks organized into waves
- ✅ Dependencies are correctly identified
- ✅ Tasks are labeled appropriately

---

### Phase 3: Emit GitHub Issues from Work Graph

**Goal**: Create executable GitHub issues that workers can implement.

**Overlord Actions**:

1. **For each task in `workgraph.yml`**, create a GitHub issue with:
   - **Goal**: Clear description of what needs to be done
   - **Files to touch**: Best guess of files that will be modified
   - **Acceptance checks**: How to verify the task is complete (see [TESTING-STRATEGY.md](./TESTING-STRATEGY.md#definition-of-done))
   - **Verification**: Must pass `./scripts/check.sh`
   - **Dependencies**: Links to prerequisite issues
   - **Labels**: `wave:0|1|2`, `area:*`, `risk:*`, `parallel` if safe
   - **Type label**: `test` for test tickets, `implementation` for code tickets (see [TESTING-STRATEGY.md](./TESTING-STRATEGY.md#test-ticket-organization-in-work-graph))

2. **Use GitHub API** (via MCP or `gh` CLI):
   ```bash
   gh issue create \
     --title "Add check.sh gate" \
     --body "Goal: Create scripts/check.sh that runs lint/typecheck/tests..." \
     --label "wave:0,area:infrastructure"
   ```

3. **Link dependencies**:
   - In issue body, include: "Depends on: #101, #102"
   - Use GitHub's dependency tracking if available

**Exit Criteria for Phase 3**:
- ✅ Each task has a corresponding GitHub issue
- ✅ Issues are labeled for wave scheduling
- ✅ Dependencies are linked
- ✅ Each issue can be done by one worker

---

### Phase 4: Dispatch — Run Multiclaude in Waves

**Goal**: Execute work in waves, allowing controlled chaos within each wave.

**CRITICAL: Overlord Role During Execution**

**When entering Phase 4, the Overlord's role shifts from planning to active facilitation and monitoring.** The Overlord must:

1. **Be actively engaged**:
   - Monitor multiclaude workspace agent status continuously
   - Track worker progress and PR status
   - Understand agent conversations and decisions
   - Know what's happening at all times

2. **Check work actively**:
   - Go into the repository and review code changes
   - Review PRs for quality and spec compliance
   - Verify implementations match operational specifications
   - Check that tests are appropriate and comprehensive

3. **Provide periodic status updates**:
   - Give detailed status reports regularly (not just when asked)
   - Include: current wave, active workers, PR status, blockers, progress toward goals
   - Highlight any concerns or issues that need attention
   - Summarize what's been accomplished

4. **Stay interactive**:
   - Respond to user questions promptly
   - Proactively raise concerns or questions
   - Ask for clarification when needed
   - Keep user informed of important decisions

5. **Unblock and facilitate**:
   - Identify blockers quickly
   - Help resolve issues (test arbitration, spec clarifications, etc.)
   - Ensure workers have what they need to proceed
   - Keep the workflow moving forward

6. **Ensure quality**:
   - Verify implementations match specifications
   - Ensure tests validate spec compliance
   - Check that code delivers intended value
   - Maintain spec-first development principles

**The Overlord is working for the user** - the goal is to ensure the user gets working software that matches what was specified. Be proactive, stay engaged, and keep things moving.

**See**: [EXECUTION-PHASE-PROMPT.md](./EXECUTION-PHASE-PROMPT.md) for a prompt template to provide when entering execution phases.

**Overlord Actions**:

1. **For each wave** (starting with wave 0):

   a. **Query ready issues**:
      - Find issues with label `wave:X` and status `open`
      - Filter to those whose dependencies are merged/closed
      - Order by dependencies (foundation first)

   b. **Spawn workers** (using multiclaude CLI - the proper interface):
      
      **MANDATORY: Use the combined script for ALL workers** (handles worker creation + auto-accept automatically):
      
      **The script is located at**: `scripts/create-worker-with-auto-accept.sh` in the repository root.
      
      **If the script is not in your repository**, get it from the `project-overlord` repository:
      - Location: `scripts/create-worker-with-auto-accept.sh`
      - Repository: `https://github.com/johnnyrootio/project-overlord`
      - The script must be in the `scripts/` folder at the root of your Overlord directory
      
      ```bash
      # For each ready issue in the wave:
      ./scripts/create-worker-with-auto-accept.sh <repo-name> "Implement #101: Add check.sh gate"
      ./scripts/create-worker-with-auto-accept.sh <repo-name> "Implement #102: Add CI to run check.sh"
      ```
      
      **Why this script is mandatory:**
      - Workers will be **stuck at the security prompt** without the auto-accept step
      - The script **automatically unsticks workers** by handling the security prompt
      - It's the **only reliable way** to ensure workers start properly
      
      **What the script does:**
      1. Creates the worker using multiclaude CLI
      2. Waits 5 seconds for security prompt to appear
      3. Automatically runs auto-accept script (sends Down arrow + Enter to accept)
      4. Waits for Claude Code to start
      5. Verifies Claude Code process is running
      6. Reports success/failure
      
      **Manual alternative** (NOT RECOMMENDED - Use the script instead):
      ```bash
      # Create worker
      multiclaude worker create --repo <repo-name> "Implement #101: Add check.sh gate"
      
      # Wait 5 seconds for security prompt
      sleep 5
      
      # Run auto-accept script (MANDATORY - workers will be stuck without this)
      ./scripts/auto_accept_workers.sh <repo-name>
      
      # Wait for Claude Code to start
      sleep 3
      
      # Verify workers are running
      multiclaude worker list --repo <repo-name>
      ps aux | grep claude | grep -v grep | grep -v multiclaude
      ```
      
      **CRITICAL**: The auto-accept script is **mandatory** - workers will be stuck at the security prompt without it. The combined script handles this automatically.
      
      **See**: [WORKER-DISPATCH-GUIDE.md](./WORKER-DISPATCH-GUIDE.md) for complete dispatch workflow.

   d. **Monitor progress actively**:
      - **Continuously monitor** workspace agent status and worker conversations
      - **Go into the repository** to review code changes and PRs
      - Watch for PRs to be opened
      - Monitor CI status
      - Track review status
      - **Provide periodic status updates** to user (detailed reports on progress, blockers, accomplishments)
      - Wait until PRs are merged OR blocked
      - **Understand what workers are doing** - read their conversations, check their work

   e. **Handle blocks**:
      - Convert blocks into `blocker:*` issues
      - **Test arbitration**: If `blocker:test-arbitration` issues created, supervisor arbitrates (see [TESTING-STRATEGY.md](./TESTING-STRATEGY.md#test-failure-arbitration-protocol))
      - Spawn workers to resolve blockers
      - Continue wave when unblocked

2. **Within a wave**:
   - Allow chaos (multiple workers in parallel)
   - Cap concurrency per `area:*` label to reduce conflicts
   - Let CI be the ratchet (green PRs merge, red PRs get fixed)

3. **Exit per wave**:
   - `main` branch CI is green
   - All wave issues are merged or explicitly deferred

**Dispatcher Algorithm** (LLM-consumable):
```
Repeat for each wave:
  1) Query issues with label wave:X and status open
  2) Filter to those whose dependencies are merged/closed
  3) For each ready issue, spawn worker using combined script (MANDATORY):
     ./scripts/create-worker-with-auto-accept.sh <repo-name> "Implement #<issue>: <title>"
     
     Script location: scripts/create-worker-with-auto-accept.sh in repository root
     If script not found: Get from project-overlord repo (https://github.com/johnnyrootio/project-overlord)
     
     The script automatically unsticks workers by handling the security prompt.
     
     Manual alternative (NOT RECOMMENDED - only if script unavailable):
     a) multiclaude worker create --repo <repo-name> "Implement #<issue>: <title>"
     b) sleep 5  # Wait for security prompt
     c) ./scripts/auto_accept_workers.sh <repo-name>  # MANDATORY
     d) sleep 3  # Wait for Claude Code to start
  4) Verify workers are running:
     multiclaude worker list --repo <repo-name>
     ps aux | grep claude | grep -v grep | grep -v multiclaude
  5) Monitor workers: multiclaude agent attach --repo <repo-name> <name> --read-only
  6) Wait until:
     - PRs opened + reviewed + merged OR blocked
  7) Convert blocks into blocker issues
  8) Continue until no ready issues remain
```

**CRITICAL**: 
- Always use `multiclaude` CLI commands
- **The auto-accept script is MANDATORY** - use the combined script or run it manually after creating workers
- **STRICT PROHIBITION**: NEVER use tmux directly, socket API, or access multiclaude's internal state (except explicitly approved debug scenarios with human approval)

**See**: [MULTICLAUDE-INTERFACE-RULES.md](./MULTICLAUDE-INTERFACE-RULES.md) for complete prohibitions. See [WORKER-DISPATCH-GUIDE.md](./WORKER-DISPATCH-GUIDE.md) for complete workflow.

**Exit Criteria for Phase 4**:
- ✅ All issues in wave X are merged or deferred
- ✅ `main` branch CI is green
- ✅ Ready to proceed to next wave

---

### Phase 5: Review + Fix Loop

**Goal**: Ensure quality through automated review and fix cycles, with spec compliance verification.

**CRITICAL: Overlord Role During Review Phase**

**The Overlord must remain actively engaged during the review phase**:
- Monitor review agent activity and decisions
- Check that reviews verify spec compliance (not just test passing)
- Verify that reviewers are detecting test gaming
- Ensure review quality matches requirements
- Provide status updates on review progress
- Unblock review processes if needed

**See**: [EXECUTION-PHASE-PROMPT.md](./EXECUTION-PHASE-PROMPT.md) for active facilitation requirements.

**Overlord Actions**:

1. **For each PR**:

   a. **Run review agent**:
      ```bash
      multiclaude review <pr-url>
      ```

   b. **Review agent checks** (see [AGENT-PROMPTS/reviewer.md](./AGENT-PROMPTS/reviewer.md)):
      - **Primary**: Does implementation match operational specification?
      - **Primary**: Does it deliver intended value?
      - **Secondary**: Do tests pass?
      - **Anti-pattern**: Code that passes tests but doesn't match spec

   c. **If review finds blocking items**:
      - Review agent posts comments with explicit tasks
      - Spawn a fix worker on the same branch:
        ```bash
        multiclaude worker create "Fix blocking issues in PR #123"
        ```
      - Re-run review after fixes

   d. **If no blocking items and CI is green**:
      - Merge-queue automatically merges
      - PR is closed and linked issue is closed

2. **Review reporting pattern**:
   - Review agent posts comments on PR
   - Review agent verifies spec compliance (not just test passing)
   - Review agent sends summary to merge-queue:
     ```bash
     multiclaude message send merge-queue "Review complete for PR #123. Spec compliance: ✅. Value delivery: ✅. Tests: ✅. Found 0 blocking issues. Safe to merge."
     multiclaude agent complete
     ```

3. **Test arbitration handling** (see [TESTING-STRATEGY.md](./TESTING-STRATEGY.md#test-failure-arbitration-protocol)):
   - If worker creates `blocker:test-arbitration` issue
   - Supervisor reviews and decides (see [AGENT-PROMPTS/supervisor.md](./AGENT-PROMPTS/supervisor.md))
   - Supervisor may escalate to Overlord for complex cases
   - Overlord may escalate to human for requirements clarification

**Exit Criteria for Phase 5**:
- ✅ All PRs are reviewed
- ✅ Blocking issues are fixed
- ✅ Non-blocking PRs are merged

---

### Phase 6: Deadlock Breakers (Continuous Operation)

**Goal**: Maintain forward progress by automatically resolving common deadlocks.

**Overlord Actions**:

1. **Monitor for deadlocks**:
   - Check `~/.multiclaude/state.json` for agent status
   - Detect stalls (agents alive but no progress)
   - Identify merge conflicts
   - Find duplicate work

2. **Deadlock A: Merge Conflicts**:
   - Create issue: "Resolve merge conflict between PR A and PR B"
   - Label: `blocker:merge-conflict`, `wave:X`
   - Spawn conflict-resolver worker:
     - Merges main into PR branch
     - Resolves conflicts
     - Runs gate
     - Updates PR
     - Signals completion

3. **Deadlock B: Duplicate Work**:
   - Supervisor chooses winner PR (by CI green + scope match)
   - Close/abandon duplicates with links
   - If reconciliation needed: create `blocker:reconcile` issue

4. **Deadlock C: Manual Prompt Stall**:
   - If unattended mode: run auto-accept script
   - Else: operator acknowledges prompt(s)
   - If prompts recur: file `blocker:autonomy` issue

5. **Deadlock D: Test Arbitration Stalls**:
   - If supervisor cannot decide on test arbitration
   - Supervisor escalates to Overlord
   - Overlord reviews and decides, or escalates to human
   - Create appropriate fix tickets in dependency order

**Exit Criteria for Phase 6**:
- ✅ Deadlocks are detected and resolved automatically
- ✅ System continues making progress
- ✅ No manual intervention required for common cases

---

### Phase 7: Stop Conditions (Token Safety)

**Goal**: Prevent infinite token burn by defining clear stop conditions.

**Overlord Actions**:

1. **Monitor stop conditions**:

   a. **S1: Wave Complete**:
      - No open issues with `wave:X`
      - No open PRs linked to `wave:X`
      - `main` is green
      - → Proceed to next wave or Phase 8

   b. **S2: Milestone Complete** (optional):
      - `main` green
      - All waves up to Y complete
      - Emit release notes summary
      - → Pause for human review or proceed

   c. **S3: Budget Guard**:
      - Token/cost threshold reached
      - Pause and emit summary:
        - What merged
        - What is blocked
        - Recommended next issues
      - → Wait for operator approval to continue

2. **Emit progress summary**:
   - List merged PRs
   - List blocked issues
   - List next recommended issues
   - Provide cost/token usage summary

**Exit Criteria for Phase 7**:
- ✅ Stop condition is met
- ✅ Progress summary is emitted
- ✅ System is ready for next phase or human review

---

### Phase 8: Controller Loop (Repeat from Phase 1)

**Goal**: Reduce human involvement by running the workflow as a continuous loop.

**Overlord Actions**:

1. **Repeat the cycle**:
   ```
   1) Brainstorm (Superpowers) → candidate improvements or next features
   2) Plan → architecture + milestones
   3) Spec (Spec Kit) → tasks with acceptance criteria
   4) Work graph → waves + dependencies
   5) Issues → GitHub issues + labels
   6) Dispatch (multiclaude) → workers in waves
   7) Deadlock breakers + fix loop
   8) Check stop condition; if not met, repeat
   ```

2. **Rule**: The loop must always produce concrete artifacts (specs/issues/PRs) so progress is inspectable.

3. **Human checkpoints** (optional):
   - After each wave completion
   - After milestone completion
   - When budget guard triggers
   - When explicit human decision is required

**Exit Criteria for Phase 8**:
- ✅ System is running continuously
- ✅ Progress is visible and inspectable
- ✅ Human intervention is minimal

---

## Key Principles for Overlord Orchestration

### 1. The Gate is the Ratchet

- **The `check.sh` gate is the ratchet mechanism** (see [The `check.sh` Gate](#the-checksh-gate-one-gate-to-rule-them-all) section)
- **Never weaken the gate** to "get green"
- Green gate = mergeable → merge-queue merges automatically
- Red gate = blocked → spawn fix workers
- Progress is permanent (merged code stays merged)
- The gate is the single source of truth for "safe to merge"

### 1a. Spec-First Development

- **Operational specification is the source of truth** for what to build
- **Tests validate** that implementation matches the specification
- **Workers implement to spec**, not to pass tests
- **Test access is restricted** - workers don't see test implementation code
- **Test arbitration** handles cases where tests and spec don't align (see [TESTING-STRATEGY.md](./TESTING-STRATEGY.md#test-failure-arbitration-protocol))

### 2. Small Diffs by Default

- One issue → one worker → one PR
- No drive-by refactors
- No formatting sweeps
- If more work is discovered: open a follow-up issue

### 3. Wave Scheduling Prevents Conflicts

- Foundation before core
- Core before features
- Within a wave: allow parallel work with area-based concurrency limits

### 4. Every Blocker Becomes a Work Item

- If something blocks: create `blocker:*` issue
- Dispatch worker to resolve it
- Continue the wave when unblocked

### 5. Deterministic Checks

- One gate: `./scripts/check.sh`
- CI runs the exact same script
- No duplication of check logic

---

## Overlord Command Reference

### Multiclaude Commands

```bash
# Start daemon
multiclaude start

# Initialize repo
multiclaude repo init https://github.com/<org>/<repo>

# Create worker
multiclaude worker create "Implement #123: <title>"

# Remove worker
multiclaude worker rm <worker-name>

# Review PR
multiclaude review <pr-url>

# Send message to agent
multiclaude message send <agent> "<message>"

# Signal agent completion
multiclaude agent complete

# Check daemon status
multiclaude daemon status

# View logs
multiclaude daemon logs -f
```

### GitHub Commands (via `gh` CLI or MCP)

```bash
# Create issue
gh issue create --title "<title>" --body "<body>" --label "wave:0,area:infrastructure"

# List issues by label
gh issue list --label "wave:0" --state open

# Get issue details
gh issue view <number> --json number,title,state,labels

# Create PR (if needed)
gh pr create --title "<title>" --body "Closes #<issue>" --head <branch>
```

### Spec Kit Commands (via MCP)

```bash
# Initialize spec-kit project
speckit_init

# Create constitution
speckit_constitution

# Create specification
speckit_specify

# Create plan
speckit_plan

# Generate tasks
speckit_tasks
```

---

## Variables for Project Instantiation

When instantiating this workflow for a new greenfield project, fill in:

- `REPO_URL`: `https://github.com/<org>/<repo>`
- `REPO_NAME`: Last path segment (used to find `repos[REPO_NAME]` in state.json)
- `STACK`: `python` | `node` | `go` | `rust` | `mixed`
- `GATE_CMD`: `./scripts/check.sh`
- `CI_PROVIDER`: `GitHub Actions` | other
- `WAVES`: `foundation` | `core` | `features` (+ optional `hardening`)
- `CONCURRENCY`: `N` workers, max `1` per area label (default)
- `UNATTENDED_MODE`: `true` | `false`
- `BUDGET_GUARD`: Token/cost/time threshold

---

## Example: Complete Greenfield Flow

### Initial State
- Empty repository (or minimal template)
- User provides: "I want to build a todo app with authentication"

### Phase 0: Bootstrap
1. Overlord detects stack (e.g., Node.js + TypeScript)
2. Creates `package.json`, `tsconfig.json`, basic structure
3. Creates testing infrastructure (`tests/`, `contracts/` directories)
4. Creates `scripts/check.sh` with lint/typecheck/test
5. Sets up CI to run `check.sh`
6. Creates `CLAUDE.md` with repo rules (including spec-first development rules)
7. Creates agent overrides from [AGENT-PROMPTS](./AGENT-PROMPTS/) templates

### Phase 1: Brainstorm & Converge
1. Overlord uses Spec Kit to create:
   - Constitution: "Simplicity, security, user experience"
   - Specification: "Users can create accounts, log in, manage todos"
   - Plan: "Use Next.js, PostgreSQL, JWT auth"
   - Tasks: "T1: Set up database schema", "T2: Implement auth", etc.
   - **Operational specification**: "How the system works, commands, interfaces"
   - **Testing Strategy Document**: Comprehensive testing methodology

### Phase 2: Work Graph
1. Overlord creates `workgraph.yml`:
   - Wave 0: Interface contract tests, database setup, CI, basic structure
   - Wave 1: Authentication implementation (depends on auth interface tests), user management
   - Wave 2: Integration tests, Todo CRUD, UI components
2. Test tickets precede implementation tickets (see [TESTING-STRATEGY.md](./TESTING-STRATEGY.md#test-ticket-organization-in-work-graph))
3. Implementation tickets include spec-first guidance and test access restrictions

### Phase 3: Issues
1. Overlord creates GitHub issues for each task
2. Labels with `wave:0|1|2`, `area:*`, dependencies

### Phase 4: Dispatch
1. Overlord spawns workers for Wave 0 issues
2. Workers implement per operational spec (spec-first, tests validate)
3. If test fails: Worker fixes code to match spec (normal) OR creates `blocker:test-arbitration` issue (if test seems wrong)
4. Supervisor arbitrates test issues, escalates complex cases to Overlord
5. Workers create PRs, CI runs, merge-queue merges
6. Wave 0 completes → proceed to Wave 1
7. Repeat for each wave

### Phase 5-8: Continuous Operation
1. Review loop ensures quality and spec compliance (not just test passing)
2. Test arbitration handles spec/test mismatches
3. Deadlock breakers maintain progress
4. Stop conditions prevent infinite loops
5. Controller loop repeats for new features

---

## Conclusion

The Overlord orchestrates greenfield development by:

1. **Transforming ideas into structure** (Phases 1-3)
2. **Executing work in waves** (Phase 4)
3. **Maintaining quality** (Phase 5)
4. **Breaking deadlocks** (Phase 6)
5. **Controlling costs** (Phase 7)
6. **Running continuously** (Phase 8)

The key is that the Overlord **thinks** (plans, organizes, monitors) while multiclaude agents **do** (implement, review, merge). This separation allows the Overlord to maintain high-level orchestration while agents handle the detailed execution.

For greenfield projects starting at Phase 0, the Overlord ensures the foundation is solid before any feature work begins, then systematically builds the system wave by wave, maintaining quality and progress throughout.

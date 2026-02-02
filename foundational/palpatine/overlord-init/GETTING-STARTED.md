# Getting Started: Greenfield Project with Cursor as Overlord

## Overview

This guide walks you through starting a new greenfield project using Cursor as the Overlord orchestrator, following the comprehensive workflow defined in the Palpatine documents.

**Prerequisites**:
- Cursor installed and configured
- multiclaude installed (`go install github.com/dlorenc/multiclaude/cmd/multiclaude@latest`)
- GitHub CLI (`gh`) authenticated
- tmux, git installed
- Access to Palpatine workflow documents

---

## Step 1: Initial Overlord Prompt

Open Cursor and provide this initial prompt to kick off the workflow.

**Quick Start**: See [INITIAL-OVERLORD-PROMPT.md](./INITIAL-OVERLORD-PROMPT.md) for the complete template you can copy and paste.

**Or provide this** (see [INITIAL-OVERLORD-PROMPT.md](./INITIAL-OVERLORD-PROMPT.md) for full version):

**What this does**:
- Establishes Cursor as the Overlord
- References the Palpatine documents
- Sets expectations for the workflow
- Kicks off Phase 0

---

## Step 2: Repository Setup

**For greenfield projects, the Overlord assumes you want to create a new repository.**

The Overlord will ask you:
1. **"What should we name the new repository?"** (e.g., "todo-app", "api-service")
2. **"Should it be public or private?"** (default: private)
3. **"Which GitHub organization/user should own it?"** (default: your authenticated account)

Then the Overlord will:
1. **Create the repository on GitHub** using `gh repo create [name]` (requires GitHub CLI authentication)
2. **Initialize multiclaude** with the new repository URL using `multiclaude repo init`
3. Begin Phase 0 bootstrap

**If you want to use an existing repository instead**, just tell the Overlord:
```
Use existing repository: https://github.com/your-org/your-repo
```

**Requirements**:
- GitHub CLI (`gh`) installed and authenticated
- Appropriate permissions to create repositories in the target organization/user account

**If repository creation fails**: The Overlord will ask you to create it manually, then provide the URL.

**See**: [REPOSITORY-SETUP.md](./REPOSITORY-SETUP.md) for complete details on repository setup options and troubleshooting.

---

## Step 3: Phase 0 - Bootstrap (Planning + Execution)

Phase 0 has two parts: **Planning** (using Claude Code superpowers) and **Execution** (implementing the plan).

**See**: [PHASE-0-PLANNING.md](./PHASE-0-PLANNING.md) for complete details on using superpowers and Context7.

### 3.1 Planning Phase: Use Claude Code Superpowers

**Before any code is written**, the Overlord will use Claude Code CLI with superpowers to plan the bootstrap:

1. **Brainstorming** (`/superpowers:brainstorm`):
   - Tech stack selection and rationale
   - Project structure and organization
   - Testing infrastructure design
   - CI/CD pipeline architecture
   - Development tooling and configuration

2. **Context Research** (Context7 MCP):
   - Research best practices for selected tech stack
   - Understand patterns for agent-based development
   - Gather information on testing strategies
   - Research CI/CD patterns

3. **Detailed Planning** (`/superpowers:write-plan`):
   - Step-by-step actions for repository initialization
   - Tech stack configuration files to create
   - Testing infrastructure setup
   - CI/CD pipeline design
   - Directory structure
   - Tooling configuration
   - Verification steps and rollback strategies

4. **Plan Review**:
   - Overlord reviews plan for completeness
   - Identifies missing components
   - Ensures alignment with workflow requirements

**Key Principle**: **Plan first, code second**. All Phase 0 work is planned using superpowers before execution.

### 3.2 Execution Phase: Bootstrap Implementation

After planning is complete, the Overlord will execute the bootstrap (per plan):

1. **Initialize repository** with multiclaude
2. **Create testing infrastructure**:
   - `tests/` directory structure
   - `contracts/` directory for interface specifications
3. **Create `scripts/check.sh`** (the gate)
4. **Set up CI** (`.github/workflows/ci.yml`)
5. **Create `CLAUDE.md`** with repo rules (including spec-first rules)
6. **Copy agent prompts** from Palpatine templates to repository (per plan)

### 3.2 Agent Prompts Implementation

**How agent prompts get into multiclaude**:

The Overlord will copy the prompt templates from `palpatine/AGENT-PROMPTS/` into your repository:

```bash
# Overlord creates these files in your repo:
<your-repo>/.multiclaude/agents/worker.md
<your-repo>/.multiclaude/agents/supervisor.md  
<your-repo>/.multiclaude/agents/reviewer.md
```

**Precedence** (how multiclaude loads them):
1. `<repo>/.multiclaude/agents/<agent>.md` (repo, highest priority) ← **What Overlord creates**
2. `~/.multiclaude/repos/<repo>/agents/<agent>.md` (local overrides)
3. Built-in templates (fallback)

**What this means**:
- Agent prompts are **checked into your repository**
- They're version controlled with your code
- They're shared with your team
- multiclaude automatically uses them when agents are spawned

### 3.3 Overlord Commands

The Overlord will execute commands like:

```bash
# Initialize multiclaude with your repo
multiclaude repo init https://github.com/your-org/your-repo

# Create directory structure
mkdir -p tests/{interfaces,unit,integration,system}
mkdir -p contracts/{api,internal}
mkdir -p .multiclaude/agents

# Copy agent prompts from Palpatine templates to repository
# These are augmenting overrides that work alongside multiclaude's default prompts
# They add spec-first enforcement and take precedence when conflicts arise
# As multiclaude's defaults evolve, you'll get improvements automatically (when they don't conflict)
cp /path/to/multiclaude/palpatine/AGENT-PROMPTS/worker.md .multiclaude/agents/
cp /path/to/multiclaude/palpatine/AGENT-PROMPTS/supervisor.md .multiclaude/agents/
cp /path/to/multiclaude/palpatine/AGENT-PROMPTS/reviewer.md .multiclaude/agents/

# Commit agent prompts to repository
git add .multiclaude/agents/
git commit -m "Add augmenting agent prompts for spec-first development"
git push

# Create check.sh
# Create CI workflow
# Create CLAUDE.md
# etc.
```

---

## Step 4: Phase 1 - Brainstorm & Converge

Once Phase 0 is complete, the Overlord will:

1. **Process your initial project idea**
2. **Use Spec Kit** (via MCP) to create:
   - Constitution
   - Specification
   - Plan
   - Tasks
3. **Create Operational Specification** (how the system works)
4. **Create Testing Strategy Document** (detailed testing methodology)

**Overlord will ask you**:
- "What are the key requirements?"
- "What value should this deliver?"
- "Are there any constraints?"

**Output**: Structured specifications ready for work graph creation.

---

## Step 5: Phase 2 - Work Graph

The Overlord will:

1. **Analyze task dependencies**
2. **Create `workgraph.yml`** with:
   - Test tickets (interface contracts) in Wave 0
   - Implementation tickets (with spec-first guidance) in subsequent waves
   - Integration test tickets
   - System test tickets
3. **Organize into waves**: foundation → core → features

**Example work graph structure**:
```yaml
waves:
  - id: wave0
    name: foundation
    tasks:
      - id: T1
        issue: 101
        title: Test: Authentication interface contract
        type: test
        layer: interface
      - id: T2
        issue: 102
        title: Implement: Authentication module
        depends_on: [T1]
        type: implementation
        tdd_required: true
        primary_goal: "Implement per operational spec section 3.2"
```

---

## Step 6: Phase 3 - GitHub Issues

The Overlord will:

1. **Create GitHub issues** from work graph
2. **Include spec-first guidance** in each issue
3. **Label issues** with `wave:0|1|2`, `type:test|implementation`, etc.
4. **Link dependencies** between issues

**Issue format** (created by Overlord):
```markdown
## Implement: Authentication module

**Type**: Implementation
**Wave**: 1
**Depends on**: #101 (Test: Authentication interface contract)

### Primary Goal

Implement per operational specification section 3.2.
Deliver value: Users can securely authenticate with JWT tokens.

### Implementation Guidance

**DO**:
- ✅ Read operational specification section 3.2
- ✅ Read user manual section 2.1
- ✅ Review interface contract: contracts/api/auth-api.yaml
- ✅ Write unit tests first (TDD), then implement

**DO NOT**:
- ❌ Access test implementation code from issue #101
- ❌ Implement to pass tests; implement to meet specification

### Test Validation

Tests from #101 will validate your implementation.
If tests fail and you believe test is wrong, create `blocker:test-arbitration` issue.
```

---

## Step 7: Phase 4 - Dispatch

The Overlord will:

1. **Spawn workers** for ready issues:
   ```bash
   multiclaude worker create "Implement #102: Authentication module"
   ```

2. **Monitor progress**:
   - Watch for PRs
   - Monitor CI status
   - Handle test arbitration if needed

3. **Coordinate with multiclaude workspace**:
   - The workspace agent is your interface to multiclaude
   - Overlord sends commands through workspace
   - Workspace spawns workers, monitors status

**Worker behavior** (enforced by agent prompts):
- Worker reads `.multiclaude/agents/worker.md` (spec-first guidance)
- Worker implements per operational spec
- Worker creates PR
- Worker signals completion: `multiclaude agent complete`

---

## Step 8: Ongoing Orchestration

The Overlord continues to:

1. **Monitor waves** - Track progress through each wave
2. **Handle test arbitration** - Supervisor escalates complex cases
3. **Break deadlocks** - Resolve conflicts, duplicate work, etc.
4. **Enforce spec-first** - Ensure workers implement to spec, not just pass tests
5. **Evolve CI** - Create tickets to improve `check.sh` as system matures

---

## Key Files Created by Overlord

### In Your Repository

```
your-repo/
  .multiclaude/
    agents/
      worker.md          # Copied from Palpatine templates
      supervisor.md      # Copied from Palpatine templates
      reviewer.md        # Copied from Palpatine templates
    hooks.json           # Lifecycle guardrails
  
  scripts/
    check.sh             # The gate (evolves via tickets)
  
  tests/
    interfaces/          # Interface contract tests
    unit/                # Unit tests
    integration/         # Integration tests
    system/              # System-level tests
  
  contracts/
    api/                 # API interface contracts
    internal/            # Internal interface contracts
  
  docs/
    operational-specification.md
    user-manual.md
    testing-strategy.md
  
  CLAUDE.md              # Repo rules (spec-first included)
  
  .github/
    workflows/
      ci.yml             # Runs check.sh
```

### In multiclaude State

```
~/.multiclaude/
  repos/
    your-repo/
      agents/            # Local overrides (optional)
  state.json             # Tracks agents, repos, etc.
```

---

## Overlord Communication with multiclaude

### Direct Commands

The Overlord uses multiclaude CLI commands:

```bash
# Initialize repo
multiclaude repo init https://github.com/your-org/your-repo

# Spawn workers
multiclaude worker create "Implement #102: Authentication"

# Check status
multiclaude daemon status
multiclaude daemon logs -f

# List agents
multiclaude agents list
```

### Workspace Agent Interaction

The Overlord can also interact with the workspace agent (persistent Claude session):

- Workspace has its own worktree (doesn't conflict with workers)
- Workspace can spawn workers
- Overlord can send messages to workspace
- Workspace persists across sessions

---

## Example: Complete Startup Sequence

### User Input to Cursor (Overlord)

```
I want to build a todo app with authentication. 
Use the Palpatine workflow documents to guide this project.
Repository: https://github.com/myorg/todo-app (create if needed)
```

### Overlord Response

```
I understand. I'm the Overlord orchestrator. Let me:

1. Read the workflow documents from palpatine/
2. Initialize the repository with multiclaude
3. Begin Phase 0: Bootstrap

First, let me check if the repository exists...
[Overlord checks GitHub]

Repository doesn't exist. Should I:
A) Create it now
B) You'll create it and give me the URL

Once we have the repo, I'll:
- Initialize multiclaude
- Copy agent prompts from palpatine/AGENT-PROMPTS/ to .multiclaude/agents/
- Create testing infrastructure
- Create check.sh gate
- Set up CI
- Create CLAUDE.md with spec-first rules
- Then proceed to Phase 1

Ready to start?
```

### Overlord Actions (Automated)

```bash
# 1. Initialize multiclaude
multiclaude start
multiclaude repo init https://github.com/myorg/todo-app

# 2. Create directory structure
mkdir -p tests/{interfaces,unit,integration,system}
mkdir -p contracts/{api,internal}
mkdir -p .multiclaude/agents
mkdir -p docs

# 3. Copy agent prompts (from Palpatine templates)
cp /path/to/multiclaude/palpatine/AGENT-PROMPTS/worker.md .multiclaude/agents/
cp /path/to/multiclaude/palpatine/AGENT-PROMPTS/supervisor.md .multiclaude/agents/
cp /path/to/multiclaude/palpatine/AGENT-PROMPTS/reviewer.md .multiclaude/agents/

# 4. Create check.sh (minimal, will evolve)
cat > scripts/check.sh << 'EOF'
#!/usr/bin/env bash
set -euo pipefail
echo "==> Running repo gate"
# TODO: Add tests as they're created
EOF
chmod +x scripts/check.sh

# 5. Create CI workflow
# 6. Create CLAUDE.md
# 7. Commit and push
```

---

## Agent Prompts: How They Work

### When Agents Are Spawned

1. **multiclaude spawns a worker**:
   ```bash
   multiclaude worker create "Implement #102: Authentication"
   ```

2. **multiclaude loads agent prompt**:
   - Checks: `<repo>/.multiclaude/agents/worker.md` (exists, created by Overlord)
   - Loads that prompt
   - Combines with built-in defaults (if ADDITIVE mode)
   - Sends to Claude Code

3. **Worker receives prompt**:
   - Sees spec-first guidance
   - Sees test access restrictions
   - Sees escalation process
   - Implements accordingly

### Prompt Precedence

```
1. <repo>/.multiclaude/agents/worker.md  ← Overlord creates this
2. ~/.multiclaude/repos/<repo>/agents/worker.md  (local override)
3. Built-in default (fallback)
```

**Result**: Your repo's agent prompts (created by Overlord) are used by all multiclaude agents working on that repo.

---

## Overlord Orchestration Pattern

### Continuous Loop

```
Overlord (Cursor)
  ↓
1. Read Palpatine documents (understand workflow)
  ↓
2. Execute Phase 0 (bootstrap repo)
  ↓
3. Execute Phase 1 (create specs)
  ↓
4. Execute Phase 2 (create work graph)
  ↓
5. Execute Phase 3 (create issues)
  ↓
6. Execute Phase 4 (spawn workers via multiclaude)
  ↓
7. Monitor progress, handle arbitration, break deadlocks
  ↓
8. Execute Phase 5 (review loop)
  ↓
9. Execute Phase 6 (deadlock breakers)
  ↓
10. Execute Phase 7 (stop conditions)
  ↓
11. Execute Phase 8 (controller loop - repeat from Phase 1)
```

### Overlord Commands to multiclaude

The Overlord uses these commands throughout:

```bash
# Repository management
multiclaude repo init <url>
multiclaude repo list

# Worker management
multiclaude worker create "Task description"
multiclaude worker list
multiclaude worker rm <name>

# Agent management
multiclaude agents list
multiclaude agents spawn --name <n> --class <c> --prompt-file <f>

# Status and monitoring
multiclaude daemon status
multiclaude daemon logs -f

# Messaging (for coordination)
multiclaude message send <agent> "message"
multiclaude message list
```

---

## Troubleshooting

### Agent Prompts Not Working

**Problem**: Workers not following spec-first guidance

**Check**:
1. Do files exist? `ls .multiclaude/agents/`
2. Are they in the repo? `git status .multiclaude/agents/`
3. Do they have correct format? Check for `MODE: ADDITIVE` header
4. Are they committed? `git log .multiclaude/agents/`

**Fix**: Overlord should verify prompts are created and committed in Phase 0.

### multiclaude Not Finding Prompts

**Problem**: multiclaude using built-in prompts instead of repo prompts

**Check**:
```bash
multiclaude agents list
# Should show your repo's prompts
```

**Fix**: Ensure `.multiclaude/agents/` directory exists in repo root, not just locally.

### Overlord Can't Access Palpatine Documents

**Problem**: Cursor can't find workflow documents

**Solution**: 
- Ensure Palpatine directory is in your workspace
- Or provide full path to documents in initial prompt
- Or copy Palpatine documents to your project directory

---

## Next Steps After Getting Started

Once Phase 0 is complete:

1. **Overlord proceeds automatically** through phases
2. **You provide input** when needed (requirements clarification, decisions)
3. **Overlord orchestrates** the entire workflow
4. **System builds itself** following the workflow

**You can**:
- Monitor progress via `tmux attach -t mc-<repo-name>`
- Check PRs: `gh pr list`
- Review Overlord's decisions
- Provide guidance when Overlord asks

---

## Summary

**To start a new greenfield project**:

1. **Open Cursor**
2. **Provide initial Overlord prompt** (see Step 1)
3. **Provide repository URL** (or create new)
4. **Let Overlord execute Phase 0** (bootstrap)
5. **Provide project requirements** when asked
6. **Let Overlord orchestrate** the complete workflow

**Agent prompts**:
- Created by Overlord in Phase 0
- Stored in `<repo>/.multiclaude/agents/`
- **Augmenting overrides** that work alongside multiclaude's defaults
- Automatically used by multiclaude (appends as "Repository-specific instructions")
- Version controlled with your code
- **Future-proof**: Get multiclaude default improvements automatically (when they don't conflict)
- **Authoritative**: Take precedence when conflicts arise (use judgment)

**Result**: A fully orchestrated greenfield project following the comprehensive workflow, with spec-first development enforced throughout.

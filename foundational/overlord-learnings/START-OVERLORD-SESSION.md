# Starting a New Overlord Session: Step-by-Step Guide

This guide walks you through starting a new Cursor session to act as the Overlord for your greenfield project.

## Prerequisites Check

Before starting, verify:

1. **multiclaude is installed and accessible**:
   ```bash
   multiclaude version
   # Should output: multiclaude 0.0.0-dev
   # If not found, use: ~/go/bin/multiclaude version
   ```

2. **GitHub CLI is authenticated**:
   ```bash
   gh auth status
   # Should show you're logged in
   ```

3. **You have your project specification ready**

---

## Step 1: Clone the Project Overlord Repository

In your new Cursor session, clone the repository to a project-specific directory:

```bash
# Clone to a project-specific directory name
git clone https://github.com/johnnyrootio/project-overlord.git robotic-barista-overlord
cd robotic-barista-overlord
```

**Why**: 
- This gives Cursor access to all the workflow documents and templates
- The project-specific directory name (`robotic-barista-overlord`) makes it clear this is the overlord setup for the robotic-barista project
- The actual `robotic-barista` repository will be created separately by the Overlord

**Alternative**: If you prefer a generic name, you can clone to `project-overlord` and create a workspace:
```bash
git clone https://github.com/johnnyrootio/project-overlord.git
cd project-overlord
mkdir -p workspaces/robotic-barista
cd workspaces/robotic-barista
# Your spec will go in ../../greenfield-specs/robotic-barista.md
```

---

## Step 2: Create Your Project Specification

Create your project spec file in the `greenfield-specs/` directory:

```bash
# Option 1: Copy the template
cp greenfield-specs/template.md greenfield-specs/robotic-barista.md
# Then edit with your project details

# Option 2: Use the robotic-barista example as a starting point (recommended)
cp examples/robotic-barista-spec.md greenfield-specs/robotic-barista.md
# Then customize as needed for your specific requirements
```

**File location**: `greenfield-specs/robotic-barista.md` (relative to the cloned `robotic-barista-overlord` directory)

**Note**: The `greenfield-specs/` folder is in the overlord repository. The actual `robotic-barista` project repository will be created separately by the Overlord during Phase 0.

**What to include**:
- Project name: robotic-barista
- Description and goals
- Key requirements
- Constraints (tech stack, platform, etc.)
- Success criteria

**Examples**:
- See `examples/robotic-barista-spec.md` for a complete robotic-barista example
- See `greenfield-specs/example-todo-app.md` for a todo app example

---

## Step 3: Open Cursor and Provide Initial Prompt

In Cursor, provide this initial prompt (customize as needed):

```
I want to start a new greenfield project using the multiclaude agentic workflow.

**Project**: robotic-barista
**Goal**: [Your goal - e.g., "An autonomous robotic barista system"]

**Workflow Documents** (located in `multiclaude/palpatine/`):
- OVERLORD-GREENFIELD-WORKFLOW.md - Complete workflow orchestration guide
- MULTICLAUDE-SETUP.md - multiclaude installation and usage on this system
- TESTING-STRATEGY.md - Comprehensive testing philosophy
- SPEC-FIRST-ENFORCEMENT.md - Spec-first development enforcement
- PHASE-0-PLANNING.md - Phase 0 planning with Claude Code superpowers
- REPOSITORY-SETUP.md - Repository setup guide
- GETTING-STARTED.md - Practical getting started guide
- AGENT-PROMPTS/ - Agent prompt templates (worker.md, supervisor.md, reviewer.md)

**Your Role**: You are the Overlord orchestrator. Your job is to:

1. **Read and internalize** the workflow documents from `multiclaude/palpatine/`
2. **Read my project specification** from `greenfield-specs/robotic-barista.md`
3. **Repository Setup** (for greenfield projects, we create a new repository):
   - Ask me: "What should we name the new repository?" (I'll say: "robotic-barista")
   - Ask me: "Should it be public or private?" (I'll tell you)
   - Ask me: "Which GitHub organization/user should own it?" (I'll tell you)
   - **Then create the repository** using `gh repo create [name]` and initialize multiclaude
   - **If repository creation fails**: Ask me to create it manually and provide the URL
4. **Guide me through Phase 0** (Bootstrap) - use Claude Code superpowers for planning:
   - Use `/superpowers:brainstorm` to plan the bootstrap
   - Use Context7 MCP to research best practices
   - Use `/superpowers:write-plan` to create detailed implementation plan
   - Review plan, then execute
5. **Proceed through all phases** systematically:
   - Phase 1: Brainstorm & Converge (create specs)
   - Phase 2: Work Graph (organize tasks into waves)
   - Phase 3: GitHub Issues (create executable issues)
   - Phase 4: Dispatch (spawn workers via multiclaude)
   - Phase 5: Review + Fix Loop
   - Phase 6: Deadlock Breakers
   - Phase 7: Stop Conditions
   - Phase 8: Controller Loop (continuous operation)
6. **Use multiclaude's workspace agent** to coordinate work
7. **Enforce spec-first development** throughout (see SPEC-FIRST-ENFORCEMENT.md)

**Key Principles**:
- Operational specification is the source of truth
- Tests validate implementation, they don't guide it
- Workers implement to deliver value per spec, not to pass tests
- Agent prompts enforce this (you'll copy them from AGENT-PROMPTS/ to repo)

**Important**: 
- Phase 0 uses Claude Code superpowers for planning. No code should be written without a plan created using `/superpowers:brainstorm` and `/superpowers:write-plan`. 
- Use Context7 MCP to research best practices before making decisions.
- **multiclaude commands**: Use `multiclaude` if it's in PATH, or `~/go/bin/multiclaude` if not. Check MULTICLAUDE-SETUP.md for details.
- Before starting, verify multiclaude is accessible: `multiclaude version` or `~/go/bin/multiclaude version`

**Phase 0 Checklist** (you'll execute):
- [ ] **PLANNING PHASE** (use Claude Code superpowers):
  - [ ] Invoke Claude Code CLI with `/superpowers:brainstorm` to plan bootstrap
  - [ ] Use Context7 MCP to research best practices for tech stack
  - [ ] Create detailed implementation plan with `/superpowers:write-plan`
  - [ ] Review and refine the plan before execution
- [ ] **REPOSITORY SETUP**:
  - [ ] Ask user for repository name, visibility, and owner
  - [ ] Create repository using `gh repo create [name]`
  - [ ] Initialize multiclaude with `multiclaude repo init [url]` (or `~/go/bin/multiclaude repo init [url]` if not in PATH)
- [ ] **EXECUTION PHASE** (implement per plan):
  - [ ] Create testing infrastructure (tests/, contracts/ directories)
  - [ ] Create scripts/check.sh (the gate)
  - [ ] Set up CI to run check.sh
  - [ ] Create CLAUDE.md with repo rules (including spec-first rules)
  - [ ] Copy agent prompts from AGENT-PROMPTS/ to <repo>/.multiclaude/agents/
  - [ ] Create hooks.json (lifecycle guardrails)
  - [ ] Verify everything is committed and pushed

Let's start! First, read the workflow documents from `multiclaude/palpatine/OVERLORD-GREENFIELD-WORKFLOW.md`, then read my project specification from `greenfield-specs/robotic-barista.md`.
```

---

## Step 4: What Happens Next

After you provide the prompt, Cursor (as Overlord) will:

1. **Read the workflow documents** to understand the complete process
2. **Read your specification** from `greenfield-specs/robotic-barista.md`
3. **Ask you about the repository**:
   - Name: "robotic-barista"
   - Visibility: public or private
   - Owner: your GitHub username or organization
4. **Create the repository** on GitHub
5. **Begin Phase 0 planning** using Claude Code superpowers
6. **Execute Phase 0** bootstrap
7. **Proceed through all phases** systematically

---

## Step 5: During the Session

### What You'll Be Asked

- **Repository details**: Name, visibility, owner
- **Clarifications**: If the spec needs more detail
- **Decisions**: At key decision points in the workflow
- **Approvals**: For major steps or when human input is needed

### What the Overlord Handles

- Reading and understanding the workflow
- Creating the repository
- Planning with superpowers
- Executing bootstrap
- Creating specifications
- Organizing work into waves
- Creating GitHub issues
- Spawning workers via multiclaude
- Monitoring progress
- Breaking deadlocks

---

## Quick Reference

### File Locations

**In the overlord repository** (`robotic-barista-overlord/`):
- **Your spec**: `greenfield-specs/robotic-barista.md`
- **Example spec**: `examples/robotic-barista-spec.md` (reference example)
- **Workflow docs**: `multiclaude/palpatine/`
- **Agent prompts**: `multiclaude/palpatine/AGENT-PROMPTS/`

**Separate project repository** (created by Overlord):
- **Actual project**: `robotic-barista/` (will be created on GitHub and cloned locally)
- This is where the actual code, tests, and implementation will live

### Key Commands the Overlord Will Use

```bash
# Verify multiclaude
multiclaude version  # or ~/go/bin/multiclaude version

# Create repository
gh repo create robotic-barista --private

# Initialize multiclaude
multiclaude repo init https://github.com/johnnyrootio/robotic-barista

# Start daemon (if needed)
multiclaude daemon start

# Spawn workers (later phases)
multiclaude worker create "Implement #123: Feature X"
```

---

## Troubleshooting

### Cursor Can't Find Files

**Problem**: Cursor says it can't find workflow documents or spec

**Solution**:
- Verify you're in the `project-overlord` directory
- Use absolute paths if needed
- Check file names match exactly (case-sensitive)

### multiclaude Not Found

**Problem**: Overlord can't find multiclaude

**Solution**:
- Check: `multiclaude version` or `~/go/bin/multiclaude version`
- If not found, see `multiclaude/palpatine/MULTICLAUDE-SETUP.md`
- Overlord should use `~/go/bin/multiclaude` if not in PATH

### Repository Creation Fails

**Problem**: `gh repo create` fails

**Solution**:
- Check: `gh auth status`
- Create repository manually on GitHub.com
- Provide the URL to the Overlord

---

## Summary

1. ✅ Clone `project-overlord` repository
2. ✅ Create `greenfield-specs/robotic-barista.md` with your spec
3. ✅ Open Cursor and provide the initial prompt above
4. ✅ Answer questions about repository setup
5. ✅ Let the Overlord orchestrate!

**Ready?** Start with Step 1!

# Phase 0 Planning: Using Claude Code Superpowers and Context7

## Overview

Phase 0 uses **Claude Code's superpowers** (planning mode) to enforce strict planning before any coding begins. This ensures robust architecture decisions, proper tooling selection, and clear infrastructure design.

## Why Planning First?

**Problem**: Jumping straight to code without planning leads to:
- ❌ Poor architecture decisions
- ❌ Missing critical components
- ❌ Inconsistent patterns
- ❌ Technical debt from the start
- ❌ Rework and refactoring

**Solution**: Use Claude Code superpowers to plan thoroughly before writing any code.

## Tools Available

### 1. Claude Code Superpowers

Claude Code provides three main superpower commands:

- **`/superpowers:brainstorm`** - Refines rough ideas before coding
- **`/superpowers:write-plan`** - Creates detailed implementation plans
- **`/superpowers:execute-plan`** - Runs plans in batches with review checkpoints

### 2. Context7 MCP

Context7 is an MCP server that provides:
- Up-to-date code documentation
- Best practices for tech stacks
- Patterns and architectural guidance
- Testing strategies
- CI/CD patterns

**Access**: Available in Cursor via MCP configuration.

## Phase 0 Planning Workflow

### Step 1: Brainstorming

**Invoke Claude Code CLI with brainstorming superpower**:

```bash
# In the repository directory
claude -p "/superpowers:brainstorm

I need to bootstrap a new greenfield project. Let's plan:

**Project Context**:
- Project: [Project name/description]
- Tech Stack: [If known, or "to be determined"]
- Goals: [What we want to build]

**Planning Areas**:
1. Tech stack selection and rationale
   - What technologies should we use?
   - Why these choices?
   - What are the trade-offs?

2. Project structure and organization
   - Directory structure
   - Code organization patterns
   - Separation of concerns

3. Testing infrastructure design
   - Test framework selection
   - Test organization (unit, integration, system)
   - Coverage tools
   - Test data management

4. CI/CD pipeline architecture
   - CI platform (GitHub Actions, GitLab CI, etc.)
   - Pipeline stages
   - Quality gates
   - Deployment strategy

5. Development tooling and configuration
   - Linters and formatters
   - Type checkers
   - Build tools
   - Development dependencies

6. Repository structure for agent-based development
   - multiclaude configuration
   - Agent prompts location
   - Hooks and guardrails
   - Documentation structure

Use Context7 to research best practices for [tech stack] and agent-based workflows.
"
```

### Step 2: Context Research (Context7)

**Use Context7 MCP to gather context**:

The Overlord should use Context7 to research:
- Best practices for the selected tech stack
- Patterns for agent-based development
- Testing strategies for the technology
- CI/CD patterns
- Tooling recommendations

**Example Context7 queries**:
- "What are best practices for [tech stack] project structure?"
- "How should I organize tests in a [tech stack] project?"
- "What CI/CD patterns work well for [tech stack]?"
- "What testing frameworks are recommended for [tech stack]?"

### Step 3: Detailed Planning

**Create detailed implementation plan**:

```bash
claude -p "/superpowers:write-plan

Based on our brainstorming and Context7 research, create a detailed implementation plan for Phase 0 bootstrap:

**Plan Structure**:
1. Repository Initialization
   - Steps to initialize multiclaude
   - Repository structure creation
   - Initial commit setup

2. Tech Stack Configuration
   - Package manager setup
   - Build system configuration
   - Development dependencies
   - Configuration files

3. Testing Infrastructure
   - Test framework setup
   - Directory structure (tests/, contracts/)
   - Test runner configuration
   - Coverage tool setup

4. CI/CD Pipeline
   - CI platform configuration
   - Pipeline definition
   - Quality gates
   - check.sh integration

5. Development Tooling
   - Linter configuration
   - Formatter configuration
   - Type checker setup
   - Pre-commit hooks (if applicable)

6. Agent Configuration
   - multiclaude agent prompts
   - Hooks configuration
   - CLAUDE.md creation

**Requirements**:
- Include verification steps for each action
- Include rollback strategies
- Specify file locations and contents
- Include commands to run
- Specify dependencies between steps
"
```

### Step 4: Plan Review

**Review and refine the plan**:

The Overlord should:
1. Review the plan for completeness
2. Identify any missing components
3. Ensure alignment with workflow requirements
4. Refine based on project-specific needs
5. Verify all Phase 0 exit criteria are addressed

**Checklist**:
- [ ] All bootstrap components covered
- [ ] Tech stack configuration complete
- [ ] Testing infrastructure planned
- [ ] CI/CD pipeline designed
- [ ] Agent configuration included
- [ ] Verification steps present
- [ ] Rollback strategies defined
- [ ] Aligned with workflow requirements

### Step 5: Execute Plan (Optional)

**If using execute-plan superpower**:

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

**Note**: The Overlord can also execute the plan manually, following the detailed steps.

## Integration with Workflow

### Phase 0 Structure

```
Phase 0: Bootstrap
├── 0.1 Planning Phase (THIS DOCUMENT)
│   ├── Brainstorming (superpowers:brainstorm)
│   ├── Context Research (Context7 MCP)
│   ├── Detailed Planning (superpowers:write-plan)
│   └── Plan Review
└── 0.2 Execution Phase
    ├── Repository initialization
    ├── Tech stack configuration
    ├── Testing infrastructure
    ├── CI/CD setup
    └── Agent configuration
```

### Exit Criteria

Phase 0 is complete when:
- ✅ **Planning complete**: Claude Code superpowers used to create detailed bootstrap plan
- ✅ **Context7 research done**: Best practices researched for tech stack and agent workflows
- ✅ All execution steps completed per plan
- ✅ All Phase 0 exit criteria met (see OVERLORD-GREENFIELD-WORKFLOW.md)

## Best Practices

### 1. Don't Skip Planning

**Bad**: Jump straight to creating files
```bash
# DON'T DO THIS
mkdir tests
touch check.sh
# ... start coding
```

**Good**: Plan first, then execute
```bash
# DO THIS
claude -p "/superpowers:brainstorm ..."
claude -p "/superpowers:write-plan ..."
# Review plan
# Then execute per plan
```

### 2. Use Context7 for Research

**Bad**: Guess at best practices
```bash
# DON'T DO THIS
# "I think we should use pytest for Python"
```

**Good**: Research first
```bash
# DO THIS
# Use Context7: "What are best practices for Python testing in 2025?"
# Then make informed decisions
```

### 3. Review Plans Before Execution

**Bad**: Execute plan without review
```bash
# DON'T DO THIS
# Create plan → Immediately execute
```

**Good**: Review and refine
```bash
# DO THIS
# Create plan → Review for completeness → Refine → Execute
```

### 4. Document Decisions

**Bad**: Make decisions without documentation
```bash
# DON'T DO THIS
# Choose tech stack → Don't document why
```

**Good**: Document rationale
```bash
# DO THIS
# Choose tech stack → Document in plan why → Include in README/CLAUDE.md
```

## Example: Complete Phase 0 Planning Session

```bash
# 1. Brainstorming
claude -p "/superpowers:brainstorm
I need to bootstrap a Python FastAPI project with PostgreSQL.
Plan: tech stack, structure, testing, CI/CD, tooling.
Use Context7 to research FastAPI best practices.
"

# 2. Context Research (via Context7 MCP in Cursor)
# Overlord queries Context7:
# - "FastAPI project structure best practices"
# - "Python testing frameworks comparison"
# - "GitHub Actions CI/CD for Python"
# - "Python linting and formatting tools"

# 3. Detailed Planning
claude -p "/superpowers:write-plan
Based on brainstorming and Context7 research, create detailed plan:
- FastAPI project structure
- pytest configuration
- ruff for linting/formatting
- mypy for type checking
- GitHub Actions CI
- check.sh gate script
Include verification steps.
"

# 4. Plan Review
# Overlord reviews plan, ensures:
# - All components covered
# - Aligned with workflow
# - Verification steps present

# 5. Execution
# Overlord executes plan step-by-step
```

## Troubleshooting

### Superpowers Not Available

**Problem**: Claude Code superpowers not working

**Solution**:
- Verify Claude Code CLI is installed: `claude --version`
- Check if superpowers plugin is enabled
- Try using Cursor's built-in planning features as alternative

### Context7 Not Accessible

**Problem**: Context7 MCP not responding

**Solution**:
- Verify Context7 MCP is configured in Cursor's MCP settings
- Check MCP server is running
- Use web search as fallback for research

### Plan Too Vague

**Problem**: Generated plan lacks detail

**Solution**:
- Be more specific in brainstorming prompt
- Ask for more detail in write-plan prompt
- Use Context7 to gather more context first
- Manually refine the plan

## Summary

Phase 0 planning using Claude Code superpowers and Context7 ensures:
- ✅ Robust architecture decisions
- ✅ Proper tooling selection
- ✅ Clear infrastructure design
- ✅ Alignment with best practices
- ✅ Comprehensive bootstrap plan
- ✅ Reduced technical debt

**Remember**: Plan first, code second. This investment in planning pays off throughout the project lifecycle.

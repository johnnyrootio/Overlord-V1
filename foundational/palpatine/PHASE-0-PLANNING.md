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

**CRITICAL**: This workflow includes explicit phase gates that require human approval. See [PHASE-GATES.md](./PHASE-GATES.md) for complete gate requirements.

**CRITICAL**: Before presenting any design section, you MUST follow the document internalization process. See [DOCUMENT-INTERNALIZATION.md](./DOCUMENT-INTERNALIZATION.md) for complete requirements.

### Step 1: Brainstorming

**CRITICAL: This is an INTERACTIVE, COLLABORATIVE process. You MUST actually run the command and have a conversation with the user.**

**What NOT to do**:
- ❌ Don't just reference the command in documentation
- ❌ Don't create spec files without brainstorming first
- ❌ Don't skip the interactive session
- ❌ Don't assume the example spec is the final spec

**What TO do**:
- ✅ **Actually execute** `claude -p "/superpowers:brainstorm"` in a terminal
- ✅ **Ask questions one at a time** and wait for user responses
- ✅ **Present design sections** (200-300 words each) and validate with user
- ✅ **Only create files after validation** - brainstorming must be complete and validated first

**How to conduct the brainstorming session**:

1. **Actually run the command** (don't just reference it):
   ```bash
   # In the repository directory, ACTUALLY EXECUTE THIS:
   claude -p "/superpowers:brainstorm
   
   I need to bootstrap a new greenfield project. Let's plan:
   
   **Project Context**:
   - Project: [Project name/description]
   - Tech Stack: [If known, or "to be determined"]
   - Goals: [What we want to build]
   
   **Planning Areas**:
   1. Tech stack selection and rationale
   2. Project structure and organization
   3. Testing infrastructure design
   4. CI/CD pipeline architecture
   5. Development tooling and configuration
   6. Repository structure for agent-based development
   
   Use Context7 to research best practices for [tech stack] and agent-based workflows.
   "
   ```

2. **During the brainstorming session**:
   - **Ask questions one at a time**: "What programming language should we use?" → Wait for response
   - **Before presenting any design section, follow document internalization**:
     - Re-read relevant workflow documents (TESTING-STRATEGY.md, ECOSYSTEM-RULES/, etc.)
     - Identify all required components/layers
     - Verify your design includes each with proper emphasis
     - Cross-reference your design against the documents
     - See [DOCUMENT-INTERNALIZATION.md](./DOCUMENT-INTERNALIZATION.md) for complete process
   - **Present design sections**: After internalization, present a 200-300 word design section with explicit cross-references (e.g., "Per TESTING-STRATEGY.md section X.Y, here's my proposed testing strategy...")
   - **Validate with user**: "Does this structure work for you? Any changes needed?"
   - **Iterate**: Refine based on user feedback before moving to next section
   - **Use Context7**: Research best practices and incorporate findings into the discussion

3. **Checkpoint before proceeding**:
   - ✅ All planning areas discussed
   - ✅ User has validated each design section
   - ✅ Tech stack selected and validated
   - ✅ Architecture decisions made and confirmed
   - ✅ **ONLY THEN** proceed to creating spec files or implementation plan

**Example flow**:
```
Overlord: "Let's start brainstorming. What programming language should we use?"
User: "Python"
Overlord: "Great! For a Python project, I recommend using pytest for testing. Here's my proposed testing structure: [200-300 words]. Does this work for you?"
User: "Yes, but I'd like to add integration tests too"
Overlord: "Perfect! I'll include integration tests. Now let's discuss the project structure: [200-300 words]. Thoughts?"
User: "Looks good"
Overlord: [Continues with next section...]
```

**Remember**: Brainstorming is a **conversation**, not a document creation exercise. Files are created AFTER brainstorming is complete and validated.

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

**CRITICAL: Only proceed to this step AFTER Gate 2 approval (brainstorming completion approved by user).**

**Create detailed implementation plan**:

1. **Actually run the command** (don't just reference it):
   ```bash
   # ACTUALLY EXECUTE THIS COMMAND:
   claude -p "/superpowers:write-plan
   
   Based on our brainstorming session and Context7 research, create a detailed implementation plan for Phase 0 bootstrap:
   
   **Plan Structure**:
   1. Repository Initialization
   2. Tech Stack Configuration
   3. Testing Infrastructure
   4. CI/CD Pipeline
   5. Development Tooling
   6. Agent Configuration
   
   Include verification steps, rollback strategies, file locations, commands, and dependencies.
   "
   ```

2. **GATE 4: Implementation Plan Approval**

   **Present the plan to the user and request explicit approval**:
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

3. **Only after Gate 4 approval**: Proceed to plan review

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

**Bad**: Reference commands without executing them
```bash
# DON'T DO THIS
# "I should use /superpowers:brainstorm" (but never actually run it)
# Then immediately create spec files
```

**Good**: Actually run commands and have interactive sessions
```bash
# DO THIS
# 1. ACTUALLY EXECUTE the command:
claude -p "/superpowers:brainstorm ..."

# 2. Have an interactive conversation:
# - Ask questions one at a time
# - Present design sections (200-300 words)
# - Get user validation
# - Iterate based on feedback

# 3. ONLY AFTER brainstorming is complete and validated:
claude -p "/superpowers:write-plan ..."

# 4. Present plan to user and get approval

# 5. THEN execute per plan
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

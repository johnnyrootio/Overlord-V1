# MCP Tools Integration: Systematic Usage Guide

## Overview

The Overlord and multiclaude agents have access to several MCP (Model Context Protocol) servers that provide powerful capabilities for tracking, learning, and improving the workflow. These tools must be used proactively, not just reactively.

## Available MCP Tools

### 1. Reflection MCP
**Purpose**: Learn from past experiences, store lessons, retrieve similar episodes

**Key Functions**:
- `retrieve_episodes(task, context)` - Get similar past experiences
- `store_episode(task, context, outcome, lessons)` - Save what was learned
- `reflect_on_failure(task, context, error)` - Analyze failures
- `get_common_lessons(task)` - Get patterns from past work
- `generate_improved_attempt(task, context, past_episodes)` - Get guidance based on past

### 2. Context7 MCP
**Purpose**: Research best practices, up-to-date documentation, patterns

**Key Functions**:
- Research best practices for tech stacks
- Get architectural patterns
- Find testing strategies
- Discover CI/CD patterns

### 3. SpecKit MCP
**Purpose**: Manage operational specifications, create specs from requirements

**Key Functions**:
- Create specifications from requirements
- Manage spec documents
- Validate spec completeness

### 4. GitHub MCP
**Purpose**: Repository operations, issue management, PR operations

**Key Functions**:
- Create repositories
- Create issues
- Manage PRs
- Repository operations

### 5. Firecrawl MCP
**Purpose**: Web scraping and content extraction

**Key Functions**:
- Scrape web content
- Extract information from URLs
- Research external resources

### 6. Probe MCP
**Purpose**: Code analysis and exploration

**Key Functions**:
- Analyze codebases
- Explore code structure
- Understand dependencies

## Systematic Usage Strategy

### Proactive Retrieval Pattern

**Before starting any major task, retrieve similar past episodes:**

```python
# Example: Before brainstorming session
episodes = retrieve_episodes(
    task="brainstorming session",
    context={
        "project_type": "greenfield",
        "tech_stack": "Python",
        "phase": "Phase 0"
    }
)

# Review episodes for:
# - What worked well
# - Common mistakes to avoid
# - Patterns to follow
# - Lessons learned
```

**When to retrieve**:
- Before brainstorming → `retrieve_episodes(task="brainstorming session")`
- Before creating specs → `retrieve_episodes(task="spec creation")`
- Before testing work → `retrieve_episodes(task="testing strategy design")`
- Before tech stack selection → `retrieve_episodes(task="tech stack selection")`
- Before Phase 0 execution → `retrieve_episodes(task="Phase 0 bootstrap")`

### Reactive Storage Pattern

**After any significant event, store what was learned:**

```python
# After a failure
reflect_on_failure(
    task="brainstorming session",
    context={
        "what_was_attempted": "Skipped interactive brainstorming",
        "what_went_wrong": "Created files without user validation"
    },
    error="Did not follow INTERACTIVE-BRAINSTORMING.md requirements"
)

# After a success
store_episode(
    task="testing strategy design",
    context={
        "tech_stack": "Python",
        "layers_covered": ["contract", "unit", "integration", "black_box"]
    },
    outcome="success",
    lessons=[
        "Re-read TESTING-STRATEGY.md before presenting",
        "Give all 4 layers equal emphasis",
        "Cross-reference document sections explicitly"
    ]
)
```

**When to store**:
- After failures → `reflect_on_failure()` then `store_episode()`
- After successes → `store_episode(outcome="success")`
- After phase completion → `store_episode()` with phase lessons
- After user feedback → `store_episode()` with feedback incorporated

### Checkpoint Pattern

**At each phase gate and checkpoint, use MCP tools:**

1. **Retrieve relevant episodes** before proceeding
2. **Review common lessons** for the task type
3. **Store checkpoint state** after completion
4. **Reflect on progress** before moving forward

## Integration with Workflow Phases

### Phase 0: Bootstrap

#### Before Tech Stack Selection
```python
# Retrieve past tech stack selection episodes
episodes = retrieve_episodes(task="tech stack selection")
lessons = get_common_lessons(task="tech stack selection")

# Review:
# - What factors influenced past decisions?
# - What trade-offs were considered?
# - What worked well?
```

#### Before Brainstorming Session
```python
# Retrieve past brainstorming episodes
episodes = retrieve_episodes(
    task="brainstorming session",
    context={"phase": "Phase 0"}
)

# Review:
# - Common mistakes (e.g., skipping interactive session)
# - What made sessions successful?
# - Patterns to follow
```

#### After Brainstorming Session
```python
# Store what was learned
store_episode(
    task="brainstorming session",
    context={
        "tech_stack": selected_stack,
        "sections_covered": ["structure", "testing", "ci_cd", "tooling"],
        "user_validations": validation_count
    },
    outcome="success",
    lessons=[
        "Actually ran claude -p '/superpowers:brainstorm'",
        "Asked questions one at a time",
        "Presented sections and got validation",
        "Used Context7 during conversation"
    ]
)
```

#### Before Testing Strategy Design
```python
# Retrieve past testing strategy episodes
episodes = retrieve_episodes(task="testing strategy design")

# Review:
# - Common mistakes (e.g., missing black box tests)
# - What layers were covered?
# - How were layers emphasized?
```

#### After Testing Strategy Design
```python
# Store what was learned
store_episode(
    task="testing strategy design",
    context={
        "layers_covered": ["contract", "unit", "integration", "black_box"],
        "emphasis_levels": {"black_box": "CRITICAL"},
        "cross_references": True
    },
    outcome="success",
    lessons=[
        "Re-read TESTING-STRATEGY.md before presenting",
        "Gave all 4 layers equal emphasis",
        "Explicitly stated black box tests derived from operational spec"
    ]
)
```

### Phase 1: Brainstorm & Converge

#### Before Spec Creation
```python
# Retrieve past spec creation episodes
episodes = retrieve_episodes(task="spec creation")

# Use SpecKit MCP to:
# - Create spec from requirements
# - Validate spec completeness
```

#### After Spec Creation
```python
# Store spec creation episode
store_episode(
    task="spec creation",
    context={
        "spec_type": "operational",
        "sections": ["overview", "requirements", "constraints"],
        "used_speckit": True
    },
    outcome="success"
)
```

### Phase Transitions

#### Before Moving to Next Phase
```python
# Retrieve episodes for the next phase
episodes = retrieve_episodes(task=f"Phase {next_phase}")

# Review common lessons
lessons = get_common_lessons(task=f"Phase {next_phase}")

# Reflect on current phase
store_episode(
    task=f"Phase {current_phase} completion",
    context=phase_context,
    outcome="success",
    lessons=phase_lessons
)
```

## Checkpoint Integration

### At Each Phase Gate

**Before requesting approval**:
1. Retrieve relevant episodes for the task
2. Review common lessons
3. Verify you're following past successful patterns
4. Check for known pitfalls

**After receiving approval**:
1. Store the checkpoint state
2. Note what was approved
3. Store any decisions made

### Example: Gate 2 (Brainstorming Completion)

```python
# Before requesting approval
episodes = retrieve_episodes(task="brainstorming completion")
lessons = get_common_lessons(task="brainstorming completion")

# Review:
# - Did I actually run the brainstorming command?
# - Did I present sections and get validation?
# - Did I use Context7?
# - Did I follow document internalization requirements?

# After approval
store_episode(
    task="brainstorming completion approval",
    context={
        "sections_validated": sections_count,
        "user_approval": True,
        "followed_process": True
    },
    outcome="success"
)
```

## Daily/Periodic Reflection

### Weekly Review
```python
# Get common lessons across all tasks
lessons = get_common_lessons(task="all")

# Review patterns:
# - What mistakes keep happening?
# - What patterns lead to success?
# - What should be emphasized more?
```

### After User Feedback
```python
# If feedback indicates a mistake
reflect_on_failure(
    task=feedback_task,
    context=feedback_context,
    error=feedback_message
)

# Store the corrected approach
store_episode(
    task=feedback_task,
    context=corrected_context,
    outcome="corrected",
    lessons=[feedback_lesson]
)
```

## Agent Instructions

### Overlord Instructions

**The Overlord MUST**:

1. **Before each major task**:
   - Retrieve similar past episodes using Reflection MCP
   - Review common lessons
   - Apply lessons to current task

2. **During each task**:
   - Use Context7 MCP for research (as documented)
   - Use SpecKit MCP for spec management (if applicable)
   - Use GitHub MCP for repository operations

3. **After each task**:
   - Store episode with outcome and lessons
   - If failure: use `reflect_on_failure()` first

4. **At each phase gate**:
   - Retrieve episodes for the gate
   - Review lessons before requesting approval
   - Store checkpoint after approval

5. **Before phase transitions**:
   - Retrieve episodes for next phase
   - Review common lessons
   - Store completion of current phase

### Multiclaude Agent Instructions

**The Overlord MUST instruct multiclaude agents to**:

1. **Use Reflection MCP**:
   - Before starting work on an issue, retrieve similar past episodes
   - After completing work, store episode with outcome
   - If blocked, use `generate_improved_attempt()` for guidance

2. **Use Context7 MCP**:
   - Research best practices when implementing features
   - Look up patterns for the tech stack
   - Find testing strategies

3. **Use SpecKit MCP**:
   - Reference operational specifications
   - Validate implementation against spec

4. **Use Probe MCP**:
   - Analyze codebase structure before making changes
   - Understand dependencies

5. **Store lessons learned**:
   - After PR completion (success or failure)
   - After resolving blockers
   - After test arbitration

## Implementation Checklist

### For Overlord

- [ ] Before tech stack selection → Retrieve episodes
- [ ] Before brainstorming → Retrieve episodes
- [ ] After brainstorming → Store episode
- [ ] Before testing strategy → Retrieve episodes
- [ ] After testing strategy → Store episode
- [ ] Before each phase gate → Retrieve episodes
- [ ] After each phase gate → Store checkpoint
- [ ] Before phase transitions → Retrieve and store
- [ ] After user feedback → Reflect and store
- [ ] Weekly → Review common lessons

### For Multiclaude Agents

- [ ] Before starting issue → Retrieve similar episodes
- [ ] During implementation → Use Context7 for research
- [ ] After PR completion → Store episode
- [ ] If blocked → Use generate_improved_attempt()
- [ ] After test arbitration → Store lesson

## Example: Complete Phase 0 Flow with MCP

```python
# 1. Before Phase 0 starts
episodes = retrieve_episodes(task="Phase 0 bootstrap")
lessons = get_common_lessons(task="Phase 0 bootstrap")

# 2. Before tech stack selection
episodes = retrieve_episodes(task="tech stack selection")
# ... select tech stack ...

# 3. Before brainstorming
episodes = retrieve_episodes(task="brainstorming session")
# ... conduct brainstorming ...
store_episode(task="brainstorming session", outcome="success", ...)

# 4. Before testing strategy
episodes = retrieve_episodes(task="testing strategy design")
# ... design testing strategy ...
store_episode(task="testing strategy design", outcome="success", ...)

# 5. Before Gate 2 (Brainstorming Approval)
episodes = retrieve_episodes(task="brainstorming completion approval")
# ... request approval ...
store_episode(task="brainstorming completion approval", outcome="success", ...)

# 6. Before Gate 4 (Plan Approval)
episodes = retrieve_episodes(task="implementation plan approval")
# ... request approval ...
store_episode(task="implementation plan approval", outcome="success", ...)

# 7. Before Gate 5 (Execution Approval)
episodes = retrieve_episodes(task="execution approval")
# ... request approval ...
store_episode(task="execution approval", outcome="success", ...)

# 8. After Phase 0 completion
store_episode(
    task="Phase 0 completion",
    context=phase_0_context,
    outcome="success",
    lessons=phase_0_lessons
)
```

## Key Principles

1. **Proactive, not reactive**: Retrieve episodes before starting, not just after failures
2. **Systematic**: Use tools at every checkpoint and phase gate
3. **Comprehensive**: Store both successes and failures
4. **Actionable**: Lessons must be specific and applicable
5. **Cross-reference**: Use multiple MCP tools together (e.g., Reflection + Context7)

## Remember

**MCP tools are not optional - they are integral to the workflow.**
- Use Reflection MCP to learn from past experiences
- Use Context7 MCP for research and best practices
- Use SpecKit MCP for spec management
- Use GitHub MCP for repository operations
- Use Probe MCP for code analysis
- Use Firecrawl MCP for web research

**The goal**: Build on past experiences, avoid repeating mistakes, and continuously improve the workflow.

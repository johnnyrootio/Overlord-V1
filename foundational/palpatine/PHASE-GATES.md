# Phase Gates: Human Approval Checkpoints

## Overview

**CRITICAL**: The Overlord MUST stop at each phase gate and wait for explicit human approval before proceeding. These gates ensure the human remains in control of key decisions during pre-code development work.

## Pre-Code Development Phase Gates

### Gate 1: Tech Stack Selection Approval

**Location**: After tech stack selection discussion

**Before gate**:
1. **Retrieve past episodes**:
   ```python
   episodes = retrieve_episodes(task="tech stack selection")
   lessons = get_common_lessons(task="tech stack selection")
   ```
2. Review what factors influenced past decisions
3. Review what trade-offs were considered
4. Apply lessons to current selection

**What happens**:
1. Overlord asks: "What programming language/ecosystem should we use?"
2. Overlord suggests ecosystems if appropriate (based on past episodes)
3. Overlord explains trade-offs (incorporating lessons learned)
4. User responds with selection

**Gate checkpoint**:
```
Overlord: "Based on our discussion, I recommend [tech stack] because [reasons]. 
Does this work for you? Please confirm: 'Yes, proceed with [tech stack]' or provide your selection."
```

**Required approval**: User must explicitly confirm tech stack selection

**Do not proceed until**: User has explicitly approved the tech stack

---

### Gate 2: Brainstorming Session Completion Approval

**Location**: After interactive brainstorming session using `/superpowers:brainstorm`

**Before gate**:
1. **Retrieve past episodes**:
   ```python
   episodes = retrieve_episodes(task="brainstorming session")
   lessons = get_common_lessons(task="brainstorming session")
   ```
2. Review common mistakes (e.g., skipping interactive session)
3. Review what made sessions successful
4. Apply lessons to current session

**What happens**:
1. Overlord actually runs `claude -p "/superpowers:brainstorm ..."`
2. Overlord has interactive conversation with user
3. Overlord presents design sections (200-300 words each)
4. User validates each section
5. All planning areas discussed

**Gate checkpoint**:
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

**Required approval**: User must explicitly approve proceeding to planning phase

**Do not proceed until**: User has explicitly approved brainstorming completion

**After approval**:
```python
store_episode(
    task="brainstorming session",
    context={
        "sections_covered": sections,
        "user_validations": validation_count,
        "used_superpowers": True,
        "used_context7": True
    },
    outcome="approved",
    lessons=["Actually ran brainstorming command", "Got user validation", "Used Context7"]
)
```

---

### Gate 3: Context7 Research Completion Approval

**Location**: After Context7 research (can be combined with brainstorming or separate)

**What happens**:
1. Overlord uses Context7 MCP to research best practices
2. Overlord presents research findings
3. Overlord incorporates findings into design

**Gate checkpoint** (if separate from brainstorming):
```
Overlord: "I've completed Context7 research on:
- [Finding 1]
- [Finding 2]
- [Finding 3]

These findings have been incorporated into our design.
Do you approve proceeding? Please confirm: 'Yes, proceed' or provide feedback."
```

**Required approval**: User must explicitly approve research completion (if separate gate)

**Note**: This can be combined with Gate 2 if research is done during brainstorming

---

### Gate 4: Implementation Plan Approval

**Location**: After creating detailed plan with `/superpowers:write-plan`

**Before gate**:
1. **Retrieve past episodes**:
   ```python
   episodes = retrieve_episodes(task="implementation plan creation")
   lessons = get_common_lessons(task="implementation plan creation")
   ```
2. Review what made plans successful
3. Review common missing components
4. Apply lessons to current plan

**What happens**:
1. Overlord actually runs `claude -p "/superpowers:write-plan ..."`
2. Overlord receives detailed implementation plan
3. Overlord presents complete plan to user

**Gate checkpoint**:
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

**Required approval**: User must explicitly approve the implementation plan

**Do not proceed until**: User has explicitly approved the plan

**After approval**:
```python
store_episode(
    task="implementation plan approval",
    context={
        "plan_sections": sections,
        "components_covered": components,
        "user_approval": True
    },
    outcome="approved",
    lessons=["Plan completeness", "User validation received"]
)
```

---

### Gate 5: Plan Review Completion Approval

**Location**: After plan review and any refinements

**What happens**:
1. Overlord reviews plan for completeness
2. Overlord identifies missing components
3. Overlord ensures alignment with workflow requirements
4. Overlord makes refinements based on user feedback (if any)

**Gate checkpoint**:
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

**Required approval**: User must explicitly approve proceeding to execution

**Do not proceed until**: User has explicitly approved execution

**After approval**:
```python
store_episode(
    task="execution approval",
    context={
        "plan_reviewed": True,
        "components_verified": True,
        "user_approval": True
    },
    outcome="approved",
    lessons=["Ready for execution"]
)
```

---

## MCP Tools Integration at Gates

**CRITICAL**: At each phase gate, the Overlord MUST use MCP tools (especially Reflection MCP) to learn from past experiences.

**Before requesting approval at any gate**:
1. **Retrieve relevant episodes** using Reflection MCP:
   ```python
   episodes = retrieve_episodes(task=f"{gate_name} approval")
   lessons = get_common_lessons(task=f"{gate_name} approval")
   ```
2. **Review lessons learned** from past similar gates
3. **Verify you're following successful patterns** and avoiding known pitfalls
4. **Apply lessons** to current gate request

**After receiving approval at any gate**:
1. **Store the checkpoint state**:
   ```python
   store_episode(
       task=f"{gate_name} approval",
       context=gate_context,
       outcome="approved",
       lessons=gate_lessons
   )
   ```

See [MCP-TOOLS-INTEGRATION.md](./MCP-TOOLS-INTEGRATION.md) for complete MCP tool usage guide.

## Gate Enforcement Rules

### 1. Explicit Approval Required

**Bad**: Assuming approval
```
Overlord: "Here's the plan. [presents plan]"
[Immediately starts executing]
```

**Good**: Explicit approval request
```
Overlord: "Here's the plan. [presents plan]"
Overlord: "Do you approve this plan? Please confirm: 'Yes, approve plan'"
[Waits for user response]
User: "Yes, approve plan"
Overlord: [Now proceeds]
```

### 2. Clear Approval Language

**Required format**: User must use explicit approval language:
- "Yes, proceed with [tech stack]"
- "Yes, proceed to planning"
- "Yes, approve plan"
- "Yes, proceed to execution"

**Not sufficient**: Vague responses like "ok", "sounds good", "looks fine"

**If user provides vague response**: Overlord should ask for explicit confirmation:
```
User: "Looks good"
Overlord: "To proceed, I need explicit confirmation. Please confirm: 'Yes, approve plan'"
```

### 3. No Proceeding Without Approval

**CRITICAL**: The Overlord MUST NOT proceed past any gate without explicit user approval.

**Checklist before proceeding**:
- [ ] User has provided explicit approval
- [ ] Approval language matches required format
- [ ] No outstanding questions or concerns
- [ ] User has confirmed readiness to proceed

### 4. Handling Feedback

**If user provides feedback instead of approval**:
1. Address the feedback
2. Make requested changes
3. Present updated version
4. Request approval again
5. **Do not proceed until approval is given**

---

## Gate Sequence

```
Phase 0: Bootstrap
│
├─ Tech Stack Discussion
│  └─ [GATE 1: Tech Stack Approval] ← STOP, WAIT FOR APPROVAL
│
├─ Brainstorming Session
│  └─ [GATE 2: Brainstorming Completion Approval] ← STOP, WAIT FOR APPROVAL
│
├─ Context7 Research (if separate)
│  └─ [GATE 3: Research Completion Approval] ← STOP, WAIT FOR APPROVAL (if separate)
│
├─ Create Implementation Plan
│  └─ [GATE 4: Plan Approval] ← STOP, WAIT FOR APPROVAL
│
├─ Plan Review
│  └─ [GATE 5: Execution Approval] ← STOP, WAIT FOR APPROVAL
│
└─ Phase 0 Execution (only after Gate 5 approval)
```

---

## Example: Complete Gate Flow

```
1. Tech Stack Selection
   Overlord: "What programming language should we use?"
   User: "Python"
   Overlord: "I recommend Python with FastAPI for this project. Does this work?"
   User: "Yes"
   Overlord: "To proceed, please confirm: 'Yes, proceed with Python'"
   User: "Yes, proceed with Python"
   ✅ GATE 1 PASSED

2. Brainstorming Session
   Overlord: [Runs claude -p "/superpowers:brainstorm ..."]
   Overlord: [Has interactive conversation]
   Overlord: "We've completed brainstorming. All sections validated. Proceed to planning?"
   User: "Yes, proceed to planning"
   ✅ GATE 2 PASSED

3. Implementation Plan
   Overlord: [Runs claude -p "/superpowers:write-plan ..."]
   Overlord: "Here's the plan: [presents plan]. Do you approve?"
   User: "Yes, approve plan"
   ✅ GATE 4 PASSED

4. Plan Review
   Overlord: "Plan reviewed. Ready for execution. Proceed?"
   User: "Yes, proceed to execution"
   ✅ GATE 5 PASSED

5. Execution
   Overlord: [Now executes Phase 0]
```

---

## Integration with Workflow Documents

These gates are integrated into:
- `PHASE-0-PLANNING.md` - Detailed planning process with gates
- `OVERLORD-GREENFIELD-WORKFLOW.md` - Main workflow with gate checkpoints
- `INITIAL-OVERLORD-PROMPT.md` - Initial prompt emphasizing gates

**The Overlord MUST reference this document and enforce all gates.**

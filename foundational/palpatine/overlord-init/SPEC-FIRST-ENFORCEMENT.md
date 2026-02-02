# Spec-First Development: Comprehensive Enforcement Guide

## Overview

This document explains how **spec-first development** is enforced throughout the multiclaude agentic workflow. It ensures that workers implement functionality to deliver value per the operational specification, not just to pass tests.

**Related Documents**:
- [TESTING-STRATEGY.md](./TESTING-STRATEGY.md) - Testing philosophy and test arbitration protocol
- [OVERLORD-GREENFIELD-WORKFLOW.md](./OVERLORD-GREENFIELD-WORKFLOW.md) - Complete workflow guide
- [AGENT-PROMPTS/](./AGENT-PROMPTS/) - Agent prompt templates

---

## The Problem: Test Gaming

**Risk**: Workers might write code that passes tests without implementing the intended functionality.

**Example**:
- Test expects: "Return user object with id=123"
- Worker implements: `return {id: 123}` (hardcoded, passes test but doesn't work)
- **Problem**: Code passes test but doesn't deliver value

**Solution**: Enforce spec-first development with test access restrictions.

---

## Enforcement Layers

### Layer 1: Agent Prompts (`.multiclaude/agents/`)

**Location**: Repository `.multiclaude/agents/` directory

**Files**:
- `worker.md` - Spec-first implementation guidance (augmenting override)
- `supervisor.md` - Test arbitration protocol (augmenting override)
- `reviewer.md` - Spec compliance verification (augmenting override)

**How it works**:
- These are **augmenting overrides** that work alongside multiclaude's default prompts
- Multiclaude appends these as "Repository-specific instructions" after the default prompt
- **Benefit**: As multiclaude's defaults evolve, you get those improvements automatically (when they don't conflict)
- **Judgment**: When conflicts arise, our prompts take precedence—they're designed for spec-first enforcement
- Our overrides add spec-first enforcement and can override defaults when better for our purposes
- Prompts explicitly state: "Implement to spec, not to pass tests"
- Prompts restrict test code access
- Prompts define escalation paths

**Precedence**:
1. `<repo>/.multiclaude/agents/<agent>.md` (our augmenting overrides - appended after defaults, can override)
2. `~/.multiclaude/repos/<repo>/agents/<agent>.md` (local overrides)
3. Built-in defaults (multiclaude's evolving prompts - fallback)

**Important**: Since our prompts are appended after defaults, they can override earlier instructions. Use judgment—if our prompts are better for spec-first enforcement, they take precedence. Don't diminish their effect to preserve defaults.

**See**: [AGENT-PROMPTS/](./AGENT-PROMPTS/) directory for full templates.

### Layer 2: Ticket Structure

**Location**: GitHub issues created from work graph

**Test Tickets** include:
- Test specification (what behavior to test)
- Operational spec reference
- **Explicit note**: "Test implementation code NOT accessible to implementers"

**Implementation Tickets** include:
- Primary goal: "Implement per operational specification"
- Implementation guidance: "Read spec, not test code"
- Test validation: "Tests will validate your implementation"
- Escalation: "If test seems wrong, create blocker:test-arbitration issue"

**How it works**:
- Every ticket embeds the guidance
- Workers see restrictions in every ticket
- Clear escalation path if tests seem wrong

**See**: [TESTING-STRATEGY.md](./TESTING-STRATEGY.md#ticket-templates) for templates.

### Layer 3: Repository Rules (`CLAUDE.md`)

**Location**: Repository root `CLAUDE.md` file

**Contents**:
- Spec-first development rules
- Test access restrictions
- Test arbitration process
- Escalation guidelines

**How it works**:
- All agents read this file
- Rules are visible to everyone
- Provides consistent guidance across all agents

**See**: [OVERLORD-GREENFIELD-WORKFLOW.md](./OVERLORD-GREENFIELD-WORKFLOW.md#phase-0-bootstrap-determinism--autonomy) for template.

### Layer 4: Test Arbitration Protocol

**Location**: Supervisor agent + Testing Strategy document

**Process**:
1. Worker suspects test is wrong → Creates `blocker:test-arbitration` issue
2. Supervisor reviews → Compares test to operational spec
3. Supervisor decides → Fix test, fix code, or escalate
4. Overlord handles complex cases → May escalate to human

**How it works**:
- Clear escalation path prevents workers from gaming tests
- Supervisor has access to test code for arbitration
- Workers don't need test code—they have the spec

**See**: [TESTING-STRATEGY.md](./TESTING-STRATEGY.md#test-failure-arbitration-protocol) for full protocol.

### Layer 5: Review Process

**Location**: Reviewer agent

**Process**:
- Reviewer verifies: "Does implementation match spec?" (primary)
- Reviewer verifies: "Do tests pass?" (secondary)
- Reviewer detects: "Code that passes tests but doesn't match spec" (anti-pattern)

**How it works**:
- Review focuses on spec compliance, not just test passing
- Anti-pattern detection catches test gaming
- Review blocks PRs that don't deliver value

**See**: [AGENT-PROMPTS/reviewer.md](./AGENT-PROMPTS/reviewer.md) for review checklist.

---

## Access Control Matrix

| Artifact | Worker Access | Supervisor Access | Reviewer Access | Overlord Access |
|----------|---------------|-------------------|-----------------|-----------------|
| Operational Spec | ✅ Full | ✅ Full | ✅ Full | ✅ Full |
| User Manual | ✅ Full | ✅ Full | ✅ Full | ✅ Full |
| Interface Contracts (as specs) | ✅ Full | ✅ Full | ✅ Full | ✅ Full |
| Test Specifications | ✅ Full | ✅ Full | ✅ Full | ✅ Full |
| Test Results | ✅ Full | ✅ Full | ✅ Full | ✅ Full |
| Test Implementation Code | ❌ No | ✅ Yes (for arbitration) | ✅ Yes (for review) | ✅ Yes |
| Test Internals | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes |

**Why**: Workers implement to spec, supervisors/reviewers verify correctness, Overlord orchestrates.

---

## Enforcement Checklist

### Phase 0: Bootstrap

- [ ] Create `CLAUDE.md` with spec-first rules
- [ ] Create agent prompts in `.multiclaude/agents/` from templates
- [ ] Set up test infrastructure (workers won't access test code)

### Phase 1: Specification

- [ ] Create operational specification (source of truth)
- [ ] Create Testing Strategy Document (includes access restrictions)
- [ ] Define test specifications (not test code)

### Phase 2: Work Graph

- [ ] Create test tickets with access restrictions noted
- [ ] Create implementation tickets with spec-first guidance
- [ ] Link tickets to operational spec sections

### Phase 3: Issues

- [ ] Create GitHub issues from work graph
- [ ] Include spec-first guidance in issue descriptions
- [ ] Include test access restrictions in test issues

### Phase 4: Dispatch

- [ ] Workers use agent prompts (enforce spec-first)
- [ ] Workers create `blocker:test-arbitration` if tests seem wrong
- [ ] Supervisor arbitrates test issues

### Phase 5: Review

- [ ] Reviewer verifies spec compliance (primary)
- [ ] Reviewer verifies test passing (secondary)
- [ ] Reviewer detects test gaming anti-patterns

---

## Example: Complete Enforcement Flow

### Scenario: Worker implements authentication

1. **Worker receives ticket**:
   - Issue #102: "Implement: Authentication module"
   - Primary goal: "Implement per operational spec section 3.2"
   - Guidance: "DO NOT access test code from issue #101"
   - Validation: "Tests from #101 will validate your implementation"

2. **Worker reads agent prompt** (`.multiclaude/agents/worker.md`):
   - "Implement to operational specification"
   - "Tests validate, not guide"
   - "No access to test implementation code"

3. **Worker reads CLAUDE.md**:
   - "Spec is truth"
   - "No test gaming"
   - "Test arbitration process"

4. **Worker implements**:
   - Reads operational spec section 3.2
   - Reads user manual section 2.1
   - Reviews interface contract (as spec, not test code)
   - Writes unit tests (TDD)
   - Implements to match spec
   - Runs `./scripts/check.sh`

5. **Test fails**:
   - Worker checks implementation against spec
   - Implementation matches spec
   - Worker suspects test is wrong
   - Worker creates `blocker:test-arbitration` issue

6. **Supervisor arbitrates**:
   - Reads operational spec section 3.2
   - Reads test from issue #101 (supervisor has access)
   - Compares: Test expects X, spec says Y
   - Decision: Test doesn't match spec → Fix test
   - Creates ticket: "Fix test: Authentication interface contract"

7. **Test engineer fixes test**:
   - Updates test to match operational spec
   - Test now validates spec correctly

8. **Worker's implementation**:
   - Now passes updated test
   - Implementation matches spec ✅
   - Tests validate correctly ✅

9. **Reviewer reviews PR**:
   - Checks: Does implementation match spec? ✅
   - Checks: Do tests pass? ✅
   - Checks: Does it deliver value? ✅
   - Approves: "Spec compliance: ✅. Value delivery: ✅. Tests: ✅"

10. **Merge-queue merges**:
    - CI green (tests pass)
    - Review approved (spec compliant)
    - PR merged ✅

---

## Key Principles

1. **Spec is truth**: Operational specification is the source of truth, not tests
2. **Tests validate**: Tests verify spec compliance, they don't define requirements
3. **Value delivery**: Code must deliver value, not just pass tests
4. **Access control**: Workers don't need test code—they have the spec
5. **Arbitration**: Clear escalation path when tests and spec don't align
6. **Review focus**: Review verifies spec compliance, not just test passing

---

## Summary

Spec-first development is enforced through:
- ✅ **Agent prompts** that guide behavior
- ✅ **Ticket structure** that embeds guidance
- ✅ **Repository rules** that set expectations
- ✅ **Test arbitration** that handles conflicts
- ✅ **Review process** that verifies compliance

**Result**: Workers implement to deliver value per the operational specification, with tests as validation tools, not implementation guides.

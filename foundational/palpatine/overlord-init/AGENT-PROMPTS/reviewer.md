MODE: ADDITIVE (recommended)

# Review Agent: Spec Compliance Override

**This augments multiclaude's default review prompt with spec compliance verification.**

**How it works**: multiclaude appends this as "Repository-specific instructions" after the default prompt. You get:
- ✅ Default review behavior (check ROADMAP.md, post comments, etc.)
- ✅ **Spec compliance verification** (primary check) - **takes precedence when it conflicts**
- ✅ **Test gaming detection** - **authoritative for our workflow**
- ✅ **Enhanced merge-queue reporting** - **our process**

**When conflicts arise**: These instructions come after defaults, so they can override. Prioritize spec compliance verification when it conflicts with default review criteria.

## Additional Review Focus

In addition to your default review process (check ROADMAP.md, post comments, message merge-queue):

**Primary check**: Does the implementation match the operational specification and deliver value?

**Secondary check**: Do tests pass? (CI green)

**Anti-pattern to detect**: Code that passes tests but doesn't match the operational specification.

## Additional Review Checklist

**Add these checks to your default review process**:

- [ ] **Spec compliance**: Implementation matches operational specification (PRIMARY)
- [ ] **Value delivery**: Code delivers intended value per spec
- [ ] **No test gaming**: Implementation matches spec, not just passing tests
- [ ] **Tests validate**: Tests verify spec requirements are met

**Default review checks still apply**:
- [ ] ROADMAP.md compliance (out-of-scope = blocking)
- [ ] Security vulnerabilities (blocking)
- [ ] Obvious bugs (blocking)
- [ ] Tests pass (CI green)

## Enhanced Review Summary (Augments Default)

**Add to your default merge-queue message**:

```bash
# Include spec compliance in summary:
multiclaude message send merge-queue "Review complete for PR #123. Spec compliance: ✅. Value delivery: ✅. Tests: ✅. 0 blocking (per default rules), 3 suggestions. Safe to merge."
multiclaude agent complete
```

**Default reporting format still applies** - just add spec compliance verification.

## Additional Escalation Cases

**Beyond default blocking criteria**, also flag:
- **Test gaming**: Code passes tests but doesn't match operational spec → Blocking
- **Spec/test mismatch**: Note in review, supervisor will handle via test arbitration

## Key Principles (Additions to Default)

- **Spec is truth**: Operational specification is source of truth
- **Tests validate**: Tests verify spec compliance, not define requirements
- **Value delivery**: Code must deliver value per spec, not just pass tests

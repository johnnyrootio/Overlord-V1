# Testing Strategy: Comprehensive Testing Philosophy for Greenfield Development

## Overview

This document defines the comprehensive testing philosophy that governs how software is built using the multiclaude agentic workflow. It establishes the principles, methodologies, and implementation patterns that ensure **provable correctness** as the system evolves through waves.

**Related Documents**:
- [OVERLORD-GREENFIELD-WORKFLOW.md](./OVERLORD-GREENFIELD-WORKFLOW.md) - Complete workflow orchestration guide
- See [Phase 0](./OVERLORD-GREENFIELD-WORKFLOW.md#phase-0-bootstrap-determinism--autonomy) for bootstrap context
- See [The `check.sh` Gate](./OVERLORD-GREENFIELD-WORKFLOW.md#the-checksh-gate-one-gate-to-rule-them-all) for CI implementation

---

## Core Principles

### 1. Test-Driven Development (TDD) with Spec-First Implementation

**Every piece of work must follow TDD, but implementation must be spec-first:**

- Tests are written **before** code
- Tests define the expected behavior
- **Code is written to implement the operational specification** (primary goal)
- Tests validate that the implementation matches the specification
- **Tests are validation tools, not implementation guides**

**Critical Rule**: Workers must **NOT** have access to test implementation code. They implement based on:
- Operational specification
- User manual
- Interface contracts (specifications, not test code)
- Test results (pass/fail, error messages)
- Test specifications (what behavior is tested)

**Why**: This prevents "gaming the test" and ensures the system embodies intended functionality, not just test-passing code. The goal is a working system that delivers value, with tests as the validation mechanism.

### 2. Tests Define the Target

The Brownian Ratchet philosophy requires a clear target. **Tests are that target.**

- Agents work to make tests pass
- Tests define what "correct" means
- As tests become more comprehensive, the system becomes more correct
- The system self-organizes to meet the test requirements

### 3. Cumulative Test Suite

**Once a test is added, it stays forever.**

- Tests accumulate across waves
- No test is ever removed (unless the feature is removed)
- Each wave adds new tests without removing old ones
- Full regression ensures nothing breaks

**Why**: This ensures progress is permanent. We never regress. The ratchet only moves forward.

### 4. Wave-Aware Testing

**Tests are organized by waves, but execution is cumulative:**

- **Wave 0 (Foundation)**: Interface contract tests
- **Wave 1 (Core)**: Interface + unit tests
- **Wave 2 (Features)**: Interface + unit + integration tests
- **System-level**: Interface + unit + integration + black box functional tests

**Execution**: All tests that exist must pass, regardless of which wave is being worked on.

### 5. Progressive Strictness

**Test thresholds become stricter over time, but tests themselves remain:**

- Coverage requirements increase (Wave 0: 60%, Wave 1: 70%, Wave 2: 80%)
- Performance thresholds tighten
- Linting rules become stricter
- Tests are never weakened to "get green"

**Why**: The system improves over time, but the bar never lowers.

---

## Testing Layers

### Layer 1: Interface Contract Tests

**Purpose**: Define and verify interface contracts between modules.

**When**: Created in **Wave 0** as separate test tickets that precede implementation.

**What they verify**:
- Input/output types and shapes
- Error conditions and edge cases
- Interface behavioral guarantees (idempotency, immutability, etc.)

**Implementation**:
- Separate contract specification files (OpenAPI/Swagger for APIs, custom schema files for internal interfaces)
- Tests verify contracts are adhered to
- Contracts are version-controlled and evolve with the system

**Example structure**:
```
contracts/
  auth-api.yaml          # OpenAPI spec for auth interface
  database-schema.json   # Database interface contract
tests/
  interfaces/
    auth-contract.test.ts
    database-contract.test.ts
```

**Work graph pattern**:
```yaml
- id: T1
  issue: 101
  title: Test: Authentication interface contract
  depends_on: []
  type: test
  layer: interface
  test_specification: |
    Tests should verify:
    - Input: JWT token string
    - Output: User object or authentication error
    - Error conditions: Invalid token, expired token, malformed token
    - Interface contract: See contracts/api/auth-api.yaml
  access_restriction: |
    Test implementation code should NOT be accessible to implementation workers.
    Workers should only see test specifications and results.
```

### Layer 2: Unit Tests

**Purpose**: Verify individual components work correctly in isolation.

**When**: Created in **Wave 1** as part of implementation tickets (TDD).

**What they verify**:
- Component logic correctness
- Edge cases and error handling
- Internal state management
- Pure function behavior

**Implementation**:
- Written as part of implementation (tests first, then code)
- Focus on single components/modules
- Fast execution (< 1 second per test)
- High coverage of component logic

**Work graph pattern**:
```yaml
- id: T2
  issue: 102
  title: Implement: Authentication module
  depends_on: [T1]  # Depends on interface contract test
  type: implementation
  tdd_required: true
  primary_goal: |
    Implement authentication per operational specification section 3.2.
    Deliver value: Users can securely authenticate with JWT tokens.
  implementation_guidance: |
    - Read operational specification section 3.2 (Authentication)
    - Read user manual section 2.1 (How to authenticate)
    - Review interface contract: contracts/api/auth-api.yaml
    - Write unit tests first (TDD), then implement to make them pass
    - DO NOT access test implementation code from issue T1
    - If tests fail and you believe test is wrong, create blocker:test-arbitration issue
  validation: |
    Tests from T1 will validate your implementation.
    Tests are validation tools - implement to spec, not to pass tests.
```

### Layer 3: Integration/Subassembly Tests

**Purpose**: Verify components work together correctly.

**When**: Created in **Wave 2+** as integration tasks.

**What they verify**:
- Component interactions
- Data flow between modules
- Subsystem composition
- Integration points

**Implementation**:
- Test multiple components together
- Verify integration contracts
- Test real data flows
- May require test databases, mock services, etc.

**Work graph pattern**:
```yaml
- id: T3
  issue: 103
  title: Test: Auth + Database integration
  depends_on: [T1, T2]
  type: test
  layer: integration
```

### Layer 4: Black Box Functional System Tests

**Purpose**: Verify the system works correctly from an external perspective.

**When**: Created based on operational specification, ongoing and cumulative.

**What they verify**:
- System produces correct input-output relationships
- System meets operational specification
- User workflows function correctly
- System observables match expectations

**Implementation**:
- Based on operational specification/user manual
- Test system as a black box
- Use realistic inputs and verify outputs
- May require comprehensive test batteries (for ML, security, etc.)

**Test battery collection** (for specialized systems):
- Collect real-world test cases (true positives, edge cases)
- Build test fixtures and data
- Continuously expand test coverage
- Context-dependent (ML systems need diverse datasets, security systems need attack vectors, etc.)

**Directory structure**:
```
tests/
  system/
    black-box/
      user-workflows.test.ts
      api-endpoints.test.ts
      cli-commands.test.ts
    test-battery/
      fixtures/
        real-world-cases/
        edge-cases/
        adversarial-cases/
      data/
        training-samples/
        validation-sets/
```

---

## Test Ticket Organization in Work Graph

### Pattern: Separate Test Tickets for Interfaces

**Interface contract tests** are separate tickets that come **before** implementation:

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
        description: |
          Define OpenAPI contract for auth endpoints.
          Test: input/output types, error conditions, edge cases.
```

### Pattern: TDD in Implementation Tickets

**Implementation tickets** include tests as part of the work, but tests are written first:

```yaml
      - id: T2
        issue: 102
        title: Implement: Authentication module
        depends_on: [T1]
        type: implementation
        tdd_required: true
        definition_of_done:
          - All interface contract tests pass
          - Unit tests written (TDD) and passing
          - Code coverage >= 70%
          - ./scripts/check.sh passes
```

### Pattern: Integration Test Tickets

**Integration tests** are separate tickets that verify subsystem composition:

```yaml
  - id: wave2
    name: features
    tasks:
      - id: T5
        issue: 105
        title: Test: Auth + User Profile integration
        depends_on: [T2, T4]  # Depends on both implementations
        type: test
        layer: integration
```

---

## Operational Specification and User Manual

### Creation Timeline

**Created in Phase 1** (after Brainstorm & Converge), used to guide all subsequent phases.

### Contents

The operational specification defines:
- **How the system works**: Architecture, data flows, component interactions
- **How commands work**: CLI interface, API endpoints, configuration
- **What interfaces exist**: Public APIs, internal contracts, data formats
- **User workflows**: How users interact with the system
- **Expected behaviors**: Input-output relationships, observables, side effects

### Relationship to Testing

- **Black box tests** are derived from the operational specification
- **Interface contracts** align with the specification
- **Integration tests** verify the specification is met
- **System tests** validate end-to-end workflows

### Documentation Structure

```
docs/
  operational-specification.md    # High-level: how system works
  user-manual.md                  # Detailed: commands, workflows, examples
  testing-strategy.md             # This document (detailed testing methodology)
  api-reference.md                # API contracts (OpenAPI, etc.)
```

---

## CI Evolution Strategy

### Phase 1: Naive Full Regression (Waves 0-2)

**Implementation**: `check.sh` runs all tests, always.

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "==> Running full regression suite"

# Run all tests that exist (cumulative)
[ -d "tests/interfaces" ] && npm run test:interfaces
[ -d "tests/unit" ] && npm run test:unit
[ -d "tests/integration" ] && npm run test:integration
[ -d "tests/system" ] && npm run test:system
```

**Why**: Simple, safe, establishes the ratchet. No complexity, no missed regressions.

### Phase 2: Wave-Aware Execution (Wave 3+)

**Implementation**: `check.sh` detects wave context and runs relevant tests, but always includes full regression on main branch.

```bash
#!/usr/bin/env bash
set -euo pipefail

# Detect wave from PR labels or environment
WAVE="${WAVE:-full}"  # Default to full regression
BRANCH="${GITHUB_REF_NAME:-main}"

echo "==> Running tests for wave: ${WAVE} (branch: ${BRANCH})"

# On main branch, always run full regression
if [ "$BRANCH" = "main" ]; then
  echo "==> Main branch: running full regression"
  [ -d "tests/interfaces" ] && npm run test:interfaces
  [ -d "tests/unit" ] && npm run test:unit
  [ -d "tests/integration" ] && npm run test:integration
  [ -d "tests/system" ] && npm run test:system
  exit 0
fi

# On feature branches, wave-aware execution
case "$WAVE" in
  "0"|"foundation")
    npm run test:interfaces
    # Also run any integration tests that might be affected
    npm run test:integration -- --grep "foundation"
    ;;
  "1"|"core")
    npm run test:interfaces
    npm run test:unit
    npm run test:integration -- --grep "core"
    ;;
  "2"|"features")
    npm run test:interfaces
    npm run test:unit
    npm run test:integration
    npm run test:system -- --grep "features"
    ;;
  "full"|*)
    # Full regression when wave unknown
    [ -d "tests/interfaces" ] && npm run test:interfaces
    [ -d "tests/unit" ] && npm run test:unit
    [ -d "tests/integration" ] && npm run test:integration
    [ -d "tests/system" ] && npm run test:system
    ;;
esac
```

**CI Integration**: GitHub Actions detects wave from PR labels:
```yaml
- name: Run gate
  env:
    WAVE: ${{ contains(github.event.pull_request.labels.*.name, 'wave:0') && '0' || contains(github.event.pull_request.labels.*.name, 'wave:1') && '1' || 'full' }}
  run: ./scripts/check.sh
```

### Phase 3: Smart Incremental (Mature System)

**Implementation**: Test dependency graph + change detection.

```bash
#!/usr/bin/env bash
set -euo pipefail

MODE="${CI_MODE:-full}"  # full | incremental | wave-aware
BRANCH="${GITHUB_REF_NAME:-main}"

# Always full regression on main
if [ "$BRANCH" = "main" ]; then
  MODE="full"
fi

if [ "$MODE" = "incremental" ]; then
  echo "==> Running incremental test suite"
  
  # Detect changed files
  CHANGED_FILES=$(git diff --name-only origin/main...HEAD)
  
  # Determine which test suites to run based on changes
  if echo "$CHANGED_FILES" | grep -q "src/auth"; then
    echo "==> Auth module changed: running auth tests"
    npm run test:unit -- --grep "auth"
    npm run test:integration -- --grep "auth"
  fi
  
  if echo "$CHANGED_FILES" | grep -q "src/database"; then
    echo "==> Database module changed: running database tests"
    npm run test:unit -- --grep "database"
    npm run test:integration -- --grep "database"
  fi
  
  # Always run integration tests for current wave
  WAVE="${WAVE:-}"
  if [ -n "$WAVE" ]; then
    npm run test:integration -- --wave="$WAVE"
  fi
  
  # Always run system tests (they're fast enough)
  npm run test:system
  
else
  # Fall back to full regression
  echo "==> Running full regression suite"
  [ -d "tests/interfaces" ] && npm run test:interfaces
  [ -d "tests/unit" ] && npm run test:unit
  [ -d "tests/integration" ] && npm run test:integration
  [ -d "tests/system" ] && npm run test:system
fi
```

### CI as Code: Versioned and Ticket-Driven

**Structure**:
```
scripts/
  check.sh              # Main gate (evolves via tickets)
  ci-helpers/
    detect-wave.sh      # Wave detection logic
    test-selector.sh   # Smart test selection
    coverage-check.sh   # Progressive strictness
    change-detector.sh  # Detect changed modules
```

**Evolution via tickets**:
- Wave 0: "Create check.sh with interface tests"
- Wave 1: "Add unit tests to check.sh"
- Wave 2: "Add integration tests to check.sh"
- Wave 3: "Implement wave-aware test execution"
- Wave 4: "Add incremental test selection"
- Wave 5: "Optimize CI performance with test caching"

**Specialized workers**: Different agent types for CI evolution:
- `.multiclaude/agents/ci-engineer.md`: Focuses on CI/CD improvements, test infrastructure
- `.multiclaude/agents/test-engineer.md`: Focuses on writing comprehensive tests
- `.multiclaude/agents/devops.md`: Focuses on infrastructure, performance, scalability

---

## Directory Structure Standards

### Recommended Structure

```
project-root/
  contracts/                    # Interface contract specifications
    api/
      auth-api.yaml            # OpenAPI spec
      user-api.yaml
    internal/
      database-schema.json     # Internal interface contracts
      service-contracts.yaml
  
  tests/
    interfaces/                # Interface contract tests (Wave 0)
      auth-contract.test.ts
      database-contract.test.ts
    
    unit/                      # Unit tests (Wave 1+)
      auth/
      database/
      services/
    
    integration/               # Integration tests (Wave 2+)
      auth-database.test.ts
      auth-user.test.ts
    
    system/                    # System-level tests (Wave 2+)
      black-box/
        user-workflows.test.ts
        api-endpoints.test.ts
        cli-commands.test.ts
      
      test-battery/            # Comprehensive test cases (context-dependent)
        fixtures/
          real-world-cases/
          edge-cases/
          adversarial-cases/
        data/
          training-samples/    # For ML systems
          validation-sets/
          attack-vectors/      # For security systems
  
  scripts/
    check.sh                   # Main gate (evolves)
    ci-helpers/
      detect-wave.sh
      test-selector.sh
      coverage-check.sh
  
  docs/
    operational-specification.md
    user-manual.md
    testing-strategy.md        # This document
    api-reference.md
```

### Principles

- **Clear**: Easy to find tests for any component
- **Organized**: Tests grouped by layer and purpose
- **Portable**: Structure works across different tech stacks
- **Expandable**: Easy to add new test types without restructuring

---

## Progressive Strictness Thresholds

### Coverage Requirements

| Wave | Minimum Coverage | Target Coverage |
|------|-----------------|----------------|
| Wave 0 | 50% | 60% |
| Wave 1 | 60% | 70% |
| Wave 2 | 70% | 80% |
| Wave 3+ | 80% | 90% |

### Implementation in `check.sh`

```bash
# Progressive coverage thresholds
WAVE="${WAVE:-0}"
case "$WAVE" in
  "0")
    COVERAGE_THRESHOLD=60
    ;;
  "1")
    COVERAGE_THRESHOLD=70
    ;;
  "2")
    COVERAGE_THRESHOLD=80
    ;;
  *)
    COVERAGE_THRESHOLD=80
    ;;
esac

npm run test:coverage -- --threshold=$COVERAGE_THRESHOLD
```

### Other Progressive Metrics

- **Performance**: Response time thresholds tighten (Wave 0: < 500ms, Wave 1: < 200ms, Wave 2: < 100ms)
- **Linting**: Rules become stricter (Wave 0: warnings allowed, Wave 1: errors only, Wave 2: strict mode)
- **Security**: Audit levels increase (Wave 0: moderate, Wave 1: high, Wave 2: critical)

---

## Test Battery Collection (Context-Dependent)

### When Needed

**Required for**:
- Machine learning systems (need diverse training/validation sets)
- Security systems (need attack vectors, exploit cases)
- Less deterministic systems (need comprehensive edge cases)
- Domain-specific systems (need real-world scenarios)

**Not needed for**:
- Novel deterministic systems
- Simple CRUD applications
- Well-defined mathematical systems

### Collection Strategy

1. **Identify need** in Phase 1 (Testing Strategy Document)
2. **Create collection task** in Wave 0 or early waves
3. **Ongoing collection** as system evolves
4. **Wave-aware**: Test battery grows with each wave
5. **Cumulative**: Once collected, test cases remain

### Implementation

```yaml
# Work graph example
waves:
  - id: wave0
    tasks:
      - id: T0
        issue: 100
        title: Collect test battery dataset
        type: test-infrastructure
        description: |
          Collect real-world test cases for malware detection:
          - True positive samples (known malware)
          - False positive samples (benign code)
          - Edge cases (obfuscated, polymorphic)
          - Adversarial cases (evasion attempts)
```

---

## Test Access and Separation of Concerns

### What Workers Can Access

**Workers implementing features have access to**:
- ✅ **Operational specification** (what the system should do)
- ✅ **User manual** (how it should work from user perspective)
- ✅ **Interface contracts** (expected inputs/outputs, error conditions - as specifications, not test code)
- ✅ **Test results** (pass/fail status, error messages from test runs)
- ✅ **Test specifications** (what behavior is being tested, acceptance criteria)
- ✅ **Test tickets** (the requirements for what tests should validate)

**Workers implementing features must NOT have access to**:
- ❌ **Test implementation code** (the actual test files: `*.test.ts`, `*_test.py`, etc.)
- ❌ **Test internals** (how tests are structured, test helper functions)
- ❌ **Test fixtures/data** (unless needed for understanding requirements)
- ❌ **Test implementation details** (mocking strategies, test setup code)

### Why This Separation Matters

**Prevents test gaming**: Workers cannot write code that merely passes tests without implementing the intended functionality.

**Ensures value delivery**: Code is written to deliver value per the operational specification, not to match test expectations.

**Maintains test integrity**: Tests remain independent validation mechanisms that verify spec compliance.

### Enforcement

- **Agent prompts** explicitly restrict test code access
- **Ticket templates** include access restrictions
- **Hooks** can block access to test files (optional, may be too restrictive)
- **Review process** checks that implementation matches spec, not just tests

---

## Test Failure Arbitration Protocol

### Escalation Path

When tests fail, there is a clear escalation path to determine whether the issue is with the code, the test, or the specification.

#### Level 1: Worker (Normal Case)

**Scenario**: Test fails, code doesn't match spec

**Assumption**: Test is correct, code is wrong

**Action**:
1. Worker reviews operational specification
2. Worker fixes implementation to match spec
3. Worker re-runs tests
4. If tests pass → Done ✅

**No escalation needed** - this is the normal TDD cycle.

#### Level 2: Supervisor (Suspected Test Issue)

**Scenario**: Worker believes test doesn't match operational specification

**Trigger**: Worker creates blocker issue with label `blocker:test-arbitration`

**Issue format**:
```markdown
## Test Arbitration Request

**Test**: [Test name/ID]
**Failing assertion**: [What the test expects]
**Operational spec reference**: [Section of spec that defines behavior]
**Discrepancy**: [Why test doesn't match spec]

**Proposed resolution**: [Fix test / Update spec / Fix code]
```

**Supervisor review process**:
1. Compare test to operational specification
2. Check if spec changed but test didn't update
3. Review test quality (is it testing the right thing?)
4. Check if spec is ambiguous

**Supervisor decision matrix**:
- ✅ **Test matches spec, code doesn't** → Fix code (create ticket)
- ✅ **Test doesn't match spec** → Fix test (create ticket: "Fix test: [description]")
- ✅ **Spec is ambiguous** → Escalate to Overlord
- ✅ **Test is poorly written** → Create ticket: "Improve test: [description]"

**Supervisor actions**:
- Create appropriate fix ticket
- Update work graph if needed
- Continue workflow

#### Level 3: Overlord (Complex Cases)

**Scenario**: Supervisor uncertain, conflicting requirements, or spec needs update

**Trigger**: Supervisor escalates to Overlord with context

**Overlord review**:
1. Review operational spec vs test vs implementation
2. Determine root cause:
   - Spec needs clarification → Update operational spec
   - Test needs update → Create test fix ticket
   - Implementation needs fix → Create implementation ticket
3. May need to update multiple artifacts in order:
   - Spec → Tests → Code (if spec changed)
   - Tests → Code (if test was wrong)
   - Code (if implementation was wrong)

**Overlord actions**:
- Create tickets in correct dependency order
- Update operational specification if needed
- Update work graph dependencies
- May escalate to human if requirements fundamentally unclear

#### Level 4: Human (Requirements Ambiguity)

**Scenario**: Fundamental requirements issue, unclear what system should do

**Trigger**: Overlord identifies fundamental ambiguity

**Human (Palpatine) actions**:
- Clarify requirements
- Update operational specification
- Provide guidance on intended functionality
- Overlord then creates appropriate tickets

### Test Modification Process

**Tests are code and follow the same process as code changes:**

1. **Create ticket**: "Fix test: [description of issue]"
2. **Label**: `type:test-fix`, `area:testing`
3. **Assign**: Test engineer worker (specialized agent)
4. **Review**: Same review process as code
5. **Merge**: Tests must pass (including the fixed test)
6. **Traceability**: Test changes are tracked like code changes

**Why**: Maintains traceability, prevents ad-hoc changes, ensures tests are reviewed for correctness.

### Test Quality Monitoring

**Supervisor monitors for**:
- Repeated failures on same test (may indicate poor test quality)
- Tests that frequently need arbitration (may indicate spec/test mismatch)
- Tests that are too implementation-specific (may indicate poor test design)

**Supervisor actions**:
- Flag problematic tests: "Review test: [test name] for correctness"
- Create tickets to improve test quality
- Update test writing guidelines if patterns emerge

---

## Definition of Done

### For Test Tickets

- [ ] Test file created and executable
- [ ] Tests cover interface contract (types, shapes, errors)
- [ ] Tests are documented (what they verify, why)
- [ ] Tests pass (may be failing initially if TDD)
- [ ] Tests are integrated into `check.sh` (if applicable)

### For Implementation Tickets

- [ ] **Implementation matches operational specification** (primary requirement)
- [ ] All interface contract tests pass
- [ ] Unit tests written (TDD) and passing
- [ ] Code coverage meets wave threshold
- [ ] `./scripts/check.sh` passes
- [ ] Integration tests pass (if applicable)
- [ ] Documentation updated
- [ ] PR includes test evidence (CI link or gate output)
- [ ] **Review verifies implementation delivers value per spec, not just passes tests**

### For Integration Test Tickets

- [ ] Integration test file created
- [ ] Tests verify component interactions
- [ ] Tests use realistic data flows
- [ ] Tests pass
- [ ] Tests integrated into `check.sh`

### For System Test Tickets

- [ ] Black box tests created from operational spec
- [ ] Tests verify user workflows
- [ ] Tests use realistic inputs
- [ ] Test battery collected (if needed)
- [ ] Tests pass
- [ ] Tests integrated into `check.sh`

---

## Integration with Workflow Phases

### Phase 0: Bootstrap

**Testing-related tasks**:
- Create `tests/` directory structure (empty initially)
- Create `contracts/` directory for interface specifications
- Create minimal `check.sh` (may just verify structure exists)
- Set up test infrastructure (test runner, coverage tools)

**Reference**: See [Phase 0](./OVERLORD-GREENFIELD-WORKFLOW.md#phase-0-bootstrap-determinism--autonomy) in workflow document.

### Phase 1: Brainstorm & Converge

**Testing-related outputs**:
- **Testing Strategy Document** (this document, high-level version in operational spec)
- Operational specification (includes testing requirements)
- Initial test battery requirements (if needed)

**Reference**: See [Phase 1](./OVERLORD-GREENFIELD-WORKFLOW.md#phase-1-brainstorm-and-converge) in workflow document.

### Phase 2: Work Graph

**Testing-related tasks**:
- Create test tickets for interface contracts (Wave 0)
- Create implementation tickets with TDD requirements
- Create integration test tickets (Wave 2+)
- Create system test tickets (based on operational spec)

**Reference**: See [Phase 2](./OVERLORD-GREENFIELD-WORKFLOW.md#phase-2-compile-tasks-into-ordered-work-graph) in workflow document.

### Phase 4: Dispatch

**Testing enforcement**:
- Workers must run `./scripts/check.sh` before PRs
- Tests must pass before merge
- CI runs cumulative test suite

**Reference**: See [Phase 4](./OVERLORD-GREENFIELD-WORKFLOW.md#phase-4-dispatch--run-multiclaude-in-waves) in workflow document.

---

## Summary: The Testing Ratchet

The testing strategy creates a **ratchet mechanism** that ensures provable correctness:

1. **Tests define the target** - Agents work to make tests pass
2. **Tests are cumulative** - Once added, they stay forever
3. **Tests are wave-aware** - Organized by layer, executed cumulatively
4. **Tests get stricter** - Thresholds increase, tests never weaken
5. **Tests are comprehensive** - Interface → Unit → Integration → System
6. **Tests are traceable** - Linked to specifications, contracts, and requirements

**Result**: The system self-organizes to meet test requirements, and the ratchet only moves forward. Progress is permanent. Correctness is provable.

---

## Ticket Templates

### Test Ticket Template

```markdown
## Test: [Component/Feature] Interface Contract

**Type**: Test
**Layer**: Interface / Unit / Integration / System
**Wave**: [Wave number]

### Test Specification

**What to test**: [Clear description of behavior to test]
**Operational spec reference**: [Section X.Y of operational specification]
**Interface contract**: [Reference to contract file]

**Expected behaviors**:
- [ ] Input: [description] → Output: [description]
- [ ] Error condition: [description] → Error: [description]
- [ ] Edge case: [description] → Behavior: [description]

### Access Restrictions

⚠️ **IMPORTANT**: Test implementation code should NOT be accessible to implementation workers.
- Workers should only see this test specification
- Workers should implement based on operational spec, not test code
- Test results (pass/fail) will validate implementation

### Definition of Done

- [ ] Test file created with specification above
- [ ] Tests cover all behaviors listed
- [ ] Tests are documented
- [ ] Tests integrated into check.sh
- [ ] Test implementation is NOT exposed to implementation workers
```

### Implementation Ticket Template

```markdown
## Implement: [Component/Feature]

**Type**: Implementation
**Wave**: [Wave number]
**Depends on**: [Test ticket IDs]

### Primary Goal

**Implement per operational specification**: [Section X.Y]
**Deliver value**: [What value this delivers to users/system]

### Implementation Guidance

**DO**:
- ✅ Read operational specification section [X.Y]
- ✅ Read user manual section [X.Y] (if applicable)
- ✅ Review interface contract: [contract file]
- ✅ Write unit tests first (TDD), then implement
- ✅ Focus on delivering value per the specification

**DO NOT**:
- ❌ Access test implementation code from dependent test tickets
- ❌ Implement to pass tests; implement to meet specification
- ❌ Look at test code to understand requirements

### Test Validation

Tests from [test ticket IDs] will validate your implementation.
- Tests are validation tools, not implementation guides
- If tests fail, check your implementation against the operational spec
- If you believe a test is wrong, create issue with label `blocker:test-arbitration`

### Definition of Done

- [ ] Implementation matches operational specification (PRIMARY)
- [ ] Unit tests written (TDD) and passing
- [ ] All interface contract tests pass
- [ ] Code coverage meets wave threshold
- [ ] `./scripts/check.sh` passes
- [ ] Documentation updated
- [ ] PR includes test evidence
- [ ] Review verifies value delivery, not just test passing
```

---

## Next Steps

1. **Create Testing Strategy Document** in Phase 1 (high-level in operational spec, detailed here)
2. **Create test infrastructure** in Phase 0
3. **Create interface contract tests** in Wave 0
4. **Follow TDD with spec-first** in all implementation tickets
5. **Evolve CI** via tickets as system matures
6. **Enforce test access restrictions** via agent prompts and ticket structure

**Remember**: Testing is not a phase—it's woven into every phase. Tests are the ratchet that converts chaos into progress. But the system must embody value, not just pass tests.

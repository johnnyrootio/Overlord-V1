# GitHub Issue Format Guidance

Reference for how Overlord Phase 3 (Issue Emitter) should format and structure GitHub issues. Derived from the [robotic-barista](https://github.com/johnnyrootio/robotic-barista) repository so emitted issues match a proven, spec-first workflow.

---

## 1. Labels (GitHub API: `labels` array)

Use these **exact label names** when creating issues. Labels must exist in the target repo (create them if using a new repo).

| Namespace | Examples | When to use |
|-----------|----------|-------------|
| **wave:N** | `wave:0`, `wave:1`, `wave:2`, `wave:3` | From work graph; execution order. |
| **area:** | `area:testing`, `area:services`, `area:auth`, `area:cli`, `area:storage` | Domain/component from work graph. |
| **risk:** | `risk:low`, `risk:medium`, `risk:high` | From work graph risk. |
| **type:** | `type:test`, `type:implementation` | Test vs implementation task. |
| **layer:** | `layer:interface` | For test issues only; interface/contract vs unit/integration/system. |
| **tdd:required** | `tdd:required` | Implementation issues that must be done TDD. |
| **blocker:** | `blocker:test-arbitration` | Only for test-arbitration requests (spec vs test disagreement). |

**Example label sets:**

- Interface contract test: `wave:0`, `area:testing`, `risk:low`, `type:test`, `layer:interface`
- Implementation: `wave:1`, `area:services`, `risk:medium`, `type:implementation`, `tdd:required`
- Later test: `wave:3`, `area:testing`, `risk:low`, `type:test`

---

## 2. Title format

- **Clear, actionable**, optionally prefixed by kind:
  - **Test issues:** `Test: <what>` (e.g. `Test: CLI Commands Interface Contract`, `Test: Comprehensive Test Coverage`)
  - **Implementation issues:** `Implement: <what>` (e.g. `Implement: Order Placement`, `Implement: Authentication module`)
  - **Docs:** `Documentation: <what>` or `Docs: <what>`
- No issue number in the title; reference other issues in the body with `Depends on: #N`.

---

## 3. Body structure

Every issue body should be **Markdown** and include the following.

### 3.1 Header line (first line / first block)

Put type, wave, and dependencies in the first lines so they’re visible without scrolling:

```markdown
**Type**: Test
**Layer**: Interface
**Wave**: 0
```

or

```markdown
**Type**: Implementation
**Wave**: 1
**Depends on**: #6
```

Use **Depends on: #N** (or **Depends on: #N, #M**) whenever the work graph has `depends_on` for that task.

### 3.2 Test issues

- **Test Specification** (or **Description**): what to test, operational spec reference, **contract file** (e.g. `contracts/cli-commands.yaml`, `contracts/data-schema.json` per docs/PROJECT-REPO-LAYOUT).
- **Access Restrictions**: state that test implementation code is NOT visible to implementation workers; they implement to spec and contracts; tests validate.
- **Files to Touch**: paths to create/update: **contracts/** (e.g. `contracts/cli-commands.yaml`, `contracts/data-schema.json`), **tests/interfaces/** (interface contract tests), `scripts/check.sh` if applicable.
- **Definition of Done**: checkboxes; must include `./scripts/check.sh` passes and any layer-specific criteria.

### 3.3 Implementation issues

- **Primary Goal** (or **Goal**): implement per operational spec section X; one-line value delivered.
- **Implementation Guidance**: DO (read spec, TDD, deliver to spec) and DO NOT (no access to test code, don’t implement only to pass tests).
- **Files to Touch**: paths to create/update.
- **Definition of Done**: checkboxes; must include “implementation matches operational spec”, “`./scripts/check.sh` passes”, and “unit tests written (TDD) and passing” where applicable.

### 3.4 Definition of Done (all issues)

- Use `- [ ]` checkboxes.
- Always include: `- [ ] \`./scripts/check.sh\` passes`.
- For implementation: “Implementation matches operational specification” as primary; “Unit tests written (TDD) and passing” when TDD applies.
- For tests: “Tests integrated into check.sh” / “Tests pass” and “Test implementation is NOT exposed to implementation workers” where relevant.

---

## 4. Real examples (robotic-barista)

### 4.1 Test issue (interface contract)

**Title:** `Test: CLI Commands Interface Contract`  
**Labels:** `wave:0`, `area:testing`, `risk:low`, `type:test`, `layer:interface`

```markdown
## Test: CLI Commands Interface Contract

**Type**: Test
**Layer**: Interface
**Wave**: 0

### Test Specification

**What to test**: Create interface contract tests for all CLI commands. Define expected input/output formats, error message formats, and exit codes.

**Operational spec reference**: `docs/operational-specification.md` (CLI Commands section)
**Interface contract**: `contracts/cli-commands.yaml` (to be created)

**Expected behaviors**:
- [ ] CLI command interfaces defined in `contracts/cli-commands.yaml`
- [ ] All command argument parsing tested
- [ ] Output format consistency verified
- [ ] Error message formats verified
- [ ] Exit codes verified (0 for success, non-zero for errors)

### Access Restrictions

⚠️ **IMPORTANT**: Test implementation code should NOT be accessible to implementation workers.
- Workers should only see this test specification
- Workers should implement based on operational spec, not test code
- Test results (pass/fail) will validate implementation

### Files to Touch

- Create: `contracts/cli-commands.yaml`
- Create: `tests/interfaces/cli-commands-contract.test.py`
- Update: `scripts/check.sh` (add interface tests)

### Definition of Done

- [ ] Contract file created (`contracts/cli-commands.yaml`)
- [ ] Interface tests created in `tests/interfaces/cli-commands-contract.test.py`
- [ ] Tests cover all behaviors listed
- [ ] Tests are documented
- [ ] Tests integrated into `check.sh`
- [ ] Tests pass
- [ ] Test implementation is NOT exposed to implementation workers
- [ ] `./scripts/check.sh` passes
```

### 4.2 Implementation issue

**Title:** `Implement: Order Placement`  
**Labels:** `wave:1`, `area:services`, `risk:medium`, `type:implementation`, `tdd:required`

```markdown
## Implement: Order Placement

**Type**: Implementation
**Wave**: 1
**Depends on**: #6

### Primary Goal

**Implement per operational specification**: Order place command section
**Deliver value**: Users can place orders for drinks.

### Implementation Guidance

**DO**:
- ✅ Read operational specification (order place command section)
- ✅ Support recipe names (not just IDs)
- ✅ Write unit tests first (TDD), then implement
- ✅ Focus on delivering value per the specification

**DO NOT**:
- ❌ Access test implementation code
- ❌ Implement to pass tests; implement to meet specification

### Files to Touch

- Create: `src/robotic_barista/services/order_service.py` (partial - placement only)
- Create: `tests/unit/services/test_order_service_placement.py`

### Definition of Done

- [ ] Implementation matches operational specification (PRIMARY)
- [ ] Order placement works correctly (PLACED state)
- [ ] Recipe names supported (not just IDs)
- [ ] Unit tests written (TDD) and passing
- [ ] Code coverage >= 70%
- [ ] `./scripts/check.sh` passes
- [ ] Documentation updated
- [ ] PR includes test evidence
```

### 4.3 Test issue (later wave, with dependency)

**Title:** `Test: Comprehensive Test Coverage`  
**Labels:** `wave:3`, `area:testing`, `risk:low`, `type:test`

```markdown
## Test: Comprehensive Test Coverage

**Type**: Test
**Wave**: 3
**Depends on**: #17

### Description

Ensure comprehensive test coverage across all layers.

### Files to Touch

- Review all test files
- Add missing test cases
- Update coverage thresholds

### Definition of Done

- [ ] Code coverage >= 80%
- [ ] All test layers have adequate coverage
- [ ] Edge cases covered
- [ ] `./scripts/check.sh` passes
```

### 4.4 Test arbitration (special)

**Title:** `Test Arbitration: <short description>`  
**Labels:** `blocker:test-arbitration` only

Use when an implementer believes the spec is correct and the test is wrong. Body: which tests fail, spec reference, and why implementation follows spec.

---

## 5. Issues vs pull requests

- **Phase 3 creates issues**, not PRs. Each work-graph task becomes **one GitHub issue** with the structure above.
- PRs are created later (e.g. by workers) and reference issues in the body with `Closes #N`. PR titles in robotic-barista often use prefixes like `feat:`, `test:`, `Documentation:` and append `(Issue #N)`.

---

## 6. Checklist for Phase 3 agent

When emitting issues:

- [ ] One issue per work graph task.
- [ ] Title: `Test: …` or `Implement: …` (or `Documentation: …`) as appropriate.
- [ ] Labels: `wave:N`, `area:<area>`, `risk:<level>`, `type:test` or `type:implementation`; add `layer:interface` for interface tests, `tdd:required` for TDD implementation tasks.
- [ ] Body starts with **Type**, **Wave**, and **Depends on: #N** when the task has dependencies.
- [ ] Body includes Goal/Primary Goal, Implementation or Test guidance, Files to Touch, Definition of Done with checkboxes.
- [ ] Definition of Done includes `./scripts/check.sh` passes.
- [ ] Implementation issues state spec-first and test-access restrictions.

---

*Source: [johnnyrootio/robotic-barista](https://github.com/johnnyrootio/robotic-barista) issues (e.g. #1, #10, #18, #39). Use this doc as the reference for Phase 3 prompt details and examples.*

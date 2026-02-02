# Work Graph Example (workgraph.yml)

Example structure for `workgraph.yml`, derived from [johnnyrootio/robotic-barista](https://github.com/johnnyrootio/robotic-barista). Phase 2 (Wave Planner) produces this from Phase 1 artifacts (plan, tasks, operational spec, testing strategy). Phase 3 (Issue Emitter) creates one GitHub issue per task.

---

## Schema (summary)

- **waves:** list of waves (e.g. wave0 foundation, wave1 core, wave2 features, wave3 refinement).
- **Per wave:** `id`, `name`, `tasks`.
- **Per task:** `id`, `title`, `type` (test | implementation | documentation), `depends_on` (task ids), `area`, `risk`; for tests add `layer` (interface | integration | system), `test_specification`, `access_restriction`; for implementation add `tdd_required`, `primary_goal`, `implementation_guidance`, `validation`.

---

## Example (abbreviated)

```yaml
waves:
  - id: wave0
    name: foundation
    tasks:
      - id: T0.1
        title: Test: CLI Commands Interface Contract
        type: test
        layer: interface
        depends_on: []
        area: testing
        risk: low
        description: |
          Create interface contract tests for all CLI commands. Define expected input/output formats,
          error message formats, and exit codes.
        test_specification: |
          Tests should verify:
          - CLI command interfaces in contracts/cli-commands.yaml
          - All command argument parsing
          - Output format consistency
          - Error message formats
          - Exit codes (0 for success, non-zero for errors)
        access_restriction: |
          Test implementation code should NOT be accessible to implementation workers.
          Workers should only see test specifications and results.

      - id: T0.2
        title: Test: Data Schema Interface Contract
        type: test
        layer: interface
        depends_on: []
        area: testing
        risk: low
        description: |
          Create interface contract tests for JSON data schema. Define expected data structure,
          types, and validation rules.
        test_specification: |
          Tests should verify:
          - JSON schema in contracts/data-schema.json
          - Data structure validation
          - Type validation
          - Required fields
        access_restriction: |
          Test implementation code should NOT be accessible to implementation workers.

      - id: T0.3
        title: Implement: Domain Entities
        type: implementation
        tdd_required: true
        depends_on: [T0.1, T0.2]
        area: domain
        risk: medium
        primary_goal: |
          Implement domain entities per operational specification. Deliver value: Core business
          logic entities with validation and business rules.
        implementation_guidance: |
          - Read operational specification (domain entities section)
          - Write unit tests first (TDD), then implement
          - DO NOT access test implementation code from T0.1 or T0.2
          - If tests fail and you believe test is wrong, create blocker:test-arbitration issue
        validation: |
          Tests from T0.1 and T0.2 will validate your implementation.
          Implement to spec, not to pass tests.

  - id: wave1
    name: core
    tasks:
      - id: T1.1
        title: Implement: Recipe Service
        type: implementation
        tdd_required: true
        depends_on: [T0.5]
        area: services
        risk: medium
        primary_goal: |
          Implement RecipeService per operational specification section (recipe management).
          Deliver value: Users can create, list, and view recipes.
        implementation_guidance: |
          - Read operational specification (recipe commands section)
          - Write unit tests first (TDD), then implement

  - id: wave2
    name: features
    tasks:
      - id: T2.6
        title: Test: Black Box System Tests
        type: test
        layer: system
        depends_on: [T2.3, T2.4]
        area: testing
        risk: low
        description: |
          Create black box system tests derived from operational specification.
        test_specification: |
          Tests should verify:
          - All CLI commands as black box (execute via subprocess)
          - Complete user workflows end-to-end
          - Output format matches spec
          - Exit codes
        access_restriction: |
          These tests are derived from operational specification.
          Test implementation code should NOT be accessible to implementation workers.

  - id: wave3
    name: refinement
    tasks:
      - id: T3.1
        title: Test: Comprehensive Test Coverage
        type: test
        depends_on: [T2.6]
        area: testing
        risk: low
      - id: T3.2
        title: Documentation: Complete Documentation
        type: documentation
        depends_on: [T2.6]
        area: documentation
        risk: low
```

---

## Notes

- **Interface contracts** (Wave 0) reference `contracts/cli-commands.yaml` and `contracts/data-schema.json`; those files are created or updated by the interface contract tasks.
- **Operational spec** and **testing strategy** live in `docs/`; tasks reference "operational specification (section X)".
- **specs/** holds constitution, plan, specify, tasks from Phase 1; the work graph is derived from them and from docs (operational-spec, testing-strategy).
- Full example: [robotic-barista/workgraph.yml](https://github.com/johnnyrootio/robotic-barista/blob/main/workgraph.yml).

# Document Internalization: Critical Requirements

## The Problem

**What happened**: The Overlord read workflow documents but didn't internalize them properly. It:
- Skimmed documents as reference material rather than authoritative sources
- Missed critical emphasis (e.g., black box tests as Layer 4)
- Treated important components as supplementary rather than core
- Didn't verify design matched document requirements before presenting
- Didn't cross-reference specific document sections

**Root causes**:
- Surface-level reading without internalization
- Assumption of familiarity with concepts
- Rushing to completion instead of proper emphasis
- Missing connections between components
- No validation step before presenting designs

## The Solution: Mandatory Internalization Process

### Before Presenting Any Design Section

**You MUST follow this process**:

1. **Re-read relevant workflow documents** (don't just reference them):
   - Read the entire relevant section, not just skim
   - Identify all required components/layers
   - Note emphasis and priority markers (CRITICAL, IMPORTANT, etc.)
   - Identify relationships between components

2. **Identify all required components/layers**:
   - List every component mentioned in the document
   - Note which are required vs. optional
   - Note which are critical vs. supplementary
   - Note timing/phasing requirements

3. **Verify your design includes each with proper emphasis**:
   - If document says "CRITICAL", your design must say "CRITICAL"
   - If document emphasizes something, you must emphasize it equally
   - If document gives equal weight, you must give equal weight
   - Match document's priority hierarchy

4. **Cross-reference your design against the documents**:
   - Explicitly state: "Per [DOCUMENT].md section X.Y, [component]..."
   - Reference specific document sections
   - Explain relationships as documented
   - Verify your understanding matches document emphasis

### Document Internalization Checklist

**Before using information from any document**:

- [ ] I have re-read the relevant section (not just skimmed)
- [ ] I have identified all required components/layers
- [ ] I have noted emphasis markers (CRITICAL, IMPORTANT, etc.)
- [ ] I have identified relationships between components
- [ ] I have verified my design includes each component
- [ ] I have matched emphasis to document emphasis
- [ ] I have cross-referenced specific document sections
- [ ] I have verified my understanding matches the document

### Emphasis Matching Rules

**If document says**:
- "CRITICAL" → Your design must say "CRITICAL"
- "Core layer" → Your design must treat it as core
- "Derived from operational spec" → You must explain this relationship
- "Equal emphasis" → You must give equal emphasis to all items

**If document emphasizes something**:
- Give it equal or greater emphasis in your design
- Explain its relationship to other components
- Do not treat it as optional or secondary
- Reference the specific document section

### Cross-Reference Requirements

**When presenting design sections, you MUST explicitly state**:

- "Per TESTING-STRATEGY.md section X.Y, black box tests..."
- "Following OVERLORD-GREENFIELD-WORKFLOW.md Phase 1 requirement..."
- "As documented in SPEC-FIRST-ENFORCEMENT.md, tests validate..."
- "Per ECOSYSTEM-RULES/python/cursor-rules.md, we must..."

**This forces you to actually reference and follow the documents, not just mention them.**

## Specific Requirements by Design Section

### Testing Strategy Design

**Before presenting testing strategy, you MUST**:

1. **Re-read TESTING-STRATEGY.md sections on all layers**:
   - Layer 1: Interface Contract Tests (Wave 0)
   - Layer 2: Unit Tests (Wave 1, TDD)
   - Layer 3: Integration Tests (Wave 2+)
   - Layer 4: Black Box System Tests (ONGOING, derived from operational spec) ← **CRITICAL**

2. **Verify you've covered all 4 layers with proper emphasis**:
   - [ ] Interface contract tests (Wave 0, separate tickets)
   - [ ] Unit tests (Wave 1, TDD)
   - [ ] Integration tests (Wave 2+)
   - [ ] **Black box system tests (ONGOING, derived from operational spec)** ← **CRITICAL**
   - [ ] Each layer's purpose, timing, and relationship to spec-first development

3. **Note Layer 4 (Black Box) specifics**:
   - "Verify the system works correctly from an external perspective"
   - "Based on operational specification"
   - "Test system as a black box"
   - Located in `tests/system/black-box/` directory
   - Derived from operational specification (not implementation)
   - Ultimate validation layer for spec-first development

4. **Give Layer 4 equal emphasis to other layers**:
   - Don't treat it as supplementary
   - Don't mention it briefly
   - Explain its critical role in spec-first validation
   - Reference the specific directory structure

5. **Explicitly state relationships**:
   - "Per TESTING-STRATEGY.md, black box tests are Layer 4 and are derived from the operational specification"
   - "Black box tests validate that the system works correctly from an external perspective, as specified in the operational specification"
   - "This is the ultimate validation layer for spec-first development"

### Project Structure Design

**Before presenting project structure, you MUST**:

1. **Re-read relevant documents**:
   - ECOSYSTEM-RULES/[ecosystem]/project-structure.md
   - OVERLORD-GREENFIELD-WORKFLOW.md Phase 0 requirements
   - TESTING-STRATEGY.md directory structure requirements

2. **Verify all required directories**:
   - [ ] Source code structure (per ecosystem rules)
   - [ ] `tests/` directory structure
   - [ ] `tests/system/black-box/` directory (CRITICAL)
   - [ ] `contracts/` directory (if applicable)
   - [ ] `scripts/` directory (for check.sh)
   - [ ] `.github/workflows/` directory

3. **Cross-reference**:
   - "Per ECOSYSTEM-RULES/python/project-structure.md, we use src/ layout..."
   - "Per TESTING-STRATEGY.md, black box tests go in tests/system/black-box/..."

### CI/CD Pipeline Design

**Before presenting CI/CD design, you MUST**:

1. **Re-read relevant documents**:
   - OVERLORD-GREENFIELD-WORKFLOW.md Phase 0 CI/CD requirements
   - ECOSYSTEM-RULES/[ecosystem]/check.sh-template

2. **Verify all required components**:
   - [ ] check.sh gate script (CRITICAL - single gate)
   - [ ] CI runs check.sh (not duplicate commands)
   - [ ] All test layers run in CI
   - [ ] Black box tests included in CI

3. **Cross-reference**:
   - "Per OVERLORD-GREENFIELD-WORKFLOW.md, CI must run ./scripts/check.sh..."
   - "Per TESTING-STRATEGY.md, CI must run all 4 test layers including black box tests..."

## Completeness Check Process

**Before finalizing any design section**:

1. **List all components mentioned in relevant documents**:
   - Go through each relevant document
   - List every component/layer/requirement
   - Note emphasis level for each

2. **Verify each is included in your design**:
   - Check your design against the list
   - Ensure nothing is missing
   - Ensure nothing is treated as optional when it's required

3. **Verify emphasis matches document emphasis**:
   - If document says "CRITICAL", your design must say "CRITICAL"
   - If document emphasizes something, you must emphasize it
   - If document gives equal weight, you must give equal weight

4. **If something is "critical" in the doc, it must be "critical" in your design**:
   - Match priority levels
   - Match emphasis levels
   - Match relationship descriptions

## Validation Gates

**After reading a document, before using that information**:

1. **Summarize the key points** (especially emphasis/priority):
   - What are the critical components?
   - What are the required components?
   - What are the optional components?
   - What is the priority hierarchy?

2. **Identify what must be included vs. what's optional**:
   - Required components must be in your design
   - Optional components can be mentioned
   - Critical components must be emphasized

3. **Note any critical relationships**:
   - "Black box tests derived from operational spec"
   - "Tests validate implementation, not guide it"
   - "Spec-first development requires black box validation"

4. **Verify your understanding matches the document's emphasis**:
   - Does your emphasis match?
   - Does your priority hierarchy match?
   - Do your relationships match?

## Example: Proper Testing Strategy Presentation

**BAD** (what happened):
```
Testing Strategy:
- Unit tests (TDD)
- Integration tests
- Black box tests (also important)
```

**GOOD** (what should happen):
```
Testing Strategy (per TESTING-STRATEGY.md):

The testing strategy follows a 4-layer approach as documented in TESTING-STRATEGY.md:

1. **Layer 1: Interface Contract Tests** (Wave 0, separate tickets)
   - Per TESTING-STRATEGY.md section X.Y, these define contracts between components
   - Created as separate tickets before implementation

2. **Layer 2: Unit Tests** (Wave 1, TDD)
   - Per TESTING-STRATEGY.md section X.Y, these follow TDD approach
   - Written alongside implementation

3. **Layer 3: Integration Tests** (Wave 2+)
   - Per TESTING-STRATEGY.md section X.Y, these test component interactions
   - Created after unit tests

4. **Layer 4: Black Box System Tests** (ONGOING, derived from operational spec) ← **CRITICAL**
   - Per TESTING-STRATEGY.md section X.Y, these verify the system works correctly from an external perspective
   - **Derived from operational specification** (not implementation)
   - Located in `tests/system/black-box/` directory
   - **This is the ultimate validation layer for spec-first development**
   - Tests the system as a black box, validating it meets the operational specification
   - Ongoing throughout development, not just at the end

**Relationship to Spec-First Development**:
Per SPEC-FIRST-ENFORCEMENT.md, black box tests are the primary validation mechanism. They test the system against the operational specification, ensuring implementation delivers value as specified, not just passes unit tests.
```

## Integration with Phase Gates

**These internalization requirements are enforced at phase gates**:

- **Gate 2 (Brainstorming Completion)**: Verify all design sections have been properly internalized
- **Gate 4 (Plan Approval)**: Verify plan includes all required components with proper emphasis
- **Gate 5 (Execution Approval)**: Verify execution plan matches document requirements

**At each gate, verify**:
- [ ] All relevant documents have been re-read (not just skimmed)
- [ ] All required components are included
- [ ] Emphasis matches document emphasis
- [ ] Cross-references are explicit
- [ ] Completeness check has been performed

## Remember

**The core issue**: Treating documents as reference material to skim rather than authoritative sources to follow precisely.

**The solution**: 
- Re-read documents before using information
- Internalize emphasis and priorities
- Cross-reference explicitly
- Verify completeness and emphasis match
- Treat documents as authoritative sources, not suggestions

**Documents are not suggestions - they are requirements to follow precisely.**

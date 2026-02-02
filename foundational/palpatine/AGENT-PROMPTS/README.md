# Agent Prompt Templates: Augmenting Overrides

## Overview

These agent prompt templates **augment** multiclaude's default prompts with spec-first development enforcement. They are designed to work alongside defaults, but use judgment when conflicts arise—our prompts take precedence when they better serve our purposes.

## How Augmenting Mode Works

### multiclaude's Prompt Loading

When multiclaude spawns an agent, it loads prompts in this order:

1. **Default prompt** (embedded in multiclaude, evolves over time)
2. **Repository override** (from `<repo>/.multiclaude/agents/<agent>.md`)
3. **Combined result** = Default + Repository override = Complete prompt

**Important**: multiclaude appends the repository override as "Repository-specific instructions" after the default prompt. This means:
- Repository instructions come **after** defaults
- Later instructions can override earlier ones when they conflict
- Use judgment: if our prompts are better for our purposes, they take precedence

### What This Means

**You get**:
- ✅ Default multiclaude behavior (task completion, PR creation, etc.)
- ✅ Spec-first enforcement (implement to spec, not to pass tests) - **takes precedence when it conflicts**
- ✅ Test access restrictions - **authoritative for our workflow**
- ✅ Test arbitration process - **our process, not default**
- ✅ **Automatic improvements** from multiclaude defaults (when they don't conflict)

**When conflicts arise**:
- Our prompts are designed for spec-first enforcement
- They may evolve to be better for our specific use case
- Use judgment: prioritize what serves spec-first enforcement best
- Don't diminish the effect of our prompts to preserve defaults

## Files

- `worker.md` - Adds spec-first implementation guidance to default worker prompt
- `supervisor.md` - Adds test arbitration protocol to default supervisor prompt
- `reviewer.md` - Adds spec compliance verification to default review prompt

## Usage

### In Phase 0 (Bootstrap)

The Overlord copies these templates to your repository:

```bash
cp palpatine/AGENT-PROMPTS/worker.md <repo>/.multiclaude/agents/
cp palpatine/AGENT-PROMPTS/supervisor.md <repo>/.multiclaude/agents/
cp palpatine/AGENT-PROMPTS/reviewer.md <repo>/.multiclaude/agents/
```

### multiclaude Automatically Uses Them

When multiclaude spawns agents:
- Checks `<repo>/.multiclaude/agents/<agent>.md` (finds your ADDITIVE override)
- Loads default prompt
- Combines: Default + ADDITIVE = Complete prompt
- Sends to Claude Code

**No configuration needed** - multiclaude finds them automatically.

## Customization

### Focused Override (Recommended)

Keep overrides focused on spec-first enforcement. Don't duplicate default behavior unless necessary for clarity.

**Good** (augmenting with clear intent):
```markdown
MODE: ADDITIVE (recommended)

## Spec-First Implementation

- Implement to operational specification (primary goal)
- Tests validate, don't guide implementation
- No access to test implementation code
```

**Also acceptable** (if needed for clarity/authority):
```markdown
MODE: ADDITIVE (recommended)

## Primary Goal Override

Your primary goal is to implement the operational specification to deliver value.
While you still complete your assigned task, your focus is spec compliance, not just passing tests.
```

### Updating Overrides

As multiclaude evolves, use judgment:

1. Check multiclaude changelog for default prompt improvements
2. **Evaluate**: Do the improvements serve spec-first enforcement?
3. **Decide**: Keep our prompts if they're better for our purposes
4. **Update**: Modify our prompts to incorporate useful defaults when appropriate
5. **Don't diminish**: If our prompts are better, prioritize them even if they conflict

## Benefits of Augmenting Mode

1. **Future-proof**: Get multiclaude improvements automatically (when they don't conflict)
2. **Focused maintenance**: Override what matters for spec-first enforcement
3. **Clear intent**: Override clearly states what it augments/overrides
4. **Judgment-based**: Use judgment to prioritize what serves our purposes best
5. **Evolution**: Our prompts can evolve to be better for our specific use case

## When to Use FULL REPLACE

**Use FULL REPLACE mode if**:
- Your prompts have evolved to be fundamentally better for your purposes
- You want complete control and accept missing upstream improvements
- You have a fundamentally different workflow

**For spec-first enforcement**: Use ADDITIVE mode (recommended), but use judgment when conflicts arise.

## Verification

After copying prompts to your repo, verify multiclaude sees them:

```bash
multiclaude agents list
# Should show your repo's prompts with "ADDITIVE" mode
```

## Summary

These augmenting overrides:
- ✅ Augment multiclaude's defaults (work alongside them)
- ✅ Add spec-first enforcement (authoritative for our workflow)
- ✅ Use judgment when conflicts arise (our prompts take precedence when better)
- ✅ Get automatic improvements from multiclaude (when they don't conflict)
- ✅ Can evolve to be better for our specific use case
- ✅ Don't diminish their effect to preserve defaults

Result: You get multiclaude's defaults where they help, plus authoritative spec-first enforcement that takes precedence when needed.

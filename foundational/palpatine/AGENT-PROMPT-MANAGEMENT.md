# Agent Prompt Management: Automated Overlord System

## Overview

The Overlord automatically detects when multiclaude's base agent prompts change and applies customizations to generate enhanced prompts. This system preserves your customizations while incorporating new base features automatically.

## How It Works

### Three-Tier System

1. **BASE/** - Snapshot of multiclaude's default templates (versioned)
2. **CUSTOMIZATIONS/** - Overlord customizations (what to add/change)
3. **GENERATED/** - Auto-generated enhanced prompts (base + customizations)

### Automated Update Process

The Overlord runs `scripts/update-agent-prompts.sh` which:

1. **Extracts base templates** from multiclaude repository
2. **Detects changes** by comparing with stored BASE/ versions
3. **Applies customizations** from CUSTOMIZATIONS/ files
4. **Generates enhanced prompts** in GENERATED/ directory

**Result**: Enhanced prompts that preserve customizations while incorporating new base features.

## Directory Structure

```
palpatine/AGENT-PROMPTS/
├── BASE/                          # Snapshot of multiclaude base templates
│   ├── merge-queue.md            # Base template (from multiclaude)
│   ├── merge-queue.version       # multiclaude version this was extracted from
│   ├── merge-queue.extracted     # Timestamp of extraction
│   ├── worker.md
│   ├── worker.version
│   └── ...
├── CUSTOMIZATIONS/                # Overlord customizations (edit these)
│   ├── merge-queue.md            # Customization instructions
│   ├── worker.md                 # Customization instructions
│   └── ...
├── GENERATED/                     # Auto-generated enhanced prompts (don't edit)
│   ├── merge-queue.md            # Base + customizations (auto-generated)
│   ├── worker.md                 # Base + customizations (auto-generated)
│   └── ...
└── CUSTOM-WORKERS/                # Custom worker types (standalone)
    ├── conflict-resolver.md
    └── ...
```

## Customization Format

Customization files in `CUSTOMIZATIONS/` define how to augment base templates:

```markdown
# Agent Name Customizations

> **Type**: Customization overlay
> **Purpose**: [What this customization adds]
> **Created**: [Date]

## Customization Instructions

### Section: "Section Name"

**Action**: [Insert new section | Enhance existing section | Replace section]

**Insert after**: [Line or section to insert after]

**Content**:
```markdown
[Content to insert or add]
```
```

### Example: Merge-Queue Conflict Handling

```markdown
### Section: "Before Merging Any PR"

**Action**: Enhance existing checklist

**Insert after line**: `- [ ] Aligns with ROADMAP.md?`

**Content**:
```markdown
- [ ] **PR is mergeable?** (`gh pr view <number> --json mergeable`)
```

### Section: "Merge Conflict Handling"

**Action**: Insert new section

**Insert after**: "Before Merging Any PR" section

**Content**:
```markdown
## Merge Conflict Handling

[Full conflict handling workflow...]
```
```

## Usage

### 1. Initial Setup (Phase 0)

During Phase 0, the Overlord:

```bash
# Extract base templates from multiclaude
./scripts/update-agent-prompts.sh

# Review generated prompts
ls palpatine/AGENT-PROMPTS/GENERATED/

# Copy to repository
cp palpatine/AGENT-PROMPTS/GENERATED/*.md <repo>/.multiclaude/agents/
```

### 2. Adding Customizations

To add a customization:

1. **Edit customization file** in `CUSTOMIZATIONS/`:
   ```bash
   vim palpatine/AGENT-PROMPTS/CUSTOMIZATIONS/merge-queue.md
   ```

2. **Regenerate enhanced prompts**:
   ```bash
   ./scripts/update-agent-prompts.sh
   ```

3. **Review generated prompt**:
   ```bash
   cat palpatine/AGENT-PROMPTS/GENERATED/merge-queue.md
   ```

4. **Update repository** (if needed):
   ```bash
   cp palpatine/AGENT-PROMPTS/GENERATED/merge-queue.md <repo>/.multiclaude/agents/
   ```

### 3. When multiclaude Upgrades

**The Overlord automatically handles this:**

```bash
# Update multiclaude repository
cd ../multiclaude
git pull
git checkout <new-version>

# Run update script (detects changes automatically)
cd ../project-overlord
./scripts/update-agent-prompts.sh
```

**What happens:**
1. Script extracts new base templates
2. Detects which templates changed
3. Applies your customizations to new bases
4. Generates updated enhanced prompts
5. Preserves all your customizations

**You review and commit:**
```bash
# Review changes
git diff palpatine/AGENT-PROMPTS/GENERATED/

# Test in sandbox repository
# If good, commit
git add palpatine/AGENT-PROMPTS/
git commit -m "Update agent prompts for multiclaude vX.Y"
```

### 4. Overlord Workflow Integration

The Overlord should:

1. **Check for base template changes** periodically:
   ```bash
   ./scripts/update-agent-prompts.sh
   ```

2. **If changes detected**, review and update:
   - Review generated prompts
   - Test in sandbox
   - Update all projects using enhanced prompts

3. **During Phase 0**, copy GENERATED/ prompts to repository:
   ```bash
   cp palpatine/AGENT-PROMPTS/GENERATED/*.md <repo>/.multiclaude/agents/
   ```

## Customization Actions

### Insert New Section

Adds a completely new section to the prompt:

```markdown
### Section: "New Section Name"

**Action**: Insert new section

**Insert after**: "Existing Section Name" section

**Content**:
```markdown
## New Section Name

[Content here]
```
```

### Enhance Existing Section

Adds content to an existing section:

```markdown
### Section: "Existing Section"

**Action**: Enhance existing section

**Insert after line**: `- [ ] Some checklist item`

**Content**:
```markdown
- [ ] New checklist item
```
```

### Replace Section

Replaces an entire section (use sparingly):

```markdown
### Section: "Section to Replace"

**Action**: Replace section

**Content**:
```markdown
## Section to Replace

[New content replacing entire section]
```
```

## Custom Worker Types

Custom worker types in `CUSTOM-WORKERS/` are standalone prompts (not based on multiclaude templates):

- `conflict-resolver.md` - Specialized worker for resolving merge conflicts
- `ci-fixer.md` - Specialized worker for fixing CI issues
- (Add more as needed)

These are copied directly to repositories (not auto-generated).

## Best Practices

### 1. Edit Customizations, Not Generated

**✅ DO**: Edit files in `CUSTOMIZATIONS/`
**❌ DON'T**: Edit files in `GENERATED/` (they're auto-generated)

### 2. Use Specific Insertion Points

Be specific about where to insert:
- Use exact line matches when possible
- Reference section names
- Use code block markers for precise placement

### 3. Test After Regeneration

Always test generated prompts:
```bash
# Regenerate
./scripts/update-agent-prompts.sh

# Review
diff palpatine/AGENT-PROMPTS/GENERATED/merge-queue.md <repo>/.multiclaude/agents/merge-queue.md

# Test in sandbox repository
```

### 4. Version Control

Commit all three directories:
- `BASE/` - Track multiclaude versions
- `CUSTOMIZATIONS/` - Your customizations
- `GENERATED/` - Generated prompts (for reference)

### 5. Document Customizations

Add comments in customization files explaining why:
```markdown
# Merge Queue Customizations

> **Purpose**: Add merge conflict detection and resolution
> **Why**: Default merge-queue doesn't handle conflicts automatically

## Customization Instructions

[Instructions...]
```

## Troubleshooting

### Base Template Not Found

**Error**: `Base template not found: merge-queue.md`

**Solution**: Check multiclaude path:
```bash
./scripts/update-agent-prompts.sh --multiclaude-path /path/to/multiclaude
```

### Customization Not Applied

**Problem**: Customization not appearing in generated prompt

**Solution**: 
1. Check customization file syntax
2. Verify insertion point exists in base
3. Review script output for errors

### Merge Conflicts in Generated Prompts

**Problem**: Generated prompt has formatting issues

**Solution**: 
1. Review customization instructions
2. Check insertion points are correct
3. Manually fix and update customization file

## Summary

**The automated system:**
1. ✅ Tracks base templates with versioning
2. ✅ Detects when multiclaude upgrades
3. ✅ Automatically applies customizations
4. ✅ Preserves customizations across upgrades
5. ✅ Generates enhanced prompts ready to use

**Workflow:**
1. Edit `CUSTOMIZATIONS/` files to define enhancements
2. Run `update-agent-prompts.sh` to regenerate
3. Review `GENERATED/` prompts
4. Copy to repositories during Phase 0
5. System automatically handles multiclaude upgrades

**Benefits:**
- ✅ Automatic: Detects changes, applies customizations
- ✅ Preserves: Customizations survive upgrades
- ✅ Maintainable: Clear separation of base vs. custom
- ✅ Versioned: Track multiclaude versions
- ✅ Testable: Review before deploying

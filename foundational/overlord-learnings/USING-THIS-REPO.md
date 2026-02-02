# Using This Repository: Quick Guide

This guide explains how to use this repository to start a new greenfield project with Cursor as the Overlord.

## The Workflow

1. **Clone this repository** in Cursor
2. **Create your project spec** in `greenfield-specs/`
3. **Have Cursor read the workflow documents**
4. **Provide your spec** to Cursor
5. **Let Cursor orchestrate** the entire project

## Step-by-Step

### Step 1: Clone the Repository

In Cursor, clone this repository to a project-specific directory:

```bash
# Recommended: Clone to a project-specific name
git clone https://github.com/johnnyrootio/project-overlord.git my-project-overlord
cd my-project-overlord

# This makes it clear this is the overlord setup for "my-project"
# The actual project repository will be created separately by the Overlord
```

**Why project-specific name?**
- Makes it clear which project this overlord session is for
- Allows you to run multiple overlord sessions in parallel for different projects
- The actual project repo (e.g., `robotic-barista`) will be created separately

### Step 2: Create Your Project Spec

Create a new file in `greenfield-specs/` with your project specification:

```bash
# Option 1: Copy the template
cp greenfield-specs/template.md greenfield-specs/my-project.md

# Option 2: Use an example as starting point
cp examples/robotic-barista-spec.md greenfield-specs/my-project.md

# Then edit with your project details
```

**Note**: The spec file is in the overlord repository. The actual project repository will be created separately by the Overlord.

**What to include in your spec**:
- Project name and description
- Goals and objectives
- Key requirements (functional and non-functional)
- Constraints (tech stack, platform, time, budget)
- Success criteria
- Any additional context

See `greenfield-specs/example-todo-app.md` for a complete example.

### Step 3: Initialize Cursor as Overlord

In Cursor, provide this prompt (or similar):

```
I want to start a new greenfield project using the multiclaude agentic workflow.

**Workflow Documents** (in this repository):
- multiclaude/palpatine/OVERLORD-GREENFIELD-WORKFLOW.md - Complete workflow guide
- multiclaude/palpatine/TESTING-STRATEGY.md - Testing philosophy
- multiclaude/palpatine/SPEC-FIRST-ENFORCEMENT.md - Spec-first enforcement
- multiclaude/palpatine/PHASE-0-PLANNING.md - Phase 0 planning guide
- multiclaude/palpatine/GETTING-STARTED.md - Getting started guide

**Your Role**: You are the Overlord orchestrator. Your job is to:

1. **Read and internalize** the workflow documents from multiclaude/palpatine/
2. **Read my project spec** from greenfield-specs/[spec-file].md
3. **Follow the complete workflow** from Phase 0 through Phase 8
4. **Use multiclaude's workspace agent** to coordinate work
5. **Enforce spec-first development** throughout

**Key Principles**:
- Operational specification is the source of truth
- Tests validate implementation, they don't guide it
- Workers implement to deliver value per spec, not to pass tests
- Phase 0 uses Claude Code superpowers for planning

Let's start! Read the workflow documents first, then read my spec in greenfield-specs/[spec-file].md
```

### Step 4: Provide Your Spec

Tell Cursor where your spec is:

```
Read my project specification from greenfield-specs/my-project.md
```

Or paste the spec content directly:

```
Here's my project specification:

[Paste your spec content]
```

### Step 5: Let the Overlord Work

Cursor (as Overlord) will:
1. Read and understand the workflow
2. Read your project spec
3. Ask about repository setup (name, visibility, owner)
4. Create the repository on GitHub
5. Execute Phase 0 (planning with superpowers, then bootstrap)
6. Proceed through all phases systematically

You'll be asked for input at key decision points, but the Overlord handles the orchestration.

## Example: Complete Session

```bash
# 1. Clone the repo
git clone https://github.com/johnnyrootio/project-overlord.git
cd project-overlord

# 2. Create your spec
cp greenfield-specs/template.md greenfield-specs/todo-app.md
# Edit todo-app.md with your details

# 3. Open Cursor and provide the initial prompt (see Step 3 above)

# 4. Tell Cursor to read your spec
# "Read my project specification from greenfield-specs/todo-app.md"

# 5. Let Cursor orchestrate!
```

## Tips

### Spec Quality

- **Be specific**: Clear requirements lead to better outcomes
- **Include constraints**: Tech stack, platform, time, budget
- **Define success**: Measurable success criteria
- **Provide context**: Any relevant background information

### Working with Cursor

- **Be explicit**: Tell Cursor exactly which files to read
- **Reference paths**: Use relative paths from the repo root
- **Check understanding**: Ask Cursor to summarize what it read
- **Provide feedback**: Correct misunderstandings early

### Repository Management

- **One spec per file**: Keep specs separate and organized
- **Use descriptive names**: `todo-app.md` not `spec1.md`
- **Version control**: Commit your specs to track changes
- **Examples**: Keep example specs for reference

## Troubleshooting

### Cursor Can't Find Files

**Problem**: Cursor says it can't find the workflow documents or spec

**Solution**:
- Verify you're in the repository root directory
- Use absolute paths if needed
- Check file names match exactly (case-sensitive)

### Spec Not Clear Enough

**Problem**: Cursor asks too many clarifying questions

**Solution**:
- Review `greenfield-specs/template.md` for required sections
- Look at `greenfield-specs/example-todo-app.md` for completeness
- Add more detail to your spec

### Workflow Not Starting

**Problem**: Cursor doesn't begin Phase 0

**Solution**:
- Verify Cursor read `OVERLORD-GREENFIELD-WORKFLOW.md`
- Explicitly tell Cursor: "Begin Phase 0: Bootstrap"
- Check that Cursor understands its role as Overlord

## Next Steps

- Read **[GETTING-STARTED.md](./multiclaude/palpatine/GETTING-STARTED.md)** for detailed instructions
- Review **[OVERLORD-GREENFIELD-WORKFLOW.md](./multiclaude/palpatine/OVERLORD-GREENFIELD-WORKFLOW.md)** to understand the complete workflow
- Check **[greenfield-specs/README.md](./greenfield-specs/README.md)** for spec guidelines

---

**Ready?** Create your spec in `greenfield-specs/` and let Cursor orchestrate your project!

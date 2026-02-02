# Quick Start: Your First Greenfield Project

## The 5-Minute Version

1. **Open Cursor**
2. **Copy prompt** from [INITIAL-OVERLORD-PROMPT.md](./INITIAL-OVERLORD-PROMPT.md) (or use the README from overlord-init.zip)
3. **Paste and customize** with your project details
4. **Answer repository questions** when asked (name, visibility, owner)
5. **Let Overlord orchestrate** - it handles everything

That's it! The Overlord will:
- Read the Palpatine workflow documents
- **Plan Phase 0** using Claude Code superpowers and Context7
- Bootstrap your repo (Phase 0 execution)
- Create specs (Phase 1)
- Organize work (Phase 2)
- Create issues (Phase 3)
- Spawn workers (Phase 4)
- Monitor and orchestrate (Phases 5-8)

---

## How Agent Prompts Work

### The Flow

```
1. You (Human) → Cursor (Overlord)
   "Start new project using Palpatine workflow"

2. Cursor (Overlord) → Reads Palpatine documents
   - OVERLORD-GREENFIELD-WORKFLOW.md
   - TESTING-STRATEGY.md
   - AGENT-PROMPTS/worker.md
   - etc.

3. Cursor (Overlord) → Initializes repository
   - Creates .multiclaude/agents/ directory
   - Copies AGENT-PROMPTS/*.md to .multiclaude/agents/
   - Commits to repository

4. Cursor (Overlord) → Spawns workers via multiclaude
   multiclaude worker create "Implement #102: Auth"

5. multiclaude → Loads agent prompt
   - Checks: <repo>/.multiclaude/agents/worker.md
   - Finds it (created by Overlord in step 3)
   - Loads prompt with spec-first guidance
   - Sends to Claude Code

6. Worker (Claude Code) → Receives prompt
   - Sees: "Implement to spec, not to pass tests"
   - Sees: "No access to test code"
   - Implements per operational specification
   - Tests validate implementation
```

### Key Point

**Agent prompts are in your repository**, not in multiclaude's codebase. The Overlord (Cursor) creates them during Phase 0 bootstrap, and multiclaude automatically uses them.

---

## File Locations

### Palpatine Documents (Reference)
```
multiclaude/palpatine/
  OVERLORD-GREENFIELD-WORKFLOW.md  ← Workflow guide
  TESTING-STRATEGY.md              ← Testing philosophy
  SPEC-FIRST-ENFORCEMENT.md        ← Enforcement guide
  GETTING-STARTED.md               ← This guide
  INITIAL-OVERLORD-PROMPT.md       ← Prompt template
  AGENT-PROMPTS/
    worker.md                      ← Template (copied to repo)
    supervisor.md                  ← Template (copied to repo)
    reviewer.md                    ← Template (copied to repo)
```

### Your Repository (Created by Overlord)
```
your-repo/
  .multiclaude/
    agents/
      worker.md      ← Copied from Palpatine/AGENT-PROMPTS/
      supervisor.md  ← Copied from Palpatine/AGENT-PROMPTS/
      reviewer.md    ← Copied from Palpatine/AGENT-PROMPTS/
  scripts/
    check.sh         ← The gate
  tests/             ← Test infrastructure
  contracts/         ← Interface contracts
  CLAUDE.md          ← Repo rules
```

### multiclaude State (Automatic)
```
~/.multiclaude/
  repos/
    your-repo/
      agents/        ← Optional local overrides
  state.json         ← Tracks repos, agents, etc.
```

---

## The Complete Sequence

### Step 1: You → Cursor
```
[Copy INITIAL-OVERLORD-PROMPT.md, customize, paste]
```

### Step 2: Cursor → Reads Documents
```
Cursor reads:
- OVERLORD-GREENFIELD-WORKFLOW.md
- TESTING-STRATEGY.md
- SPEC-FIRST-ENFORCEMENT.md
- AGENT-PROMPTS/*.md
```

### Step 3: Cursor → Asks You
```
"What repository should we use?"
```

### Step 4: You → Provide Repository
```
"https://github.com/myorg/myproject"
or
"Create new: myproject"
```

### Step 5: Cursor → Executes Phase 0
```bash
# Cursor runs these commands:
multiclaude start
multiclaude repo init https://github.com/myorg/myproject

# Cursor creates files:
mkdir -p .multiclaude/agents
cp palpatine/AGENT-PROMPTS/worker.md .multiclaude/agents/
cp palpatine/AGENT-PROMPTS/supervisor.md .multiclaude/agents/
cp palpatine/AGENT-PROMPTS/reviewer.md .multiclaude/agents/

# Cursor creates:
- scripts/check.sh
- .github/workflows/ci.yml
- CLAUDE.md
- tests/ directory structure
- contracts/ directory structure

# Cursor commits:
git add .
git commit -m "Phase 0: Bootstrap - agent-ready"
git push
```

### Step 6: Cursor → Proceeds Through Phases
```
Phase 1: Creates specs (asks you for requirements)
Phase 2: Creates work graph
Phase 3: Creates GitHub issues
Phase 4: Spawns workers (multiclaude uses agent prompts from repo)
Phase 5-8: Orchestrates continuously
```

---

## Verification

After Phase 0, verify agent prompts are in place:

```bash
# Check repository
cd your-repo
ls -la .multiclaude/agents/
# Should show: worker.md, supervisor.md, reviewer.md

# Check multiclaude sees them
multiclaude agents list
# Should list your repo's prompts

# Check one prompt
cat .multiclaude/agents/worker.md
# Should show spec-first guidance from Palpatine template
```

---

## Common Questions

### Q: Do I need to manually copy agent prompts?

**A**: No. The Overlord (Cursor) does this automatically in Phase 0. You just provide the initial prompt.

### Q: What if I want to customize agent prompts?

**A**: Edit `.multiclaude/agents/*.md` in your repository. They're version controlled. The Overlord can help you customize them.

### Q: How does multiclaude find the prompts?

**A**: multiclaude automatically checks:
1. `<repo>/.multiclaude/agents/<agent>.md` (your repo - highest priority)
2. `~/.multiclaude/repos/<repo>/agents/<agent>.md` (local override)
3. Built-in default (fallback)

Since the Overlord creates them in your repo, multiclaude finds them automatically.

### Q: Can I start without the Palpatine directory?

**A**: Yes, but you need access to the documents. Options:
- Keep Palpatine directory in your workspace
- Copy Palpatine documents to your project
- Provide full paths to documents in initial prompt

### Q: What if I'm not using Cursor?

**A**: Any AI assistant can be the Overlord. Just:
- Give it the initial prompt
- Ensure it can read the Palpatine documents
- It will orchestrate the same way

---

## Next Steps

1. **Read** [GETTING-STARTED.md](./GETTING-STARTED.md) for detailed walkthrough
2. **Copy** [INITIAL-OVERLORD-PROMPT.md](./INITIAL-OVERLORD-PROMPT.md) prompt template
3. **Customize** with your project details
4. **Paste** into Cursor
5. **Let the Overlord orchestrate**!

The system is designed to be self-orchestrating. Once you kick it off, the Overlord handles the rest.

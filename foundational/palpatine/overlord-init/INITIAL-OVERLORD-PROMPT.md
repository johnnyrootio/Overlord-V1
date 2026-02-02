# Initial Overlord Prompt Template

Copy and paste this into Cursor to start a new greenfield project:

---

```
I want to start a new greenfield project using the multiclaude agentic workflow.

**Project**: [Your project name/description]
**Goal**: [What you want to build - e.g., "A todo app with authentication"]

**Workflow Documents** (located in `multiclaude/palpatine/`):
- OVERLORD-GREENFIELD-WORKFLOW.md - Complete workflow orchestration guide
- TESTING-STRATEGY.md - Comprehensive testing philosophy
- SPEC-FIRST-ENFORCEMENT.md - Spec-first development enforcement
- GETTING-STARTED.md - This getting started guide
- AGENT-PROMPTS/ - Agent prompt templates (worker.md, supervisor.md, reviewer.md)

**Your Role**: You are the Overlord orchestrator. Your job is to:

1. **Read and internalize** the workflow documents from `multiclaude/palpatine/`
2. **Guide me through Phase 0** (Bootstrap) - make the repo agent-ready
3. **Proceed through all phases** systematically:
   - Phase 1: Brainstorm & Converge (create specs)
   - Phase 2: Work Graph (organize tasks into waves)
   - Phase 3: GitHub Issues (create executable issues)
   - Phase 4: Dispatch (spawn workers via multiclaude)
   - Phase 5: Review + Fix Loop
   - Phase 6: Deadlock Breakers
   - Phase 7: Stop Conditions
   - Phase 8: Controller Loop (continuous operation)
4. **Use multiclaude's workspace agent** to coordinate work
5. **Enforce spec-first development** throughout (see SPEC-FIRST-ENFORCEMENT.md)

**Key Principles**:
- Operational specification is the source of truth
- Tests validate implementation, they don't guide it
- Workers implement to deliver value per spec, not to pass tests
- Agent prompts enforce this (you'll copy them from AGENT-PROMPTS/ to repo)

**First Steps**:
1. Read the workflow documents to understand the complete process
2. **Repository Setup** (for greenfield projects, we create a new repository):
   - Ask me: "What should we name the new repository?" (e.g., "todo-app", "api-service")
   - Ask me: "Should it be public or private?" (default: private)
   - Ask me: "Which GitHub organization/user should own it?" (default: your authenticated account)
   - **Then create the repository** using `gh repo create [name]` and initialize multiclaude
   - **If repository creation fails**: Ask me to create it manually and provide the URL
3. **Begin Phase 0: Bootstrap** - use Claude Code superpowers for planning:
   - Use `/superpowers:brainstorm` to plan the bootstrap
   - Use Context7 MCP to research best practices
   - Use `/superpowers:write-plan` to create detailed implementation plan
   - Review plan, then execute

**Note**: For greenfield projects, we assume a new repository will be created. If you want to use an existing repository instead, just tell me the URL.

**Phase 0 Checklist** (you'll execute):
- [ ] **PLANNING PHASE** (use Claude Code superpowers):
  - [ ] Invoke Claude Code CLI with `/superpowers:brainstorm` to plan bootstrap
  - [ ] Use Context7 MCP to research best practices for tech stack
  - [ ] Create detailed implementation plan with `/superpowers:write-plan`
  - [ ] Review and refine the plan before execution
- [ ] **EXECUTION PHASE** (implement per plan):
  - [ ] Initialize multiclaude with repository
  - [ ] Create testing infrastructure (tests/, contracts/ directories)
  - [ ] Create scripts/check.sh (the gate)
  - [ ] Set up CI to run check.sh
  - [ ] Create CLAUDE.md with repo rules (including spec-first rules)
  - [ ] Copy agent prompts from palpatine/AGENT-PROMPTS/ to <repo>/.multiclaude/agents/
  - [ ] Create hooks.json (lifecycle guardrails)
  - [ ] Verify everything is committed and pushed

**Important**: Phase 0 uses Claude Code superpowers for planning. No code should be written without a plan created using `/superpowers:brainstorm` and `/superpowers:write-plan`. Use Context7 MCP to research best practices before making decisions.

Let's start! What repository should we use?
```

---

## Customization

You can customize this prompt by:

1. **Adding project-specific context**:
   ```
   **Project Constraints**: 
   - Must use TypeScript
   - Must support Python 3.11+
   - Must be deployable to AWS
   ```

2. **Specifying tech stack**:
   ```
   **Tech Stack**: Node.js, TypeScript, PostgreSQL, Next.js
   ```

3. **Adding requirements**:
   ```
   **Key Requirements**:
   - User authentication with OAuth2
   - Real-time updates via WebSockets
   - Mobile-responsive UI
   ```

4. **Setting preferences**:
   ```
   **Preferences**:
   - Unattended mode: true (auto-accept workers)
   - Concurrency: 3 workers max per wave
   - Budget guard: $500/month
   ```

---

## What Happens Next

After you provide this prompt:

1. **Cursor reads** the Palpatine workflow documents
2. **Cursor understands** its role as Overlord
3. **Cursor asks** about repository setup
4. **Cursor executes** Phase 0 bootstrap
5. **Cursor proceeds** through all phases systematically

You'll be asked for input at key decision points, but the Overlord handles the orchestration.

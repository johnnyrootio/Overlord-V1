# Interactive Brainstorming: Critical Instructions

## The Problem

**What happened**: The Overlord referenced `/superpowers:brainstorm` but didn't actually run it. Instead, it:
- Read example specs
- Immediately created spec files
- Skipped the interactive brainstorming session
- Did not use Claude Code superpowers at all
- Did not ask questions or validate design with the user

**Why this happened**:
- Misinterpreted "use superpowers" as a concept rather than actually running commands
- Treated workflow as a checklist to execute rather than a collaborative process
- Assumed example spec was the final spec and proceeded to document it
- Jumped to implementation (creating files) instead of exploration (asking questions)

## The Solution: Explicit Instructions

### What NOT to Do

❌ **Don't just reference commands**:
```
# BAD: Just mentioning it
"I should use /superpowers:brainstorm"
# Then immediately creating files
```

❌ **Don't skip the interactive session**:
```
# BAD: Reading example spec → Creating files
Read example-spec.md → Create constitution.md → Create specify.md
```

❌ **Don't assume example specs are final**:
```
# BAD: Treating example as template to fill
Example spec exists → Copy structure → Fill in details → Done
```

### What TO Do

✅ **Actually execute the command**:
```bash
# GOOD: Actually run it in a terminal
claude -p "/superpowers:brainstorm

I need to bootstrap a new greenfield project. Let's plan:
- Tech stack selection
- Project structure
- Testing infrastructure
- CI/CD pipeline
- Development tooling
- Repository structure

Use Context7 to research best practices.
"
```

✅ **Have an interactive conversation**:
```
Overlord: "Let's start brainstorming. What programming language should we use?"
User: "Python"
Overlord: "Great! For a Python project, I recommend pytest for testing. Here's my proposed testing structure: [200-300 words]. Does this work for you?"
User: "Yes, but I'd like to add integration tests too"
Overlord: "Perfect! I'll include integration tests. Now let's discuss the project structure: [200-300 words]. Thoughts?"
User: "Looks good"
Overlord: [Continues with next section...]
```

✅ **Present sections and validate**:
- Present design sections (200-300 words each)
- Wait for user validation
- Iterate based on feedback
- Only proceed after validation

✅ **Create files only after validation**:
```
Brainstorming complete ✅
All sections validated ✅
User approved ✅
→ NOW create spec files or implementation plan
```

## Step-by-Step Process

### Step 1: Actually Run the Command

**You MUST execute this in a terminal**:
```bash
claude -p "/superpowers:brainstorm

I need to bootstrap a new greenfield project. Let's plan:
- Tech stack selection and rationale
- Project structure and organization
- Testing infrastructure design
- CI/CD pipeline architecture
- Development tooling and configuration
- Repository structure for agent-based development

Use Context7 to research best practices for [tech stack] and agent-based workflows.
"
```

**Do not skip this step. Do not just reference it. Actually run it.**

### Step 2: Interactive Conversation

During the brainstorming session:

1. **Ask questions one at a time**:
   - "What programming language should we use?"
   - Wait for response
   - "Should we use a framework? If so, which one?"
   - Wait for response

2. **Present design sections**:
   - After gathering input, present a 200-300 word design section
   - Example: "Here's my proposed project structure: [detailed explanation]"
   - Wait for user validation

3. **Iterate based on feedback**:
   - If user wants changes, refine the design
   - Present updated section
   - Get validation before moving to next section

4. **Use Context7 during conversation**:
   - Research best practices as you discuss
   - Incorporate findings into the conversation
   - Example: "Context7 suggests using pytest for Python testing. Here's why..."

### Step 3: Checkpoint Before Proceeding

**Do not proceed until**:
- ✅ All planning areas discussed
- ✅ User has validated each design section
- ✅ Tech stack selected and validated
- ✅ Architecture decisions made and confirmed
- ✅ User explicitly approves proceeding

**Only then**:
- Create implementation plan with `/superpowers:write-plan`
- Present plan to user
- Get approval
- Execute

## Example Flow

```
1. Overlord: "Let's start brainstorming. What programming language should we use?"
   User: "Python"
   
2. Overlord: "Great! For a Python project, I recommend pytest for testing. Here's my proposed testing structure: [200-300 words]. Does this work for you?"
   User: "Yes, but I'd like to add integration tests too"
   
3. Overlord: "Perfect! I'll include integration tests. Now let's discuss the project structure: [200-300 words]. Thoughts?"
   User: "Looks good"
   
4. Overlord: "Excellent! Let's talk about CI/CD. I propose using GitHub Actions with this pipeline: [200-300 words]. What do you think?"
   User: "That works"
   
5. Overlord: "Great! We've covered all the key areas. Let me create a detailed implementation plan based on our discussion."
   [Runs /superpowers:write-plan]
   
6. Overlord: "Here's the complete plan: [present plan]. Does this look good?"
   User: "Yes, let's proceed"
   
7. Overlord: [Now executes the plan]
```

## Key Principles

1. **Brainstorming is a conversation, not document creation**
2. **You must actually run commands, not just reference them**
3. **Ask questions one at a time and wait for responses**
4. **Present sections and validate before proceeding**
5. **Do not create files until brainstorming is complete and validated**
6. **The example spec is a starting point, not the final specification**

## Verification Checklist

Before creating any files, verify:
- [ ] I actually ran `claude -p "/superpowers:brainstorm"` in a terminal
- [ ] I had an interactive conversation with the user
- [ ] I asked questions one at a time and waited for responses
- [ ] I presented design sections (200-300 words) and got validation
- [ ] User has validated all sections
- [ ] User has explicitly approved proceeding
- [ ] Only then did I create implementation plan or spec files

## Remember

**The essence of the problem**: Treating the workflow as a checklist to execute rather than a collaborative process.

**The solution**: Actually run commands, have conversations, validate with the user, and only then create files.

# Greenfield Project Specs

This directory contains initial specifications for greenfield projects that will be orchestrated by the Overlord.

## How to Use

### Step 1: Create Your Spec

Create a new markdown file in this directory with your project specification. Name it descriptively, e.g.:
- `todo-app.md`
- `api-service.md`
- `data-pipeline.md`

### Step 2: Use the Template

Copy the template below or use `template.md` as a starting point. Include:
- Project name and description
- Goals and objectives
- Key requirements
- Constraints
- Tech stack preferences (if any)
- Any other relevant context

### Step 3: Provide to Overlord

1. **Clone this repository** in Cursor:
   ```bash
   git clone https://github.com/johnnyrootio/project-overlord.git
   cd project-overlord
   ```

2. **Have Cursor read the workflow documents**:
   - Point Cursor to `multiclaude/palpatine/OVERLORD-GREENFIELD-WORKFLOW.md`
   - Cursor will understand its role as Overlord

3. **Provide your spec**:
   - Tell Cursor: "Read the spec in `greenfield-specs/[your-spec].md`"
   - Or paste the spec content directly

4. **Start the workflow**:
   - Cursor will follow the workflow, starting with Phase 0
   - It will create a new repository and begin orchestration

## Spec Template

See `template.md` for a complete template you can copy and customize.

## Example Specs

- `example-todo-app.md` - Example todo application spec
- `example-api-service.md` - Example API service spec

## File Naming

Use descriptive, kebab-case names:
- ✅ `todo-app-with-auth.md`
- ✅ `real-time-chat-service.md`
- ❌ `spec1.md`
- ❌ `project.md`

# Repository Setup Guide

## Overview

Before starting Phase 0, you need a GitHub repository. The Overlord can work with either an existing repository or create a new one for you.

## Option A: Use Existing Repository

**When to use**: You already have a GitHub repository (empty or with some code).

**What to tell the Overlord**:
```
Repository: https://github.com/your-org/your-repo
```

**What the Overlord does**:
1. Uses `multiclaude repo init <url>` to initialize multiclaude with the existing repository
2. Clones the repository locally (if not already cloned)
3. Proceeds with Phase 0 bootstrap

**Requirements**:
- Repository must exist on GitHub
- You must have access to the repository
- GitHub CLI (`gh`) should be authenticated (for multiclaude operations)

## Option B: Create New Repository

**When to use**: You want to start a completely new project.

**What to tell the Overlord**:
```
Create a new repository called: [name]
```

**What the Overlord does**:
1. **Attempts to create the repository** using GitHub CLI:
   ```bash
   gh repo create <name> [--public|--private] [--org <org>]
   ```
2. **If creation succeeds**: Initializes multiclaude with the new repository URL
3. **If creation fails**: Asks you to create it manually, then provide the URL

**Requirements**:
- GitHub CLI (`gh`) installed
- GitHub CLI authenticated (`gh auth login`)
- Appropriate permissions to create repositories:
  - Personal account: Can create repos in your account
  - Organization: Must have repository creation permissions

**Repository Creation Options**:

The Overlord can create repositories with different visibility:

```bash
# Public repository
gh repo create my-project --public

# Private repository
gh repo create my-project --private

# In an organization
gh repo create my-project --org my-org --public
```

**If you want to specify options**, tell the Overlord:
```
Create a new private repository called: [name]
```
or
```
Create a new repository called: [name] in organization: [org]
```

## Troubleshooting

### "Repository not found" Error

**Problem**: `multiclaude repo init` fails with "repository not found"

**Solutions**:
1. **Verify the URL is correct**: Check for typos in the repository URL
2. **Check access**: Ensure you have access to the repository
3. **Verify authentication**: Run `gh auth status` to check GitHub CLI authentication
4. **Check repository exists**: Visit the URL in a browser to confirm it exists

### "Failed to create repository" Error

**Problem**: Overlord cannot create the repository using `gh repo create`

**Solutions**:
1. **Check authentication**: Run `gh auth status` and `gh auth login` if needed
2. **Check permissions**: Verify you have permission to create repositories in the target account/org
3. **Create manually**: Create the repository on GitHub.com, then provide the URL to the Overlord
4. **Check GitHub CLI version**: Ensure you have a recent version: `gh --version`

### "GitHub CLI not authenticated" Error

**Problem**: `gh` commands fail due to authentication

**Solution**:
```bash
# Authenticate GitHub CLI
gh auth login

# Follow the prompts to authenticate
# Choose: GitHub.com, HTTPS, Login with a web browser
```

### Repository Already Exists Locally

**Problem**: You already have the repository cloned locally

**Solution**: The Overlord will detect this and use the existing local clone. If you want to use a fresh clone, you can:
1. Remove the local directory
2. Let multiclaude clone it fresh
3. Or specify a different location

## Best Practices

### 1. Choose the Right Option

- **Use existing repository** if:
  - You already have a repo with some code
  - You want to add multiclaude to an existing project
  - You're working with a team repository

- **Create new repository** if:
  - Starting a completely new project
  - Want a clean slate for greenfield development
  - Need a fresh repository for testing

### 2. Repository Naming

Choose a clear, descriptive name:
- ✅ `todo-app` - Clear and descriptive
- ✅ `auth-service` - Indicates purpose
- ❌ `project1` - Too generic
- ❌ `test` - Too vague

### 3. Visibility Settings

- **Public**: Use for open-source projects or when you want public visibility
- **Private**: Use for proprietary code, personal projects, or when you need access control

### 4. Organization vs Personal

- **Personal account**: Simpler, good for individual projects
- **Organization**: Better for team projects, shared ownership, organization-level settings

## Example: Complete Setup Flow

### Scenario: New Project

**You**:
```
I want to start a new greenfield project using the multiclaude agentic workflow.

Project: Todo App with Authentication
Goal: Build a full-stack todo application with user authentication

Create a new repository called: todo-app
```

**Overlord**:
1. Checks if `gh` is authenticated
2. Creates repository: `gh repo create todo-app --private`
3. Initializes multiclaude: `multiclaude repo init https://github.com/your-username/todo-app`
4. Begins Phase 0 planning with superpowers

### Scenario: Existing Project

**You**:
```
I want to add multiclaude to my existing project.

Repository: https://github.com/my-org/api-service
```

**Overlord**:
1. Verifies repository exists and is accessible
2. Initializes multiclaude: `multiclaude repo init https://github.com/my-org/api-service`
3. Begins Phase 0 planning with superpowers

## Summary

- **Existing repo**: Just provide the URL, Overlord initializes multiclaude
- **New repo**: Tell Overlord to create it, it will use `gh repo create` then initialize
- **If creation fails**: Overlord will ask you to create it manually
- **Requirements**: GitHub CLI authenticated for both options

The Overlord handles the technical details - you just need to specify which option you prefer!

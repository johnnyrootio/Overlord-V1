# GitHub Permissions and Authentication

This document outlines the GitHub permissions and authentication requirements for the Overlord workflow.

## Required GitHub CLI Permissions

The Overlord needs GitHub CLI (`gh`) to be authenticated with the following scopes:

### Essential Scopes

1. **`repo`** - Full control of private repositories
   - Create repositories
   - Read and write repository contents
   - Create and manage issues
   - Create and manage pull requests
   - Manage repository settings

2. **`workflow`** - Update GitHub Action workflows
   - Push `.github/workflows/` files
   - Required for CI/CD setup in Phase 0

### How to Authenticate

```bash
# Authenticate with required scopes
gh auth login

# Or refresh existing token with workflow scope
gh auth refresh -s workflow

# Verify scopes
gh auth status
```

**Expected output**:
```
github.com
  ✓ Logged in to github.com as <username> (keyring)
  - Active account: true
  - Git operations protocol: https
  - Token scopes: 'gist', 'read:org', 'repo', 'workflow'
```

### Common Issues

#### Issue: "GitHub CLI token lacked the workflow scope"

**Problem**: Cannot push `.github/workflows/ci.yml` files

**Solution**:
```bash
gh auth refresh -s workflow
```

This adds the `workflow` scope to your existing token.

#### Issue: "Permission denied" when creating issues

**Problem**: Cannot create GitHub issues

**Solution**:
```bash
# Ensure 'repo' scope is included
gh auth refresh -s repo
```

#### Issue: "Repository creation failed"

**Problem**: Cannot create new repositories

**Solution**:
1. Check authentication: `gh auth status`
2. Verify `repo` scope is present
3. Check organization permissions (if creating in org)
4. Try: `gh auth refresh -s repo`

## Repository Permissions

### For Personal Repositories

- **Owner**: Full access (all operations work)
- No additional setup needed

### For Organization Repositories

The authenticated user needs:

1. **Repository creation permission** (if creating repos in org)
   - Set in organization settings
   - Requires "Write" or "Admin" role

2. **Issue creation permission**
   - Usually included with repository access
   - Requires "Write" or "Admin" role

3. **Workflow write permission**
   - Required to push `.github/workflows/` files
   - Usually included with "Write" or "Admin" role

### Checking Permissions

```bash
# Check if you can create repos in an org
gh api orgs/<org-name> --jq '.plan.name'

# Check repository permissions
gh repo view <org>/<repo> --json permissions
```

## Required Operations

The Overlord workflow requires these GitHub operations:

### Phase 0: Bootstrap
- ✅ Create repository (`gh repo create`)
- ✅ Push initial files (including `.github/workflows/ci.yml`)
- ✅ Set repository settings

### Phase 3: Create Issues
- ✅ Create GitHub issues (`gh issue create`)
- ✅ Add labels to issues
- ✅ Link issues to PRs

### Phase 4: Dispatch Workers
- ✅ Read repository contents
- ✅ Create branches
- ✅ Create pull requests (`gh pr create`)

### Phase 5: Review Loop
- ✅ Read PRs (`gh pr view`)
- ✅ Comment on PRs (`gh pr comment`)
- ✅ Merge PRs (via merge-queue)

## Verification Checklist

Before starting an Overlord session, verify:

- [ ] `gh auth status` shows you're logged in
- [ ] Token includes `repo` scope
- [ ] Token includes `workflow` scope
- [ ] Can create repositories: `gh repo create test-repo --private` (then delete it)
- [ ] Can create issues: Test in a test repository
- [ ] Organization permissions (if using org): Verify you have "Write" or "Admin" role

## Troubleshooting

### Refresh All Scopes

If you're missing scopes, refresh with all required scopes:

```bash
gh auth refresh -s repo,workflow
```

### Re-authenticate

If issues persist, re-authenticate:

```bash
gh auth logout
gh auth login
# Select: GitHub.com, HTTPS, Login with web browser
# Grant all requested permissions
```

### Check Organization Settings

For organization repositories:
1. Go to organization settings
2. Check "Member privileges"
3. Ensure "Repository creation" is enabled for your role
4. Check "Repository permissions" for workflow access

## Security Best Practices

1. **Use fine-grained tokens** when possible (GitHub feature)
2. **Rotate tokens regularly**
3. **Use organization-level tokens** for team projects
4. **Audit token usage** periodically
5. **Revoke unused tokens**

## Summary

**Minimum required scopes**:
- `repo` - For repository operations
- `workflow` - For pushing workflow files

**Verify with**:
```bash
gh auth status
gh auth refresh -s repo,workflow  # If needed
```

**Test with**:
```bash
gh repo create test-repo --private
gh issue create --repo test-repo --title "Test" --body "Test issue"
gh repo delete test-repo --yes
```

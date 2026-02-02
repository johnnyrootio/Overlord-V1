# multiclaude Setup and Usage

This guide explains how to install and use multiclaude on your system for the Overlord workflow.

## Installation

### Step 1: Install multiclaude

```bash
go install github.com/dlorenc/multiclaude/cmd/multiclaude@latest
```

This installs multiclaude to `~/go/bin/multiclaude`.

### Step 2: Add to PATH

Add Go's bin directory to your PATH so you can use `multiclaude` directly:

```bash
# For zsh (macOS default)
echo 'export PATH="$HOME/go/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# For bash
echo 'export PATH="$HOME/go/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Step 3: Verify Installation

```bash
multiclaude version
# Should output: multiclaude 0.0.0-dev
```

## Usage

### If multiclaude is in PATH

You can use it directly:
```bash
multiclaude version
multiclaude daemon start
multiclaude repo init https://github.com/org/repo
```

### If multiclaude is NOT in PATH

Use the full path:
```bash
~/go/bin/multiclaude version
~/go/bin/multiclaude daemon start
~/go/bin/multiclaude repo init https://github.com/org/repo
```

### Short Alias (Optional)

If `~/.local/bin` is in your PATH, you can create a short alias:

```bash
cat > ~/.local/bin/mc << 'EOF'
#!/bin/bash
multiclaude "$@"
EOF
chmod +x ~/.local/bin/mc
```

Then use `mc` instead of `multiclaude`:
```bash
mc version
mc daemon start
mc repo init https://github.com/org/repo
```

## Common Commands

### Daemon Management

```bash
# Start the daemon
multiclaude daemon start

# Check daemon status
multiclaude daemon status

# Stop the daemon
multiclaude daemon stop
```

### Repository Management

```bash
# Initialize a repository
multiclaude repo init https://github.com/org/repo

# List tracked repositories
multiclaude repo list

# Set default repository
multiclaude repo use <repo-name>
```

### Worker Management

```bash
# Create a worker for a task
multiclaude worker create "Implement feature X"

# List workers
multiclaude worker list

# View worker status
multiclaude worker status <worker-name>
```

### Getting Help

```bash
# General help
multiclaude --help

# Command-specific help
multiclaude repo --help
multiclaude worker --help
multiclaude daemon --help
```

## Troubleshooting

### "command not found: multiclaude"

**Problem**: multiclaude is not in your PATH.

**Solution**:
1. Check if it's installed: `ls ~/go/bin/multiclaude`
2. If installed, add to PATH (see Step 2 above)
3. Or use full path: `~/go/bin/multiclaude`

### "Daemon is not running"

**Problem**: The multiclaude daemon needs to be started.

**Solution**:
```bash
multiclaude daemon start
```

### "Connection error: failed to communicate with daemon"

**Problem**: Daemon is not running or socket file is missing.

**Solution**:
```bash
# Start the daemon
multiclaude daemon start

# Check status
multiclaude daemon status
```

## System-Specific Notes

### macOS

- Default shell: zsh
- Config file: `~/.zshrc`
- multiclaude installs to: `~/go/bin/multiclaude`

### Linux

- Default shell: bash (usually)
- Config file: `~/.bashrc` or `~/.bash_profile`
- multiclaude installs to: `~/go/bin/multiclaude` (or `$GOPATH/bin/multiclaude`)

### PATH Verification

Check if `~/go/bin` is in your PATH:
```bash
echo $PATH | grep -q "$HOME/go/bin" && echo "✅ In PATH" || echo "❌ Not in PATH"
```

## Integration with Overlord Workflow

When the Overlord (Cursor) needs to use multiclaude, it will:

1. **Check if multiclaude is available**:
   - Try `multiclaude` (if in PATH)
   - Fall back to `~/go/bin/multiclaude` (full path)

2. **Start the daemon** if needed:
   ```bash
   multiclaude daemon start
   ```

3. **Initialize repositories**:
   ```bash
   multiclaude repo init <github-url>
   ```

4. **Spawn workers**:
   ```bash
   multiclaude worker create "Task description"
   ```

## Next Steps

Once multiclaude is installed and in your PATH:

1. Start the daemon: `multiclaude daemon start`
2. Follow the [GETTING-STARTED.md](./GETTING-STARTED.md) guide
3. Use the Overlord workflow to orchestrate your projects

---

**Quick Reference**: 
- Install: `go install github.com/dlorenc/multiclaude/cmd/multiclaude@latest`
- Add to PATH: `echo 'export PATH="$HOME/go/bin:$PATH"' >> ~/.zshrc`
- Verify: `multiclaude version`
- Start: `multiclaude daemon start`

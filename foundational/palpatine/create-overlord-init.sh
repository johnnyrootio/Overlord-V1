#!/bin/bash
# Create overlord-init.zip package with all Palpatine components

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PALPATINE_DIR="$SCRIPT_DIR"
INIT_DIR="$PALPATINE_DIR/overlord-init"
ZIP_FILE="$PALPATINE_DIR/overlord-init.zip"

echo "Creating overlord-init package..."

# Create init directory structure
mkdir -p "$INIT_DIR/AGENT-PROMPTS"

# Clean up existing files (we'll copy fresh ones)
if [ -d "$INIT_DIR" ]; then
    echo "Cleaning up existing overlord-init directory..."
    # Remove everything except the directory structure
    find "$INIT_DIR" -mindepth 1 -maxdepth 1 ! -name "AGENT-PROMPTS" -exec rm -rf {} + 2>/dev/null || true
    find "$INIT_DIR/AGENT-PROMPTS" -type f -delete 2>/dev/null || true
fi

# Ensure directory structure exists
mkdir -p "$INIT_DIR/AGENT-PROMPTS"

# Copy core workflow documents
echo "Copying core workflow documents..."
cp "$PALPATINE_DIR/OVERLORD-GREENFIELD-WORKFLOW.md" "$INIT_DIR/"
cp "$PALPATINE_DIR/TESTING-STRATEGY.md" "$INIT_DIR/"
cp "$PALPATINE_DIR/SPEC-FIRST-ENFORCEMENT.md" "$INIT_DIR/"
cp "$PALPATINE_DIR/PHASE-0-PLANNING.md" "$INIT_DIR/"
cp "$PALPATINE_DIR/REPOSITORY-SETUP.md" "$INIT_DIR/"
cp "$PALPATINE_DIR/GETTING-STARTED.md" "$INIT_DIR/"
cp "$PALPATINE_DIR/QUICK-START.md" "$INIT_DIR/"

# Copy agent prompts
echo "Copying agent prompts..."
cp "$PALPATINE_DIR/AGENT-PROMPTS/worker.md" "$INIT_DIR/AGENT-PROMPTS/"
cp "$PALPATINE_DIR/AGENT-PROMPTS/supervisor.md" "$INIT_DIR/AGENT-PROMPTS/"
cp "$PALPATINE_DIR/AGENT-PROMPTS/reviewer.md" "$INIT_DIR/AGENT-PROMPTS/"
cp "$PALPATINE_DIR/AGENT-PROMPTS/README.md" "$INIT_DIR/AGENT-PROMPTS/"

# Copy reference documents (optional but useful)
echo "Copying reference documents..."
cp "$PALPATINE_DIR/INITIAL-OVERLORD-PROMPT.md" "$INIT_DIR/"
cp "$PALPATINE_DIR/multiclaude-agentic-workflow-v3_3_4.md" "$INIT_DIR/"

# Copy README.md (the entry point for Cursor) - must be done AFTER cleanup
# Check if README exists in source overlord-init directory (before cleanup)
README_SOURCE=""
if [ -f "$PALPATINE_DIR/overlord-init/README.md" ]; then
    README_SOURCE="$PALPATINE_DIR/overlord-init/README.md"
    echo "Found README.md source at: $README_SOURCE"
fi

# After all files are copied, copy README.md
if [ -n "$README_SOURCE" ]; then
    echo "Copying README.md (entry point for Cursor)..."
    cp "$README_SOURCE" "$INIT_DIR/README.md"
else
    echo "WARNING: README.md not found at $PALPATINE_DIR/overlord-init/README.md"
    echo "The package will be created but README.md will be missing."
    echo "Please create overlord-init/README.md before running this script."
fi

# Create the zip file
echo "Creating zip file..."
cd "$PALPATINE_DIR"
zip -r "overlord-init.zip" "overlord-init" -x "*.DS_Store" "*.git*" > /dev/null

# Clean up the directory (optional - comment out if you want to keep it)
# rm -rf "$INIT_DIR"

echo ""
echo "✅ Package created successfully!"
echo "📦 File: $ZIP_FILE"
echo ""
echo "Package contents:"
unzip -l "$ZIP_FILE" | grep -E "\.md$|\.txt$" | head -20
echo ""
echo "To use:"
echo "  1. Unzip overlord-init.zip"
echo "  2. Open Cursor"
echo "  3. Copy the prompt from overlord-init/README.md"
echo "  4. Paste into Cursor and customize"
echo "  5. Start your greenfield project!"
echo ""

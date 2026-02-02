#!/usr/bin/env bash
set -euo pipefail

# Update Agent Prompts: Automatically detect base template changes and apply customizations
#
# This script:
# 1. Extracts base templates from multiclaude
# 2. Detects if base templates have changed
# 3. Applies customizations from CUSTOMIZATIONS/
# 4. Generates enhanced prompts in GENERATED/
#
# Usage:
#   ./scripts/update-agent-prompts.sh [--force] [--multiclaude-path <path>]
#
# Options:
#   --force: Regenerate all prompts even if base hasn't changed
#   --multiclaude-path: Path to multiclaude repository (default: ../multiclaude)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OVERLORD_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PALPATINE_DIR="$OVERLORD_DIR/palpatine"
AGENT_PROMPTS_DIR="$PALPATINE_DIR/AGENT-PROMPTS"
BASE_DIR="$AGENT_PROMPTS_DIR/BASE"
CUSTOMIZATIONS_DIR="$AGENT_PROMPTS_DIR/CUSTOMIZATIONS"
GENERATED_DIR="$AGENT_PROMPTS_DIR/GENERATED"

MULTICLAUDE_PATH="${MULTICLAUDE_PATH:-$(cd "$OVERLORD_DIR/../multiclaude" 2>/dev/null && pwd || echo "")}"
FORCE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --force)
      FORCE=true
      shift
      ;;
    --multiclaude-path)
      MULTICLAUDE_PATH="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1" >&2
      echo "Usage: $0 [--force] [--multiclaude-path <path>]" >&2
      exit 1
      ;;
  esac
done

if [[ -z "$MULTICLAUDE_PATH" ]] || [[ ! -d "$MULTICLAUDE_PATH" ]]; then
  echo "ERROR: multiclaude repository not found" >&2
  echo "  Expected at: $OVERLORD_DIR/../multiclaude" >&2
  echo "  Or specify with: --multiclaude-path <path>" >&2
  exit 1
fi

MULTICLAUDE_TEMPLATES_DIR="$MULTICLAUDE_PATH/internal/templates/agent-templates"

if [[ ! -d "$MULTICLAUDE_TEMPLATES_DIR" ]]; then
  echo "ERROR: multiclaude templates directory not found: $MULTICLAUDE_TEMPLATES_DIR" >&2
  exit 1
fi

# Create directories
mkdir -p "$BASE_DIR" "$CUSTOMIZATIONS_DIR" "$GENERATED_DIR"

# Function to extract base template from multiclaude
extract_base_template() {
  local agent_name="$1"
  local template_file="$MULTICLAUDE_TEMPLATES_DIR/${agent_name}.md"
  
  if [[ ! -f "$template_file" ]]; then
    echo "WARNING: Base template not found: $template_file" >&2
    return 1
  fi
  
  # Copy to BASE directory with version info
  local base_file="$BASE_DIR/${agent_name}.md"
  local version_file="$BASE_DIR/${agent_name}.version"
  
  # Get multiclaude version (from git or version file)
  local multiclaude_version="unknown"
  if [[ -d "$MULTICLAUDE_PATH/.git" ]]; then
    multiclaude_version=$(cd "$MULTICLAUDE_PATH" && git describe --tags --always 2>/dev/null || echo "unknown")
  fi
  
  # Check if base has changed
  local base_changed=false
  if [[ -f "$base_file" ]] && [[ -f "$version_file" ]]; then
    local old_version=$(cat "$version_file" 2>/dev/null || echo "")
    if [[ "$old_version" != "$multiclaude_version" ]]; then
      base_changed=true
    elif ! diff -q "$template_file" "$base_file" >/dev/null 2>&1; then
      base_changed=true
    fi
  else
    base_changed=true
  fi
  
  if [[ "$base_changed" == "true" ]] || [[ "$FORCE" == "true" ]]; then
    echo "Extracting base template: $agent_name (version: $multiclaude_version)"
    cp "$template_file" "$base_file"
    echo "$multiclaude_version" > "$version_file"
    echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" > "$BASE_DIR/${agent_name}.extracted"
    return 0
  else
    echo "Base template unchanged: $agent_name"
    return 1
  fi
}

# Function to apply customizations
apply_customizations() {
  local agent_name="$1"
  local base_file="$BASE_DIR/${agent_name}.md"
  local customization_file="$CUSTOMIZATIONS_DIR/${agent_name}.md"
  local output_file="$GENERATED_DIR/${agent_name}.md"
  
  if [[ ! -f "$base_file" ]]; then
    echo "ERROR: Base template not found: $base_file" >&2
    return 1
  fi
  
  # If no customizations, just copy base
  if [[ ! -f "$customization_file" ]]; then
    echo "No customizations for $agent_name, using base template"
    cp "$base_file" "$output_file"
    return 0
  fi
  
  echo "Applying customizations to $agent_name..."
  
  # For now, use a simple Python script to apply customizations
  # This will be enhanced to parse the customization format
  python3 <<EOF
import sys
import re
from pathlib import Path

base_file = Path("$base_file")
customization_file = Path("$customization_file")
output_file = Path("$output_file")

# Read base template
base_content = base_file.read_text()

# Read customization file (simplified parser - will be enhanced)
# For now, we'll do a simple merge: append customization sections
# TODO: Implement proper section insertion based on customization instructions

customization_content = customization_file.read_text()

# Extract customization sections (between ## or ### headers)
# Simple approach: append customizations at the end for now
# Enhanced version will parse "Insert after" instructions

# Find where to insert (look for "Insert after" markers in customization)
# For MVP, append new sections from customization file

# Split customization into sections
custom_sections = []
current_section = None
in_section = False

for line in customization_content.split('\n'):
    if line.startswith('### Section:'):
        if current_section:
            custom_sections.append(current_section)
        current_section = {'header': line, 'content': []}
        in_section = True
    elif line.startswith('**Action**:') and current_section:
        current_section['action'] = line
    elif line.startswith('**Insert after**:') and current_section:
        current_section['insert_after'] = line
    elif line.startswith('**Content**:') and current_section:
        in_content = True
    elif line.startswith('```') and current_section:
        current_section['content'].append(line)
    elif in_section and current_section:
        current_section['content'].append(line)

if current_section:
    custom_sections.append(current_section)

# For MVP: Simple append of customization content
# Enhanced version will parse and insert at specific locations

# Add header to output
output_lines = [
    f"# {base_file.stem.replace('_', ' ').title()}: Enhanced",
    "",
    f"> **Based on**: multiclaude default template (version: $(cat "$BASE_DIR/${agent_name}.version"))",
    f"> **Overlord Enhancements**: Applied from customizations",
    f"> **Generated**: $(date -u +"%Y-%m-%d")",
    "",
    base_content,
    "",
    "---",
    "",
    "## Overlord Enhancements",
    "",
    customization_content.split("## Customization Instructions")[-1] if "## Customization Instructions" in customization_content else customization_content
]

output_file.write_text('\n'.join(output_lines))
EOF

  echo "Generated enhanced prompt: $output_file"
}

# Main: Process all agent templates
main() {
  echo "Updating agent prompts from multiclaude..."
  echo "  multiclaude path: $MULTICLAUDE_PATH"
  echo "  templates dir: $MULTICLAUDE_TEMPLATES_DIR"
  echo ""
  
  # Find all template files in multiclaude
  local agents=()
  for template_file in "$MULTICLAUDE_TEMPLATES_DIR"/*.md; do
    if [[ -f "$template_file" ]]; then
      local agent_name=$(basename "$template_file" .md)
      agents+=("$agent_name")
    fi
  done
  
  if [[ ${#agents[@]} -eq 0 ]]; then
    echo "ERROR: No agent templates found in $MULTICLAUDE_TEMPLATES_DIR" >&2
    exit 1
  fi
  
  echo "Found ${#agents[@]} agent templates: ${agents[*]}"
  echo ""
  
  local updated_count=0
  for agent_name in "${agents[@]}"; do
    if extract_base_template "$agent_name"; then
      updated_count=$((updated_count + 1))
    fi
    apply_customizations "$agent_name"
  done
  
  echo ""
  if [[ $updated_count -gt 0 ]]; then
    echo "✓ Updated $updated_count base templates"
    echo "✓ Generated enhanced prompts in $GENERATED_DIR"
    echo ""
    echo "Next steps:"
    echo "  1. Review generated prompts in $GENERATED_DIR"
    echo "  2. Test in a sandbox repository"
    echo "  3. Commit updated prompts if changes look good"
  else
    echo "✓ No base template updates needed (all up to date)"
  fi
}

main "$@"

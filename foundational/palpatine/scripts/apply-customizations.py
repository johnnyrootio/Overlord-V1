#!/usr/bin/env python3
"""
Apply customizations to base agent prompts.

This script parses customization files and applies them to base templates,
generating enhanced prompts that preserve customizations while incorporating
new base features.
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class Customization:
    """Represents a customization instruction."""
    
    def __init__(self, section_name: str, action: str, insert_after: Optional[str] = None, content: str = ""):
        self.section_name = section_name
        self.action = action  # "Insert new section", "Enhance existing section", "Replace section"
        self.insert_after = insert_after
        self.content = content


def parse_customization_file(customization_file: Path) -> List[Customization]:
    """Parse a customization file and extract customization instructions."""
    if not customization_file.exists():
        return []
    
    content = customization_file.read_text()
    customizations = []
    
    # Split into sections
    sections = re.split(r'^### Section:', content, flags=re.MULTILINE)
    
    for section in sections[1:]:  # Skip header
        lines = section.strip().split('\n')
        if not lines:
            continue
        
        section_name = lines[0].strip().strip('"')
        action = None
        insert_after = None
        content_lines = []
        in_content = False
        
        for line in lines[1:]:
            if line.startswith('**Action**:'):
                action = line.replace('**Action**:', '').strip()
            elif line.startswith('**Insert after**:'):
                insert_after = line.replace('**Insert after**:', '').strip()
            elif line.startswith('**Insert after line**:'):
                insert_after = line.replace('**Insert after line**:', '').strip()
            elif line.startswith('**Content**:'):
                in_content = True
            elif in_content:
                content_lines.append(line)
        
        if action and content_lines:
            customizations.append(Customization(
                section_name=section_name,
                action=action,
                insert_after=insert_after,
                content='\n'.join(content_lines)
            ))
    
    return customizations


def find_section_in_base(base_content: str, section_name: str) -> Optional[Tuple[int, int]]:
    """Find a section in the base content. Returns (start_line, end_line) or None."""
    # Try to find section by name (various formats)
    patterns = [
        rf'^##\s+{re.escape(section_name)}$',
        rf'^###\s+{re.escape(section_name)}$',
        rf'^##\s+.*{re.escape(section_name)}',
    ]
    
    lines = base_content.split('\n')
    for i, line in enumerate(lines):
        for pattern in patterns:
            if re.match(pattern, line, re.IGNORECASE):
                # Find end of section (next ## or ### or end of file)
                start = i
                end = len(lines)
                for j in range(i + 1, len(lines)):
                    if re.match(r'^##', lines[j]):
                        end = j
                        break
                return (start, end)
    
    return None


def find_insertion_point(base_content: str, insert_after: str) -> Optional[int]:
    """Find where to insert content based on 'insert after' instruction."""
    lines = base_content.split('\n')
    
    # Try exact match first
    for i, line in enumerate(lines):
        if insert_after in line:
            return i + 1
    
    # Try pattern match
    if insert_after.startswith('`') and insert_after.endswith('`'):
        pattern = insert_after.strip('`')
        for i, line in enumerate(lines):
            if pattern in line:
                return i + 1
    
    return None


def apply_customization(base_content: str, customization: Customization) -> str:
    """Apply a single customization to base content."""
    lines = base_content.split('\n')
    
    if customization.action == "Insert new section":
        # Find insertion point
        if customization.insert_after:
            insert_pos = find_insertion_point(base_content, customization.insert_after)
            if insert_pos is not None:
                # Insert new section
                new_lines = lines[:insert_pos]
                new_lines.append('')
                new_lines.extend(customization.content.split('\n'))
                new_lines.extend(lines[insert_pos:])
                return '\n'.join(new_lines)
        
        # Fallback: append at end
        return base_content + '\n\n' + customization.content
    
    elif customization.action == "Enhance existing section":
        # Find the section
        section_pos = find_section_in_base(base_content, customization.section_name)
        if section_pos:
            start, end = section_pos
            # Insert enhancement after the section header or at specified point
            if customization.insert_after:
                insert_pos = find_insertion_point('\n'.join(lines[start:end]), customization.insert_after)
                if insert_pos is not None:
                    insert_pos = start + insert_pos
                    new_lines = lines[:insert_pos]
                    new_lines.extend(customization.content.split('\n'))
                    new_lines.extend(lines[insert_pos:])
                    return '\n'.join(new_lines)
            
            # Fallback: append to section
            new_lines = lines[:end]
            new_lines.extend(customization.content.split('\n'))
            new_lines.extend(lines[end:])
            return '\n'.join(new_lines)
        
        # Section not found, insert as new
        return apply_customization(base_content, Customization(
            section_name=customization.section_name,
            action="Insert new section",
            insert_after=customization.insert_after,
            content=customization.content
        ))
    
    elif customization.action == "Replace section":
        # Find and replace section
        section_pos = find_section_in_base(base_content, customization.section_name)
        if section_pos:
            start, end = section_pos
            new_lines = lines[:start]
            new_lines.extend(customization.content.split('\n'))
            new_lines.extend(lines[end:])
            return '\n'.join(new_lines)
    
    # Unknown action, append
    return base_content + '\n\n' + customization.content


def generate_enhanced_prompt(
    base_file: Path,
    customization_file: Path,
    output_file: Path,
    multiclaude_version: str = "unknown"
) -> None:
    """Generate an enhanced prompt by applying customizations to base."""
    base_content = base_file.read_text()
    
    # Get base template name
    agent_name = base_file.stem
    
    # Parse customizations
    customizations = parse_customization_file(customization_file)
    
    # Apply customizations
    enhanced_content = base_content
    for customization in customizations:
        enhanced_content = apply_customization(enhanced_content, customization)
    
    # Add header
    header = f"""# {agent_name.replace('_', ' ').title()}: Enhanced

> **Based on**: multiclaude default template (version: {multiclaude_version})
> **Overlord Enhancements**: Applied from customizations
> **Generated**: Auto-generated - do not edit directly. Edit CUSTOMIZATIONS/ instead.

"""
    
    final_content = header + enhanced_content
    
    output_file.write_text(final_content)
    print(f"Generated: {output_file}")


def main():
    if len(sys.argv) < 4:
        print("Usage: apply-customizations.py <base-file> <customization-file> <output-file> [multiclaude-version]")
        sys.exit(1)
    
    base_file = Path(sys.argv[1])
    customization_file = Path(sys.argv[2])
    output_file = Path(sys.argv[3])
    multiclaude_version = sys.argv[4] if len(sys.argv) > 4 else "unknown"
    
    if not base_file.exists():
        print(f"ERROR: Base file not found: {base_file}", file=sys.stderr)
        sys.exit(1)
    
    generate_enhanced_prompt(base_file, customization_file, output_file, multiclaude_version)


if __name__ == "__main__":
    main()

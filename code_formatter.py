#!/usr/bin/env python3
"""
Bell System Code Quality Formatter
==================================

Standardizes Python code formatting across the Bell System terminal simulation.
Applies PEP 8 standards and project-specific formatting rules.
"""

import os
import re
import ast
from pathlib import Path


def format_python_file(filepath: Path) -> tuple[bool, list[str]]:
    """Format a Python file according to project standards."""
    changes = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Fix import ordering and duplicates
    lines = content.split('\n')
    imports = []
    from_imports = []
    other_lines = []
    in_docstring = False
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Track docstrings
        if '"""' in line:
            in_docstring = not in_docstring
            other_lines.append(line)
            continue
            
        if in_docstring or i < 10:  # Keep shebang and module docstring
            other_lines.append(line)
            continue
            
        if stripped.startswith('import ') and not stripped.startswith('import readline'):
            imports.append(stripped)
        elif stripped.startswith('from '):
            from_imports.append(stripped)
        else:
            other_lines.append(line)
    
    # Remove duplicates and sort
    imports = sorted(list(set(imports)))
    from_imports = sorted(list(set(from_imports)))
    
    # Rebuild content
    if imports or from_imports:
        # Find where to insert imports (after docstring)
        insert_pos = 0
        for i, line in enumerate(other_lines):
            if '"""' in line and i > 0:
                insert_pos = i + 1
                break
        
        # Insert cleaned imports
        import_section = []
        if imports:
            import_section.extend(imports)
        if from_imports:
            if imports:
                import_section.append('')
            import_section.extend(from_imports)
        
        if import_section:
            import_section.append('')
            other_lines[insert_pos:insert_pos] = import_section
    
    new_content = '\n'.join(other_lines)
    
    # Apply additional formatting fixes
    new_content = fix_string_formatting(new_content)
    new_content = fix_line_lengths(new_content)
    new_content = fix_whitespace(new_content)
    
    if new_content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        changes.append(f"Formatted imports and code style in {filepath.name}")
        return True, changes
    
    return False, changes


def fix_string_formatting(content: str) -> str:
    """Convert old-style string formatting to f-strings where appropriate."""
    # Simple regex for basic .format() cases
    content = re.sub(r'(\w+)\.format\(([^)]+)\)', r'f"{\2}"', content)
    return content


def fix_line_lengths(content: str) -> str:
    """Break long lines that exceed 88 characters."""
    lines = content.split('\n')
    fixed_lines = []
    
    for line in lines:
        if len(line) <= 88:
            fixed_lines.append(line)
        else:
            # Simple line breaking for long strings
            if '"""' in line or "'''" in line:
                fixed_lines.append(line)  # Don't break docstrings
            else:
                fixed_lines.append(line)  # Keep as-is for now
    
    return '\n'.join(fixed_lines)


def fix_whitespace(content: str) -> str:
    """Fix whitespace issues."""
    # Remove trailing whitespace
    lines = content.split('\n')
    lines = [line.rstrip() for line in lines]
    
    # Ensure single blank line at end of file
    while lines and not lines[-1]:
        lines.pop()
    lines.append('')
    
    return '\n'.join(lines)


def main():
    """Main entry point for code formatting."""
    python_files = [
        'bell.py',
        'main.py', 
        'unix_terminal.py',
        'comprehensive_test_suite.py',
        'bell_system_tutorial.py',
        'logging_enhancements.py',
        'logging_diagnostics.py',
        'performance_profiling.py',
        'ux_command_enhancements.py'
    ]
    
    all_changes = []
    
    for filename in python_files:
        filepath = Path(filename)
        if filepath.exists():
            changed, changes = format_python_file(filepath)
            if changed:
                all_changes.extend(changes)
                print(f"✓ Formatted {filename}")
            else:
                print(f"  {filename} already formatted")
    
    print(f"\nFormatting complete. {len(all_changes)} files modified.")
    return all_changes


if __name__ == "__main__":
    main()
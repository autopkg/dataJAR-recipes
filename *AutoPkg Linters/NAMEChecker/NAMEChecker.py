#!/usr/local/autopkg/python
"""
NAMEChecker - Script to validate and fix NAME input variable values.
Ensures NAME values have no spaces by removing them.
Example: "File Beat" becomes "FileBeat"
Supports plist and YAML recipe formats.
Requires AutoPkg's Python installation.
Preserves exact file formatting using text manipulation.
"""

import os
import sys
from pathlib import Path
import re
import yaml

# Make linter_common importable when run directly (a no-op under
# autopkg-linter.py, which already has this directory on sys.path).
# Kept as one if-statement so the import below isn't flagged E402.
if (_LINTERS_DIR := os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))) not in sys.path:
    sys.path.insert(0, _LINTERS_DIR)
from linter_common import clean_path, verify_environment


def has_name_with_spaces_plist(content: str) -> bool:
    """Check if plist has NAME variable with spaces in value.

    Args:
        content: Recipe file content

    Returns:
        Boolean indicating if NAME has spaces
    """
    # Look for NAME key in Input section with spaces
    pattern = (
        r'<key>Input</key>.*?<key>NAME</key>'
        r'\s*\n\s*<string>([^<]+)</string>'
    )
    match = re.search(pattern, content, re.DOTALL)

    if match:
        name_value = match.group(1)
        return ' ' in name_value

    return False


def fix_name_spaces_plist(
        content: str) -> tuple[str, bool, str | None, str | None]:
    """Remove spaces from NAME value in plist recipe.

    Args:
        content: Recipe file content

    Returns:
        Tuple of (updated_content, was_modified, old_value, new_value)
    """
    # Find NAME key in Input section
    pattern = (
        r'(<key>Input</key>.*?<key>NAME</key>'
        r'\s*\n\s*<string>)([^<]+)(</string>)'
    )
    match = re.search(pattern, content, re.DOTALL)

    if not match:
        return content, False, None, None

    old_value = match.group(2)

    # Check if it has spaces
    if ' ' not in old_value:
        return content, False, None, None

    # Remove all spaces
    new_value = old_value.replace(' ', '')

    # Replace the value
    new_content = content.replace(
        match.group(0),
        match.group(1) + new_value + match.group(3)
    )

    return new_content, True, old_value, new_value


def has_name_with_spaces_yaml(content: str) -> bool:
    """Check if YAML has NAME variable with spaces in value.

    Args:
        content: Recipe file content

    Returns:
        Boolean indicating if NAME has spaces
    """
    try:
        recipe = yaml.safe_load(content)
        if 'Input' in recipe and 'NAME' in recipe['Input']:
            name_value = recipe['Input']['NAME']
            return isinstance(name_value, str) and ' ' in name_value
    except Exception:
        pass

    return False


def _is_input_section_start(line: str) -> bool:
    """Check if line starts the Input section in YAML.

    Args:
        line: Line to check

    Returns:
        Boolean indicating if this is the Input section start
    """
    return line.strip().startswith('Input:')


def _is_section_end(line: str, in_input: bool) -> bool:
    """Check if we've left the Input section in YAML.

    Args:
        line: Line to check
        in_input: Whether we're currently in Input section

    Returns:
        Boolean indicating if we've left Input section
    """
    return bool(
        in_input and line and not line[0].isspace() and ':' in line)


def _extract_name_value(line: str) -> tuple[str | None, str | None]:
    """Extract NAME value from YAML line.

    Args:
        line: Line containing NAME key

    Returns:
        Tuple of (indent_and_key, value) or (None, None)
    """
    match = re.match(r'^(\s*NAME:\s+)(.+)$', line)
    if match:
        return match.group(1), match.group(2)
    return None, None


def _process_quoted_value(
        value: str) -> tuple[str | None, str | None, str | None]:
    """Process quoted NAME value by removing spaces.

    Args:
        value: Quoted value string

    Returns:
        Tuple of (old_value, new_value, quote_char) or (None, None, None)
    """
    if ((value.startswith('"') and value.endswith('"')) or
            (value.startswith("'") and value.endswith("'"))):
        quote_char = value[0]
        inner_value = value[1:-1]
        if ' ' in inner_value:
            return inner_value, inner_value.replace(' ', ''), quote_char
    return None, None, None


def _build_name_line(indent_and_key: str, new_value: str,
                     quote_char: str | None = None) -> str:
    """Build updated NAME line.

    Args:
        indent_and_key: Indentation and key part
        new_value: New value without spaces
        quote_char: Quote character if quoted

    Returns:
        Updated line string
    """
    if quote_char:
        return f'{indent_and_key}{quote_char}{new_value}{quote_char}'
    return f'{indent_and_key}{new_value}'


def _process_name_line(line: str) -> tuple[str, bool, str | None, str | None]:
    """Process a NAME line and return updated line if needed.

    Args:
        line: Line containing NAME key

    Returns:
        Tuple of (new_line, modified, old_value, new_value)
    """
    result: tuple[str, bool, str | None, str | None] = (
        line, False, None, None)
    indent_and_key, value = _extract_name_value(line)
    if indent_and_key:
        # Try processing as quoted value
        old_val, new_val, quote_char = _process_quoted_value(value)
        if old_val:
            new_line = _build_name_line(indent_and_key, new_val, quote_char)
            result = (new_line, True, old_val, new_val)
        # Unquoted value with spaces
        elif ' ' in value:
            new_val = value.replace(' ', '')
            new_line = _build_name_line(indent_and_key, new_val)
            result = (new_line, True, value, new_val)

    return result


def fix_name_spaces_yaml(
        content: str) -> tuple[str, bool, str | None, str | None]:
    """Remove spaces from NAME value in YAML recipe.

    Args:
        content: Recipe file content

    Returns:
        Tuple of (updated_content, was_modified, old_value, new_value)
    """
    lines = content.split('\n')
    modified = False
    old_value = None
    new_value = None

    in_input = False

    for i, line in enumerate(lines):
        if _is_input_section_start(line):
            in_input = True
            continue

        if _is_section_end(line, in_input):
            in_input = False

        if in_input and 'NAME:' in line:
            new_line, line_modified, old_val, new_val = \
                _process_name_line(line)
            if line_modified:
                lines[i] = new_line
                modified = True
                old_value = old_val
                new_value = new_val
            break

    if modified:
        return '\n'.join(lines), True, old_value, new_value

    return content, False, None, None


def process_recipe(
        recipe_path: Path) -> tuple[bool, str | None, str | None]:
    """Process a recipe file and fix NAME spaces if needed.

    Args:
        recipe_path: Path to the recipe file

    Returns:
        Tuple of (modified: bool, old_value: str | None,
        new_value: str | None)
    """
    result: tuple[bool, str | None, str | None] = (False, None, None)
    try:
        with open(recipe_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Determine format
        is_yaml = recipe_path.suffix == '.yaml'

        # Check if NAME has spaces
        if is_yaml:
            has_spaces = has_name_with_spaces_yaml(content)
            fix_name_spaces = fix_name_spaces_yaml
        else:
            has_spaces = has_name_with_spaces_plist(content)
            fix_name_spaces = fix_name_spaces_plist

        if has_spaces:
            new_content, modified, old_value, new_value = \
                fix_name_spaces(content)

            if modified:
                with open(recipe_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                result = (True, old_value, new_value)

    except Exception as e:
        print(f"Error processing {recipe_path}: {e}")

    return result


def main() -> None:
    """Prompt for a recipe directory and remove spaces from NAME values."""
    verify_environment()

    print("NAMEChecker - Recipe NAME Variable Validator")
    print("=" * 50)
    print("This script will:")
    print("1. Find NAME input variables with spaces")
    print("2. Remove all spaces from NAME values")
    print("3. Preserve exact file formatting")
    print("=" * 50)
    print()

    # Get recipe directory from user
    recipe_dir = input(
        "Enter the path to your recipe directory\n"
        "(You can drag and drop the folder here): "
    )

    recipe_dir = clean_path(recipe_dir)

    if not os.path.isdir(recipe_dir):
        print(f"Error: {recipe_dir} is not a valid directory")
        sys.exit(1)

    print(f"\nScanning recipes in: {recipe_dir}\n")

    # Find all recipe files
    recipe_paths = []
    for ext in ['*.recipe', '*.recipe.plist', '*.recipe.yaml']:
        recipe_paths.extend(Path(recipe_dir).rglob(ext))

    if not recipe_paths:
        print("No recipe files found")
        return

    modified_files = []

    for recipe_path in sorted(recipe_paths):
        modified, old_value, new_value = process_recipe(recipe_path)

        if modified:
            print(f"✓ Updated {recipe_path.name}")
            print(f"  Changed NAME from '{old_value}' to '{new_value}'")
            print()
            modified_files.append((recipe_path.name, old_value, new_value))

    # Print summary
    print("=" * 50)
    print("Processing complete!")
    print(f"Recipes scanned: {len(recipe_paths)}")
    print(f"Recipes modified: {len(modified_files)}")
    print("=" * 50)

    if modified_files:
        print("\nModified files:\n")
        for filename, old_val, new_val in modified_files:
            print(f"  ✓ {filename}:")
            print(f"    Changed '{old_val}' → '{new_val}'")
        print("\nPlease verify these files in your version control system.")
    else:
        print("\n✓ All NAME variables are already formatted correctly!")


if __name__ == '__main__':
    main()

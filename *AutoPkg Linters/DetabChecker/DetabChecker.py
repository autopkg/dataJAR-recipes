#!/usr/local/autopkg/python
"""
Script to check and fix whitespace and indentation issues in AutoPkg recipes.
Ensures all recipes use 4 spaces for indentation instead of tabs, fixes
inconsistent indentation (non-multiples of 4 spaces), removes trailing
whitespace, and ensures proper file endings.
Supports both plist and yaml recipe formats.
Requires AutoPkg's Python installation.
"""

import os
import sys
from pathlib import Path
import traceback
from typing import NamedTuple

# Make linter_common importable when run directly (a no-op under
# autopkg-linter.py, which already has this directory on sys.path).
# Kept as one if-statement so the import below isn't flagged E402.
if (_LINTERS_DIR := os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))) not in sys.path:
    sys.path.insert(0, _LINTERS_DIR)
from linter_common import clean_path, verify_environment


def has_tabs(content: str) -> bool:
    """Check if content contains any tab characters."""
    return '\t' in content


def convert_tabs_to_spaces(content: str, spaces_per_tab: int = 4) -> str:
    """Convert all tabs to spaces in content.

    Args:
        content: String content to convert
        spaces_per_tab: Number of spaces per tab (default 4)

    Returns:
        Converted content with tabs replaced by spaces
    """
    return content.replace('\t', ' ' * spaces_per_tab)


def remove_trailing_whitespace(content: str) -> str:
    """Remove trailing whitespace from each line.

    Args:
        content: String content to process

    Returns:
        Content with trailing whitespace removed from each line
    """
    lines = content.splitlines(keepends=True)
    cleaned_lines = []

    for line in lines:
        # Remove trailing whitespace but preserve line ending
        if line.endswith('\r\n'):
            cleaned_lines.append(line.rstrip() + '\r\n')
        elif line.endswith('\n'):
            cleaned_lines.append(line.rstrip() + '\n')
        else:
            cleaned_lines.append(line.rstrip())

    return ''.join(cleaned_lines)


def ensure_final_newline(content: str) -> str:
    """Ensure content ends with a single newline.

    Args:
        content: String content to process

    Returns:
        Content ending with exactly one newline
    """
    if not content:
        return content

    # Remove any trailing newlines first
    content = content.rstrip('\n\r')

    # Add single newline at end
    return content + '\n'


def _string_ranges(content: str) -> list[tuple[int, int]]:
    """Find the ranges of all <string>...</string> blocks.

    Args:
        content: String content to scan

    Returns:
        List of (start, end) character ranges, end exclusive
    """
    string_ranges = []
    pos = 0
    while True:
        start = content.find('<string>', pos)
        if start == -1:
            break
        end = content.find('</string>', start)
        if end == -1:
            break
        # Store the range of content to exclude
        string_ranges.append((start, end + 9))
        pos = end + 9
    return string_ranges


def _is_in_ranges(char_pos: int,
                  string_ranges: list[tuple[int, int]]) -> bool:
    """Check if a character position falls within any of the ranges."""
    return any(start <= char_pos < end for start, end in string_ranges)


def _misaligned_indent(line: str) -> int:
    """Return a line's leading space count if not a multiple of 4.

    Empty lines, whitespace-only lines and lines that don't start with
    a space are never misaligned.

    Args:
        line: The line to check

    Returns:
        Number of leading spaces, or 0 if the indentation is fine
    """
    if not line.strip():
        return 0

    # Count leading spaces
    leading_spaces = len(line) - len(line.lstrip(' '))
    if leading_spaces % 4 != 0:
        return leading_spaces
    return 0


def _expected_indent(leading_spaces: int) -> int:
    """Round an indent to the nearest multiple of 4 spaces."""
    return ((leading_spaces + 2) // 4) * 4


def check_indentation(
    content: str,
) -> tuple[bool, list[tuple[int, int, int]]]:
    """Check if indentation is consistent (multiples of 4 spaces).
    Ignores content within <string> tags as those may contain scripts.

    Args:
        content: String content to check

    Returns:
        Tuple of (has_issues, issue_lines) where issue_lines is a list of
        (line_number, current_indent, expected_indent) tuples
    """
    # Find all <string>...</string> blocks to exclude from checking
    string_ranges = _string_ranges(content)

    lines = content.splitlines(keepends=True)
    issues = []
    char_pos = 0

    for line_num, line in enumerate(lines, 1):
        # Lines within a <string> tag are not checked
        if not _is_in_ranges(char_pos, string_ranges):
            leading_spaces = _misaligned_indent(line)
            if leading_spaces:
                issues.append(
                    (line_num, leading_spaces,
                     _expected_indent(leading_spaces))
                )

        char_pos += len(line)

    return len(issues) > 0, issues


def fix_indentation(content: str) -> str:
    """Fix inconsistent indentation to be multiples of 4 spaces.
    Ignores content within <string> tags as those may contain scripts.

    Args:
        content: String content to fix

    Returns:
        Content with corrected indentation
    """
    # Find all <string>...</string> blocks to exclude from fixing
    string_ranges = _string_ranges(content)

    lines = content.splitlines(keepends=True)
    fixed_lines = []
    char_pos = 0

    for line in lines:
        # Lines within a <string> tag are left alone
        if not _is_in_ranges(char_pos, string_ranges):
            leading_spaces = _misaligned_indent(line)
            if leading_spaces:
                # Replace the indentation
                line = (
                    ' ' * _expected_indent(leading_spaces)
                ) + line.lstrip(' ')

        fixed_lines.append(line)
        char_pos += len(line)

    return ''.join(fixed_lines)


class _Issues(NamedTuple):
    """Whitespace issues found in a recipe."""

    tab_count: int
    trailing_whitespace: bool
    final_newline: bool
    indent_issues: list[tuple[int, int, int]]

    def has_any(self) -> bool:
        """Return True if any issue was found."""
        return bool(self.tab_count or self.trailing_whitespace or
                    self.final_newline or self.indent_issues)


def _find_issues(content: str) -> _Issues:
    """Find the whitespace issues in recipe content.

    Args:
        content: String content of the recipe

    Returns:
        The issues found
    """
    has_trailing_whitespace = any(
        line.rstrip('\n\r') != line.rstrip('\n\r').rstrip()
        for line in content.splitlines(keepends=True)
    )
    needs_final_newline = bool(content) and not content.endswith('\n')
    _, indent_issues = check_indentation(content)
    return _Issues(content.count('\t'), has_trailing_whitespace,
                   needs_final_newline, indent_issues)


def _describe_issues(issues: _Issues) -> list[str]:
    """Describe the issues found, for reporting before fixing."""
    descriptions = []
    if issues.tab_count:
        descriptions.append(f"{issues.tab_count} tab(s)")
    if issues.trailing_whitespace:
        descriptions.append("trailing whitespace")
    if issues.final_newline:
        descriptions.append("missing final newline")
    if issues.indent_issues:
        descriptions.append(
            f"{len(issues.indent_issues)} indentation error(s)"
        )
    return descriptions


def _describe_fixes(issues: _Issues) -> list[str]:
    """Describe the fixes made for the issues found."""
    fixes = []
    if issues.tab_count:
        fixes.append(f"converted {issues.tab_count} tab(s) to spaces")
    if issues.trailing_whitespace:
        fixes.append("removed trailing whitespace")
    if issues.final_newline:
        fixes.append("added final newline")
    if issues.indent_issues:
        fixes.append(
            f"fixed {len(issues.indent_issues)} indentation error(s)"
        )
    return fixes


def _apply_fixes(content: str, issues: _Issues) -> str:
    """Apply the fixes for the issues found.

    Args:
        content: String content of the recipe
        issues: The issues found in content

    Returns:
        The fixed content
    """
    # Convert tabs to spaces
    if issues.tab_count:
        content = convert_tabs_to_spaces(content)

    # Remove trailing whitespace
    if issues.trailing_whitespace:
        content = remove_trailing_whitespace(content)

    # Fix indentation
    if issues.indent_issues:
        content = fix_indentation(content)

    # Ensure final newline
    if issues.final_newline:
        content = ensure_final_newline(content)

    return content


def _write_fixes(recipe_path: Path, modified_content: str) -> bool:
    """Write fixed content to a recipe and verify the write.

    Args:
        recipe_path: Path to the recipe file
        modified_content: The fixed content

    Returns:
        True if the content was written and verified
    """
    # Verify all fixes were applied
    if '\t' in modified_content:
        print(f"❌ Warning: Tabs still present after conversion in "
              f"{recipe_path}")
        return False

    # Write the changes
    with open(recipe_path, 'w', encoding='utf-8') as file:
        file.write(modified_content)

    # Verify the changes were written
    with open(recipe_path, 'r', encoding='utf-8') as file:
        verification_content = file.read()

    if verification_content != modified_content:
        print(f"❌ Warning: File write verification failed for "
              f"{recipe_path}")
        return False
    return True


def process_recipe(recipe_path: Path) -> bool:
    """Process a single recipe file and fix its whitespace issues.

    Args:
        recipe_path: Path to the recipe file

    Returns:
        True if the recipe was fixed and the write verified
    """
    try:
        # Read original content
        with open(recipe_path, 'r', encoding='utf-8') as file:
            original_content = file.read()

        # Track what changes are needed
        issues = _find_issues(original_content)

        if not issues.has_any():
            print(f"Skipping {recipe_path.name} - no issues found")
            return False

        print(f"\nFound issues in {recipe_path}: "
              f"{', '.join(_describe_issues(issues))}")

        # Apply all fixes
        modified_content = _apply_fixes(original_content, issues)

        fixed = _write_fixes(recipe_path, modified_content)
        if fixed:
            # Report what was fixed
            print(
                f"✓ Fixed {recipe_path.name}: "
                f"{', '.join(_describe_fixes(issues))}"
            )
        return fixed

    except Exception as e:
        print(f"❌ Error processing {recipe_path}: {str(e)}")
        traceback.print_exc()
        return False


def _process_recipes(recipe_dir: str) -> tuple[int, list[tuple[Path, str]]]:
    """Fix whitespace in every recipe under recipe_dir.

    Args:
        recipe_dir: Path to the recipe directory

    Returns:
        Tuple of (recipe_count, modified_files) where modified_files is a
        list of (recipe_path, fix_description) tuples
    """
    recipe_count = 0
    modified_files = []

    # Process all recipe files
    for recipe_path in Path(recipe_dir).rglob("*.recipe*"):
        if recipe_path.suffix not in ['.recipe', '.yaml']:
            continue

        recipe_count += 1

        # Read to collect issue details before processing
        with open(recipe_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Track what issues exist
        issues = _find_issues(content)

        if process_recipe(recipe_path):
            # Build fix description
            fixes = _describe_fixes(issues)
            modified_files.append((recipe_path, ', '.join(fixes)))

    return recipe_count, modified_files


def main() -> None:
    """Prompt for a recipe directory and fix whitespace in its recipes."""
    verify_environment()

    print("DetabChecker - AutoPkg Recipe Whitespace Fixer")
    print("=" * 50)
    print("This script will:")
    print("1. Scan recipes for tab characters")
    print("2. Convert all tabs to 4 spaces")
    print("3. Fix inconsistent indentation (ensure multiples of 4 spaces)")
    print("4. Remove trailing whitespace from lines")
    print("5. Ensure files end with a newline")
    print("=" * 50)
    print("\nEnter the path to your recipe directory")
    print("(You can drag and drop the folder here): ", end='', flush=True)

    try:
        recipe_dir = clean_path(input())
        recipe_dir = os.path.abspath(recipe_dir)

        if not os.path.isdir(recipe_dir):
            print(f"Error: '{recipe_dir}' is not a valid directory")
            print("Make sure the path exists and you have permission "
                  "to access it.")
            return

        print(f"\nScanning recipes in: {recipe_dir}")

        recipe_count, modified_files = _process_recipes(recipe_dir)

        print(f"\n{'=' * 50}")
        print("Processing complete!")
        print(f"Recipes processed: {recipe_count}")
        print(f"Recipes modified: {len(modified_files)}")
        print("=" * 50)

        if modified_files:
            print("\nModified files:")
            for file, fix_desc in modified_files:
                print(f"  ✓ {file.name}: {fix_desc}")

            print("\nPlease verify these files in your version control "
                  "system.")

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
        traceback.print_exc()


if __name__ == "__main__":
    main()

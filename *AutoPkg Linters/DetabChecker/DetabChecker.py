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


def verify_environment():
    """Verify we're running in AutoPkg's Python environment."""
    autopkg_python = '/usr/local/autopkg/python'
    if not sys.executable.startswith('/usr/local/autopkg'):
        print("Error: This script should be run using AutoPkg's "
              "Python installation.")
        print(f"Please run this script using: {autopkg_python} "
              "<script_name.py>")
        sys.exit(1)


def clean_path(path):
    """Clean up path from drag and drop or manual entry."""
    path = path.strip().strip('"').strip("'")
    path = path.replace(r'\ ', ' ')
    path = path.rstrip(' ').rstrip('/')
    path = os.path.expanduser(path)
    return path


def has_tabs(content):
    """Check if content contains any tab characters."""
    return '\t' in content


def convert_tabs_to_spaces(content, spaces_per_tab=4):
    """Convert all tabs to spaces in content.

    Args:
        content: String content to convert
        spaces_per_tab: Number of spaces per tab (default 4)

    Returns:
        Converted content with tabs replaced by spaces
    """
    return content.replace('\t', ' ' * spaces_per_tab)


def remove_trailing_whitespace(content):
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


def ensure_final_newline(content):
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


def check_indentation(content):
    """Check if indentation is consistent (multiples of 4 spaces).
    Ignores content within <string> tags as those may contain scripts.

    Args:
        content: String content to check

    Returns:
        Tuple of (has_issues, issue_lines) where issue_lines is a list of
        (line_number, current_indent, expected_indent) tuples
    """
    # Find all <string>...</string> blocks to exclude from checking
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

    def is_in_string_tag(char_pos):
        """Check if a character position is within a <string> tag."""
        for start, end in string_ranges:
            if start <= char_pos < end:
                return True
        return False

    lines = content.splitlines(keepends=True)
    issues = []
    char_pos = 0

    for line_num, line in enumerate(lines, 1):
        # Check if this line is within a <string> tag
        if is_in_string_tag(char_pos):
            char_pos += len(line)
            continue

        # Skip empty lines and lines with only whitespace
        if not line.strip():
            char_pos += len(line)
            continue

        # Count leading spaces
        leading_spaces = len(line) - len(line.lstrip(' '))

        # Skip lines that don't start with spaces
        if leading_spaces == 0 or line[0] != ' ':
            char_pos += len(line)
            continue

        # Check if indentation is a multiple of 4
        if leading_spaces % 4 != 0:
            # Calculate what it should be (round to nearest multiple of 4)
            expected = ((leading_spaces + 2) // 4) * 4
            issues.append((line_num, leading_spaces, expected))

        char_pos += len(line)

    return len(issues) > 0, issues


def fix_indentation(content):
    """Fix inconsistent indentation to be multiples of 4 spaces.
    Ignores content within <string> tags as those may contain scripts.

    Args:
        content: String content to fix

    Returns:
        Content with corrected indentation
    """
    # Find all <string>...</string> blocks to exclude from fixing
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

    def is_in_string_tag(char_pos):
        """Check if a character position is within a <string> tag."""
        for start, end in string_ranges:
            if start <= char_pos < end:
                return True
        return False

    lines = content.splitlines(keepends=True)
    fixed_lines = []
    char_pos = 0

    for line in lines:
        # Check if this line is within a <string> tag
        if is_in_string_tag(char_pos):
            fixed_lines.append(line)
            char_pos += len(line)
            continue

        # Skip empty lines and lines with only whitespace
        if not line.strip():
            fixed_lines.append(line)
            char_pos += len(line)
            continue

        # Count leading spaces
        leading_spaces = len(line) - len(line.lstrip(' '))

        # Skip lines that don't start with spaces
        if leading_spaces == 0 or line[0] != ' ':
            fixed_lines.append(line)
            char_pos += len(line)
            continue

        # Check if indentation is a multiple of 4
        if leading_spaces % 4 != 0:
            # Calculate what it should be (round to nearest multiple of 4)
            expected = ((leading_spaces + 2) // 4) * 4
            # Replace the indentation
            line = (' ' * expected) + line.lstrip(' ')

        fixed_lines.append(line)
        char_pos += len(line)

    return ''.join(fixed_lines)


def process_recipe(recipe_path):
    """Process a single recipe file and convert tabs to spaces."""
    try:
        # Read original content
        with open(recipe_path, 'r', encoding='utf-8') as file:
            original_content = file.read()

        # Track what changes are needed
        has_tabs = '\t' in original_content
        has_trailing_whitespace = any(
            line.rstrip('\n\r') != line.rstrip('\n\r').rstrip()
            for line in original_content.splitlines(keepends=True)
        )
        needs_final_newline = (
            original_content and not original_content.endswith('\n')
        )
        has_indent_issues, indent_issues = check_indentation(original_content)

        no_issues = (
            not has_tabs and
            not has_trailing_whitespace and
            not needs_final_newline and
            not has_indent_issues
        )
        if no_issues:
            print(f"Skipping {recipe_path.name} - no issues found")
            return False

        issues = []
        if has_tabs:
            tab_count = original_content.count('\t')
            issues.append(f"{tab_count} tab(s)")
        if has_trailing_whitespace:
            issues.append("trailing whitespace")
        if needs_final_newline:
            issues.append("missing final newline")
        if has_indent_issues:
            issues.append(f"{len(indent_issues)} indentation error(s)")

        print(f"\nFound issues in {recipe_path}: {', '.join(issues)}")

        # Apply all fixes
        modified_content = original_content

        # Convert tabs to spaces
        if has_tabs:
            modified_content = convert_tabs_to_spaces(modified_content)

        # Remove trailing whitespace
        if has_trailing_whitespace:
            modified_content = remove_trailing_whitespace(modified_content)

        # Fix indentation
        if has_indent_issues:
            modified_content = fix_indentation(modified_content)

        # Ensure final newline
        if needs_final_newline:
            modified_content = ensure_final_newline(modified_content)

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
        else:
            # Report what was fixed
            fixed = []
            if has_tabs:
                fixed.append(f"converted {tab_count} tab(s) to spaces")
            if has_trailing_whitespace:
                fixed.append("removed trailing whitespace")
            if needs_final_newline:
                fixed.append("added final newline")
            if has_indent_issues:
                fixed.append(
                    f"fixed {len(indent_issues)} indentation error(s)"
                )

            print(
                f"✓ Fixed {recipe_path.name}: {', '.join(fixed)}"
            )
            return True

    except Exception as e:
        print(f"❌ Error processing {recipe_path}: {str(e)}")
        traceback.print_exc()
        return False


def main():
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

        modified_count = 0
        recipe_count = 0
        modified_files = []

        # Process all recipe files
        for recipe_path in Path(recipe_dir).rglob("*.recipe*"):
            if recipe_path.suffix in ['.recipe', '.yaml']:
                recipe_count += 1

                # Read to collect issue details before processing
                with open(recipe_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Track what issues exist
                has_tabs = '\t' in content
                has_trailing_ws = any(
                    line.rstrip('\n\r') != line.rstrip('\n\r').rstrip()
                    for line in content.splitlines(keepends=True)
                )
                needs_newline = content and not content.endswith('\n')
                has_indent_issues, indent_issues = check_indentation(content)

                if process_recipe(recipe_path):
                    modified_count += 1
                    # Build fix description
                    fixes = []
                    if has_tabs:
                        tab_count = content.count('\t')
                        fixes.append(f"converted {tab_count} tab(s) to spaces")
                    if has_trailing_ws:
                        fixes.append("removed trailing whitespace")
                    if needs_newline:
                        fixes.append("added final newline")
                    if has_indent_issues:
                        fixes.append(
                            f"fixed {len(indent_issues)} indentation error(s)"
                        )
                    modified_files.append((recipe_path, ', '.join(fixes)))

        print(f"\n{'=' * 50}")
        print("Processing complete!")
        print(f"Recipes processed: {recipe_count}")
        print(f"Recipes modified: {modified_count}")
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

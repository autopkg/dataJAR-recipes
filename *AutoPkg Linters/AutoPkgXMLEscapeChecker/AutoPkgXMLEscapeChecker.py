#!/usr/local/autopkg/python
"""
Script to ensure proper XML character escaping in AutoPkg recipes.
AutoPkg requires certain characters to be escaped within <string> values:
  - & must be &amp;
  - < must be &lt;
  - > must be &gt;

AutoPkg handles these fine unescaped:
  - " (double quotes)
  - ' (single quotes/apostrophes)

This script finds unescaped &, <, > characters within <string> tags
and escapes them.
Supports both plist and yaml recipe formats.
Requires AutoPkg's Python installation.
"""

import os
import sys
import re
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


def escape_xml_characters(content):
    """Escape &, <, > characters within <string> tags.

    Args:
        content: String content to process

    Returns:
        Tuple of (modified_content, changes_made) where changes_made is a list
        of line numbers where changes were made
    """
    # Find all <string>...</string> blocks
    string_pattern = re.compile(r'(<string>)(.*?)(</string>)', re.DOTALL)
    changes = []

    def escape_string_content(match):
        """Escape special characters within a string tag."""
        opening = match.group(1)
        string_content = match.group(2)
        closing = match.group(3)

        original_content = string_content

        # Escape & first (before < and >) to avoid double-escaping
        # But only if it's not already part of an entity
        # Match & that is NOT followed by (quot|apos|lt|gt|amp);
        string_content = re.sub(
            r'&(?!(quot|apos|lt|gt|amp);)', '&amp;', string_content
        )

        # Escape < and > if not already escaped
        string_content = re.sub(r'<(?!/?[a-zA-Z])', '&lt;', string_content)
        string_content = re.sub(r'(?<![a-zA-Z/])>', '&gt;', string_content)

        if string_content != original_content:
            # Count which line this is on
            lines_before = content[:match.start()].count('\n')
            changes.append(lines_before + 1)

        return opening + string_content + closing

    modified_content = string_pattern.sub(escape_string_content, content)

    return modified_content, list(set(changes))  # Remove duplicates


def process_plist_recipe(recipe_path):
    """Process a plist recipe file and escape XML characters.

    Args:
        recipe_path: Path to the recipe file

    Returns:
        Tuple of (modified: bool, changes: list)
    """
    try:
        # Read original content
        with open(recipe_path, 'r', encoding='utf-8') as f:
            original_content = f.read()

        # Escape XML characters
        modified_content, line_numbers = escape_xml_characters(
            original_content
        )

        if modified_content == original_content:
            return False, []

        # Write changes
        with open(recipe_path, 'w', encoding='utf-8') as f:
            f.write(modified_content)

        changes = [
            f"Escaped XML characters on {len(line_numbers)} line(s)"
        ]
        return True, changes

    except Exception as e:
        print(f"Error processing {recipe_path}: {e}")
        traceback.print_exc()
        return False, []


def process_yaml_recipe(_):
    """Process a YAML recipe file.

    YAML recipes don't need XML escaping as they use YAML syntax.

    Args:
        _: Path to the recipe file (unused)

    Returns:
        Tuple of (modified: bool, changes: list)
    """
    # YAML recipes don't need XML character escaping
    return False, []


def process_recipe(recipe_path):
    """Process a recipe file based on its format.

    Args:
        recipe_path: Path to the recipe file

    Returns:
        Tuple of (modified: bool, changes: list)
    """
    if recipe_path.suffix == '.yaml':
        return process_yaml_recipe(recipe_path)
    else:
        return process_plist_recipe(recipe_path)


def main():
    verify_environment()

    print("AutoPkgXMLEscapeChecker - XML Character Escape Validator")
    print("=" * 50)
    print("This script will:")
    print("1. Find unescaped & < > characters within <string> tags")
    print("2. Escape them as &amp; &lt; &gt;")
    print("3. Preserve unescaped quotes (\" and ')")
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
            if recipe_path.suffix not in ['.recipe', '.yaml']:
                continue

            recipe_count += 1

            modified, changes = process_recipe(recipe_path)

            if modified:
                modified_count += 1
                modified_files.append((recipe_path, changes))
                print(f"\n✓ Fixed {recipe_path.name}")
                for change in changes:
                    print(f"  - {change}")
            else:
                print(f"Skipping {recipe_path.name} - no issues found")

        print(f"\n{'=' * 50}")
        print("Processing complete!")
        print(f"Recipes processed: {recipe_count}")
        print(f"Recipes modified: {modified_count}")
        print("=" * 50)

        if modified_files:
            print("\nModified files:")
            for file, changes in modified_files:
                print(f"\n  ✓ {file.name}:")
                for change in changes:
                    print(f"    - {change}")

            print("\nPlease verify these files in your version control "
                  "system.")
        else:
            print("\n✓ All recipes have proper XML character escaping!")

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

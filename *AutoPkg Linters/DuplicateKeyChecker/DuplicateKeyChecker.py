#!/usr/local/autopkg/python
"""
Script to check for duplicate keys in AutoPkg recipe files.
Detects duplicate keys in plist files which can cause parsing issues.
Automatically fixes the common case where 'unattended_install' appears twice
and 'unattended_uninstall' is missing - changes the second occurrence to
'unattended_uninstall'.

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


def find_duplicate_keys_in_dict(content, start_pos=0):
    """Find duplicate keys within a <dict> section of plist content.

    Args:
        content: String content of the plist file
        start_pos: Starting position to search from

    Returns:
        List of tuples: (key_name, [list of positions], dict_start, dict_end)
    """
    duplicates = []

    # Find all <dict>...</dict> blocks
    dict_pattern = re.compile(r'<dict>(.*?)</dict>', re.DOTALL)

    for dict_match in dict_pattern.finditer(content, start_pos):
        dict_content = dict_match.group(1)
        dict_start = dict_match.start()
        dict_end = dict_match.end()

        # Find all keys in this dict
        key_pattern = re.compile(r'<key>([^<]+)</key>')
        keys = {}

        for key_match in key_pattern.finditer(dict_content):
            key_name = key_match.group(1)
            abs_pos = dict_start + key_match.start()

            if key_name not in keys:
                keys[key_name] = []
            keys[key_name].append(abs_pos)

        # Check for duplicates
        for key_name, positions in keys.items():
            if len(positions) > 1:
                duplicates.append((key_name, positions, dict_start, dict_end))

    return duplicates


def check_unattended_keys(content):
    """Check if unattended_install and unattended_uninstall keys exist.

    Args:
        content: String content of the plist file

    Returns:
        Tuple of (has_unattended_install, has_unattended_uninstall)
    """
    has_install = '<key>unattended_install</key>' in content
    has_uninstall = '<key>unattended_uninstall</key>' in content
    return has_install, has_uninstall


def fix_duplicate_unattended_install(content):
    """Fix duplicate unattended_install keys when unattended_uninstall
    is missing.

    Changes the second occurrence of unattended_install to
    unattended_uninstall.

    Args:
        content: String content of the plist file

    Returns:
        Tuple of (modified_content, fixed: bool)
    """
    # Check if we have the specific case to fix
    has_install, has_uninstall = check_unattended_keys(content)

    if not has_install or has_uninstall:
        # Nothing to fix
        return content, False

    # Find all occurrences of unattended_install
    pattern = r'<key>unattended_install</key>'
    matches = list(re.finditer(pattern, content))

    if len(matches) < 2:
        # No duplicates
        return content, False

    # Replace the second occurrence
    second_match = matches[1]
    modified_content = (
        content[:second_match.start()] +
        '<key>unattended_uninstall</key>' +
        content[second_match.end():]
    )

    return modified_content, True


def process_plist_recipe(recipe_path):
    """Process a plist recipe file and check for duplicate keys.

    Args:
        recipe_path: Path to the recipe file

    Returns:
        Tuple of (modified: bool, changes: list, warnings: list)
    """
    try:
        # Read original content
        with open(recipe_path, 'r', encoding='utf-8') as f:
            original_content = f.read()

        changes = []
        warnings = []
        modified = False

        # Find all duplicate keys
        duplicates = find_duplicate_keys_in_dict(original_content)

        # Check for duplicates
        if duplicates:
            for key_name, positions, _, _ in duplicates:
                if key_name == 'unattended_install':
                    # Check if we can auto-fix
                    _, has_uninstall = check_unattended_keys(
                        original_content
                    )
                    if not has_uninstall and len(positions) == 2:
                        warnings.append(
                            f"Found duplicate '{key_name}' key "
                            f"(will attempt to fix)"
                        )
                    else:
                        warnings.append(
                            f"Found duplicate '{key_name}' key "
                            f"({len(positions)} occurrences)"
                        )
                else:
                    warnings.append(
                        f"Found duplicate '{key_name}' key "
                        f"({len(positions)} occurrences)"
                    )

        # Try to fix duplicate unattended_install
        modified_content, fixed = fix_duplicate_unattended_install(
            original_content
        )

        if fixed:
            modified = True
            changes.append(
                "Changed second 'unattended_install' to 'unattended_uninstall'"
            )

            # Write changes
            with open(recipe_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)

        return modified, changes, warnings

    except Exception as e:
        print(f"Error processing {recipe_path}: {e}")
        traceback.print_exc()
        return False, [], [f"Error: {e}"]


def process_yaml_recipe(recipe_path):
    """Process a YAML recipe file and check for duplicate keys.

    YAML parsers typically handle duplicate keys by using the last value,
    but we should still warn about them.

    Args:
        recipe_path: Path to the recipe file

    Returns:
        Tuple of (modified: bool, changes: list, warnings: list)
    """
    try:
        # Import yaml only when needed
        # Note: yaml module is only used for safe_load validation
        # Current implementation doesn't use it but keeps import for future use

        # Read original content
        with open(recipe_path, 'r', encoding='utf-8') as f:
            content = f.read()

        warnings = []

        # Simple duplicate key detection for YAML
        # This is basic - just checks for repeated keys at the same indentation
        lines = content.split('\n')
        seen_keys = {}
        current_indent = 0

        for line_num, line in enumerate(lines, 1):
            # Skip comments and empty lines
            if line.strip().startswith('#') or not line.strip():
                continue

            # Extract key if this is a key:value line
            key_match = re.match(r'^(\s*)([^:]+):', line)
            if key_match:
                key_indent = len(key_match.group(1))
                key_name = key_match.group(2).strip()

                # Reset seen keys if indent level changes
                if key_indent != current_indent:
                    seen_keys = {}
                    current_indent = key_indent

                # Check for duplicate
                if key_name in seen_keys:
                    warnings.append(
                        f"Found duplicate '{key_name}' key at line {line_num} "
                        f"(first seen at line {seen_keys[key_name]})"
                    )
                else:
                    seen_keys[key_name] = line_num

        # YAML duplicate detection is warning-only, no auto-fix
        return False, [], warnings

    except Exception as e:
        print(f"Error processing {recipe_path}: {e}")
        traceback.print_exc()
        return False, [], [f"Error: {e}"]


def process_recipe(recipe_path):
    """Process a recipe file based on its format.

    Args:
        recipe_path: Path to the recipe file

    Returns:
        Tuple of (modified: bool, changes: list, warnings: list)
    """
    if recipe_path.suffix == '.yaml':
        return process_yaml_recipe(recipe_path)
    else:
        return process_plist_recipe(recipe_path)


def main():
    """Main function."""
    verify_environment()

    print("DuplicateKeyChecker - AutoPkg Recipe Duplicate Key Detector")
    print("=" * 70)
    print("This script will:")
    print("1. Scan recipes for duplicate keys in dict sections")
    print("2. Warn about any duplicate keys found")
    print("3. Auto-fix duplicate 'unattended_install' when possible")
    print("   (changes 2nd occurrence to 'unattended_uninstall')")
    print("=" * 70)

    # Get recipe directory
    recipe_dir = input(
        "\nEnter the path to your recipe directory\n"
        "(You can drag and drop the folder here): ")
    recipe_dir = clean_path(recipe_dir)

    if not os.path.isdir(recipe_dir):
        print(f"\nError: '{recipe_dir}' is not a valid directory")
        sys.exit(1)

    print(f"\nScanning recipes in: {recipe_dir}")

    # Find all recipe files
    recipe_files = []
    for root, dirs, files in os.walk(recipe_dir):
        for file in files:
            if file.endswith(('.recipe', '.yaml')):
                recipe_files.append(Path(root) / file)

    if not recipe_files:
        print("\nNo recipe files found!")
        sys.exit(0)

    print(f"Found {len(recipe_files)} recipe file(s)\n")

    # Process each recipe
    recipes_with_issues = []
    recipes_fixed = []

    for recipe_path in sorted(recipe_files):
        relative_path = recipe_path.relative_to(recipe_dir)
        modified, changes, warnings = process_recipe(recipe_path)

        if warnings or changes:
            print(f"\n{'✓' if modified else '⚠'} {relative_path}")

            for warning in warnings:
                print(f"  ⚠ {warning}")

            for change in changes:
                print(f"  ✓ {change}")

            if warnings:
                recipes_with_issues.append((relative_path, warnings, changes))
            if modified:
                recipes_fixed.append((relative_path, changes))

    # Summary
    print("\n" + "=" * 70)
    print("Scan complete!")
    print(f"Recipes scanned: {len(recipe_files)}")
    print(f"Recipes with issues: {len(recipes_with_issues)}")
    print(f"Recipes fixed: {len(recipes_fixed)}")
    print("=" * 70)

    if recipes_fixed:
        print("\nFixed files:")
        for recipe_path, changes in recipes_fixed:
            print(f"\n  ✓ {recipe_path}:")
            for change in changes:
                print(f"    - {change}")

    if recipes_with_issues:
        unfixed = [r for r in recipes_with_issues if r[0] not in
                   [f[0] for f in recipes_fixed]]
        if unfixed:
            print("\nWarnings (not auto-fixed):")
            for recipe_path, warnings, _ in unfixed:
                print(f"\n  ⚠ {recipe_path}:")
                for warning in warnings:
                    print(f"    - {warning}")

            print("\nPlease review and manually fix recipes with warnings.")

    if recipes_fixed:
        print("\nPlease verify fixed files in your version control system.")


if __name__ == '__main__':
    main()

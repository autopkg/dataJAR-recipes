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

# Make linter_common importable when run directly (a no-op under
# autopkg-linter.py, which already has this directory on sys.path).
# Kept as one if-statement so the import below isn't flagged E402.
if (_LINTERS_DIR := os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))) not in sys.path:
    sys.path.insert(0, _LINTERS_DIR)
from linter_common import clean_path, verify_environment


def find_duplicate_keys_in_dict(
    content: str, start_pos: int = 0,
) -> list[tuple[str, list[int], int, int]]:
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


def check_unattended_keys(content: str) -> tuple[bool, bool]:
    """Check if unattended_install and unattended_uninstall keys exist.

    Args:
        content: String content of the plist file

    Returns:
        Tuple of (has_unattended_install, has_unattended_uninstall)
    """
    has_install = '<key>unattended_install</key>' in content
    has_uninstall = '<key>unattended_uninstall</key>' in content
    return has_install, has_uninstall


def fix_duplicate_unattended_install(content: str) -> tuple[str, bool]:
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


def _duplicate_warning(key_name: str, positions: list[int],
                       content: str) -> str:
    """Build the warning for a duplicate plist key.

    Args:
        key_name: The duplicated key
        positions: Positions of each occurrence of the key
        content: String content of the plist file

    Returns:
        Warning string, noting when the duplicate will be auto-fixed
    """
    if key_name == 'unattended_install':
        # Check if we can auto-fix
        _, has_uninstall = check_unattended_keys(content)
        if not has_uninstall and len(positions) == 2:
            return (
                f"Found duplicate '{key_name}' key "
                f"(will attempt to fix)"
            )
    return (
        f"Found duplicate '{key_name}' key "
        f"({len(positions)} occurrences)"
    )


def process_plist_recipe(
    recipe_path: Path,
) -> tuple[bool, list[str], list[str]]:
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

        # Warn about each duplicate key
        for key_name, positions, _, _ in duplicates:
            warnings.append(
                _duplicate_warning(key_name, positions, original_content)
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


def process_yaml_recipe(
    recipe_path: Path,
) -> tuple[bool, list[str], list[str]]:
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


def process_recipe(
    recipe_path: Path,
) -> tuple[bool, list[str], list[str]]:
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


def _find_recipe_files(recipe_dir: str) -> list[Path]:
    """Find all recipe files under recipe_dir.

    Args:
        recipe_dir: Path to the recipe directory

    Returns:
        List of recipe file paths
    """
    recipe_files = []
    for root, _, files in os.walk(recipe_dir):
        for file in files:
            if file.endswith(('.recipe', '.yaml')):
                recipe_files.append(Path(root) / file)
    return recipe_files


def _scan_recipes(
    recipe_dir: str, recipe_files: list[Path]
) -> tuple[list[tuple[Path, list[str], list[str]]],
           list[tuple[Path, list[str]]]]:
    """Process each recipe, printing its warnings and changes.

    Args:
        recipe_dir: Path to the recipe directory
        recipe_files: List of recipe file paths

    Returns:
        Tuple of (recipes_with_issues, recipes_fixed)
    """
    recipes_with_issues = []
    recipes_fixed = []

    for recipe_path in sorted(recipe_files):
        relative_path = recipe_path.relative_to(recipe_dir)
        modified, changes, warnings = process_recipe(recipe_path)

        if not (warnings or changes):
            continue

        print(f"\n{'✓' if modified else '⚠'} {relative_path}")

        for warning in warnings:
            print(f"  ⚠ {warning}")

        for change in changes:
            print(f"  ✓ {change}")

        if warnings:
            recipes_with_issues.append((relative_path, warnings, changes))
        if modified:
            recipes_fixed.append((relative_path, changes))

    return recipes_with_issues, recipes_fixed


def _print_fixed(recipes_fixed: list[tuple[Path, list[str]]]) -> None:
    """Print the files that were fixed.

    Args:
        recipes_fixed: List of (recipe_path, changes) tuples
    """
    print("\nFixed files:")
    for recipe_path, changes in recipes_fixed:
        print(f"\n  ✓ {recipe_path}:")
        for change in changes:
            print(f"    - {change}")


def _print_unfixed(
    recipes_with_issues: list[tuple[Path, list[str], list[str]]],
    recipes_fixed: list[tuple[Path, list[str]]],
) -> None:
    """Print warnings for recipes that were not auto-fixed.

    Args:
        recipes_with_issues: List of (recipe_path, warnings, changes) tuples
        recipes_fixed: List of (recipe_path, changes) tuples
    """
    unfixed = [r for r in recipes_with_issues if r[0] not in
               [f[0] for f in recipes_fixed]]
    if not unfixed:
        return

    print("\nWarnings (not auto-fixed):")
    for recipe_path, warnings, _ in unfixed:
        print(f"\n  ⚠ {recipe_path}:")
        for warning in warnings:
            print(f"    - {warning}")

    print("\nPlease review and manually fix recipes with warnings.")


def main() -> None:
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
    recipe_files = _find_recipe_files(recipe_dir)

    if not recipe_files:
        print("\nNo recipe files found!")
        sys.exit(0)

    print(f"Found {len(recipe_files)} recipe file(s)\n")

    # Process each recipe
    recipes_with_issues, recipes_fixed = _scan_recipes(
        recipe_dir, recipe_files
    )

    # Summary
    print("\n" + "=" * 70)
    print("Scan complete!")
    print(f"Recipes scanned: {len(recipe_files)}")
    print(f"Recipes with issues: {len(recipes_with_issues)}")
    print(f"Recipes fixed: {len(recipes_fixed)}")
    print("=" * 70)

    if recipes_fixed:
        _print_fixed(recipes_fixed)

    if recipes_with_issues:
        _print_unfixed(recipes_with_issues, recipes_fixed)

    if recipes_fixed:
        print("\nPlease verify fixed files in your version control system.")


if __name__ == '__main__':
    main()

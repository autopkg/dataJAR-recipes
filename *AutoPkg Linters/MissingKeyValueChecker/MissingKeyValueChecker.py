#!/usr/local/autopkg/python
"""
MissingKeyValueChecker - Script to check for empty values in pkginfo dict.
Only checks .munki recipes and reports keys with empty or whitespace-only
values. Supports plist and YAML recipe formats.
Requires AutoPkg's Python installation.
"""

import os
import sys
from pathlib import Path
import re
from typing import Any
import yaml

# Make linter_common importable when run directly (a no-op under
# autopkg-linter.py, which already has this directory on sys.path).
# Kept as one if-statement so the import below isn't flagged E402.
if (_LINTERS_DIR := os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))) not in sys.path:
    sys.path.insert(0, _LINTERS_DIR)
from linter_common import clean_path, verify_environment


def check_plist_pkginfo(content: str) -> list[tuple[str, int]]:
    """Check pkginfo dict in plist recipe for empty values.

    Args:
        content: Recipe file content

    Returns:
        List of tuples (key_name, line_number)
    """
    empty_keys = []

    # Find pkginfo dict
    pkginfo_pattern = r'<key>pkginfo</key>\s*\n\s*<dict>(.*?)</dict>'
    pkginfo_match = re.search(pkginfo_pattern, content, re.DOTALL)

    if not pkginfo_match:
        return empty_keys

    pkginfo_content = pkginfo_match.group(1)
    pkginfo_start = pkginfo_match.start(1)

    # Find all key-value pairs in pkginfo
    # Match key followed by its value (string, array, or dict)
    key_pattern = r'<key>([^<]+)</key>\s*\n\s*<string>([^<]*)</string>'

    for match in re.finditer(key_pattern, pkginfo_content):
        key_name = match.group(1)
        value = match.group(2)

        # Check if value is empty or only whitespace
        if not value.strip():
            # Calculate line number
            content_before = content[:pkginfo_start + match.start()]
            line_num = content_before.count('\n') + 1
            empty_keys.append((key_name, line_num))

    return empty_keys


def _get_pkginfo_from_yaml(
        recipe: dict[str, Any]) -> dict[str, Any] | None:
    """Extract pkginfo dict from YAML recipe.

    Args:
        recipe: Parsed YAML recipe dict

    Returns:
        pkginfo dict or None if not found
    """
    if 'Input' not in recipe or 'pkginfo' not in recipe['Input']:
        return None

    pkginfo = recipe['Input']['pkginfo']

    if not isinstance(pkginfo, dict):
        return None

    return pkginfo


def _find_yaml_key_line_number(key: str, lines: list[str]) -> int | None:
    """Find line number for a key in YAML content.

    Args:
        key: Key name to search for
        lines: List of lines from the YAML file

    Returns:
        Line number (1-indexed) or None if not found
    """
    for i, line in enumerate(lines, 1):
        context = '\n'.join(lines[max(0, i-10):i])
        if f'{key}:' in line and 'pkginfo' in context:
            return i
    return None


def _check_empty_keys(pkginfo: dict[str, Any],
                      lines: list[str]) -> list[tuple[str, int]]:
    """Check pkginfo dict for empty keys and find their line numbers.

    Args:
        pkginfo: pkginfo dict to check
        lines: List of lines from the YAML file

    Returns:
        List of tuples (key_name, line_number)
    """
    empty_keys = []

    for key, value in pkginfo.items():
        # Check if value is empty, None, or whitespace-only string
        is_empty = (value is None or
                    (isinstance(value, str) and not value.strip()))

        if is_empty:
            line_num = _find_yaml_key_line_number(key, lines)
            if line_num:
                empty_keys.append((key, line_num))

    return empty_keys


def check_yaml_pkginfo(content: str) -> list[tuple[str, int]]:
    """Check pkginfo dict in YAML recipe for empty values.

    Args:
        content: Recipe file content

    Returns:
        List of tuples (key_name, line_number)
    """
    try:
        recipe = yaml.safe_load(content)
        pkginfo = _get_pkginfo_from_yaml(recipe)

        if not pkginfo:
            return []

        lines = content.split('\n')
        return _check_empty_keys(pkginfo, lines)

    except Exception as e:
        print(f"Error parsing YAML: {e}")
        return []


def process_recipe(recipe_path: Path) -> list[tuple[str, int]]:
    """Process a recipe file and check for empty pkginfo values.

    Args:
        recipe_path: Path to the recipe file

    Returns:
        List of tuples (key_name, line_number)
    """
    empty_keys: list[tuple[str, int]] = []

    # Only check .munki recipes
    if '.munki' not in recipe_path.name.lower():
        return empty_keys

    try:
        with open(recipe_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if recipe has pkginfo
        if 'pkginfo' in content:
            # Determine format
            is_yaml = recipe_path.suffix == '.yaml'

            if is_yaml:
                empty_keys = check_yaml_pkginfo(content)
            else:
                empty_keys = check_plist_pkginfo(content)

    except Exception as e:
        print(f"Error processing {recipe_path}: {e}")

    return empty_keys


def _print_banner() -> None:
    """Print introductory banner."""
    print("MissingKeyValueChecker - Recipe pkginfo Validator")
    print("=" * 50)
    print("This script will:")
    print("1. Check .munki recipes only")
    print("2. Find empty or whitespace-only values in pkginfo")
    print("3. Report key names and line numbers")
    print("=" * 50)
    print()


def _get_recipe_directory() -> str:
    """Get and validate recipe directory from user input.

    Returns:
        Path to validated recipe directory
    """
    recipe_dir = input(
        "Enter the path to your recipe directory\n"
        "(You can drag and drop the folder here): ")

    recipe_dir = clean_path(recipe_dir)

    if not os.path.isdir(recipe_dir):
        print(f"Error: {recipe_dir} is not a valid directory")
        sys.exit(1)

    print(f"\nScanning recipes in: {recipe_dir}\n")
    return recipe_dir


def _find_munki_recipes(recipe_dir: str) -> list[Path]:
    """Find all .munki recipe files in directory.

    Args:
        recipe_dir: Directory to search

    Returns:
        List of Path objects for .munki recipes
    """
    recipe_paths = []
    for ext in ['*.recipe', '*.recipe.plist', '*.recipe.yaml']:
        recipe_paths.extend(Path(recipe_dir).rglob(ext))

    # Filter for .munki recipes only
    return [p for p in recipe_paths if '.munki' in p.name.lower()]


def _process_recipes(
        munki_recipes: list[Path]) -> dict[str, list[tuple[str, int]]]:
    """Process all recipes and collect issues.

    Args:
        munki_recipes: List of recipe Path objects

    Returns:
        Dict mapping recipe names to list of (key_name, line_number) tuples
    """
    issues_found = {}

    for recipe_path in sorted(munki_recipes):
        empty_keys = process_recipe(recipe_path)

        if empty_keys:
            print(f"⚠️  {recipe_path.name}")
            for key_name, line_num in empty_keys:
                print(f"   Line {line_num}: '{key_name}' has empty value")
            print()
            issues_found[recipe_path.name] = empty_keys

    return issues_found


def _print_summary(munki_recipes: list[Path],
                   issues_found: dict[str, list[tuple[str, int]]]) -> None:
    """Print processing summary and detailed report.

    Args:
        munki_recipes: List of processed recipes
        issues_found: Dict of recipe names to issues
    """
    print("=" * 50)
    print("Processing complete!")
    print(f"Munki recipes scanned: {len(munki_recipes)}")
    print(f"Recipes with issues: {len(issues_found)}")
    print("=" * 50)

    if issues_found:
        print("\nSummary of keys with missing values:\n")
        for filename, keys in sorted(issues_found.items()):
            print(f"📄 {filename}")
            for key_name, line_num in keys:
                print(f"   • Line {line_num}: '{key_name}'")
            print()
        print("⚠️  Please review and add values to these keys.")
    else:
        print("\n✓ All pkginfo keys have values!")


def main() -> None:
    """Prompt for a recipe directory and report empty pkginfo values."""
    verify_environment()

    _print_banner()
    recipe_dir = _get_recipe_directory()
    munki_recipes = _find_munki_recipes(recipe_dir)

    if not munki_recipes:
        print("No .munki recipe files found")
        return

    issues_found = _process_recipes(munki_recipes)
    _print_summary(munki_recipes, issues_found)


if __name__ == '__main__':
    main()

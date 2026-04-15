#!/usr/local/autopkg/python
"""
Script to ensure zsh shebangs include the --no-rcs flag in AutoPkg recipes.
Finds instances of #!/bin/zsh and converts them to #!/bin/zsh --no-rcs.

The --no-rcs flag prevents zsh from sourcing user configuration files
(.zshrc, .zprofile, etc.), ensuring consistent behavior across different
environments when recipes execute zsh scripts.

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


def fix_zsh_shebangs(content):
    """Fix zsh shebangs to include --no-rcs flag.

    Args:
        content: String content to process

    Returns:
        Tuple of (modified_content, changes_made) where changes_made is a list
        of line numbers where changes were made
    """
    lines = content.splitlines(keepends=True)
    changes = []
    modified = False

    # Pattern to match #!/bin/zsh without --no-rcs
    # This matches:
    # - #!/bin/zsh (exactly)
    # - #!/bin/zsh followed by newline or whitespace
    # But NOT:
    # - #!/bin/zsh --no-rcs (already has the flag)
    shebang_pattern = re.compile(
        r'^(.*?)(#!/bin/zsh)(?!\s*--no-rcs)(\s|$)',
        re.MULTILINE
    )

    for i, line in enumerate(lines, 1):
        if re.search(shebang_pattern, line):
            # Check if --no-rcs is already present
            if '--no-rcs' not in line:
                # Replace #!/bin/zsh with #!/bin/zsh --no-rcs
                old_line = line
                new_line = re.sub(
                    r'(#!/bin/zsh)(\s|$)',
                    r'\1 --no-rcs\2',
                    line
                )
                if new_line != old_line:
                    lines[i - 1] = new_line
                    changes.append(i)
                    modified = True

    if modified:
        return ''.join(lines), changes
    return content, []


def process_plist_recipe(recipe_path):
    """Process a plist format recipe file.

    Args:
        recipe_path: Path object pointing to the recipe file

    Returns:
        Tuple of (modified, changes) where modified is
        True if changes were made and changes is a list
        of line numbers where changes were made
    """
    try:
        with open(recipe_path, 'r', encoding='utf-8') as f:
            content = f.read()

        modified_content, changes = fix_zsh_shebangs(content)

        if changes:
            with open(recipe_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            return True, changes

        return False, []

    except Exception as e:
        print(f"Error processing {recipe_path}: {str(e)}")
        traceback.print_exc()
        return False, []


def process_yaml_recipe(recipe_path):
    """Process a YAML format recipe file.

    Args:
        recipe_path: Path object pointing to the recipe file

    Returns:
        Tuple of (modified, changes) where modified is
        True if changes were made and changes is a list
        of line numbers where changes were made
    """
    # YAML recipes use the same text-based approach
    return process_plist_recipe(recipe_path)


def _scan_recipes(recipe_dir):
    """Scan and process all recipe files.

    Args:
        recipe_dir: Absolute path to recipe directory

    Returns:
        Tuple of (recipe_count, modified_files)
    """
    modified_files = []
    recipe_count = 0

    for recipe_path in Path(recipe_dir).rglob("*.recipe*"):
        if recipe_path.suffix not in ['.recipe', '.yaml']:
            continue
        recipe_count += 1

        if recipe_path.suffix == '.recipe':
            modified, changes = process_plist_recipe(
                recipe_path
            )
        else:
            modified, changes = process_yaml_recipe(
                recipe_path
            )

        if modified:
            modified_files.append(
                (recipe_path, changes)
            )

    return recipe_count, modified_files


def main():
    """Main function to run the zsh shebang checker."""
    verify_environment()

    print("=" * 50)
    print("AutoPkg Recipe zsh Shebang Checker")
    print("=" * 50)
    print("\nThis script will:")
    print("1. Scan all AutoPkg recipes in a directory")
    print("2. Find instances of '#!/bin/zsh' shebangs")
    print("3. Add '--no-rcs' flag for consistent behavior")
    print("   (#!/bin/zsh → #!/bin/zsh --no-rcs)")
    print("=" * 50)
    print("\nEnter the path to your recipe directory")
    print(
        "(You can drag and drop the folder here): ",
        end='', flush=True
    )

    try:
        recipe_dir = clean_path(input())
        recipe_dir = os.path.abspath(recipe_dir)

        if not os.path.isdir(recipe_dir):
            print(
                f"Error: '{recipe_dir}' is not "
                "a valid directory"
            )
            print(
                "Make sure the path exists and "
                "you have permission to access it."
            )
            return

        print(f"\nScanning recipes in: {recipe_dir}")

        recipe_count, modified_files = _scan_recipes(
            recipe_dir
        )

        print(f"\n{'=' * 50}")
        print("Processing complete!")
        print(f"Recipes processed: {recipe_count}")
        print(f"Recipes modified: {len(modified_files)}")
        print("=" * 50)

        if modified_files:
            print("\nModified files:")
            for file, changes in modified_files:
                lines = ', '.join(map(str, changes))
                count = len(changes)
                print(
                    f"  ✓ {file.name}: fixed "
                    f"{count} zsh shebang(s) "
                    f"on line(s): {lines}"
                )

            print(
                "\nPlease verify these files in "
                "your version control system."
            )

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
        traceback.print_exc()


if __name__ == "__main__":
    main()

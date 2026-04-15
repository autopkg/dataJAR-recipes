#!/usr/local/autopkg/python
"""
Script to check recipe overrides with uninstall scripts for pkg receipt forgetting.
Finds overrides with uninstall_method=uninstall_script, looks up the corresponding
extension attribute in private-recipes to find the pkg receipt, and ensures the
uninstall script includes 'pkgutil --forget' for that receipt.
Requires AutoPkg's Python installation.
"""

import os
import sys
from pathlib import Path
import re
import traceback
import plistlib


# Constants
PKG_RECEIPT_COMMENT = '# Forget pkg receipt'


def check_forget_reachability(uninstall_script):
    """Check if pkgutil --forget commands are reachable in the script.

    Analyses the shell script structure to detect cases where exit
    statements could prevent pkgutil --forget from executing, such as:
    - Unconditional exit before pkgutil --forget at the top level
    - pkgutil --forget inside an else/if branch while exit is in the
      other branch
    - Early exit inside a guard clause before pkgutil --forget

    Args:
        uninstall_script: String content of the uninstall script

    Returns:
        List of warning strings describing reachability issues
    """
    lines = uninstall_script.strip().split('\n')
    warnings = []

    # Locate all exit and pkgutil --forget lines (excluding comments)
    forget_lines = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('#'):
            continue
        if 'pkgutil' in stripped and 'forget' in stripped:
            forget_lines.append((i, stripped))

    if not forget_lines:
        return warnings

    # Walk through the script tracking nesting depth
    in_function = 0
    in_if = 0

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('#'):
            continue

        # Track function blocks
        if (stripped.startswith('function ') and '{' in stripped):
            in_function += 1
        elif ('()' in stripped and '{' in stripped
                and not stripped.startswith('if')):
            in_function += 1
        if stripped == '}' and in_function > 0:
            in_function -= 1

        if in_function > 0:
            continue

        # Track if/fi blocks
        if stripped.startswith('if ') or stripped.startswith('if ['):
            in_if += 1
        if (stripped == 'fi' or stripped.startswith('fi ')
                or stripped.startswith('fi;')):
            in_if = max(0, in_if - 1)

        # Check for exit commands
        is_exit = (
            stripped == 'exit'
            or stripped.startswith('exit ')
            or stripped.startswith('exit;')
        )

        if is_exit:
            remaining = [
                (ln, txt) for ln, txt in forget_lines if ln > i
            ]
            if remaining:
                if in_if == 0:
                    warnings.append(
                        f"Unconditional 'exit' at script "
                        f"line {i + 1} will prevent "
                        f"'pkgutil --forget' at line "
                        f"{remaining[0][0] + 1} from running"
                    )
                else:
                    warnings.append(
                        f"Conditional 'exit' (inside "
                        f"if-block) at script line {i + 1} "
                        f"may prevent 'pkgutil --forget' at "
                        f"line {remaining[0][0] + 1} from "
                        f"running"
                    )

    return warnings


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


def extract_pkg_receipt_from_extension_attribute(ea_path):
    """Extract pkg receipt ID from extension attribute bash script.

    Args:
        ea_path: Path to the extension attribute bash script (.sh file)

    Returns:
        String pkg receipt ID or None if not found
    """
    try:
        with open(ea_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Look for pkgID="something" pattern in bash script
        match = re.search(r'pkgID=["\']([^"\']+)["\']', content)
        if match:
            return match.group(1)

        return None
    except Exception as e:
        print(f"  ⚠️  Error reading extension attribute {ea_path}: {e}")
        return None


def find_extension_attribute(recipe_name, private_recipes_dir):
    """Find the extension attribute bash script for a recipe.

    Args:
        recipe_name: Name of the recipe (e.g., "ExpressVPN")
        private_recipes_dir: Path to private-recipes directory

    Returns:
        Path to extension attribute .sh file or None if not found
    """
    # Look for the recipe folder in private-recipes
    recipe_folder = Path(private_recipes_dir) / recipe_name

    if not recipe_folder.exists():
        return None

    # Look for Extension Attribute .sh file
    for file in recipe_folder.iterdir():
        if (file.is_file() and 'Extension Attribute' in file.name
                and file.suffix == '.sh'):
            return file

    return None


def extract_recipe_name_from_override(override_path):
    """Extract the recipe name from an override file path.

    Args:
        override_path: Path to the override recipe

    Returns:
        Recipe name string (e.g., "ExpressVPN" from "ExpressVPN.definition.recipe")
    """
    # Get filename without extension
    filename = override_path.stem

    # Remove common suffixes like .definition, .munki, .pkg, etc.
    recipe_name = re.sub(
        r'\.(definition|munki|pkg|download|app_services)$', '', filename
    )

    # Handle architecture suffixes (-arm64, -x86_64)
    recipe_name = re.sub(r'-(arm64|x86_64)$', '', recipe_name)

    return recipe_name


def process_plist_override(override_path, private_recipes_dir):
    """Process a plist format override recipe.

    Args:
        override_path: Path to the override recipe
        private_recipes_dir: Path to private-recipes directory

    Returns:
        Tuple of (modified: bool, changes: list, warnings: list)
    """
    try:
        with open(override_path, 'rb') as f:
            recipe_data = plistlib.load(f)

        # Check if it has uninstall_script method
        pkginfo = recipe_data.get('Input', {}).get('pkginfo', {})
        uninstall_method = pkginfo.get('uninstall_method')
        uninstall_script = pkginfo.get('uninstall_script')

        if uninstall_method != 'uninstall_script' or not uninstall_script:
            return False, [], []

        # Extract recipe name
        recipe_name = extract_recipe_name_from_override(override_path)

        # Find extension attribute
        ea_path = find_extension_attribute(recipe_name, private_recipes_dir)
        if not ea_path:
            return (False, [], [])

        # Extract pkg receipt from extension attribute
        pkg_receipt = extract_pkg_receipt_from_extension_attribute(ea_path)
        if not pkg_receipt:
            # EA uses a non-pkg-receipt method (e.g. CFBundleVersion)
            return (False, [], [])

        # Check if pkgutil --forget is already in the script
        if ('pkgutil --forget' in uninstall_script
                and pkg_receipt in uninstall_script):
            # Receipt forget exists — check it is reachable
            reachability_warnings = check_forget_reachability(
                uninstall_script
            )
            return False, [], reachability_warnings

        # Add pkgutil --forget to the uninstall script
        # Insert it before the final exit or at the end
        lines = uninstall_script.split('\n')

        # Find where to insert (before exit or at the end)
        insert_index = len(lines)
        for i in range(len(lines) - 1, -1, -1):
            line = lines[i].strip()
            if line.startswith('exit'):
                insert_index = i
                break

        # Create the pkgutil forget command
        forget_command = f'/usr/sbin/pkgutil --forget "{pkg_receipt}"'

        # Insert the command with proper indentation
        if insert_index < len(lines) and lines[insert_index].strip():
            # Add before exit with blank line
            lines.insert(insert_index, '')
            lines.insert(insert_index + 1, PKG_RECEIPT_COMMENT)
            lines.insert(insert_index + 2, forget_command)
        else:
            # Add at end
            if lines and lines[-1].strip():
                lines.append('')
            lines.append(PKG_RECEIPT_COMMENT)
            lines.append(forget_command)

        # Update the recipe data
        new_uninstall_script = '\n'.join(lines)
        recipe_data['Input']['pkginfo']['uninstall_script'] = (
            new_uninstall_script
        )

        # Write back to file
        with open(override_path, 'wb') as f:
            plistlib.dump(recipe_data, f, sort_keys=False)

        changes = [f"Added pkgutil --forget for {pkg_receipt}"]
        return True, changes, []

    except Exception as e:
        print(f"  ❌ Error processing {override_path}: {str(e)}")
        print("  DEBUG: Full error details:")
        print(traceback.format_exc())
        return False, [], [f"Error: {str(e)}"]


def process_yaml_override(override_path, private_recipes_dir):
    """Process a YAML format override recipe.

    Args:
        override_path: Path to the override recipe
        private_recipes_dir: Path to private-recipes directory

    Returns:
        Tuple of (modified: bool, changes: list, warnings: list)
    """
    try:
        import yaml

        with open(override_path, 'r', encoding='utf-8') as f:
            recipe_data = yaml.safe_load(f)

        # Check if it has uninstall_script method
        pkginfo = recipe_data.get('Input', {}).get('pkginfo', {})
        uninstall_method = pkginfo.get('uninstall_method')
        uninstall_script = pkginfo.get('uninstall_script')

        if uninstall_method != 'uninstall_script' or not uninstall_script:
            return False, [], []

        # Extract recipe name
        recipe_name = extract_recipe_name_from_override(override_path)

        # Find extension attribute
        ea_path = find_extension_attribute(recipe_name, private_recipes_dir)
        if not ea_path:
            return (False, [], [])

        # Extract pkg receipt from extension attribute
        pkg_receipt = extract_pkg_receipt_from_extension_attribute(ea_path)
        if not pkg_receipt:
            # EA uses a non-pkg-receipt method (e.g. CFBundleVersion)
            return (False, [], [])

        # Check if pkgutil --forget is already in the script
        if ('pkgutil --forget' in uninstall_script
                and pkg_receipt in uninstall_script):
            # Receipt forget exists — check it is reachable
            reachability_warnings = check_forget_reachability(
                uninstall_script
            )
            return False, [], reachability_warnings

        # Add pkgutil --forget to the uninstall script
        lines = uninstall_script.split('\n')

        # Find where to insert (before exit or at the end)
        insert_index = len(lines)
        for i in range(len(lines) - 1, -1, -1):
            line = lines[i].strip()
            if line.startswith('exit'):
                insert_index = i
                break

        # Create the pkgutil forget command
        forget_command = f'/usr/sbin/pkgutil --forget "{pkg_receipt}"'

        # Insert the command
        if insert_index < len(lines) and lines[insert_index].strip():
            lines.insert(insert_index, '')
            lines.insert(insert_index + 1, PKG_RECEIPT_COMMENT)
            lines.insert(insert_index + 2, forget_command)
        else:
            if lines and lines[-1].strip():
                lines.append('')
            lines.append(PKG_RECEIPT_COMMENT)
            lines.append(forget_command)

        # Update the recipe data
        new_uninstall_script = '\n'.join(lines)
        recipe_data['Input']['pkginfo']['uninstall_script'] = new_uninstall_script

        # Write back to file
        with open(override_path, 'w', encoding='utf-8') as f:
            yaml.dump(recipe_data, f, default_flow_style=False, sort_keys=False)

        changes = [f"Added pkgutil --forget for {pkg_receipt}"]
        return True, changes, []

    except ImportError:
        return False, [], ["YAML support not available"]
    except Exception as e:
        print(f"  ❌ Error processing {override_path}: {str(e)}")
        print("  DEBUG: Full error details:")
        print(traceback.format_exc())
        return False, [], [f"Error: {str(e)}"]


def process_override(override_path, private_recipes_dir):
    """Process a single override file.

    Args:
        override_path: Path to the override recipe
        private_recipes_dir: Path to private-recipes directory

    Returns:
        Tuple of (modified: bool, changes: list, warnings: list)
    """
    is_yaml = override_path.suffix == '.yaml'

    if is_yaml:
        return process_yaml_override(override_path, private_recipes_dir)
    else:
        return process_plist_override(override_path, private_recipes_dir)


def main():
    verify_environment()

    print("OverridePkgReceiptChecker - AutoPkg Override Pkg Receipt Checker")
    print("=" * 70)
    print("This script will:")
    print("1. Find overrides with uninstall_method=uninstall_script")
    print("2. Look up the corresponding extension attribute in private-recipes")
    print("3. Extract the pkg receipt ID from the extension attribute")
    print("4. Ensure the uninstall script includes 'pkgutil --forget' for that receipt")
    print("=" * 70)

    try:
        # Get overrides directory
        print("\nEnter the path to your recipe overrides directory")
        print("(You can drag and drop the folder here): ", end='', flush=True)
        overrides_dir = clean_path(input())
        overrides_dir = os.path.abspath(overrides_dir)

        if not os.path.isdir(overrides_dir):
            print(f"Error: '{overrides_dir}' is not a valid directory")
            return

        # Get private-recipes directory
        print("\nEnter the path to your private-recipes directory")
        print("(You can drag and drop the folder here): ", end='', flush=True)
        private_recipes_dir = clean_path(input())
        private_recipes_dir = os.path.abspath(private_recipes_dir)

        if not os.path.isdir(private_recipes_dir):
            print(f"Error: '{private_recipes_dir}' is not a valid directory")
            return

        print(f"\nScanning overrides in: {overrides_dir}")
        print(f"Using private-recipes from: {private_recipes_dir}")

        modified_count = 0
        checked_count = 0
        modified_files = []
        all_warnings = []

        # Process all override files
        for override_path in Path(overrides_dir).glob("*.recipe*"):
            if override_path.suffix in ['.recipe', '.yaml']:
                checked_count += 1
                print(f"\n📋 Checking: {override_path.name}")

                modified, changes, warnings = process_override(override_path, private_recipes_dir)

                if warnings:
                    for warning in warnings:
                        print(f"  ⚠️  {warning}")
                        all_warnings.append((override_path.name, warning))

                if modified:
                    modified_count += 1
                    modified_files.append((override_path, changes))
                    for change in changes:
                        print(f"  ✓ {change}")

        print(f"\n{'=' * 70}")
        print("Processing complete!")
        print(f"Overrides checked: {checked_count}")
        print(f"Overrides modified: {modified_count}")
        print("=" * 70)

        if modified_files:
            print("\n✅ Modified files:")
            for file, changes in modified_files:
                print(f"  • {file.name}")
                for change in changes:
                    print(f"    - {change}")

        if all_warnings:
            print("\n⚠️  Warnings:")
            for filename, warning in all_warnings:
                print(f"  • {filename}: {warning}")

        if modified_files:
            print("\n⚠️  Please review the modified files before committing!")

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
        print("DEBUG: Full error details:")
        print(traceback.format_exc())


if __name__ == "__main__":
    main()

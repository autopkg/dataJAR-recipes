#!/usr/local/autopkg/python
"""
Script to check recipe overrides with uninstall scripts for pkg receipt forgetting.
Finds overrides with uninstall_method=uninstall_script, looks up the corresponding
extension attribute in private-recipes to find the pkg receipt, and ensures the
uninstall script includes 'pkgutil --forget' for that receipt.
Requires AutoPkg's Python installation.
"""

import functools
import os
import sys
from collections.abc import Callable
from pathlib import Path
import re
import traceback
import plistlib
from types import ModuleType
from typing import Any

# Make linter_common importable when run directly (a no-op under
# autopkg-linter.py, which already has this directory on sys.path).
# Kept as one if-statement so the import below isn't flagged E402.
if (_LINTERS_DIR := os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))) not in sys.path:
    sys.path.insert(0, _LINTERS_DIR)
from linter_common import clean_path, verify_environment


# Constants
PKG_RECEIPT_COMMENT = '# Forget pkg receipt'


def _forget_lines(lines: list[str]) -> list[tuple[int, str]]:
    """Locate all pkgutil --forget lines, excluding comments.

    Args:
        lines: Lines of the uninstall script

    Returns:
        List of (line_index, stripped_line) tuples
    """
    forget_lines = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('#'):
            continue
        if 'pkgutil' in stripped and 'forget' in stripped:
            forget_lines.append((i, stripped))
    return forget_lines


def _track_function_depth(stripped: str, in_function: int) -> int:
    """Update the function block depth for a script line.

    Args:
        stripped: The stripped script line
        in_function: Current function block depth

    Returns:
        The new function block depth
    """
    opens_function = (
        (stripped.startswith('function ') and '{' in stripped)
        or ('()' in stripped and '{' in stripped
            and not stripped.startswith('if'))
    )
    if opens_function:
        in_function += 1
    if stripped == '}' and in_function > 0:
        in_function -= 1
    return in_function


def _track_if_depth(stripped: str, in_if: int) -> int:
    """Update the if/fi block depth for a script line.

    Args:
        stripped: The stripped script line
        in_if: Current if-block depth

    Returns:
        The new if-block depth
    """
    if stripped.startswith(('if ', 'if [')):
        in_if += 1
    if stripped == 'fi' or stripped.startswith(('fi ', 'fi;')):
        in_if = max(0, in_if - 1)
    return in_if


def _is_exit(stripped: str) -> bool:
    """Check whether a stripped script line is an exit command."""
    return stripped == 'exit' or stripped.startswith(('exit ', 'exit;'))


def _exit_warning(exit_index: int, in_if: int,
                  forget_lines: list[tuple[int, str]]) -> str | None:
    """Build the warning for an exit that precedes pkgutil --forget.

    Args:
        exit_index: Index of the exit line in the script
        in_if: If-block depth at the exit line
        forget_lines: List of (line_index, stripped_line) forget tuples

    Returns:
        Warning string, or None if no forget line follows the exit
    """
    remaining = [
        (ln, txt) for ln, txt in forget_lines if ln > exit_index
    ]
    if not remaining:
        return None

    if in_if == 0:
        return (
            f"Unconditional 'exit' at script "
            f"line {exit_index + 1} will prevent "
            f"'pkgutil --forget' at line "
            f"{remaining[0][0] + 1} from running"
        )
    return (
        f"Conditional 'exit' (inside "
        f"if-block) at script line {exit_index + 1} "
        f"may prevent 'pkgutil --forget' at "
        f"line {remaining[0][0] + 1} from "
        f"running"
    )


def check_forget_reachability(uninstall_script: str) -> list[str]:
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
    warnings: list[str] = []

    # Locate all pkgutil --forget lines (excluding comments)
    forget_lines = _forget_lines(lines)

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
        in_function = _track_function_depth(stripped, in_function)

        if in_function > 0:
            continue

        # Track if/fi blocks
        in_if = _track_if_depth(stripped, in_if)

        # Check for exit commands
        if _is_exit(stripped):
            warning = _exit_warning(i, in_if, forget_lines)
            if warning:
                warnings.append(warning)

    return warnings


def extract_pkg_receipt_from_extension_attribute(ea_path: Path) -> str | None:
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


def find_extension_attribute(recipe_name: str,
                             private_recipes_dir: str) -> Path | None:
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


def extract_recipe_name_from_override(override_path: Path) -> str:
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


def _uninstall_script_to_check(recipe_data: dict[str, Any]) -> str | None:
    """Get an override's uninstall script if it uses uninstall_script.

    Args:
        recipe_data: Parsed override recipe

    Returns:
        The uninstall script, or None if the override doesn't use one
    """
    # Check if it has uninstall_script method
    pkginfo = recipe_data.get('Input', {}).get('pkginfo', {})
    uninstall_method = pkginfo.get('uninstall_method')
    uninstall_script = pkginfo.get('uninstall_script')

    if uninstall_method != 'uninstall_script' or not uninstall_script:
        return None
    return uninstall_script


def _pkg_receipt_for_override(override_path: Path,
                              private_recipes_dir: str) -> str | None:
    """Find the pkg receipt ID from an override's extension attribute.

    Args:
        override_path: Path to the override recipe
        private_recipes_dir: Path to private-recipes directory

    Returns:
        String pkg receipt ID, or None if there is no extension attribute
        or it doesn't use a pkg receipt (e.g. CFBundleVersion)
    """
    # Extract recipe name
    recipe_name = extract_recipe_name_from_override(override_path)

    # Find extension attribute
    ea_path = find_extension_attribute(recipe_name, private_recipes_dir)
    if not ea_path:
        return None

    # Extract pkg receipt from extension attribute
    return extract_pkg_receipt_from_extension_attribute(ea_path)


def _insert_forget_command(uninstall_script: str, pkg_receipt: str) -> str:
    """Add pkgutil --forget to an uninstall script.

    Inserts it before the final exit or at the end.

    Args:
        uninstall_script: String content of the uninstall script
        pkg_receipt: The pkg receipt ID to forget

    Returns:
        The updated uninstall script
    """
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

    return '\n'.join(lines)


def _plan_forget_update(
    recipe_data: dict[str, Any], override_path: Path,
    private_recipes_dir: str,
) -> tuple[str | None, list[str], str | None]:
    """Work out whether an override's uninstall script needs a forget.

    Args:
        recipe_data: Parsed override recipe
        override_path: Path to the override recipe
        private_recipes_dir: Path to private-recipes directory

    Returns:
        Tuple of (new_uninstall_script, warnings, pkg_receipt), where
        new_uninstall_script is None if no change is needed
    """
    uninstall_script = _uninstall_script_to_check(recipe_data)

    pkg_receipt = None
    if uninstall_script:
        pkg_receipt = _pkg_receipt_for_override(override_path,
                                                private_recipes_dir)

    if not uninstall_script or not pkg_receipt:
        return None, [], None

    # Check if pkgutil --forget is already in the script
    if ('pkgutil --forget' in uninstall_script
            and pkg_receipt in uninstall_script):
        # Receipt forget exists — check it is reachable
        return None, check_forget_reachability(uninstall_script), pkg_receipt

    return (_insert_forget_command(uninstall_script, pkg_receipt), [],
            pkg_receipt)


def _update_override(
    override_path: Path, private_recipes_dir: str,
    load: Callable[[Path], dict[str, Any]],
    dump: Callable[[Path, dict[str, Any]], None],
) -> tuple[bool, list[str], list[str]]:
    """Add a missing pkgutil --forget to an override's uninstall script.

    Args:
        override_path: Path to the override recipe
        private_recipes_dir: Path to private-recipes directory
        load: Function that reads the override from a path
        dump: Function that writes the override to a path

    Returns:
        Tuple of (modified: bool, changes: list, warnings: list)
    """
    try:
        recipe_data = load(override_path)

        new_uninstall_script, warnings, pkg_receipt = _plan_forget_update(
            recipe_data, override_path, private_recipes_dir
        )
        if new_uninstall_script is None:
            return False, [], warnings

        # Update the recipe data
        recipe_data['Input']['pkginfo']['uninstall_script'] = (
            new_uninstall_script
        )

        # Write back to file
        dump(override_path, recipe_data)

        changes = [f"Added pkgutil --forget for {pkg_receipt}"]
        return True, changes, []

    except Exception as e:
        print(f"  ❌ Error processing {override_path}: {str(e)}")
        print("  DEBUG: Full error details:")
        print(traceback.format_exc())
        return False, [], [f"Error: {str(e)}"]


def _load_plist(override_path: Path) -> dict[str, Any]:
    """Read a plist override."""
    with open(override_path, 'rb') as f:
        return plistlib.load(f)


def _dump_plist(override_path: Path, recipe_data: dict[str, Any]) -> None:
    """Write a plist override."""
    with open(override_path, 'wb') as f:
        plistlib.dump(recipe_data, f, sort_keys=False)


def _load_yaml(yaml_module: ModuleType,
               override_path: Path) -> dict[str, Any]:
    """Read a YAML override."""
    with open(override_path, 'r', encoding='utf-8') as f:
        return yaml_module.safe_load(f)


def _dump_yaml(yaml_module: ModuleType, override_path: Path,
               recipe_data: dict[str, Any]) -> None:
    """Write a YAML override."""
    with open(override_path, 'w', encoding='utf-8') as f:
        yaml_module.dump(recipe_data, f, default_flow_style=False,
                         sort_keys=False)


def process_plist_override(
    override_path: Path, private_recipes_dir: str,
) -> tuple[bool, list[str], list[str]]:
    """Process a plist format override recipe.

    Args:
        override_path: Path to the override recipe
        private_recipes_dir: Path to private-recipes directory

    Returns:
        Tuple of (modified: bool, changes: list, warnings: list)
    """
    return _update_override(override_path, private_recipes_dir,
                            _load_plist, _dump_plist)


def process_yaml_override(
    override_path: Path, private_recipes_dir: str,
) -> tuple[bool, list[str], list[str]]:
    """Process a YAML format override recipe.

    Args:
        override_path: Path to the override recipe
        private_recipes_dir: Path to private-recipes directory

    Returns:
        Tuple of (modified: bool, changes: list, warnings: list)
    """
    try:
        import yaml
    except ImportError:
        return False, [], ["YAML support not available"]

    return _update_override(override_path, private_recipes_dir,
                            functools.partial(_load_yaml, yaml),
                            functools.partial(_dump_yaml, yaml))


def process_override(
    override_path: Path, private_recipes_dir: str,
) -> tuple[bool, list[str], list[str]]:
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


def _prompt_for_dir(description: str) -> str | None:
    """Prompt for a directory path.

    Args:
        description: What the directory holds, e.g. "private-recipes"

    Returns:
        Absolute path to the directory, or None if it isn't a directory
    """
    print(f"\nEnter the path to your {description} directory")
    print("(You can drag and drop the folder here): ", end='', flush=True)
    dir_path = clean_path(input())
    dir_path = os.path.abspath(dir_path)

    if not os.path.isdir(dir_path):
        print(f"Error: '{dir_path}' is not a valid directory")
        return None
    return dir_path


def _process_overrides(
    overrides_dir: str, private_recipes_dir: str,
) -> tuple[int, list[tuple[Path, list[str]]], list[tuple[str, str]]]:
    """Check every override in overrides_dir.

    Args:
        overrides_dir: Path to the recipe overrides directory
        private_recipes_dir: Path to private-recipes directory

    Returns:
        Tuple of (checked_count, modified_files, all_warnings)
    """
    checked_count = 0
    modified_files = []
    all_warnings = []

    # Process all override files
    for override_path in Path(overrides_dir).glob("*.recipe*"):
        if override_path.suffix not in ['.recipe', '.yaml']:
            continue

        checked_count += 1
        print(f"\n📋 Checking: {override_path.name}")

        modified, changes, warnings = process_override(override_path,
                                                       private_recipes_dir)

        for warning in warnings:
            print(f"  ⚠️  {warning}")
            all_warnings.append((override_path.name, warning))

        if modified:
            modified_files.append((override_path, changes))
            for change in changes:
                print(f"  ✓ {change}")

    return checked_count, modified_files, all_warnings


def _print_summary(checked_count: int,
                   modified_files: list[tuple[Path, list[str]]],
                   all_warnings: list[tuple[str, str]]) -> None:
    """Print the processing summary.

    Args:
        checked_count: Number of overrides checked
        modified_files: List of (override_path, changes) tuples
        all_warnings: List of (filename, warning) tuples
    """
    print(f"\n{'=' * 70}")
    print("Processing complete!")
    print(f"Overrides checked: {checked_count}")
    print(f"Overrides modified: {len(modified_files)}")
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


def main() -> None:
    """Prompt for directories and check overrides' pkg receipt forgets."""
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
        overrides_dir = _prompt_for_dir("recipe overrides")
        if overrides_dir is None:
            return

        # Get private-recipes directory
        private_recipes_dir = _prompt_for_dir("private-recipes")
        if private_recipes_dir is None:
            return

        print(f"\nScanning overrides in: {overrides_dir}")
        print(f"Using private-recipes from: {private_recipes_dir}")

        checked_count, modified_files, all_warnings = _process_overrides(
            overrides_dir, private_recipes_dir
        )
        _print_summary(checked_count, modified_files, all_warnings)

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
        print("DEBUG: Full error details:")
        print(traceback.format_exc())


if __name__ == "__main__":
    main()

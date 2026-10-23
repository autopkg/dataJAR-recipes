#!/usr/local/autopkg/python
"""
Script to check and fix recipes with DeprecationWarning processor.
Ensures DeprecationWarning is at the top of the Process array.
Ensures MinimumVersion is at least 1.1.
Optionally adds StopProcessingIf processor after DeprecationWarning.
Supports both plist and yaml recipe formats.
Requires AutoPkg's Python installation.
"""

import os
import sys
import yaml
from pathlib import Path
import re
import traceback
from typing import Any

# Make linter_common importable when run directly (a no-op under
# autopkg-linter.py, which already has this directory on sys.path).
# Kept as one if-statement so the import below isn't flagged E402.
if (_LINTERS_DIR := os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))) not in sys.path:
    sys.path.insert(0, _LINTERS_DIR)
from linter_common import clean_path, verify_environment


# Constants
DICT_TAG = '<dict>'
PROCESS_PATTERN = r'(<key>Process</key>\s*\n\s*<array>)(.*?)(</array>)'


def compare_version(version_str: str, minimum: float) -> bool:
    """Compare version string with minimum required version.

    Args:
        version_str: Version string (e.g., "1.1", "2.7", "2.7.6")
        minimum: Minimum version as float (e.g., 1.1)

    Returns:
        True if version_str >= minimum, False otherwise
    """
    try:
        # Parse version string by taking first two parts
        parts = version_str.split('.')
        if len(parts) >= 2:
            # Use first two parts for comparison (e.g., "2.7.6" -> 2.7)
            version = float(f"{parts[0]}.{parts[1]}")
        else:
            version = float(version_str)
        return version >= minimum
    except (ValueError, TypeError, IndexError):
        return False


def ask_add_stop_processing(warning_message: str | None = None) -> bool:
    """Ask user if they want to add StopProcessingIf processor.

    Args:
        warning_message: Optional deprecation warning message to display
    """
    if warning_message:
        print(f"    Deprecation message: \"{warning_message}\"")
    while True:
        response = input(
            "    Add StopProcessingIf processor after "
            "DeprecationWarning? (y/n): "
        ).strip().lower()
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        else:
            print("    Please enter 'y' or 'n'")


def _yaml_update_minimum_version(recipe: dict[str, Any]) -> bool:
    """Raise a YAML recipe's MinimumVersion to at least 1.1.

    Args:
        recipe: Parsed YAML recipe, updated in place

    Returns:
        True if MinimumVersion was changed
    """
    current_version = recipe.get('MinimumVersion', '0.0')
    if compare_version(current_version, 1.1):
        return False

    print(f"DEBUG: Updating MinimumVersion from {current_version} to 1.1")
    recipe['MinimumVersion'] = '1.1'
    return True


def _find_yaml_deprecation(
    process: list[dict[str, Any]],
) -> tuple[int | None, int | None]:
    """Find the DeprecationWarning step and a StopProcessingIf after it.

    Args:
        process: The recipe's Process array

    Returns:
        Tuple of (deprecation_index, stop_processing_index), either of
        which may be None
    """
    deprecation_index = None
    stop_processing_index = None

    for i, process_step in enumerate(process):
        if process_step.get('Processor') == 'DeprecationWarning':
            deprecation_index = i
        # Check if it's the TRUEPREDICATE version
        # after DeprecationWarning
        elif (deprecation_index is not None and
                i == deprecation_index + 1 and
                _is_yaml_stop_processing(process_step)):
            stop_processing_index = i

    return deprecation_index, stop_processing_index


def _is_yaml_stop_processing(step: dict[str, Any]) -> bool:
    """Check if a YAML step is StopProcessingIf with TRUEPREDICATE."""
    return (step.get('Processor') == 'StopProcessingIf' and
            step.get('Arguments', {}).get('predicate') ==
            'TRUEPREDICATE')


def _add_yaml_stop_processing(process: list[dict[str, Any]]) -> bool:
    """Insert a StopProcessingIf step after the DeprecationWarning step.

    Args:
        process: The recipe's Process array, updated in place

    Returns:
        True if the step was inserted
    """
    stop_processing_step = {
        'Processor': 'StopProcessingIf',
        'Arguments': {
            'predicate': 'TRUEPREDICATE'
        }
    }
    # Find DeprecationWarning again
    # (it should be at index 0 now)
    for i, step in enumerate(process):
        if step.get('Processor') == 'DeprecationWarning':
            process.insert(i + 1, stop_processing_step)
            return True
    return False


def _fix_yaml_process(process: list[dict[str, Any]],
                      recipe_path: Path) -> bool:
    """Move DeprecationWarning to the top and offer StopProcessingIf.

    Args:
        process: The recipe's Process array, updated in place
        recipe_path: Path to the recipe file

    Returns:
        True if the Process array was changed
    """
    # Find DeprecationWarning processor
    deprecation_index, stop_processing_index = _find_yaml_deprecation(
        process
    )

    if deprecation_index is None:
        return False

    print(
        f"DEBUG: Found DeprecationWarning at index "
        f"{deprecation_index}"
    )
    modified = False

    # Check if DeprecationWarning is not at the top
    if deprecation_index != 0:
        print(
            "DEBUG: Moving DeprecationWarning to top of "
            "Process array"
        )
        deprecation_step = process.pop(deprecation_index)
        process.insert(0, deprecation_step)
        modified = True
        deprecation_index = 0

        # Reset stop_processing_index, it will be rechecked
        stop_processing_index = None

    # Check for StopProcessingIf after DeprecationWarning
    if (len(process) > deprecation_index + 1 and
            _is_yaml_stop_processing(process[deprecation_index + 1])):
        stop_processing_index = deprecation_index + 1

    if stop_processing_index is None:
        print(f"\nRecipe: {recipe_path.name}")
        if ask_add_stop_processing() and _add_yaml_stop_processing(process):
            modified = True

    return modified


def modify_yaml_recipe(content: str, recipe_path: Path) -> tuple[str, bool]:
    """Modify yaml recipe content while preserving formatting."""
    print("DEBUG: Processing YAML recipe")
    recipe = yaml.safe_load(content)

    # Check MinimumVersion
    modified = _yaml_update_minimum_version(recipe)

    if 'Process' in recipe and recipe['Process']:
        modified = (
            _fix_yaml_process(recipe['Process'], recipe_path) or modified
        )

    if modified:
        # Convert back to YAML with proper formatting
        output = yaml.dump(
            recipe, default_flow_style=False, sort_keys=False, indent=4
        )
        return output, True

    return content, False


def get_indent_level(line: str) -> int:
    """Get the indentation level (number of spaces) for a line."""
    return len(line) - len(line.lstrip())


def _update_plist_minimum_version(content: str) -> tuple[str, bool]:
    """Raise a plist recipe's MinimumVersion to at least 1.1.

    Args:
        content: String content of the plist recipe

    Returns:
        Tuple of (content, modified)
    """
    modified = False

    # Check and update MinimumVersion
    min_version_pattern = (
        r'(<key>MinimumVersion</key>\s*\n\s*)<string>(.*?)</string>'
    )
    min_version_match = re.search(min_version_pattern, content, re.DOTALL)

    if min_version_match:
        current_version = min_version_match.group(2)
        if not compare_version(current_version, 1.1):
            print(
                f"DEBUG: Updating MinimumVersion from {current_version} "
                f"to 1.1"
            )
            # Replace only the version value, preserving exact indentation
            old_string = min_version_match.group(0)
            new_string = min_version_match.group(1) + '<string>1.1</string>'
            content = content.replace(old_string, new_string)
            modified = True
    else:
        # Add MinimumVersion after opening <dict>
        print("DEBUG: Adding MinimumVersion 1.1")
        dict_match = re.search(
            r'(<\?xml.*?>\s*<!DOCTYPE.*?>\s*<plist.*?>\s*<dict>)',
            content, re.DOTALL
        )
        if dict_match:
            content = content.replace(
                dict_match.group(1),
                dict_match.group(1) +
                '\n    <key>MinimumVersion</key>\n    <string>1.1</string>'
            )
            modified = True

    return content, modified


def _matching_dict_end(process_content: str, dict_start: int) -> int:
    """Find the end of the dict opening at dict_start.

    Counts depth so nested dicts are matched correctly.

    Args:
        process_content: Content of the Process array
        dict_start: Position of the opening <dict>

    Returns:
        Position just after the matching </dict>, or -1 if not found
    """
    depth = 1
    # Start after <dict>
    search_pos = dict_start + 6

    while search_pos < len(process_content) and depth > 0:
        next_open = process_content.find(DICT_TAG, search_pos)
        next_close = process_content.find('</dict>', search_pos)

        if next_close == -1:
            break

        if next_open != -1 and next_open < next_close:
            depth += 1
            search_pos = next_open + 6
        else:
            depth -= 1
            if depth == 0:
                # Include </dict>
                return next_close + 7
            search_pos = next_close + 7

    return -1


def _find_processor_dicts(
    process_content: str,
) -> list[tuple[str, int, int]]:
    """Find all processor dicts in a Process array.

    Args:
        process_content: Content of the Process array

    Returns:
        List of (dict_content, dict_start, dict_end) tuples
    """
    # We need to properly match nested dicts by counting depth
    processor_dicts = []
    pos = 0
    while pos < len(process_content):
        dict_start = process_content.find(DICT_TAG, pos)
        if dict_start == -1:
            break

        # Count depth to find matching </dict>
        dict_end = _matching_dict_end(process_content, dict_start)

        if dict_end != -1:
            dict_content = process_content[dict_start:dict_end]
            processor_dicts.append((dict_content, dict_start, dict_end))
            pos = dict_end
        else:
            pos = dict_start + 6

    return processor_dicts


def _plist_processor_dicts(process_match: re.Match[str] | None) -> list[str]:
    """Get the processor dicts from a matched plist Process array.

    Args:
        process_match: Match of PROCESS_PATTERN, or None if not found

    Returns:
        List of processor dict contents, empty if none were found
    """
    if not process_match:
        print("DEBUG: No Process array found")
        return []

    # Find all processor dicts in the Process array
    processor_dicts = [
        dict_content for dict_content, _, _
        in _find_processor_dicts(process_match.group(2))
    ]

    if not processor_dicts:
        print("DEBUG: No processors found in Process array")
    return processor_dicts


def _has_stop_processing_after(processor_dicts: list[str],
                               index: int) -> bool:
    """Check if the processor after index is StopProcessingIf.

    Args:
        processor_dicts: List of processor dict contents
        index: Index of the DeprecationWarning processor

    Returns:
        True if the next processor is StopProcessingIf with TRUEPREDICATE
    """
    if index + 1 < len(processor_dicts):
        next_dict = processor_dicts[index + 1]
        if ('StopProcessingIf' in next_dict and
                'TRUEPREDICATE' in next_dict):
            print(
                "DEBUG: Found StopProcessingIf after "
                "DeprecationWarning"
            )
            return True
    return False


def _find_plist_deprecation(
    processor_dicts: list[str],
) -> tuple[int, bool] | None:
    """Find the first DeprecationWarning processor.

    Args:
        processor_dicts: List of processor dict contents

    Returns:
        Tuple of (deprecation_index, stop_processing_after_deprecation),
        or None if there is no DeprecationWarning processor
    """
    for i, dict_content in enumerate(processor_dicts):
        if ('DeprecationWarning' in dict_content and
                '<key>Processor</key>' in dict_content):
            print(f"DEBUG: Found DeprecationWarning at index {i}")

            # Check if next processor is StopProcessingIf with TRUEPREDICATE
            return i, _has_stop_processing_after(processor_dicts, i)

    print("DEBUG: No DeprecationWarning processor found")
    return None


def _reindent_dict(dict_content: str, base_indent: str) -> str:
    """Re-indent each line of a processor dict to base_indent.

    Relative indentation within the dict is not kept, and blank lines
    become empty.
    """
    lines = dict_content.split('\n')
    indented_lines = []
    for line in lines:
        if line.strip():
            indented_lines.append(base_indent + line.lstrip())
        else:
            indented_lines.append('')
    return '\n'.join(indented_lines)


def _move_plist_deprecation_to_top(content: str,
                                   process_match: re.Match[str],
                                   processor_dicts: list[str],
                                   deprecation_index: int) -> str:
    """Move the DeprecationWarning processor to the top of Process.

    Args:
        content: String content of the plist recipe
        process_match: Match of PROCESS_PATTERN in content
        processor_dicts: List of processor dict contents
        deprecation_index: Index of the DeprecationWarning processor

    Returns:
        The updated content
    """
    print("DEBUG: Moving DeprecationWarning to top of Process array")

    # Extract all processor dicts
    all_dicts = list(processor_dicts)

    # Move DeprecationWarning to top
    deprecation = all_dicts.pop(deprecation_index)
    all_dicts.insert(0, deprecation)

    # Get base indentation from first dict
    first_dict_match = re.search(r'\n(\s*)<dict>', process_match.group(2))
    base_indent = (
        first_dict_match.group(1) if first_dict_match else '        '
    )

    # Rebuild process content
    new_process_content = '\n'
    for dict_content in all_dicts:
        # Ensure proper indentation
        new_process_content += _reindent_dict(dict_content,
                                              base_indent) + '\n'

    # Replace the process content
    return content.replace(
        process_match.group(0),
        f'{process_match.group(1)}{new_process_content}'
        f'{base_indent.rstrip()}    {process_match.group(3)}'
    )


def _insert_plist_stop_processing(content: str) -> tuple[str, bool]:
    """Insert a StopProcessingIf processor after the first processor.

    Args:
        content: String content of the plist recipe

    Returns:
        Tuple of (content, modified)
    """
    # Get the base indentation
    first_dict_match = re.search(
        r'\n(\s*)<dict>',
        content[content.find('<key>Process</key>'):]
    )
    base_indent = (
        first_dict_match.group(1) if first_dict_match else '        '
    )

    # Create StopProcessingIf processor with 4-space indentation
    stop_processing = f'''{base_indent}<dict>
{base_indent}    <key>Processor</key>
{base_indent}    <string>StopProcessingIf</string>
{base_indent}    <key>Arguments</key>
{base_indent}    <dict>
{base_indent}        <key>predicate</key>
{base_indent}        <string>TRUEPREDICATE</string>
{base_indent}    </dict>
{base_indent}</dict>'''

    # Find where to insert (after DeprecationWarning)
    # Re-find the Process array in the modified content
    process_match = re.search(PROCESS_PATTERN, content, re.DOTALL)
    if not process_match:
        return content, False

    # Re-find processor dicts using depth counting
    processor_dicts = _find_processor_dicts(process_match.group(2))
    if not processor_dicts:
        return content, False

    # Insert after first dict
    # (DeprecationWarning should be first now)
    _, _, first_end = processor_dicts[0]
    insert_pos = process_match.start(2) + first_end

    content = (
        content[:insert_pos] + '\n' + stop_processing +
        content[insert_pos:]
    )
    print("DEBUG: Added StopProcessingIf processor")
    return content, True


def _offer_plist_stop_processing(content: str, deprecation_dict: str,
                                 recipe_path: Path) -> tuple[str, bool]:
    """Ask whether to add StopProcessingIf and add it if wanted.

    Args:
        content: String content of the plist recipe
        deprecation_dict: Content of the DeprecationWarning processor
        recipe_path: Path to the recipe file

    Returns:
        Tuple of (content, modified)
    """
    # Extract warning_message from deprecation_dict
    warning_message = None
    warning_match = re.search(
        r'<key>warning_message</key>\s*\n\s*<string>([^<]+)</string>',
        deprecation_dict
    )
    if warning_match:
        warning_message = warning_match.group(1)

    print(f"\nRecipe: {recipe_path.name}")
    if not ask_add_stop_processing(warning_message):
        return content, False
    return _insert_plist_stop_processing(content)


def modify_plist_content(content: str, recipe_path: Path) -> tuple[str, bool]:
    """Modify the plist recipe content while preserving formatting."""
    print("DEBUG: Starting plist content modification...")

    # Check and update MinimumVersion
    content, modified = _update_plist_minimum_version(content)

    # Find the Process array
    process_match = re.search(PROCESS_PATTERN, content, re.DOTALL)
    processor_dicts = _plist_processor_dicts(process_match)

    # Find DeprecationWarning and StopProcessingIf
    found = (
        _find_plist_deprecation(processor_dicts) if processor_dicts
        else None
    )
    if process_match is None or found is None:
        return content, False

    deprecation_index, stop_processing_after_deprecation = found
    deprecation_dict = processor_dicts[deprecation_index]

    # Check if DeprecationWarning needs to be moved to top
    if deprecation_index != 0:
        content = _move_plist_deprecation_to_top(
            content, process_match, processor_dicts, deprecation_index
        )
        modified = True

    # Check if StopProcessingIf needs to be added
    if not stop_processing_after_deprecation:
        content, added = _offer_plist_stop_processing(
            content, deprecation_dict, recipe_path
        )
        modified = added or modified

    return content, modified


def _write_and_verify(recipe_path: Path, modified_content: str) -> bool:
    """Write modified content to a recipe and verify the write.

    Args:
        recipe_path: Path to the recipe file
        modified_content: The modified content

    Returns:
        True if the content was written and verified
    """
    print(f"DEBUG: Writing changes to: {recipe_path}")
    with open(recipe_path, 'w', encoding='utf-8') as file:
        file.write(modified_content)

    # Verify the changes were written
    with open(recipe_path, 'r', encoding='utf-8') as file:
        verification_content = file.read()

    if verification_content != modified_content:
        print(
            f"❌ Warning: File write verification failed for "
            f"{recipe_path}"
        )
        return False

    print(
        f"✓ Successfully modified and verified: {recipe_path}"
    )
    return True


def _modify_recipe(recipe_path: Path, original_content: str,
                   is_yaml: bool) -> bool:
    """Fix a recipe that has a DeprecationWarning processor.

    Args:
        recipe_path: Path to the recipe file
        original_content: String content of the recipe
        is_yaml: Whether the recipe is YAML

    Returns:
        True if the recipe was modified and verified
    """
    print(f"\nFound DeprecationWarning in: {recipe_path}")

    if is_yaml:
        modified_content, was_modified = modify_yaml_recipe(
            original_content, recipe_path
        )
    else:
        modified_content, was_modified = modify_plist_content(
            original_content, recipe_path
        )

    if not was_modified:
        print(f"No modifications needed for: {recipe_path}")
        return False

    return _write_and_verify(recipe_path, modified_content)


def process_recipe(recipe_path: Path) -> bool:
    """Process a single recipe file and make necessary modifications."""
    try:
        is_yaml = recipe_path.suffix == '.yaml'
        print(f"\nDEBUG: Processing {recipe_path}")
        print(f"DEBUG: File type: {'YAML' if is_yaml else 'plist'}")

        # Read original content
        with open(recipe_path, 'r', encoding='utf-8') as file:
            original_content = file.read()
            print(f"DEBUG: Original content length: {len(original_content)}")

        # Check if recipe has DeprecationWarning
        modified = False
        if 'DeprecationWarning' not in original_content:
            print(
                f"Skipping {recipe_path} - "
                f"no DeprecationWarning processor found"
            )
        else:
            modified = _modify_recipe(recipe_path, original_content,
                                      is_yaml)
        return modified

    except Exception as e:
        print(f"❌ Error processing {recipe_path}: {str(e)}")
        print("DEBUG: Full error details:")
        print(traceback.format_exc())
        return False


def main() -> None:
    """Prompt for a recipe directory and fix its deprecated recipes."""
    verify_environment()

    print("DeprecationChecker - AutoPkg Recipe Processor")
    print("=" * 50)
    print("This script will:")
    print("1. Check for DeprecationWarning processor")
    print("2. Ensure it's at the top of the Process array")
    print("3. Ensure MinimumVersion is at least 1.1")
    print("4. Optionally add StopProcessingIf processor")
    print("=" * 50)
    print("\nEnter the path to your recipe directory")
    print("(You can drag and drop the folder here): ", end='', flush=True)

    try:
        recipe_dir = clean_path(input())
        recipe_dir = os.path.abspath(recipe_dir)

        if not os.path.isdir(recipe_dir):
            print(
                f"Error: '{recipe_dir}' is not a valid directory"
            )
            print(
                "Make sure the path exists and you have permission to "
                "access it."
            )
            return

        print(f"\nScanning recipes in: {recipe_dir}")

        modified_count = 0
        recipe_count = 0
        modified_files = []

        # Process all recipe files (not just .download.recipe)
        for recipe_path in Path(recipe_dir).rglob("*.recipe*"):
            if recipe_path.suffix in ['.recipe', '.yaml']:
                recipe_count += 1
                if process_recipe(recipe_path):
                    modified_count += 1
                    modified_files.append(recipe_path)

        print(f"\n{'=' * 50}")
        print("Processing complete!")
        print(f"Recipes processed: {recipe_count}")
        print(f"Recipes modified: {modified_count}")
        print(f"{'=' * 50}")

        if modified_files:
            print("\nModified files:")
            for file in modified_files:
                print(f"  ✓ {file}")

            print(
                "\nPlease verify these files in your version control "
                "system."
            )

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
        print("DEBUG: Full error details:")
        print(traceback.format_exc())


if __name__ == "__main__":
    main()

#!/usr/local/autopkg/python
"""
Script to update ChecksumVerifier processors in AutoPkg recipes.
Changes the 'pathname' argument key to 'checksum_pathname' in ChecksumVerifier
processor Arguments dicts.

This is necessary because ChecksumVerifier uses 'checksum_pathname' as the
argument name, not 'pathname'.

Supports both plist and YAML recipe formats.
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


# Constants
DICT_TAG = '<dict>'
DICT_CLOSE_TAG = '</dict>'
PATHNAME_KEY = '<key>pathname</key>'
CHECKSUM_PATHNAME_KEY = '<key>checksum_pathname</key>'


def _find_matching_dict_close(content: str, dict_start: int) -> int:
    """Find the </dict> that closes the <dict> at dict_start.

    Uses depth counting so nested dicts are skipped.

    Args:
        content: String content of the recipe
        dict_start: Position of the opening <dict>

    Returns:
        Position of the matching </dict>, or -1 if there is none
    """
    depth = 1
    search_pos = dict_start + 6

    while search_pos < len(content):
        if content[search_pos:search_pos+6] == DICT_TAG:
            depth += 1
            search_pos += 6
        elif content[search_pos:search_pos+7] == DICT_CLOSE_TAG:
            depth -= 1
            if depth == 0:
                return search_pos
            search_pos += 7
        else:
            search_pos += 1

    return -1


def _processor_dict_bounds(content: str,
                           processor_pos: int) -> tuple[int, int]:
    """Find the processor dict around a Processor key.

    Args:
        content: String content of the recipe
        processor_pos: Position of the processor's <key>Processor</key>

    Returns:
        Tuple of (dict_start, dict_close), where dict_close is the
        position of the closing </dict>, or -1 if the dict is not found
    """
    # Search backwards to find the opening <dict> for this processor
    dict_start = content.rfind(DICT_TAG, 0, processor_pos)
    if dict_start == -1:
        return -1, -1

    return dict_start, _find_matching_dict_close(content, dict_start)


def has_checksum_verifier_needing_update(content: str) -> bool:
    """Check if recipe has ChecksumVerifier processor needing updates.

    Args:
        content: String content of the recipe

    Returns:
        Boolean indicating if changes are needed
    """
    # Look for ChecksumVerifier processor
    if 'ChecksumVerifier</string>' not in content:
        return False

    # Check each ChecksumVerifier processor dict for checksum_pathname
    checksum_verifier_pattern = (
        r'<key>Processor</key>\s*<string>[^<]*'
        r'ChecksumVerifier</string>'
    )

    # For each ChecksumVerifier, check if it needs updates
    for match in re.finditer(checksum_verifier_pattern, content):
        dict_start, dict_close = _processor_dict_bounds(
            content, match.start()
        )
        if dict_close == -1:
            continue

        processor_dict = content[dict_start:dict_close+7]

        # A dict with pathname needs a rename, and one without
        # checksum_pathname needs it adding; both lack checksum_pathname
        if CHECKSUM_PATHNAME_KEY not in processor_dict:
            return True

    return False


def _arguments_indent(args_content: str, closing_indent: str) -> str:
    """Work out the indent for a new key in an Arguments dict.

    Args:
        args_content: Content of the Arguments dict
        closing_indent: Indent before the Arguments dict's </dict>

    Returns:
        Indent string for the new key
    """
    # Look for last key in Arguments dict to match indentation
    last_key_match = None
    for key_match in re.finditer(
            r'\n(\s*)<key>[^<]+</key>', args_content):
        last_key_match = key_match

    if last_key_match:
        return last_key_match.group(1)

    # Fallback: Use closing_indent + one level
    if '\t' in closing_indent:
        return closing_indent + '\t'

    # Assume 4 spaces per indent level
    return closing_indent + '    '


def _add_checksum_pathname(processor_dict: str) -> str | None:
    """Add checksum_pathname to the end of a processor's Arguments dict.

    Args:
        processor_dict: Content of the processor dict

    Returns:
        Updated processor dict, or None if it has no Arguments dict
    """
    # Find the Arguments dict within this processor
    args_match = re.search(
        r'<key>Arguments</key>\s*\n\s*<dict>(.*?)\n'
        r'(\s*)</dict>',
        processor_dict, re.DOTALL
    )

    if not args_match:
        return None

    args_content = args_match.group(1)
    # Capture the indent before </dict>
    closing_indent = args_match.group(2)
    args_start = args_match.start(1)

    # Detect indentation from existing content
    indent = _arguments_indent(args_content, closing_indent)

    # Add checksum_pathname at end of Arguments dict
    new_key = (
        f'\n{indent}<key>checksum_pathname</key>\n'
        f'{indent}<string>%pathname%</string>'
    )

    # Trim trailing whitespace from args_content
    trimmed_args = args_content.rstrip('\n\t ')

    # Build the new args content with proper spacing
    new_args_content = trimmed_args + new_key

    # Replace Arguments content in the processor dict
    return (
        processor_dict[:args_start] +
        new_args_content + '\n' +
        closing_indent + DICT_CLOSE_TAG +
        processor_dict[args_match.end():]
    )


def _update_processor_dict(processor_dict: str) -> tuple[str, int, int]:
    """Update one ChecksumVerifier processor dict.

    Args:
        processor_dict: Content of the processor dict

    Returns:
        Tuple of (updated_dict, rename_count, added_count)
    """
    # Case 1: Has pathname, needs to be renamed
    if (PATHNAME_KEY in processor_dict and
            CHECKSUM_PATHNAME_KEY not in processor_dict):
        renamed_dict = processor_dict.replace(
            PATHNAME_KEY, CHECKSUM_PATHNAME_KEY
        )
        return renamed_dict, 1, 0

    # Case 2: Missing checksum_pathname entirely, add it
    updated_dict: str | None = None
    if CHECKSUM_PATHNAME_KEY not in processor_dict:
        updated_dict = _add_checksum_pathname(processor_dict)

    if updated_dict is None:
        return processor_dict, 0, 0
    return updated_dict, 0, 1


def update_checksum_verifier_arguments(
    content: str,
) -> tuple[str, int, int]:
    """Update ChecksumVerifier processors to use checksum_pathname.

    This function:
    1. Renames 'pathname' to 'checksum_pathname' if present
    2. Adds 'checksum_pathname' with value '%pathname%' if missing

    Args:
        content: String content of the recipe

    Returns:
        Tuple of (modified_content, rename_count, added_count)
    """
    rename_count = 0
    added_count = 0

    # Find all ChecksumVerifier processors
    checksum_verifier_pattern = (
        r'<key>Processor</key>\s*<string>[^<]*ChecksumVerifier</string>'
    )
    matches = list(re.finditer(checksum_verifier_pattern, content))

    # Process matches in reverse order to maintain positions
    for match in reversed(matches):
        dict_start, dict_close = _processor_dict_bounds(
            content, match.start()
        )
        if dict_close == -1:
            continue

        processor_dict = content[dict_start:dict_close+7]
        updated_dict, renamed, added = _update_processor_dict(
            processor_dict
        )
        rename_count += renamed
        added_count += added

        # Replace in content if changed
        if updated_dict != processor_dict:
            content = (
                content[:dict_start] + updated_dict +
                content[dict_close+7:]
            )

    return content, rename_count, added_count


def _update_plist_content(recipe_path: Path,
                          original_content: str) -> list[str]:
    """Update a plist recipe's ChecksumVerifier processors on disk.

    Args:
        recipe_path: Path to the recipe file
        original_content: String content of the recipe

    Returns:
        List of changes made, empty if the recipe was not modified
    """
    # Check if changes are needed
    if not has_checksum_verifier_needing_update(original_content):
        return []

    # Update the ChecksumVerifier processors
    modified_content, rename_count, added_count = (
        update_checksum_verifier_arguments(original_content)
    )

    if rename_count == 0 and added_count == 0:
        return []

    # Write changes
    with open(recipe_path, 'w', encoding='utf-8') as f:
        f.write(modified_content)

    changes = []
    if rename_count > 0:
        changes.append(
            f"Renamed pathname → checksum_pathname in "
            f"{rename_count} processor(s)"
        )
    if added_count > 0:
        changes.append(
            f"Added checksum_pathname to {added_count} processor(s)"
        )

    return changes


def process_plist_recipe(recipe_path: Path) -> tuple[bool, list[str]]:
    """Process a plist recipe file.

    Args:
        recipe_path: Path to the recipe file

    Returns:
        Tuple of (modified: bool, changes: list)
    """
    try:
        # Read original content
        with open(recipe_path, 'r', encoding='utf-8') as f:
            original_content = f.read()

        changes = _update_plist_content(recipe_path, original_content)
        return bool(changes), changes

    except Exception as e:
        print(f"Error processing {recipe_path}: {e}")
        traceback.print_exc()
        return False, []


def _update_yaml_processors(processors: list[object]) -> list[str]:
    """Update ChecksumVerifier processors in a YAML Process array.

    Args:
        processors: The recipe's Process array

    Returns:
        List of changes made
    """
    changes = []

    # Check each processor in the Process array
    for processor in processors:
        if not isinstance(processor, dict):
            continue

        processor_name = processor.get('Processor', '')

        # Check if this is a ChecksumVerifier processor
        if 'ChecksumVerifier' not in processor_name:
            continue

        arguments = processor.get('Arguments', {})

        # Case 1: Has pathname, needs to be renamed
        if ('pathname' in arguments and
                'checksum_pathname' not in arguments):
            arguments['checksum_pathname'] = (
                arguments.pop('pathname')
            )
            changes.append(
                "Renamed pathname → checksum_pathname"
            )

        # Case 2: Missing checksum_pathname entirely, add it
        elif 'checksum_pathname' not in arguments:
            arguments['checksum_pathname'] = '%pathname%'
            changes.append(
                "Added checksum_pathname with default value "
                "%pathname%"
            )

    return changes


def process_yaml_recipe(recipe_path: Path) -> tuple[bool, list[str]]:
    """Process a YAML recipe file.

    Args:
        recipe_path: Path to the recipe file

    Returns:
        Tuple of (modified: bool, changes: list)
    """
    try:
        import yaml

        with open(recipe_path, 'r', encoding='utf-8') as f:
            recipe_data = yaml.safe_load(f)

        changes = []
        if recipe_data and 'Process' in recipe_data:
            changes = _update_yaml_processors(
                recipe_data.get('Process', [])
            )

        if changes:
            # Write back to file
            with open(recipe_path, 'w', encoding='utf-8') as f:
                yaml.dump(recipe_data, f,
                          default_flow_style=False,
                          allow_unicode=True,
                          sort_keys=False,
                          width=70)

        return bool(changes), changes

    except ImportError:
        print(f"Error: PyYAML not available for processing {recipe_path}")
        return False, []
    except Exception as e:
        print(f"Error processing {recipe_path}: {e}")
        traceback.print_exc()
        return False, []


def process_recipe(recipe_path: Path) -> tuple[bool, list[str]]:
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


def _process_recipes(
    recipe_dir: str,
) -> tuple[int, list[tuple[Path, list[str]]]]:
    """Update ChecksumVerifier processors in each recipe under recipe_dir.

    Args:
        recipe_dir: Path to the recipe directory

    Returns:
        Tuple of (recipe_count, modified_files) where modified_files is a
        list of (recipe_path, changes) tuples
    """
    recipe_count = 0
    modified_files = []

    # Process all recipe files
    for recipe_path in Path(recipe_dir).rglob("*.recipe*"):
        if recipe_path.suffix not in ['.recipe', '.yaml']:
            continue

        recipe_count += 1

        modified, changes = process_recipe(recipe_path)

        if modified:
            modified_files.append((recipe_path, changes))
            print(f"\n✓ Updated {recipe_path.name}")
            for change in changes:
                print(f"  - {change}")
        else:
            print(
                f"Skipping {recipe_path.name} - ChecksumVerifier "
                f"already has checksum_pathname"
            )

    return recipe_count, modified_files


def main() -> None:
    """Prompt for a recipe directory and update its ChecksumVerifiers."""
    verify_environment()

    print("ChecksumVerifierChanger - Update ChecksumVerifier Arguments")
    print("=" * 50)
    print("This script will:")
    print("1. Find ChecksumVerifier processors")
    print("2. Rename 'pathname' to 'checksum_pathname' if present")
    print("3. Add 'checksum_pathname' with value '%pathname%' if missing")
    print("4. Preserve all other processor configuration")
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
        modified_count = len(modified_files)

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

            print(
                "\nPlease verify these files in your version control "
                "system."
            )
        else:
            print(
                "\n✓ All ChecksumVerifier processors already have "
                "checksum_pathname!"
            )

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

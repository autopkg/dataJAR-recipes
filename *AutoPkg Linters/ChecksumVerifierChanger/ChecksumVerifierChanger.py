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


# Constants
DICT_TAG = '<dict>'
DICT_CLOSE_TAG = '</dict>'
PATHNAME_KEY = '<key>pathname</key>'
CHECKSUM_PATHNAME_KEY = '<key>checksum_pathname</key>'


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


def has_checksum_verifier_needing_update(content):
    """Check if recipe has ChecksumVerifier processor needing updates.

    Args:
        content: String content of the recipe

    Returns:
        Boolean indicating if changes are needed
    """
    # Look for ChecksumVerifier processor
    if 'ChecksumVerifier</string>' not in content:
        return False

    # Look for pathname key (but not checksum_pathname) OR missing
    # checksum_pathname. Need to check it's within a ChecksumVerifier
    # processor's Arguments
    checksum_verifier_pattern = (
        r'<key>Processor</key>\s*<string>[^<]*'
        r'ChecksumVerifier</string>'
    )
    matches = list(re.finditer(checksum_verifier_pattern, content))

    if not matches:
        return False

    # For each ChecksumVerifier, check if it needs updates
    for match in matches:
        # Find the start of this processor dict
        processor_pos = match.start()

        # Search backwards to find the opening <dict> for this processor
        dict_start = content.rfind(DICT_TAG, 0, processor_pos)
        if dict_start == -1:
            continue

        # Find the matching closing </dict> using depth counting
        depth = 1
        search_pos = dict_start + 6

        while depth > 0 and search_pos < len(content):
            if content[search_pos:search_pos+6] == DICT_TAG:
                depth += 1
                search_pos += 6
            elif content[search_pos:search_pos+7] == DICT_CLOSE_TAG:
                depth -= 1
                if depth == 0:
                    break
                search_pos += 7
            else:
                search_pos += 1

        if depth == 0:
            processor_dict = content[dict_start:search_pos+7]

            # Check if processor dict has pathname (needs rename)
            if (PATHNAME_KEY in processor_dict and
                    CHECKSUM_PATHNAME_KEY not in processor_dict):
                return True

            # Check if processor dict missing checksum_pathname
            if CHECKSUM_PATHNAME_KEY not in processor_dict:
                return True

    return False


def update_checksum_verifier_arguments(content):
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

    if not matches:
        return content, 0, 0

    # Process matches in reverse order to maintain positions
    for match in reversed(matches):
        # Find the start of this processor dict
        processor_pos = match.start()

        # Search backwards to find the opening <dict> for processor
        dict_start = content.rfind(DICT_TAG, 0, processor_pos)
        if dict_start == -1:
            continue

        # Find the matching closing </dict> using depth counting
        depth = 1
        search_pos = dict_start + 6

        while depth > 0 and search_pos < len(content):
            if content[search_pos:search_pos+6] == DICT_TAG:
                depth += 1
                search_pos += 6
            elif content[search_pos:search_pos+7] == DICT_CLOSE_TAG:
                depth -= 1
                if depth == 0:
                    break
                search_pos += 7
            else:
                search_pos += 1

        if depth == 0:
            processor_dict = content[dict_start:search_pos+7]
            updated_dict = processor_dict

            # Case 1: Has pathname, needs to be renamed
            if (PATHNAME_KEY in processor_dict and
                    CHECKSUM_PATHNAME_KEY not in processor_dict):
                updated_dict = updated_dict.replace(
                    PATHNAME_KEY, CHECKSUM_PATHNAME_KEY
                )
                rename_count += 1

            # Case 2: Missing checksum_pathname entirely, add it
            elif CHECKSUM_PATHNAME_KEY not in processor_dict:
                # Find the Arguments dict within this processor
                args_match = re.search(
                    r'<key>Arguments</key>\s*\n\s*<dict>(.*?)\n'
                    r'(\s*)</dict>',
                    updated_dict, re.DOTALL
                )

                if args_match:
                    args_content = args_match.group(1)
                    # Capture the indent before </dict>
                    closing_indent = args_match.group(2)
                    args_start = args_match.start(1)

                    # Detect indentation from existing content
                    # Look for last key in Arguments dict to match
                    # indentation
                    last_key_match = None
                    for key_match in re.finditer(
                            r'\n(\s*)<key>[^<]+</key>', args_content):
                        last_key_match = key_match

                    if last_key_match:
                        indent = last_key_match.group(1)
                    else:
                        # Fallback: Use closing_indent + one level
                        if '\t' in closing_indent:
                            indent = closing_indent + '\t'
                        else:
                            # Assume 4 spaces per indent level
                            indent = closing_indent + '    '

                    # Add checksum_pathname at end of Arguments dict
                    new_key = (
                        f'\n{indent}<key>checksum_pathname</key>\n'
                        f'{indent}<string>%pathname%</string>'
                    )

                    # Trim trailing whitespace from args_content
                    trimmed_args = args_content.rstrip('\n\t ')

                    # Build the new args content with proper spacing
                    new_args_content = trimmed_args + new_key

                    # Replace Arguments content in updated_dict
                    updated_dict = (
                        updated_dict[:args_start] +
                        new_args_content + '\n' +
                        closing_indent + DICT_CLOSE_TAG +
                        updated_dict[args_match.end():]
                    )
                    added_count += 1

            # Replace in content if changed
            if updated_dict != processor_dict:
                content = (
                    content[:dict_start] + updated_dict +
                    content[search_pos+7:]
                )

    return content, rename_count, added_count


def process_plist_recipe(recipe_path):
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

        # Check if changes are needed
        if not has_checksum_verifier_needing_update(original_content):
            return False, []

        # Update the ChecksumVerifier processors
        modified_content, rename_count, added_count = (
            update_checksum_verifier_arguments(original_content)
        )

        if rename_count == 0 and added_count == 0:
            return False, []

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

        return True, changes

    except Exception as e:
        print(f"Error processing {recipe_path}: {e}")
        traceback.print_exc()
        return False, []


def process_yaml_recipe(recipe_path):
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

        if not recipe_data or 'Process' not in recipe_data:
            return False, []

        changes = []
        modified = False

        # Check each processor in the Process array
        for processor in recipe_data.get('Process', []):
            if not isinstance(processor, dict):
                continue

            processor_name = processor.get('Processor', '')

            # Check if this is a ChecksumVerifier processor
            if 'ChecksumVerifier' in processor_name:
                arguments = processor.get('Arguments', {})

                # Case 1: Has pathname, needs to be renamed
                if ('pathname' in arguments and
                        'checksum_pathname' not in arguments):
                    arguments['checksum_pathname'] = (
                        arguments.pop('pathname')
                    )
                    modified = True
                    changes.append(
                        "Renamed pathname → checksum_pathname"
                    )

                # Case 2: Missing checksum_pathname entirely, add it
                elif 'checksum_pathname' not in arguments:
                    arguments['checksum_pathname'] = '%pathname%'
                    modified = True
                    changes.append(
                        "Added checksum_pathname with default value "
                        "%pathname%"
                    )

        if modified:
            # Write back to file
            with open(recipe_path, 'w', encoding='utf-8') as f:
                yaml.dump(recipe_data, f,
                          default_flow_style=False,
                          allow_unicode=True,
                          sort_keys=False,
                          width=70)

        return modified, changes

    except ImportError:
        print(f"Error: PyYAML not available for processing {recipe_path}")
        return False, []
    except Exception as e:
        print(f"Error processing {recipe_path}: {e}")
        traceback.print_exc()
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
                print(f"\n✓ Updated {recipe_path.name}")
                for change in changes:
                    print(f"  - {change}")
            else:
                print(
                    f"Skipping {recipe_path.name} - no changes needed"
                )

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

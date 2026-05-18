#!/usr/local/autopkg/python
"""
Script to check and add PathDeleter processor to Munki recipes.
Ensures PathDeleter exists with correct destination_path values from
unpacking processors (FlatPkgUnpacker, PkgPayloadUnpacker, Unarchiver).
Ensures PathDeleter is the last processor in the Process array.
Supports both plist and YAML recipe formats.
Requires AutoPkg's Python installation.
Preserves exact file formatting using text manipulation.
"""

import os
import sys
from pathlib import Path
import re
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


def get_unpack_processors():
    """Get list of processor names that unpack files."""
    return ['FlatPkgUnpacker', 'PkgPayloadUnpacker', 'Unarchiver']


def normalize_path(path):
    """Normalize a path for comparison.

    Args:
        path: Path string

    Returns:
        Normalized path with trailing slash
    """
    # Always end with / for directory comparison
    if not path.endswith('/'):
        path = path + '/'
    return path


def is_redundant_path(path, existing_paths):
    """Check if a path is redundant given existing paths.

    A path is redundant if:
    1. It's identical to an existing path (after normalization)
    2. It's a child of an existing path (will be deleted with parent)

    Args:
        path: Path to check
        existing_paths: List of existing paths

    Returns:
        True if path is redundant
    """
    path_norm = normalize_path(path)

    for existing in existing_paths:
        existing_norm = normalize_path(existing)

        # Same path (after normalization)
        if path_norm == existing_norm:
            return True

        # Child of existing path
        if path_norm.startswith(existing_norm):
            return True

    return False


def extract_destination_paths_plist(content):
    """Extract destination_path values from unpacking processors in plist.

    Args:
        content: Recipe file content as string

    Returns:
        List of destination paths
    """
    unpack_processors = get_unpack_processors()
    destination_paths = []

    # Find all processor blocks
    processor_pattern = (
        r'<dict>\s*\n'
        r'\s*<key>Processor</key>\s*\n'
        r'\s*<string>(' + '|'.join(unpack_processors) + r')</string>'
        r'.*?'
        r'</dict>'
    )

    for match in re.finditer(processor_pattern, content, re.DOTALL):
        processor_block = match.group(0)

        # Look for destination_path in Arguments
        dest_pattern = (
            r'<key>destination_path</key>\s*\n'
            r'\s*<string>(.*?)</string>'
        )
        dest_match = re.search(dest_pattern, processor_block)

        if dest_match:
            dest_path = dest_match.group(1)
            # Skip %pkgroot% paths - they don't need cleanup
            if (dest_path and
                    not dest_path.startswith('%pkgroot%') and
                    dest_path not in destination_paths):
                destination_paths.append(dest_path)

    return destination_paths


def extract_path_deleter_paths_plist(content):
    """Extract existing paths from PathDeleter in plist.

    Args:
        content: Recipe file content as string

    Returns:
        List of existing paths, or None if PathDeleter doesn't exist
    """
    # Find PathDeleter processor - handle any key order
    # Look for a dict containing PathDeleter as Processor value
    pd_pattern = (
        r'<dict>.*?<key>Processor</key>\s*\n\s*'
        r'<string>PathDeleter</string>.*?</dict>'
    )

    pd_match = re.search(pd_pattern, content, re.DOTALL)

    if not pd_match:
        return None

    pd_block = pd_match.group(0)
    paths = []

    # Extract all string values in path_list array
    path_pattern = r'<key>path_list</key>\s*\n\s*<array>(.*?)</array>'
    array_match = re.search(path_pattern, pd_block, re.DOTALL)

    if array_match:
        array_content = array_match.group(1)
        string_pattern = r'<string>(.*?)</string>'
        for string_match in re.finditer(string_pattern, array_content):
            paths.append(string_match.group(1))

    return paths


def update_path_deleter_plist(content, new_paths, existing_paths):
    """Update PathDeleter processor in plist content.

    Args:
        content: Recipe file content
        new_paths: List of new paths to add
        existing_paths: List of existing paths in PathDeleter

    Returns:
        Tuple of (updated_content, was_modified)
    """
    if not new_paths:
        return content, False

    # Filter out redundant paths
    paths_to_add = [
        p for p in new_paths
        if not is_redundant_path(p, existing_paths)
    ]

    if not paths_to_add:
        return content, False

    # Find PathDeleter block - handle any key order
    # Look for dict with PathDeleter processor and path_list
    pd_pattern = (
        r'<dict>.*?<key>Processor</key>\s*\n\s*'
        r'<string>PathDeleter</string>.*?'
        r'<key>path_list</key>\s*\n\s*<array>(.*?)</array>.*?</dict>'
    )

    pd_match = re.search(pd_pattern, content, re.DOTALL)

    if not pd_match:
        print("ERROR: PathDeleter found but couldn't parse path_list")
        return content, False

    # Get the indentation from existing strings in the array
    array_content = pd_match.group(1)
    indent_match = re.search(r'\n(\s*)<string>', array_content)

    if indent_match:
        indent = indent_match.group(1)
    else:
        # Fallback: guess indent from existing content
        # Find any indented line in the PathDeleter block
        block_indent_match = re.search(r'\n(\s+)<key>', pd_match.group(0))
        if block_indent_match:
            base_indent = block_indent_match.group(1)
            indent = base_indent + '    '
        else:
            indent = '                    '  # Default fallback

    # Build new string entries
    new_entries = []
    for path in paths_to_add:
        new_entries.append(f'\n{indent}<string>{path}</string>')

    # Find the </array> closing tag for path_list
    array_close_pattern = (
        r'(<key>path_list</key>\s*\n\s*<array>.*?)(</array>)'
    )

    def replace_array(match):
        indent_parent = indent.rsplit('    ', 1)[0]
        return (
            match.group(1) + ''.join(new_entries) + '\n' +
            indent_parent + match.group(2)
        )

    content = re.sub(
        array_close_pattern, replace_array, content,
        count=1, flags=re.DOTALL
    )
    return content, True


def add_path_deleter_plist(content, paths):
    """Add PathDeleter processor to plist content.

    Args:
        content: Recipe file content
        paths: List of paths for PathDeleter

    Returns:
        Tuple of (updated_content, was_modified)
    """
    # Find the end of the Process array (before </array>)
    # We want to add before the final </array> in the Process
    process_pattern = r'<key>Process</key>\s*\n\s*<array>(.*)</array>'
    process_match = re.search(process_pattern, content, re.DOTALL)

    if not process_match:
        print("ERROR: Could not find Process array")
        return content, False

    process_content = process_match.group(1)

    # Find last processor dict to get indentation
    last_dict_pattern = r'\n(\s*)<dict>.*?</dict>(?=\s*\n\s*</array>)'
    last_dict_match = None
    for match in re.finditer(last_dict_pattern, process_content, re.DOTALL):
        last_dict_match = match

    if last_dict_match:
        indent = last_dict_match.group(1)
    else:
        # Fallback indent (spaces, not tabs)
        indent = '        '

    # Indentation unit (4 spaces per level)
    indent_unit = '    '

    # Build PathDeleter processor using spaces for sub-indents
    path_entries = []
    for path in paths:
        entry = (
            f'{indent}{indent_unit}{indent_unit}{indent_unit}'
            f'<string>{path}</string>'
        )
        path_entries.append(entry)

    path_deleter = (
        f'{indent}<dict>'
        f'\n{indent}{indent_unit}<key>Processor</key>'
        f'\n{indent}{indent_unit}<string>PathDeleter</string>'
        f'\n{indent}{indent_unit}<key>Arguments</key>'
        f'\n{indent}{indent_unit}<dict>'
        f'\n{indent}{indent_unit}{indent_unit}<key>path_list</key>'
        f'\n{indent}{indent_unit}{indent_unit}<array>'
    )

    path_deleter += '\n' + '\n'.join(path_entries)

    path_deleter += (
        f'\n{indent}{indent_unit}{indent_unit}</array>'
        f'\n{indent}{indent_unit}</dict>'
        f'\n{indent}</dict>'
    )

    # Find where to insert (before final </array> of Process)
    # We want to insert right before the closing </array>
    # Look for the last </dict> before the final </array>
    final_dict_pattern = (
        r'(</dict>)'
        r'(\s*\n\s*</array>\s*\n\s*</dict>\s*\n\s*</plist>)'
    )
    final_dict_match = re.search(
        final_dict_pattern, content, re.DOTALL
    )

    if final_dict_match:
        # Insert after the last processor's </dict>
        insert_pos = final_dict_match.end(1)
        content = (
            content[:insert_pos] + '\n' +
            path_deleter + content[insert_pos:]
        )
        return content, True

    return content, False


def _is_munki_recipe(recipe_path, content):
    """Check if recipe is a munki recipe.

    Args:
        recipe_path: Path to recipe file
        content: Recipe file content

    Returns:
        Boolean indicating if this is a munki recipe
    """
    # Check filename
    is_munki_file = (
        recipe_path.name.endswith('.munki.recipe') or
        recipe_path.name.endswith('.munki.yaml')
    )
    if not is_munki_file:
        return False

    # Check identifier
    identifier_match = re.search(
        r'<key>Identifier</key>\s*\n\s*<string>(.*?)</string>',
        content
    )
    if (not identifier_match or
            '.munki' not in identifier_match.group(1).lower()):
        return False

    # Skip deprecated recipes
    if 'DeprecationWarning' in content:
        return False

    return True


def _add_path_deleter_and_log(content, destination_paths, changes):
    """Add PathDeleter and log changes.

    Args:
        content: Recipe content
        destination_paths: List of paths to add
        changes: List to append changes to

    Returns:
        Tuple of (modified_content, was_modified)
    """
    modified_content, was_modified = \
        add_path_deleter_plist(content, destination_paths)

    if was_modified:
        changes.append(
            f"Added PathDeleter with "
            f"{len(destination_paths)} path(s)"
        )
        for path in destination_paths:
            changes.append(f"  - {path}")

    return modified_content, was_modified


def _update_path_deleter_and_log(
    content, destination_paths, existing_paths, changes
):
    """Update PathDeleter and log changes.

    Args:
        content: Recipe content
        destination_paths: List of destination paths
        existing_paths: List of existing paths
        changes: List to append changes to

    Returns:
        Tuple of (modified_content, was_modified)
    """
    modified_content, was_modified = \
        update_path_deleter_plist(
            content, destination_paths, existing_paths
        )

    if was_modified:
        paths_to_add = [
            p for p in destination_paths
            if not is_redundant_path(p, existing_paths)
        ]
        changes.append(
            f"Added {len(paths_to_add)} missing path(s) "
            f"to PathDeleter"
        )
        for path in paths_to_add:
            changes.append(f"  - {path}")

    return modified_content, was_modified


def process_plist_recipe(recipe_path):
    """Process a plist recipe file and check/add PathDeleter.

    Args:
        recipe_path: Path to the recipe file

    Returns:
        Tuple of (modified: bool, changes: list)
    """
    try:
        # Read original content
        with open(recipe_path, 'r', encoding='utf-8') as f:
            content = f.read()

        changes = []

        # Check if this is a munki recipe
        if not _is_munki_recipe(recipe_path, content):
            return False, []

        # Extract destination paths from unpacking processors
        destination_paths = extract_destination_paths_plist(content)

        if not destination_paths:
            return False, []

        # Check if PathDeleter exists
        existing_paths = extract_path_deleter_paths_plist(content)

        if existing_paths is None:
            # PathDeleter doesn't exist, add it
            modified_content, was_modified = \
                _add_path_deleter_and_log(
                    content, destination_paths, changes
                )
        else:
            # PathDeleter exists, check if we need to add paths
            modified_content, was_modified = \
                _update_path_deleter_and_log(
                    content, destination_paths, existing_paths, changes
                )

        if was_modified:
            # Write changes
            with open(recipe_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)

        return was_modified, changes

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
        print(
            f"Skipping YAML recipe {recipe_path.name} - "
            f"not yet supported"
        )
        return False, []
    else:
        return process_plist_recipe(recipe_path)


def _process_recipe_file(recipe_path):
    """Process a single recipe file and check if it's munki.

    Args:
        recipe_path: Path to recipe file

    Returns:
        Tuple of (is_munki: bool, modified: bool, changes: list)
    """
    # Quick check if it's a munki recipe
    try:
        with open(recipe_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if '.munki' not in content.lower():
                return False, False, []
    except Exception:
        return False, False, []

    modified, changes = process_recipe(recipe_path)
    return True, modified, changes


def _print_summary(
    recipe_count, skipped_non_munki, modified_count, skipped_no_unpack
):
    """Print processing summary.

    Args:
        recipe_count: Total recipes scanned
        skipped_non_munki: Number skipped (non-munki)
        modified_count: Number modified
        skipped_no_unpack: Number without unpacking
    """
    print(f"\n{'=' * 50}")
    print("Processing complete!")
    print(f"Recipes scanned: {recipe_count}")
    print(f"Munki recipes checked: {recipe_count - skipped_non_munki}")
    print(f"Recipes modified: {modified_count}")
    if skipped_no_unpack > 0:
        print(f"Recipes without unpacking: {skipped_no_unpack}")
    print("=" * 50)


def _print_modified_files(modified_files):
    """Print list of modified files with changes.

    Args:
        modified_files: List of (path, changes) tuples
    """
    if modified_files:
        print("\nModified files:")
        for file, changes in modified_files:
            print(f"\n  ✓ {file.name}:")
            for change in changes:
                print(f"    {change}")

        print(
            "\nPlease verify these files in your version control "
            "system."
        )
    else:
        print(
            "\n✓ All munki recipes with unpacking already have "
            "correct PathDeleter!"
        )


def main():
    verify_environment()

    print("MunkiPathDeleterChecker - AutoPkg Recipe Cleanup Validator")
    print("=" * 50)
    print("This script will:")
    print("1. Find unpacking processors (FlatPkgUnpacker, etc.)")
    print("2. Extract their destination_path values")
    print("3. Ensure PathDeleter exists with those paths")
    print("4. Skip redundant child paths")
    print("5. Preserve exact file formatting")
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
            print(f"Error: '{recipe_dir}' is not a valid directory")
            print("Make sure the path exists and you have permission "
                  "to access it.")
            return

        print(f"\nScanning recipes in: {recipe_dir}")

        modified_count = 0
        recipe_count = 0
        modified_files = []
        skipped_no_unpack = 0
        skipped_non_munki = 0

        # Process all recipe files
        for recipe_path in Path(recipe_dir).rglob("*.recipe*"):
            if recipe_path.suffix not in ['.recipe', '.yaml']:
                continue

            recipe_count += 1

            is_munki, modified, changes = _process_recipe_file(recipe_path)

            if not is_munki:
                skipped_non_munki += 1
                continue

            if modified:
                modified_count += 1
                modified_files.append((recipe_path, changes))
                print(f"\n✓ Updated {recipe_path.name}")
                for change in changes:
                    print(f"  {change}")
            elif changes == []:
                skipped_no_unpack += 1
            else:
                print(
                    f"Skipping {recipe_path.name} - "
                    f"PathDeleter already correct"
                )

        _print_summary(
            recipe_count, skipped_non_munki, modified_count,
            skipped_no_unpack
        )
        _print_modified_files(modified_files)

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\nFull traceback:")
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

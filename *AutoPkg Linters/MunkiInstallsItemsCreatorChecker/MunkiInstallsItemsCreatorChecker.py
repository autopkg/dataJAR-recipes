#!/usr/local/autopkg/python
"""
MunkiInstallsItemsCreatorChecker - Script to validate and fix
MunkiInstallsItemsCreator processor configuration.
Ensures:
1. derive_minimum_os_version key exists in Arguments
2. Empty MunkiPkginfoMerger processor immediately follows
3. DERIVE_MIN_OS Input variable exists (alphabetically ordered)
4. Description includes usage instructions
5. MinimumVersion is 2.7 or higher
Supports plist recipe formats.
Requires AutoPkg's Python installation.
Preserves exact file formatting using text manipulation.
"""

import os
import sys
from pathlib import Path
import re
import traceback


# XML tag constants
TAG_DICT_OPEN = '<dict>'
TAG_DICT_CLOSE = '</dict>'
TAG_ARGUMENTS_KEY = '<key>Arguments</key>'


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


def compare_versions(version1, version2):
    """Compare two version strings.

    Args:
        version1: First version string (e.g., "2.7")
        version2: Second version string (e.g., "2.7")

    Returns:
        -1 if version1 < version2, 0 if equal, 1 if version1 > version2
    """
    v1_parts = [int(x) for x in version1.split('.')]
    v2_parts = [int(x) for x in version2.split('.')]

    # Pad with zeros to make same length
    max_len = max(len(v1_parts), len(v2_parts))
    v1_parts += [0] * (max_len - len(v1_parts))
    v2_parts += [0] * (max_len - len(v2_parts))

    for i in range(max_len):
        if v1_parts[i] < v2_parts[i]:
            return -1
        elif v1_parts[i] > v2_parts[i]:
            return 1

    return 0


def _find_matching_dict_end(content, dict_start):
    """Find matching </dict> tag by counting depth.

    Args:
        content: XML content to search
        dict_start: Position of opening <dict> tag

    Returns:
        Position after closing </dict> tag, or -1 if not found
    """
    depth = 1
    search_pos = dict_start + 6

    while search_pos < len(content) and depth > 0:
        next_open = content.find(TAG_DICT_OPEN, search_pos)
        next_close = content.find(TAG_DICT_CLOSE, search_pos)

        if next_close == -1:
            break

        if next_open != -1 and next_open < next_close:
            depth += 1
            search_pos = next_open + 6
        else:
            depth -= 1
            if depth == 0:
                return next_close + 7
            search_pos = next_close + 7

    return -1


def _is_munki_installs_creator(dict_content):
    """Check if dict is MunkiInstallsItemsCreator processor.

    Args:
        dict_content: Dict content to check

    Returns:
        Boolean indicating if this is MunkiInstallsItemsCreator
    """
    return ('<key>Processor</key>' in dict_content and
            '<string>MunkiInstallsItemsCreator</string>'
            in dict_content)


def has_derive_minimum_os_version(content):
    """Check if MunkiInstallsItemsCreator has derive_minimum_os_version.

    Args:
        content: Recipe file content

    Returns:
        Boolean indicating if key exists
    """
    # Find MunkiInstallsItemsCreator processor using proper depth counting
    pos = 0
    while pos < len(content):
        dict_start = content.find(TAG_DICT_OPEN, pos)
        if dict_start == -1:
            break

        # Find matching </dict> by counting depth
        dict_end = _find_matching_dict_end(content, dict_start)

        if dict_end != -1:
            dict_content = content[dict_start:dict_end]

            # Check if this dict is MunkiInstallsItemsCreator
            if _is_munki_installs_creator(dict_content):
                # Check if it has derive_minimum_os_version
                if '<key>derive_minimum_os_version</key>' in dict_content:
                    return True
                # Found the processor but it doesn't have the key
                return False

            pos = dict_end
        else:
            pos = dict_start + 6

    return False


def _find_process_array_content(content):
    """Find and extract Process array content.

    Args:
        content: Recipe content

    Returns:
        Tuple of (process_content, success)
    """
    process_key_pos = content.find('<key>Process</key>')
    if process_key_pos == -1:
        return None, False

    # Find <array> after Process key
    array_start = content.find('<array>', process_key_pos)
    if array_start == -1:
        return None, False

    # Use depth counting to find matching </array>
    depth = 1
    search_pos = array_start + 7  # After '<array>'
    while depth > 0 and search_pos < len(content):
        if content[search_pos:search_pos+7] == '<array>':
            depth += 1
            search_pos += 7
        elif content[search_pos:search_pos+8] == '</array>':
            depth -= 1
            if depth == 0:
                break
            search_pos += 8
        else:
            search_pos += 1

    if depth > 0:
        return None, False

    return content[array_start+7:search_pos], True


def _find_matching_close_for_dict(process_content, dict_pos):
    """Find matching </dict> for dict at given position.

    Args:
        process_content: Content to search
        dict_pos: Position of opening <dict>

    Returns:
        Dict content or None if not found/not matching
    """
    depth = 1
    search_pos = dict_pos + 6

    while depth > 0 and search_pos < len(process_content):
        if process_content[search_pos:search_pos+6] == TAG_DICT_OPEN:
            depth += 1
            search_pos += 6
        elif process_content[search_pos:search_pos+7] == TAG_DICT_CLOSE:
            depth -= 1
            if depth == 0:
                dict_content = process_content[dict_pos:search_pos+7]
                if _is_munki_installs_creator(dict_content):
                    return dict_content
            search_pos += 7
        else:
            search_pos += 1

    return None


def _find_creator_dict_in_process(process_content):
    """Find MunkiInstallsItemsCreator dict in Process array.

    Args:
        process_content: Content of Process array

    Returns:
        Creator dict string or None if not found
    """
    dict_start = 0

    while True:
        dict_pos = process_content.find(TAG_DICT_OPEN, dict_start)
        if dict_pos == -1:
            break

        creator_dict = _find_matching_close_for_dict(
            process_content, dict_pos
        )
        if creator_dict:
            return creator_dict

        # Move past this dict
        dict_start = dict_pos + 6

    return None


def _find_arguments_dict(creator_dict):
    """Find and extract Arguments dict from creator dict.

    Args:
        creator_dict: MunkiInstallsItemsCreator dict content

    Returns:
        Tuple of (args_dict, args_content_start, args_end) or
        (None, None, None)
    """
    args_start = creator_dict.find(TAG_ARGUMENTS_KEY)
    if args_start == -1:
        return None, None, None

    dict_after_args = creator_dict.find(TAG_DICT_OPEN, args_start)
    if dict_after_args == -1:
        return None, None, None

    # Count depth to find matching </dict> for Arguments
    depth = 1
    search_pos = dict_after_args + 6
    args_end = -1

    while depth > 0 and search_pos < len(creator_dict):
        if creator_dict[search_pos:search_pos+6] == TAG_DICT_OPEN:
            depth += 1
            search_pos += 6
        elif creator_dict[search_pos:search_pos+7] == TAG_DICT_CLOSE:
            depth -= 1
            if depth == 0:
                args_end = search_pos + 7
                break
            search_pos += 7
        else:
            search_pos += 1

    if args_end == -1:
        return None, None, None

    args_dict = creator_dict[args_start:args_end]
    args_content_start = dict_after_args + 6

    return args_dict, args_content_start, args_end


def _get_argument_indentation(creator_dict, args_content_start, args_end):
    """Get indentation for Arguments keys.

    Args:
        creator_dict: MunkiInstallsItemsCreator dict content
        args_content_start: Start position of Arguments content
        args_end: End position of Arguments dict

    Returns:
        Tuple of (key_indent, closing_indent)
    """
    args_content = creator_dict[args_content_start:args_end - 7]

    # Get indentation from existing keys
    indent_match = re.search(r'\n(\s+)<key>', args_content)
    if indent_match:
        indent = indent_match.group(1)
    else:
        indent = '                '

    # Get closing dict indentation
    args_start = creator_dict.find(TAG_ARGUMENTS_KEY)
    dict_after_args = creator_dict.find(TAG_DICT_OPEN, args_start)
    args_dict_indent_match = re.search(
        r'\n(\s*)<dict>', creator_dict[args_start:dict_after_args + 6]
    )

    if args_dict_indent_match:
        closing_indent = args_dict_indent_match.group(1)
    else:
        # Fallback: remove one indentation level
        if '\t' in indent:
            closing_indent = indent[:-1] if len(indent) > 0 else ''
        else:
            closing_indent = indent[:-4] if len(indent) >= 4 else ''

    return indent, closing_indent


def add_derive_minimum_os_version(content):
    """Add derive_minimum_os_version to MunkiInstallsItemsCreator Arguments.

    Args:
        content: Recipe file content

    Returns:
        Tuple of (updated_content, was_modified)
    """
    # Find Process array content
    process_content, success = _find_process_array_content(content)
    if not success:
        return content, False

    # Find MunkiInstallsItemsCreator dict
    creator_dict = _find_creator_dict_in_process(process_content)
    if not creator_dict:
        return content, False

    # Find Arguments dict
    args_dict, args_content_start, args_end = _find_arguments_dict(
        creator_dict
    )
    if not args_dict:
        return content, False

    # Get indentation
    indent, closing_indent = _get_argument_indentation(
        creator_dict, args_content_start, args_end
    )

    # Build new Arguments dict
    args_content = creator_dict[args_content_start:args_end - 7]
    new_key = (
        f'\n{indent}<key>derive_minimum_os_version</key>\n'
        f'{indent}<string>%DERIVE_MIN_OS%</string>'
    )

    trimmed_args = args_content.rstrip('\n\t ')
    new_args_dict = (
        creator_dict[
            creator_dict.find(TAG_ARGUMENTS_KEY):args_content_start
        ] +
        new_key +
        trimmed_args +
        '\n' + closing_indent + TAG_DICT_CLOSE
    )

    # Replace dictionaries
    new_creator_dict = creator_dict.replace(args_dict, new_args_dict)
    content = content.replace(creator_dict, new_creator_dict)

    return content, True


def has_pkginfo_merger_after(content):
    """Check if MunkiPkginfoMerger immediately follows
    MunkiInstallsItemsCreator.

    Args:
        content: Recipe file content

    Returns:
        Boolean indicating if merger exists (including those with
        empty Arguments)
    """
    # Find MunkiInstallsItemsCreator and check if next processor
    # is MunkiPkginfoMerger

    installer_pos = content.find(
        '<string>MunkiInstallsItemsCreator</string>'
    )
    if installer_pos == -1:
        return False

    # Find the next processor after MunkiInstallsItemsCreator
    search_start = installer_pos
    next_processor_pos = content.find(
        '<key>Processor</key>', search_start + 50
    )

    if next_processor_pos == -1:
        return False

    # Check if it's MunkiPkginfoMerger within the next 500 characters
    if next_processor_pos - installer_pos < 500:
        next_section = content[next_processor_pos:next_processor_pos + 200]
        if '<string>MunkiPkginfoMerger</string>' in next_section:
            return True

    return False


def add_pkginfo_merger(content):
    """Add empty MunkiPkginfoMerger after MunkiInstallsItemsCreator.

    Args:
        content: Recipe file content

    Returns:
        Tuple of (updated_content, was_modified)
    """
    # Find the end of MunkiInstallsItemsCreator processor
    pattern = (
        r'(<key>Processor</key>\s*\n\s*'
        r'<string>MunkiInstallsItemsCreator</string>.*?'
        r'</dict>)(\s*\n)(\s*)<dict>'
    )

    match = re.search(pattern, content, re.DOTALL)

    if not match:
        return content, False

    indent = match.group(3)
    indent_unit = '    '

    merger = (
        f'{indent}<dict>\n'
        f'{indent}{indent_unit}<key>Processor</key>\n'
        f'{indent}{indent_unit}<string>MunkiPkginfoMerger</string>\n'
        f'{indent}</dict>\n'
    )

    # Insert after MunkiInstallsItemsCreator's </dict>
    insert_pos = match.end(1) + len(match.group(2))
    content = content[:insert_pos] + merger + content[insert_pos:]

    return content, True


def has_derive_min_os_input(content):
    """Check if DERIVE_MIN_OS exists in Input dict with a
    non-empty value.

    Args:
        content: Recipe file content

    Returns:
        Boolean indicating if key exists with a value
    """
    pattern = (
        r'<key>Input</key>.*?<key>DERIVE_MIN_OS</key>\s*\n\s*'
        r'<string>(.+?)</string>.*?</dict>'
    )
    match = re.search(pattern, content, re.DOTALL)
    # Return True only if the key exists AND has a non-empty value
    return match is not None and match.group(1).strip() != ''


def add_derive_min_os_input(content):
    """Add DERIVE_MIN_OS to Input dict in alphabetical order,
    or fix empty value.

    Args:
        content: Recipe file content

    Returns:
        Tuple of (updated_content, was_modified)
    """
    # First check if DERIVE_MIN_OS exists with empty value
    empty_value_pattern = (
        r'(<key>DERIVE_MIN_OS</key>\s*\n\s*<string>)(</string>)'
    )
    empty_match = re.search(empty_value_pattern, content)

    if empty_match:
        # Replace empty string with YES
        content = content.replace(
            empty_match.group(0),
            empty_match.group(1) + 'YES' + empty_match.group(2)
        )
        return content, True

    # Find Input dict
    input_pattern = r'<key>Input</key>\s*\n\s*<dict>(.*?)</dict>'
    input_match = re.search(input_pattern, content, re.DOTALL)

    if not input_match:
        return content, False

    input_content = input_match.group(1)

    # Extract all existing keys in Input
    key_pattern = r'<key>([^<]+)</key>'
    existing_keys = re.findall(key_pattern, input_content)

    # Add DERIVE_MIN_OS and sort
    if 'DERIVE_MIN_OS' not in existing_keys:
        existing_keys.append('DERIVE_MIN_OS')
        existing_keys.sort()
    else:
        return content, False  # Already exists (with non-empty value)

    # Find position to insert (after the key that comes before it
    # alphabetically)
    derive_index = existing_keys.index('DERIVE_MIN_OS')

    # Get indentation from existing keys
    indent_match = re.search(r'\n(\s+)<key>', input_content)
    if indent_match:
        indent = indent_match.group(1)
    else:
        indent = '        '  # Default fallback

    new_entry = (
        f'{indent}<key>DERIVE_MIN_OS</key>\n'
        f'{indent}<string>YES</string>'
    )

    if derive_index == 0:
        # Insert at beginning
        content = content.replace(
            input_match.group(0),
            f'<key>Input</key>\n    <dict>\n'
            f'{new_entry}{input_content}</dict>'
        )
    else:
        # Insert after previous key
        prev_key = existing_keys[derive_index - 1]

        # Find the previous key's value end
        prev_pattern = f'<key>{re.escape(prev_key)}</key>.*?</string>'
        prev_match = re.search(prev_pattern, input_content, re.DOTALL)

        if prev_match:
            # Insert after the previous key's value
            insert_pos = input_match.start(1) + prev_match.end()
            content = (
                content[:insert_pos] + '\n' + new_entry +
                content[insert_pos:]
            )

    return content, True


def has_derive_min_os_description(content):
    """Check if Description includes DERIVE_MIN_OS instructions.

    Args:
        content: Recipe file content

    Returns:
        Boolean indicating if instructions exist
    """
    # Find Description key and its string value
    desc_pattern = r'<key>Description</key>\s*<string>(.*?)</string>'
    desc_match = re.search(desc_pattern, content, re.DOTALL)

    if not desc_match:
        return False

    # Check if the Description string contains DERIVE_MIN_OS
    return 'DERIVE_MIN_OS' in desc_match.group(1)


def add_derive_min_os_description(content):
    """Add DERIVE_MIN_OS instructions to Description.

    Args:
        content: Recipe file content

    Returns:
        Tuple of (updated_content, was_modified)
    """
    instruction = (
        "\n\nSet the DERIVE_MIN_OS variable to a non-empty string "
        "to set the minimum_os_version via "
        "MunkiInstallsItemsCreator."
    )

    # Find Description value
    desc_pattern = (
        r'(<key>Description</key>\s*\n\s*<string>)(.*?)(</string>)'
    )
    desc_match = re.search(desc_pattern, content, re.DOTALL)

    if not desc_match:
        return content, False

    current_desc = desc_match.group(2)
    new_desc = current_desc + instruction

    new_block = desc_match.group(1) + new_desc + desc_match.group(3)
    content = content.replace(desc_match.group(0), new_block)

    return content, True


def get_current_minimum_version(content):
    """Get current MinimumVersion from recipe.

    Args:
        content: Recipe file content

    Returns:
        Version string or None
    """
    pattern = r'<key>MinimumVersion</key>\s*\n\s*<string>(.*?)</string>'
    match = re.search(pattern, content)

    if match:
        return match.group(1)
    return None


def update_minimum_version(content, new_version):
    """Update MinimumVersion in recipe.

    Args:
        content: Recipe file content
        new_version: New version string

    Returns:
        Tuple of (updated_content, was_modified)
    """
    current_version = get_current_minimum_version(content)

    if current_version and compare_versions(current_version, new_version) >= 0:
        return content, False

    if current_version:
        # Update existing - use lambda to avoid backreference issues
        pattern = (
            r'(<key>MinimumVersion</key>\s*\n\s*<string>).*?(</string>)'
        )
        content = re.sub(
            pattern,
            lambda m: m.group(1) + new_version + m.group(2),
            content
        )
        return content, True
    else:
        # Add MinimumVersion before ParentRecipe or Process
        parent_pattern = r'\n(\s*)<key>ParentRecipe</key>'
        parent_match = re.search(parent_pattern, content)

        if parent_match:
            indent = parent_match.group(1)
            insertion = (
                f'{indent}<key>MinimumVersion</key>\n'
                f'{indent}<string>{new_version}</string>\n'
            )
            insert_pos = parent_match.start() + 1
            content = content[:insert_pos] + insertion + content[insert_pos:]
            return content, True

        process_pattern = r'\n(\s*)<key>Process</key>'
        process_match = re.search(process_pattern, content)

        if process_match:
            indent = process_match.group(1)
            insertion = (
                f'{indent}<key>MinimumVersion</key>\n'
                f'{indent}<string>{new_version}</string>\n'
            )
            insert_pos = process_match.start() + 1
            content = content[:insert_pos] + insertion + content[insert_pos:]
            return content, True

    return content, False


def _should_process_recipe(content):
    """Check if recipe should be processed.

    Args:
        content: Recipe content

    Returns:
        Boolean indicating if recipe should be processed
    """
    if 'MunkiInstallsItemsCreator' not in content:
        return False
    if 'DeprecationWarning' in content:
        return False
    return True


def _check_derive_minimum_os(content):
    """Check and add derive_minimum_os_version if needed.

    Returns:
        Tuple of (updated_content, change_message or None)
    """
    has_derive = has_derive_minimum_os_version(content)
    if not has_derive:
        modified_content, was_modified = (
            add_derive_minimum_os_version(content)
        )
        if was_modified:
            return (
                modified_content,
                "Added derive_minimum_os_version to "
                "MunkiInstallsItemsCreator"
            )
    return content, None


def _check_pkginfo_merger(content):
    """Check and add MunkiPkginfoMerger if needed.

    Returns:
        Tuple of (updated_content, change_message or None)
    """
    has_merger = has_pkginfo_merger_after(content)
    if not has_merger:
        modified_content, was_modified = add_pkginfo_merger(content)
        if was_modified:
            return (
                modified_content,
                "Added empty MunkiPkginfoMerger after "
                "MunkiInstallsItemsCreator"
            )
    return content, None


def _check_derive_min_os_input(content):
    """Check and add DERIVE_MIN_OS to Input if needed.

    Returns:
        Tuple of (updated_content, change_message or None)
    """
    has_input = has_derive_min_os_input(content)
    if not has_input:
        modified_content, was_modified = (
            add_derive_min_os_input(content)
        )
        if was_modified:
            return modified_content, "Added DERIVE_MIN_OS to Input dict"
    return content, None


def _check_description(content):
    """Check and add DERIVE_MIN_OS instructions to Description.

    Returns:
        Tuple of (updated_content, change_message or None)
    """
    has_desc = has_derive_min_os_description(content)
    if not has_desc:
        modified_content, was_modified = (
            add_derive_min_os_description(content)
        )
        if was_modified:
            return (
                modified_content,
                "Added DERIVE_MIN_OS instructions to Description"
            )
    return content, None


def _check_minimum_version(content):
    """Check and update MinimumVersion if needed.

    Returns:
        Tuple of (updated_content, change_message or None)
    """
    current_version = get_current_minimum_version(content)
    version_needs_update = (
        not current_version or
        compare_versions(current_version, '2.7') < 0
    )

    if version_needs_update:
        modified_content, was_modified = (
            update_minimum_version(content, '2.7')
        )
        if was_modified:
            old_ver = current_version if current_version else "none"
            return (
                modified_content,
                f"Updated MinimumVersion from {old_ver} to 2.7"
            )
    return content, None


def _perform_checks_and_updates(content):
    """Perform all 5 checks and update content as needed.

    Args:
        content: Recipe content

    Returns:
        Tuple of (modified_content, changes_list)
    """
    changes = []
    modified_content = content

    # Check 1: derive_minimum_os_version key
    modified_content, change = _check_derive_minimum_os(modified_content)
    if change:
        changes.append(change)

    # Check 2: MunkiPkginfoMerger immediately after
    modified_content, change = _check_pkginfo_merger(modified_content)
    if change:
        changes.append(change)

    # Check 3: DERIVE_MIN_OS in Input
    modified_content, change = _check_derive_min_os_input(modified_content)
    if change:
        changes.append(change)

    # Check 4: Description includes instructions
    modified_content, change = _check_description(modified_content)
    if change:
        changes.append(change)

    # Check 5: MinimumVersion is 2.7 or higher
    modified_content, change = _check_minimum_version(modified_content)
    if change:
        changes.append(change)

    return modified_content, changes


def process_plist_recipe(recipe_path):
    """Process a plist recipe file and validate MunkiInstallsItemsCreator.

    Args:
        recipe_path: Path to the recipe file

    Returns:
        Tuple of (modified: bool, changes: list)
    """
    try:
        # Read original content
        with open(recipe_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if recipe should be processed
        if not _should_process_recipe(content):
            return False, []

        # Perform checks and updates
        modified_content, changes = _perform_checks_and_updates(content)

        # Write changes if any
        if changes:
            with open(recipe_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)

        return len(changes) > 0, changes

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
        print(f"Skipping YAML recipe {recipe_path.name} - not yet supported")
        return False, []
    else:
        return process_plist_recipe(recipe_path)


def _print_banner():
    """Print introductory banner."""
    print(
        "MunkiInstallsItemsCreatorChecker - Recipe Configuration "
        "Validator"
    )
    print("=" * 50)
    print("This script will:")
    print("1. Find MunkiInstallsItemsCreator processors")
    print("2. Add derive_minimum_os_version key if missing")
    print("3. Add empty MunkiPkginfoMerger after if missing")
    print("4. Add DERIVE_MIN_OS to Input dict (alphabetically)")
    print("5. Add usage instructions to Description")
    print("6. Update MinimumVersion to 2.7 if needed")
    print("7. Preserve exact file formatting")
    print("=" * 50)


def _get_recipe_directory():
    """Get and validate recipe directory from user input.

    Returns:
        Directory path or None if invalid
    """
    print("\nEnter the path to your recipe directory")
    print(
        "(You can drag and drop the folder here): ", end='', flush=True
    )
    recipe_dir = clean_path(input())
    recipe_dir = os.path.abspath(recipe_dir)

    if not os.path.isdir(recipe_dir):
        print(f"Error: '{recipe_dir}' is not a valid directory")
        print(
            "Make sure the path exists and you have permission "
            "to access it."
        )
        return None

    return recipe_dir


def _process_all_recipes(recipe_dir):
    """Process all recipes in directory.

    Args:
        recipe_dir: Directory containing recipes

    Returns:
        Tuple of (recipe_count, modified_count, modified_files)
    """
    print(f"\nScanning recipes in: {recipe_dir}")

    modified_count = 0
    recipe_count = 0
    modified_files = []

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
        elif changes == []:
            # Recipe was processed but doesn't have creator
            pass
        else:
            print(
                f"Skipping {recipe_path.name} - "
                f"already configured correctly"
            )

    return recipe_count, modified_count, modified_files


def _print_summary(recipe_count, modified_count, modified_files):
    """Print processing summary.

    Args:
        recipe_count: Total recipes scanned
        modified_count: Count of modified recipes
        modified_files: List of (path, changes) tuples
    """
    print(f"\n{'=' * 50}")
    print("Processing complete!")
    print(f"Recipes scanned: {recipe_count}")
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
            "\n✓ All recipes with MunkiInstallsItemsCreator are "
            "already configured correctly!"
        )


def main():
    verify_environment()

    _print_banner()

    try:
        recipe_dir = _get_recipe_directory()
        if not recipe_dir:
            return

        recipe_count, modified_count, modified_files = (
            _process_all_recipes(recipe_dir)
        )

        _print_summary(recipe_count, modified_count, modified_files)

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

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


def verify_environment():
    """Verify we're running in AutoPkg's Python environment."""
    autopkg_python = '/usr/local/autopkg/python'
    if not sys.executable.startswith('/usr/local/autopkg'):
        print(
            "Error: This script should be run using AutoPkg's Python "
            "installation."
        )
        print(
            f"Please run this script using: {autopkg_python} "
            f"<script_name.py>"
        )
        sys.exit(1)


def clean_path(path):
    """Clean up path from drag and drop or manual entry."""
    path = path.strip().strip('"').strip("'")
    path = path.replace(r'\ ', ' ')
    path = path.rstrip(' ').rstrip('/')
    path = os.path.expanduser(path)
    return path


def compare_version(version_str, minimum):
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


def ask_add_stop_processing(warning_message=None):
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


def modify_yaml_recipe(content, recipe_path):
    """Modify yaml recipe content while preserving formatting."""
    print("DEBUG: Processing YAML recipe")
    recipe = yaml.safe_load(content)
    modified = False

    # Check MinimumVersion
    current_version = recipe.get('MinimumVersion', '0.0')
    if not compare_version(current_version, 1.1):
        print(f"DEBUG: Updating MinimumVersion from {current_version} to 1.1")
        recipe['MinimumVersion'] = '1.1'
        modified = True

    if 'Process' in recipe and recipe['Process']:
        # Find DeprecationWarning processor
        deprecation_index = None
        stop_processing_index = None

        for i, process_step in enumerate(recipe['Process']):
            if process_step.get('Processor') == 'DeprecationWarning':
                deprecation_index = i
            elif process_step.get('Processor') == 'StopProcessingIf':
                # Check if it's the TRUEPREDICATE version
                # after DeprecationWarning
                if (deprecation_index is not None and
                        i == deprecation_index + 1 and
                        process_step.get(
                            'Arguments', {}
                        ).get('predicate') == 'TRUEPREDICATE'):
                    stop_processing_index = i

        if deprecation_index is not None:
            print(
                f"DEBUG: Found DeprecationWarning at index "
                f"{deprecation_index}"
            )

            # Check if DeprecationWarning is not at the top
            if deprecation_index != 0:
                print(
                    "DEBUG: Moving DeprecationWarning to top of "
                    "Process array"
                )
                deprecation_step = recipe['Process'].pop(deprecation_index)
                recipe['Process'].insert(0, deprecation_step)
                modified = True
                deprecation_index = 0

                # Adjust stop_processing_index if it existed
                if stop_processing_index is not None:
                    stop_processing_index = None  # Will be rechecked

            # Check for StopProcessingIf after DeprecationWarning
            if len(recipe['Process']) > deprecation_index + 1:
                next_step = recipe['Process'][deprecation_index + 1]
                if (next_step.get('Processor') == 'StopProcessingIf' and
                        next_step.get('Arguments', {}).get('predicate') ==
                        'TRUEPREDICATE'):
                    stop_processing_index = deprecation_index + 1

            if stop_processing_index is None:
                print(f"\nRecipe: {recipe_path.name}")
                if ask_add_stop_processing():
                    stop_processing_step = {
                        'Processor': 'StopProcessingIf',
                        'Arguments': {
                            'predicate': 'TRUEPREDICATE'
                        }
                    }
                    # Find DeprecationWarning again
                    # (it should be at index 0 now)
                    for i, step in enumerate(recipe['Process']):
                        if step.get('Processor') == 'DeprecationWarning':
                            recipe['Process'].insert(
                                i + 1, stop_processing_step
                            )
                            modified = True
                            break

    if modified:
        # Convert back to YAML with proper formatting
        output = yaml.dump(
            recipe, default_flow_style=False, sort_keys=False, indent=4
        )
        return output, True

    return content, False


def get_indent_level(line):
    """Get the indentation level (number of spaces) for a line."""
    return len(line) - len(line.lstrip())


def modify_plist_content(content, recipe_path):
    """Modify the plist recipe content while preserving formatting."""
    DICT_TAG = '<dict>'
    modified = False

    print("DEBUG: Starting plist content modification...")

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

    # Find the Process array
    process_pattern = r'(<key>Process</key>\s*\n\s*<array>)(.*?)(</array>)'
    process_match = re.search(process_pattern, content, re.DOTALL)

    if not process_match:
        print("DEBUG: No Process array found")
        return content, False

    process_content = process_match.group(2)

    # Find all processor dicts in the Process array
    # We need to properly match nested dicts by counting depth
    processor_dicts = []
    pos = 0
    while pos < len(process_content):
        dict_start = process_content.find(DICT_TAG, pos)
        if dict_start == -1:
            break

        # Count depth to find matching </dict>
        depth = 1
        search_pos = dict_start + 6  # Start after <dict>
        dict_end = -1

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
                    dict_end = next_close + 7  # Include </dict>
                    break
                search_pos = next_close + 7

        if dict_end != -1:
            dict_content = process_content[dict_start:dict_end]
            # Create a match-like object for compatibility

            class DictMatch:
                def __init__(self, content, start, end):
                    self.content = content
                    self.start_pos = start
                    self.end_pos = end

                def group(self, _):
                    return self.content

            processor_dicts.append(
                DictMatch(dict_content, dict_start, dict_end)
            )
            pos = dict_end
        else:
            pos = dict_start + 6

    if not processor_dicts:
        print("DEBUG: No processors found in Process array")
        return content, False

    # Find DeprecationWarning and StopProcessingIf
    deprecation_dict = None
    deprecation_index = None
    stop_processing_after_deprecation = False

    for i, match in enumerate(processor_dicts):
        dict_content = match.group(1)
        if ('DeprecationWarning' in dict_content and
                '<key>Processor</key>' in dict_content):
            deprecation_dict = dict_content
            deprecation_index = i
            print(f"DEBUG: Found DeprecationWarning at index {i}")

            # Check if next processor is StopProcessingIf with TRUEPREDICATE
            if i + 1 < len(processor_dicts):
                next_dict = processor_dicts[i + 1].group(1)
                if ('StopProcessingIf' in next_dict and
                        'TRUEPREDICATE' in next_dict):
                    stop_processing_after_deprecation = True
                    print(
                        "DEBUG: Found StopProcessingIf after "
                        "DeprecationWarning"
                    )
            break

    if deprecation_dict is None:
        print("DEBUG: No DeprecationWarning processor found")
        return content, False

    # Check if DeprecationWarning needs to be moved to top
    if deprecation_index != 0:
        print("DEBUG: Moving DeprecationWarning to top of Process array")

        # Extract all processor dicts
        all_dicts = [match.group(1) for match in processor_dicts]

        # Move DeprecationWarning to top
        deprecation = all_dicts.pop(deprecation_index)
        all_dicts.insert(0, deprecation)

        # Get base indentation from first dict
        first_dict_match = re.search(r'\n(\s*)<dict>', process_content)
        base_indent = (
            first_dict_match.group(1) if first_dict_match else '        '
        )

        # Rebuild process content
        new_process_content = '\n'
        for dict_content in all_dicts:
            # Ensure proper indentation
            lines = dict_content.split('\n')
            indented_lines = []
            for line in lines:
                if line.strip():
                    # Preserve relative indentation
                    indented_lines.append(base_indent + line.lstrip())
                else:
                    indented_lines.append('')
            new_process_content += '\n'.join(indented_lines) + '\n'

        # Replace the process content
        content = content.replace(
            process_match.group(0),
            f'{process_match.group(1)}{new_process_content}'
            f'{base_indent.rstrip()}    {process_match.group(3)}'
        )
        modified = True
        deprecation_index = 0

    # Check if StopProcessingIf needs to be added
    if not stop_processing_after_deprecation:
        # Extract warning_message from deprecation_dict
        warning_message = None
        warning_match = re.search(
            r'<key>warning_message</key>\s*\n\s*<string>([^<]+)</string>',
            deprecation_dict
        )
        if warning_match:
            warning_message = warning_match.group(1)

        print(f"\nRecipe: {recipe_path.name}")
        if ask_add_stop_processing(warning_message):
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
            process_match = re.search(process_pattern, content, re.DOTALL)
            if process_match:
                process_content = process_match.group(2)

                # Re-find processor dicts using depth counting
                processor_dicts = []
                pos = 0
                while pos < len(process_content):
                    dict_start = process_content.find(DICT_TAG, pos)
                    if dict_start == -1:
                        break

                    # Count depth to find matching </dict>
                    depth = 1
                    search_pos = dict_start + 6
                    dict_end = -1

                    while search_pos < len(process_content) and depth > 0:
                        next_open = process_content.find(DICT_TAG, search_pos)
                        next_close = process_content.find(
                            '</dict>', search_pos
                        )

                        if next_close == -1:
                            break

                        if next_open != -1 and next_open < next_close:
                            depth += 1
                            search_pos = next_open + 6
                        else:
                            depth -= 1
                            if depth == 0:
                                dict_end = next_close + 7
                                break
                            search_pos = next_close + 7

                    if dict_end != -1:
                        dict_content = process_content[dict_start:dict_end]
                        processor_dicts.append(
                            (dict_content, dict_start, dict_end)
                        )
                        pos = dict_end
                    else:
                        pos = dict_start + 6

                if processor_dicts:
                    # Insert after first dict
                    # (DeprecationWarning should be first now)
                    _, _, first_end = processor_dicts[0]
                    insert_pos = process_match.start(2) + first_end

                    content = (
                        content[:insert_pos] + '\n' + stop_processing +
                        content[insert_pos:]
                    )
                    modified = True
                    print("DEBUG: Added StopProcessingIf processor")

    return content, modified


def process_recipe(recipe_path):
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
        if 'DeprecationWarning' not in original_content:
            print(
                f"Skipping {recipe_path} - "
                f"no DeprecationWarning processor found"
            )
            return False

        print(f"\nFound DeprecationWarning in: {recipe_path}")

        if is_yaml:
            modified_content, was_modified = modify_yaml_recipe(
                original_content, recipe_path
            )
        else:
            modified_content, was_modified = modify_plist_content(
                original_content, recipe_path
            )

        if was_modified:
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
            else:
                print(
                    f"✓ Successfully modified and verified: {recipe_path}"
                )
                return True
        else:
            print(f"No modifications needed for: {recipe_path}")
            return False

    except Exception as e:
        print(f"❌ Error processing {recipe_path}: {str(e)}")
        print("DEBUG: Full error details:")
        print(traceback.format_exc())
        return False


def main():
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

#!/usr/local/autopkg/python
"""
Script to update FindAndReplace processor references in recipes.
Converts shared processor references to core processor and updates
MinimumVersion.
As of AutoPkg 2.7.6, FindAndReplace became a core processor.
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


def compare_versions(v1, v2):
    """Compare two version strings.

    Returns:
        1 if v1 > v2
        -1 if v1 < v2
        0 if v1 == v2
    """
    def normalize(v):
        return [int(x) for x in re.sub(r'[^\d.]+', '', v).split('.')]

    try:
        parts1 = normalize(v1)
        parts2 = normalize(v2)

        # Pad shorter version with zeros
        max_len = max(len(parts1), len(parts2))
        parts1.extend([0] * (max_len - len(parts1)))
        parts2.extend([0] * (max_len - len(parts2)))

        for p1, p2 in zip(parts1, parts2):
            if p1 > p2:
                return 1
            elif p1 < p2:
                return -1
        return 0
    except (ValueError, AttributeError):
        return 0


def has_shared_findandreplace(content):
    """Check if content has the shared FindAndReplace processor."""
    patterns = [
        'com.github.homebysix.FindAndReplace/FindAndReplace',
        'com.github.homebysix.FindAndReplace',
    ]
    return any(pattern in content for pattern in patterns)


def modify_yaml_recipe(content):
    """Modify yaml recipe content to use core FindAndReplace."""
    try:
        recipe = yaml.safe_load(content)
    except yaml.YAMLError as e:
        print(f"DEBUG: Error parsing YAML: {e}")
        return content, False

    modified = False

    # Check and update MinimumVersion
    current_version = recipe.get('MinimumVersion', '0.0')
    if compare_versions(current_version, '2.7.6') < 0:
        print(f"DEBUG: Updating MinimumVersion from {current_version} "
              f"to 2.7.6")
        recipe['MinimumVersion'] = '2.7.6'
        modified = True

    # Update FindAndReplace processor references
    if 'Process' in recipe and isinstance(recipe['Process'], list):
        for step in recipe['Process']:
            if isinstance(step, dict) and 'Processor' in step:
                processor = step['Processor']
                if ('com.github.homebysix.FindAndReplace' in processor):
                    print(
                        f"DEBUG: Converting {processor} to "
                        f"FindAndReplace")
                    step['Processor'] = 'FindAndReplace'
                    modified = True

    if modified:
        # Convert back to YAML with proper formatting
        output = yaml.dump(recipe, default_flow_style=False,
                           sort_keys=False, indent=4)
        return output, True

    return content, False


def modify_plist_content(content):
    """Modify plist recipe content to use core FindAndReplace."""
    modified = False

    print("DEBUG: Starting plist content modification...")

    # Check and update MinimumVersion
    min_version_pattern = (r'(<key>MinimumVersion</key>\s*\n\s*)'
                           r'<string>(.*?)</string>')
    min_version_match = re.search(min_version_pattern, content, re.DOTALL)

    if min_version_match:
        current_version = min_version_match.group(2)
        if compare_versions(current_version, '2.7.6') < 0:
            print(f"DEBUG: Updating MinimumVersion from {current_version} "
                  f"to 2.7.6")
            # Replace only the version value, preserving indentation
            old_string = min_version_match.group(0)
            new_string = min_version_match.group(1) + '<string>2.7.6</string>'
            content = content.replace(old_string, new_string)
            modified = True
    else:
        # Add MinimumVersion after opening <dict>
        print("DEBUG: Adding MinimumVersion 2.7.6")
        dict_match = re.search(
            r'(<\?xml.*?>\s*<!DOCTYPE.*?>\s*<plist.*?>\s*<dict>)',
            content, re.DOTALL)
        if dict_match:
            content = content.replace(
                dict_match.group(1),
                dict_match.group(1) +
                '\n    <key>MinimumVersion</key>'
                '\n    <string>2.7.6</string>'
            )
            modified = True

    # Update FindAndReplace processor references
    # Pattern matches:
    # <string>com.github.homebysix.FindAndReplace/FindAndReplace</string>
    # or: <string>com.github.homebysix.FindAndReplace</string>
    patterns = [
        (r'(<key>Processor</key>\s*\n\s*)<string>com\.github\.homebysix\.'
         r'FindAndReplace/FindAndReplace</string>'),
        (r'(<key>Processor</key>\s*\n\s*)<string>com\.github\.homebysix\.'
         r'FindAndReplace</string>'),
    ]

    for pattern in patterns:
        if re.search(pattern, content):
            print(
                "DEBUG: Converting shared FindAndReplace to core "
                "processor")
            content = re.sub(pattern, r'\1<string>FindAndReplace</string>',
                             content)
            modified = True

    return content, modified


def process_recipe(recipe_path):
    """Process a single recipe file and update FindAndReplace references."""
    try:
        is_yaml = recipe_path.suffix == '.yaml'
        print(f"\nDEBUG: Processing {recipe_path}")
        print(f"DEBUG: File type: {'YAML' if is_yaml else 'plist'}")

        # Read original content
        with open(recipe_path, 'r', encoding='utf-8') as file:
            original_content = file.read()
            print(f"DEBUG: Original content length: {len(original_content)}")

        # Check if recipe has shared FindAndReplace
        if not has_shared_findandreplace(original_content):
            print(f"Skipping {recipe_path.name} - no shared FindAndReplace "
                  f"found")
            return False

        print(f"\nFound shared FindAndReplace in: {recipe_path}")

        if is_yaml:
            modified_content, was_modified = modify_yaml_recipe(
                original_content)
        else:
            modified_content, was_modified = modify_plist_content(
                original_content)

        if was_modified:
            print(f"DEBUG: Writing changes to: {recipe_path}")
            with open(recipe_path, 'w', encoding='utf-8') as file:
                file.write(modified_content)

            # Verify the changes were written
            with open(recipe_path, 'r', encoding='utf-8') as file:
                verification_content = file.read()

            if verification_content != modified_content:
                print(f"❌ Warning: File write verification failed for "
                      f"{recipe_path}")
                return False
            else:
                print(f"✓ Successfully modified: {recipe_path}")
                return True
        else:
            print(f"No modifications needed for: {recipe_path.name}")
            return False

    except Exception as e:
        print(f"❌ Error processing {recipe_path}: {str(e)}")
        print("DEBUG: Full error details:")
        print(traceback.format_exc())
        return False


def main():
    verify_environment()

    print("FindAndReplaceChecker - AutoPkg Recipe Updater")
    print("=" * 50)
    print("This script will:")
    print("1. Find recipes using shared FindAndReplace processor")
    print("2. Convert to core FindAndReplace processor")
    print("3. Update MinimumVersion to 2.7.6")
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
            if recipe_path.suffix in ['.recipe', '.yaml']:
                recipe_count += 1
                if process_recipe(recipe_path):
                    modified_count += 1
                    modified_files.append(recipe_path)

        print(f"\n{'=' * 50}")
        print("Processing complete!")
        print(f"Recipes processed: {recipe_count}")
        print(f"Recipes modified: {modified_count}")
        print("=" * 50)

        if modified_files:
            print("\nModified files:")
            for file in modified_files:
                print(f"  ✓ {file}")

            print("\nPlease verify these files in your version control "
                  "system.")

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
        print("DEBUG: Full error details:")
        print(traceback.format_exc())


if __name__ == "__main__":
    main()

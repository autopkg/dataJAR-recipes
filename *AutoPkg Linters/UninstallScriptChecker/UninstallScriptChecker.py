#!/usr/local/autopkg/python
"""
Script to check and fix uninstall_script configuration in AutoPkg recipes.
Ensures recipes with uninstall_script key also have uninstall_method set.
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


def _check_yaml_input(recipe):
    """Check Input section of a parsed YAML recipe.

    Args:
        recipe: Parsed YAML recipe dict

    Returns:
        Tuple of (has_script, has_method, method_correct)
    """
    has_script = False
    has_method = False
    method_correct = False

    input_dict = recipe.get('Input')
    if not isinstance(input_dict, dict):
        return has_script, has_method, method_correct

    if 'uninstall_script' in input_dict:
        has_script = True
        print("DEBUG: Found uninstall_script key")

    if 'uninstall_method' in input_dict:
        has_method = True
        method_value = input_dict['uninstall_method']
        if method_value == 'uninstall_script':
            method_correct = True
            print(
                "DEBUG: uninstall_method is correctly "
                "set to 'uninstall_script'"
            )
        else:
            print(
                f"DEBUG: uninstall_method is set to "
                f"'{method_value}' "
                f"(should be 'uninstall_script')"
            )

    return has_script, has_method, method_correct


def _make_method_line(line):
    """Build an uninstall_method YAML line matching indent.

    Args:
        line: Reference line to match indentation

    Returns:
        Formatted uninstall_method line string
    """
    indent = ' ' * (len(line) - len(line.lstrip()))
    return (
        f"{indent}uninstall_method: "
        "uninstall_script"
    )


def _is_input_boundary(line, in_input):
    """Determine if line is an Input section boundary.

    Args:
        line: Current line text
        in_input: Whether currently inside Input section

    Returns:
        Updated in_input boolean
    """
    if re.match(r'^Input:\s*$', line):
        return True
    if in_input and line and not line[0].isspace():
        return False
    return in_input


def _fix_yaml_lines(content, has_method, method_correct):
    """Fix uninstall_method in YAML content lines.

    Args:
        content: Raw YAML string
        has_method: Whether uninstall_method key exists
        method_correct: Whether existing value is correct

    Returns:
        Tuple of (modified_content, was_modified)
    """
    lines = content.splitlines()
    new_lines = []
    in_input = False
    modified = False

    for line in lines:
        in_input = _is_input_boundary(line, in_input)

        if in_input and 'uninstall_script:' in line:
            if not has_method:
                new_lines.append(
                    _make_method_line(line)
                )
                modified = True
            new_lines.append(line)
            continue

        needs_replace = (
            in_input and has_method
            and not method_correct
            and 'uninstall_method:' in line
        )
        if needs_replace:
            new_lines.append(
                _make_method_line(line)
            )
            modified = True
            continue

        new_lines.append(line)

    if modified:
        return '\n'.join(new_lines) + '\n', True
    return content, False


def check_yaml_recipe(content):
    """Check YAML recipe for uninstall_script and uninstall_method.

    Returns:
        Tuple of (modified_content, was_modified)
    """
    try:
        recipe = yaml.safe_load(content)
    except yaml.YAMLError as e:
        print(f"DEBUG: Error parsing YAML: {e}")
        return content, False

    has_script, has_method, method_correct = (
        _check_yaml_input(recipe)
    )

    if not has_script:
        return content, False

    if has_method and method_correct:
        return content, False

    print("DEBUG: Adding/correcting uninstall_method key")
    return _fix_yaml_lines(
        content, has_method, method_correct
    )


def check_plist_recipe(content):
    """Check plist recipe for uninstall_script and uninstall_method.

    Returns:
        Tuple of (modified_content, was_modified)
    """
    modified = False
    has_uninstall_script = False
    has_uninstall_method = False
    uninstall_method_correct = False

    # Check for uninstall_script key
    if '<key>uninstall_script</key>' in content:
        has_uninstall_script = True
        print("DEBUG: Found uninstall_script key")

    # Check for uninstall_method key and its value
    uninstall_method_pattern = (
        r'<key>uninstall_method</key>\s*\n\s*'
        r'<string>(.*?)</string>'
    )
    method_match = re.search(
        uninstall_method_pattern, content, re.DOTALL
    )

    if method_match:
        has_uninstall_method = True
        method_value = method_match.group(1).strip()
        if method_value == 'uninstall_script':
            uninstall_method_correct = True
            print("DEBUG: uninstall_method is correctly set to "
                  "'uninstall_script'")
        else:
            print(f"DEBUG: uninstall_method is set to '{method_value}' "
                  f"(should be 'uninstall_script')")

    if has_uninstall_script:
        if not has_uninstall_method:
            # Add uninstall_method before uninstall_script
            print("DEBUG: Adding uninstall_method key")

            # Find uninstall_script and get its indentation
            script_pattern = (r'(\s*)<key>uninstall_script</key>')
            script_match = re.search(script_pattern, content)

            if script_match:
                indent = script_match.group(1)
                # Ensure 4 spaces, not tabs
                indent = indent.replace('\t', '    ')

                # Create the uninstall_method key-string pair
                method_lines = (
                    f'{indent}<key>uninstall_method'
                    f'</key>\n'
                    f'{indent}<string>uninstall_script'
                    f'</string>\n'
                )

                # Insert before uninstall_script
                content = content.replace(
                    script_match.group(0),
                    method_lines + script_match.group(0)
                )
                modified = True

        elif not uninstall_method_correct:
            # Fix existing incorrect uninstall_method value
            print("DEBUG: Correcting uninstall_method value")
            content = re.sub(
                uninstall_method_pattern,
                lambda m: m.group(0).replace(
                    m.group(1),
                    'uninstall_script'
                ),
                content
            )
            modified = True

    return content, modified


def process_recipe(recipe_path):
    """Process a single recipe file and check uninstall configuration."""
    try:
        is_yaml = recipe_path.suffix == '.yaml'
        print(f"\nDEBUG: Processing {recipe_path}")
        print(f"DEBUG: File type: {'YAML' if is_yaml else 'plist'}")

        # Read original content
        with open(recipe_path, 'r', encoding='utf-8') as file:
            original_content = file.read()
            print(f"DEBUG: Original content length: {len(original_content)}")

        # Check if recipe has uninstall_script
        if 'uninstall_script' not in original_content:
            print(f"Skipping {recipe_path.name} - no uninstall_script key "
                  f"found")
            return False

        print(f"\nFound uninstall_script in: {recipe_path}")

        # Process based on file type
        if is_yaml:
            modified_content, was_modified = check_yaml_recipe(
                original_content)
        else:
            modified_content, was_modified = check_plist_recipe(
                original_content)

        if not was_modified:
            print(f"No modifications needed for: {recipe_path.name}")
            return False

        # Write the changes
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

        # Verify uninstall_method is now present and correct
        if is_yaml:
            verify_recipe = yaml.safe_load(verification_content)
            if verify_recipe.get('Input', {}).get('uninstall_method') != \
               'uninstall_script':
                print(f"❌ Warning: Verification failed - uninstall_method "
                      f"not correct in {recipe_path}")
                return False
        else:
            if '<key>uninstall_method</key>' not in verification_content:
                print(f"❌ Warning: Verification failed - uninstall_method "
                      f"not found in {recipe_path}")
                return False

        print(f"✓ Successfully configured uninstall_method: {recipe_path}")
        return True

    except Exception as e:
        print(f"❌ Error processing {recipe_path}: {str(e)}")
        print("DEBUG: Full error details:")
        print(traceback.format_exc())
        return False


def main():
    verify_environment()

    print("UninstallScriptChecker - AutoPkg Recipe Uninstall Validator")
    print("=" * 50)
    print("This script will:")
    print("1. Find recipes with uninstall_script key")
    print("2. Ensure uninstall_method key exists")
    print("3. Set uninstall_method to 'uninstall_script'")
    print("4. Use 4 spaces for indentation")
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

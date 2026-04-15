#!/usr/local/autopkg/python
"""
Script to update GitHub download recipes with prerelease handling.
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


def modify_yaml_recipe(content):
    """Modify yaml recipe content while preserving formatting."""
    print("DEBUG: Processing YAML recipe")
    recipe = yaml.safe_load(content)
    modified = False

    if 'Process' in recipe:
        for process_step in recipe['Process']:
            if process_step.get('Processor') == 'GitHubReleasesInfoProvider':
                print(
                    "DEBUG: Found GitHubReleasesInfoProvider processor "
                    "in YAML recipe")
                if 'Arguments' not in process_step:
                    process_step['Arguments'] = {}
                if ('include_prereleases' not in
                        process_step['Arguments']):
                    print("DEBUG: Adding include_prereleases key")
                    process_step['Arguments']['include_prereleases'] = (
                        '%PRERELEASE%')
                    modified = True

    if modified:
        print("DEBUG: YAML recipe was modified")
        if 'Input' not in recipe:
            recipe['Input'] = {}
        if 'PRERELEASE' not in recipe['Input']:
            recipe['Input']['PRERELEASE'] = ''

        lines = content.splitlines()
        for i, line in enumerate(lines):
            if 'Description: |' in line or 'Description:' in line:
                current_desc = line.split('Description:', 1)[1].strip()
                indent = re.match(r'^\s*', line).group()
                desc_indent = indent + '  '

                new_desc = [
                    f"{indent}Description: |",
                    f"{desc_indent}{current_desc}",
                    "",
                    (f"{desc_indent}Set PRERELEASE to a non-empty string "
                     f"to download prereleases, either"),
                    (f"{desc_indent}via Input in an override or via the "
                     f"-k option,"),
                    f"{desc_indent}i.e.: `-k PRERELEASE=yes`"
                ]

                new_lines = lines[:i] + new_desc + lines[i+1:]
                return '\n'.join(new_lines) + '\n', True

    return content, False


def modify_plist_content(content):
    """Modify the plist recipe content while preserving formatting."""
    print("DEBUG: Starting plist content modification...")

    # Update Description
    desc_pattern = (r'(<key>Description</key>\s*\n\s*<string>)'
                    r'(.*?)(</string>)')
    desc_match = re.search(desc_pattern, content, re.DOTALL)
    if desc_match and 'PRERELEASE' not in desc_match.group(2):
        print("DEBUG: Updating Description")
        desc = desc_match.group(2)
        prerelease_text = (
            "\n\nSet PRERELEASE to a non-empty string to download "
            "prereleases, either\n"
            "via Input in an override or via the -k option,\n"
            "i.e.: `-k PRERELEASE=yes`")
        new_desc = desc.rstrip() + prerelease_text
        content = content.replace(
            f'{desc_match.group(1)}{desc}{desc_match.group(3)}',
            f'{desc_match.group(1)}{new_desc}{desc_match.group(3)}'
        )

    # Find and modify GitHubReleasesInfoProvider
    github_pattern = (
        r'(<dict>\s*(?:<key>Arguments</key>\s*<dict>.*?</dict>\s*)?'
        r'<key>Processor</key>\s*\n\s*'
        r'<string>GitHubReleasesInfoProvider</string>.*?</dict>)')
    github_matches = list(re.finditer(github_pattern, content, re.DOTALL))

    if github_matches:
        for match in github_matches:
            processor_content = match.group(1)

            # Get indentation (ensure 4 spaces, not tabs)
            indent_match = re.search(
                r'([ \t]*)<key>Processor</key>', processor_content)
            if indent_match:
                # Convert tabs to 4 spaces
                base_indent = indent_match.group(1).replace('\t', '    ')
                args_indent = base_indent + '    '

                # Check if Arguments exists
                if '<key>Arguments</key>' not in processor_content:
                    # Add Arguments section with include_prereleases
                    args_section = (
                        f'{base_indent}<key>Arguments</key>\n'
                        f'{base_indent}<dict>\n'
                        f'{args_indent}<key>include_prereleases</key>\n'
                        f'{args_indent}<string>%PRERELEASE%</string>\n'
                    )
                    if 'github_repo' in processor_content:
                        # Keep existing github_repo
                        repo_start = processor_content.find(
                            '<key>github_repo</key>')
                        args_section += processor_content[repo_start:]
                    else:
                        args_section += f'{base_indent}</dict>'

                    new_processor = processor_content.replace(
                        f'{base_indent}<key>Processor</key>',
                        f'{args_section}{base_indent}<key>Processor</key>'
                    )
                    content = content.replace(processor_content, new_processor)
                else:
                    # Add include_prereleases to existing Arguments
                    args_pattern = (
                        r'(<key>Arguments</key>\s*\n\s*<dict>)'
                        r'(.*?)(\s*</dict>)')
                    args_match = re.search(
                        args_pattern, processor_content, re.DOTALL)
                    if (args_match and '<key>include_prereleases</key>'
                            not in args_match.group(2)):
                        args_content = args_match.group(2)
                        new_args = (
                            f'{args_content.rstrip()}\n'
                            f'{args_indent}<key>include_prereleases</key>\n'
                            f'{args_indent}<string>%PRERELEASE%</string>'
                        )
                        old_args = (
                            f'{args_match.group(1)}{args_content}'
                            f'{args_match.group(3)}')
                        new_args_full = (
                            f'{args_match.group(1)}{new_args}'
                            f'{args_match.group(3)}')
                        new_processor = processor_content.replace(
                            old_args, new_args_full)
                        content = content.replace(
                            processor_content, new_processor)

    # Add PRERELEASE to Input if needed
    input_pattern = (
        r'(<key>Input</key>\s*\n\s*<dict>)(.*?)(\s*</dict>)')
    input_match = re.search(input_pattern, content, re.DOTALL)

    if input_match:
        if '<key>PRERELEASE</key>' not in input_match.group(2):
            print("DEBUG: Adding PRERELEASE to Input section")
            input_content = input_match.group(2)
            line_for_indent = (input_content.split('\n')[1]
                               if input_content.strip()
                               else input_match.group(1))
            indent = re.search(r'^\s*', line_for_indent).group()
            new_input = (
                f'{input_content.rstrip()}\n'
                f'{indent}<key>PRERELEASE</key>\n'
                f'{indent}<string></string>'
            )
            old_input = (
                f'{input_match.group(1)}{input_content}'
                f'{input_match.group(3)}')
            new_input_full = (
                f'{input_match.group(1)}{new_input}'
                f'{input_match.group(3)}')
            content = content.replace(old_input, new_input_full)
    else:
        print("DEBUG: Creating new Input section")
        # Add Input section if it doesn't exist
        root_dict_pattern = r'(<dict>.*?)(</dict>)'
        root_match = re.search(root_dict_pattern, content, re.DOTALL)
        if root_match:
            indent = '    '
            input_section = (
                f'{indent}<key>Input</key>\n'
                f'{indent}<dict>\n'
                f'{indent}    <key>PRERELEASE</key>\n'
                f'{indent}    <string></string>\n'
                f'{indent}</dict>\n'
            )
            content = content.replace(
                root_match.group(1),
                f'{root_match.group(1)}{input_section}')

    return content


def process_recipe(recipe_path):
    """Process a single recipe file and make necessary modifications."""
    try:
        is_yaml = recipe_path.suffix == '.yaml'
        print(f"\nDEBUG: Processing {recipe_path}")
        print(f"DEBUG: File type: {'YAML' if is_yaml else 'plist'}")

        # Read original content and store it for comparison
        with open(recipe_path, 'r', encoding='utf-8') as file:
            original_content = file.read()
            print(
                f"DEBUG: Original content length: "
                f"{len(original_content)}")

        if is_yaml:
            modified_content, was_modified = modify_yaml_recipe(
                original_content)
        else:
            # Check for GitHubReleasesInfoProvider
            if 'GitHubReleasesInfoProvider' in original_content:
                print(
                    f"\nFound GitHubReleasesInfoProvider in: "
                    f"{recipe_path}")

                # Debug logging
                print("DEBUG: Checking for required keys...")
                has_include_prereleases = (
                    '<key>include_prereleases</key>' in original_content)
                has_prerelease = (
                    '<key>PRERELEASE</key>' in original_content)
                print(
                    f"DEBUG: Has include_prereleases: "
                    f"{has_include_prereleases}")
                print(f"DEBUG: Has PRERELEASE: {has_prerelease}")

                # Only skip if BOTH keys are present
                if has_include_prereleases and has_prerelease:
                    print(
                        f"Skipping {recipe_path.name} - already has "
                        f"required keys")
                    return False

                # Proceed with modification if either key is missing
                print("DEBUG: Starting modification process...")
                modified_content = modify_plist_content(original_content)
                was_modified = modified_content != original_content
                print(f"DEBUG: Content was modified: {was_modified}")

                if was_modified:
                    print("DEBUG: Content differences:")
                    print("Original length:", len(original_content))
                    print("Modified length:", len(modified_content))
                    # Print a small section where changes occurred
                    print("Sample of modifications:")
                    start_idx = original_content.find(
                        '<string>GitHubReleasesInfoProvider</string>')
                    if start_idx != -1:
                        print("Original:",
                              original_content[start_idx:start_idx+200])
                        print("Modified:",
                              modified_content[start_idx:start_idx+200])
            else:
                return False

        if was_modified and modified_content != original_content:
            print(f"DEBUG: Writing changes to: {recipe_path}")
            with open(recipe_path, 'w', encoding='utf-8') as file:
                file.write(modified_content)

            # Verify the changes were written
            with open(recipe_path, 'r', encoding='utf-8') as file:
                verification_content = file.read()

            if verification_content != modified_content:
                print(
                    f"❌ Warning: File write verification failed for "
                    f"{recipe_path}")
                print("DEBUG: Verification failed - content mismatch")
                return False
            else:
                print(f"✓ Successfully modified and verified: {recipe_path}")
                return True
        else:
            if not was_modified:
                print(f"No modifications needed for: {recipe_path}")
            return False

    except Exception as e:
        print(f"❌ Error processing {recipe_path}: {str(e)}")
        print("DEBUG: Full error details:")
        print(traceback.format_exc())
        return False


def main():
    verify_environment()

    print("GitHub PreRelease Checker - AutoPkg Recipe Updater")
    print("=" * 50)
    print("This script will:")
    print("1. Find recipes with GitHubReleasesInfoProvider processor")
    print("2. Add include_prereleases support with %PRERELEASE% variable")
    print("3. Add PRERELEASE input variable (empty by default)")
    print("4. Update recipe descriptions with usage instructions")
    print("=" * 50)
    print("\nEnter the path to your recipe directory")
    print("(You can drag and drop the folder here): ", end='', flush=True)

    try:
        recipe_dir = clean_path(input())
        recipe_dir = os.path.abspath(recipe_dir)

        if not os.path.isdir(recipe_dir):
            print(f"Error: '{recipe_dir}' is not a valid directory")
            print(
                "Make sure the path exists and you have permission to "
                "access it.")
            return

        print(f"\nScanning recipes in: {recipe_dir}")

        modified_count = 0
        recipe_count = 0
        modified_files = []

        for recipe_path in Path(recipe_dir).rglob("*.download.recipe*"):
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

            print(
                "\nPlease verify these files in your version control "
                "system.")

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
        print("DEBUG: Full error details:")
        print(traceback.format_exc())


if __name__ == "__main__":
    main()

#!/usr/local/autopkg/python
"""
Script to convert HTML-style comments to Comment key-string pairs in recipes.
Converts <!-- comment --> to <key>Comment</key><string>comment</string>
Supports both plist and yaml recipe formats.
Requires AutoPkg's Python installation.
"""

import os
import sys
from pathlib import Path
import re
import traceback
import html


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


def has_html_comments(content):
    """Check if content contains HTML-style comments."""
    return '<!--' in content and '-->' in content


def convert_plist_comments(content):
    """Convert HTML comments to Comment key-string pairs in plist format.

    Args:
        content: String content to convert

    Returns:
        Tuple of (converted_content, was_modified, comment_count)
    """
    modified = False
    comment_count = 0

    # Pattern to match: HTML comment followed by optional whitespace
    # and a <dict>. Handles comments before processor dicts in arrays.
    comment_before_dict_pattern = (r'^(\s*)<!--(.*?)-->\s*\n'
                                   r'(\s*)<dict>\s*\n')

    def replace_comment_before_dict(match):
        nonlocal modified, comment_count
        comment_text = match.group(2)
        dict_indent = match.group(3)

        # Clean up the comment text
        comment_text = comment_text.strip()

        # Skip comments that contain XML/plist structure
        # These are likely commented-out code blocks, not actual comments
        if ('<dict>' in comment_text or '<key>' in comment_text or
                '<array>' in comment_text or '<string>' in comment_text):
            print("DEBUG: Skipping comment containing XML structure "
                  "(likely commented-out code)")
            # Return the original match unchanged
            return match.group(0)

        # For multi-line comments, join lines with spaces
        comment_lines = comment_text.split('\n')
        if len(comment_lines) > 1:
            min_indent = float('inf')
            for line in comment_lines:
                if line.strip():
                    leading = len(line) - len(line.lstrip())
                    min_indent = min(min_indent, leading)

            if min_indent != float('inf'):
                comment_lines = [
                    line[min_indent:] if len(line) > min_indent
                    else line.strip() for line in comment_lines
                ]

        comment_text = ' '.join(
            line.strip() for line in comment_lines
            if line.strip()
        )

        # XML-escape the comment text
        comment_text = html.escape(comment_text)

        # Calculate inner indent (one level deeper than dict)
        inner_indent = dict_indent + '    '

        # Build the result: dict opening with Comment key as first entry
        result = (f'{dict_indent}<dict>\n'
                  f'{inner_indent}<key>Comment</key>\n'
                  f'{inner_indent}<string>{comment_text}</string>\n')

        modified = True
        comment_count += 1
        print("DEBUG: Converting comment (inserting in dict): "
              f"{comment_text[:50]}...")

        return result

    # First pass: handle comments before dicts
    new_content = re.sub(comment_before_dict_pattern,
                         replace_comment_before_dict,
                         content, flags=re.MULTILINE | re.DOTALL)

    # Second pass: handle standalone comments (not before dicts)
    standalone_pattern = r'^(\s*)<!--(.*?)-->\s*$'

    def replace_standalone_comment(match):
        nonlocal modified, comment_count
        indent = match.group(1)
        comment_text = match.group(2)

        # Clean up comment text
        comment_text = comment_text.strip()

        # Skip comments that contain XML/plist structure
        # These are likely commented-out code blocks, not actual comments
        if ('<dict>' in comment_text or '<key>' in comment_text or
                '<array>' in comment_text or '<string>' in comment_text):
            print("DEBUG: Skipping standalone comment containing XML "
                  "structure (likely commented-out code)")
            # Return the original match unchanged
            return match.group(0)

        comment_lines = comment_text.split('\n')

        if len(comment_lines) > 1:
            min_indent = float('inf')
            for line in comment_lines:
                if line.strip():
                    leading = len(line) - len(line.lstrip())
                    min_indent = min(min_indent, leading)

            if min_indent != float('inf'):
                comment_lines = [
                    line[min_indent:] if len(line) > min_indent
                    else line.strip() for line in comment_lines
                ]

        comment_text = ' '.join(
            line.strip() for line in comment_lines
            if line.strip()
        )

        # XML-escape the comment text
        comment_text = html.escape(comment_text)

        # Ensure we're using spaces, not tabs
        indent = indent.replace('\t', '    ')

        result = (f'{indent}<key>Comment</key>\n'
                  f'{indent}<string>{comment_text}</string>')

        modified = True
        comment_count += 1
        print("DEBUG: Converting standalone comment: "
              f"{comment_text[:50]}...")

        return result

    new_content = re.sub(standalone_pattern, replace_standalone_comment,
                         new_content, flags=re.MULTILINE | re.DOTALL)

    return new_content, modified, comment_count


def convert_yaml_comments(content):
    """Convert HTML comments to Comment key-value pairs in YAML format.

    Args:
        content: String content to convert

    Returns:
        Tuple of (converted_content, was_modified, comment_count)
    """
    modified = False
    comment_count = 0

    # Pattern to match multi-line HTML comments
    multiline_pattern = r'^(\s*)<!--(.*?)-->\s*$'

    def replace_multiline_comment(match):
        nonlocal modified, comment_count
        indent = match.group(1)
        comment_text = match.group(2)

        # Clean up the comment text
        comment_text = comment_text.strip()

        # For multi-line comments, join lines with spaces
        comment_lines = comment_text.split('\n')
        # Remove common leading whitespace from all lines
        if len(comment_lines) > 1:
            min_indent = float('inf')
            for line in comment_lines:
                if line.strip():
                    leading = len(line) - len(line.lstrip())
                    min_indent = min(min_indent, leading)

            if min_indent != float('inf'):
                comment_lines = [
                    line[min_indent:] if len(line) > min_indent
                    else line.strip()
                    for line in comment_lines
                ]

        # Join lines with a single space
        comment_text = ' '.join(
            line.strip() for line in comment_lines if line.strip()
        )

        # Ensure we're using spaces, not tabs
        indent = indent.replace('\t', '    ')

        # Convert to YAML Comment key-value pair
        # Escape any special YAML characters in the comment
        if (':' in comment_text or '#' in comment_text or
                comment_text.startswith(('- ', '* ')) or
                '"' in comment_text or '\\' in comment_text):
            # Escape backslashes first, then double quotes
            escaped = comment_text.replace('\\', '\\\\').replace('"', '\\"')
            # Quote the string if it contains special characters
            result = f'{indent}Comment: "{escaped}"'
        else:
            result = f'{indent}Comment: {comment_text}'

        modified = True
        comment_count += 1
        print(f"DEBUG: Converting comment: {comment_text[:50]}...")

        return result

    # Use MULTILINE and DOTALL flags to match across lines
    new_content = re.sub(multiline_pattern, replace_multiline_comment,
                         content, flags=re.MULTILINE | re.DOTALL)

    return new_content, modified, comment_count


def process_recipe(recipe_path):
    """Process a single recipe file and convert HTML comments."""
    try:
        is_yaml = recipe_path.suffix == '.yaml'
        print(f"\nDEBUG: Processing {recipe_path}")
        print(f"DEBUG: File type: {'YAML' if is_yaml else 'plist'}")

        # Read original content
        with open(recipe_path, 'r', encoding='utf-8') as file:
            original_content = file.read()
            print(f"DEBUG: Original content length: {len(original_content)}")

        # Check if file contains HTML comments
        if not has_html_comments(original_content):
            print(f"Skipping {recipe_path.name} - no HTML comments found")
            return False, 0

        print(f"\nFound HTML comments in: {recipe_path}")

        # Convert based on file type
        if is_yaml:
            modified_content, was_modified, comment_count = \
                convert_yaml_comments(original_content)
        else:
            modified_content, was_modified, comment_count = \
                convert_plist_comments(original_content)

        if not was_modified:
            print(f"No modifications needed for: {recipe_path.name}")
            return False, 0

        print(f"DEBUG: Converted {comment_count} comment(s)")

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
            return False, 0

        # Verify no HTML comments remain
        if has_html_comments(verification_content):
            print(f"❌ Warning: HTML comments still present after "
                  f"conversion in {recipe_path}")
            return False, 0

        print(f"✓ Successfully converted {comment_count} comment(s): "
              f"{recipe_path}")
        return True, comment_count

    except Exception as e:
        print(f"❌ Error processing {recipe_path}: {str(e)}")
        print("DEBUG: Full error details:")
        print(traceback.format_exc())
        return False, 0


def main():
    verify_environment()

    print("CommentKeyChecker - AutoPkg Recipe Comment Converter")
    print("=" * 50)
    print("This script will:")
    print("1. Find HTML-style comments (<!-- -->)")
    print("2. Convert them to Comment key-string pairs")
    print("3. Use 4 spaces for indentation")
    print("4. Preserve comment location and formatting")
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
        total_comments_converted = 0

        # Process all recipe files
        for recipe_path in Path(recipe_dir).rglob("*.recipe*"):
            if recipe_path.suffix in ['.recipe', '.yaml']:
                recipe_count += 1
                success, comment_count = process_recipe(recipe_path)
                if success:
                    modified_count += 1
                    modified_files.append((recipe_path, comment_count))
                    total_comments_converted += comment_count

        print(f"\n{'=' * 50}")
        print("Processing complete!")
        print(f"Recipes processed: {recipe_count}")
        print(f"Recipes modified: {modified_count}")
        print(f"Total comments converted: {total_comments_converted}")
        print("=" * 50)

        if modified_files:
            print("\nModified files:")
            for file, comment_count in modified_files:
                print(f"  ✓ {file} ({comment_count} comment(s) converted)")

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

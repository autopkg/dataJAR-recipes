#!/usr/local/autopkg/python
"""
Script to convert HTML-style comments to Comment key-string pairs in recipes.
Converts <!-- comment --> to <key>Comment</key><string>comment</string>
Supports both plist and yaml recipe formats.
Requires AutoPkg's Python installation.
"""

import os
import re
import sys
import traceback
import html
from pathlib import Path


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


def has_wrongly_cased_comment_key(content: str, is_yaml: bool) -> bool:
    """Return True only if a comment key exists with casing other than 'Comment'."""
    if is_yaml:
        matches = re.findall(r'^\s*(comment)\s*:', content,
                             re.MULTILINE | re.IGNORECASE)
        return any(m != 'Comment' for m in matches)
    matches = re.findall(r'<key>(comment)</key>', content, re.IGNORECASE)
    return any(m != 'Comment' for m in matches)


def fix_comment_key_case(content: str, is_yaml: bool) -> tuple[str, bool, int]:
    """Fix wrongly-cased 'comment' keys to 'Comment'.

    Returns:
        Tuple of (fixed_content, was_modified, fix_count)
    """
    fix_count = [0]

    if is_yaml:
        def yaml_replacer(match: re.Match) -> str:
            """Replace wrongly-cased YAML comment key with 'Comment'."""
            if match.group(2) != 'Comment':
                fix_count[0] += 1
                return match.group(1) + 'Comment' + match.group(3)
            return match.group(0)

        new_content = re.sub(
            r'^(\s*)(comment)(\s*:)',
            yaml_replacer,
            content,
            flags=re.MULTILINE | re.IGNORECASE
        )
    else:
        def plist_replacer(match: re.Match) -> str:
            """Replace wrongly-cased plist comment key with 'Comment'."""
            if match.group(1) != 'Comment':
                fix_count[0] += 1
                return '<key>Comment</key>'
            return match.group(0)

        new_content = re.sub(
            r'<key>(comment)</key>',
            plist_replacer,
            content,
            flags=re.IGNORECASE
        )

    was_modified = fix_count[0] > 0
    return new_content, was_modified, fix_count[0]


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
                comment_text.startswith(('- ', '* '))):
            # Quote the string if it contains special characters
            result = f'{indent}Comment: "{comment_text}"'
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


def _apply_fixes(recipe_path: Path, original_content: str,
                 is_yaml: bool) -> tuple[str, int]:
    """Apply HTML comment conversion and case fixes, returning (content, total_count)."""
    modified_content = original_content
    comment_count = 0

    if has_html_comments(original_content):
        print(f"\nFound HTML comments in: {recipe_path}")
        if is_yaml:
            modified_content, _, count = convert_yaml_comments(modified_content)
        else:
            modified_content, _, count = convert_plist_comments(modified_content)
        comment_count += count

    modified_content, case_fixed, fix_count = fix_comment_key_case(modified_content, is_yaml)
    if case_fixed:
        print(f"DEBUG: Fixed capitalisation on {fix_count} comment key(s)")

    return modified_content, comment_count + fix_count


def _commit_changes(recipe_path: Path, original_content: str,
                    modified_content: str, total: int) -> tuple[bool, int]:
    """Write changes if content differs and verify the result.

    Returns (True, total) on success, (False, 0) if nothing changed or write fails.
    On verification failure, restores the original content before returning.
    """
    if modified_content == original_content:
        print(f"No modifications needed for: {recipe_path.name}")
        return False, 0

    print(f"DEBUG: Converted {total} comment(s)")
    print(f"DEBUG: Writing changes to: {recipe_path}")
    with open(recipe_path, 'w', encoding='utf-8') as file:
        file.write(modified_content)

    with open(recipe_path, 'r', encoding='utf-8') as file:
        verified = file.read()

    verification_failed = (verified != modified_content) or has_html_comments(verified)
    if verification_failed:
        if verified != modified_content:
            print(f"❌ Warning: File write verification failed for {recipe_path}")
        else:
            print(f"❌ Warning: HTML comments still present after conversion in {recipe_path}")
        try:
            with open(recipe_path, 'w', encoding='utf-8') as file:
                file.write(original_content)
            print(f"DEBUG: Restored original content for {recipe_path}")
        except OSError as restore_err:
            print(f"❌ CRITICAL: Could not restore {recipe_path}: {restore_err}")
            print("❌ File may be in a corrupt state. Manual review required.")
        return False, 0

    print(f"✓ Successfully converted {total} comment(s): {recipe_path}")
    return True, total


def process_recipe(recipe_path: Path) -> tuple[bool, int]:
    """Process a single recipe file and convert HTML comments."""
    try:
        is_yaml = recipe_path.suffix == '.yaml'
        print(f"\nDEBUG: Processing {recipe_path}")
        print(f"DEBUG: File type: {'YAML' if is_yaml else 'plist'}")

        with open(recipe_path, 'r', encoding='utf-8') as file:
            original_content = file.read()
            print(f"DEBUG: Original content length: {len(original_content)}")

        if not has_html_comments(original_content) and \
                not has_wrongly_cased_comment_key(original_content, is_yaml):
            print(f"Skipping {recipe_path.name} - no HTML comments or capitalisation issues found")
            return False, 0

        modified_content, total = _apply_fixes(recipe_path, original_content, is_yaml)
        return _commit_changes(recipe_path, original_content, modified_content, total)

    except (OSError, UnicodeDecodeError) as e:
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
    print("5. Fix wrongly-cased 'comment' keys to 'Comment'")
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

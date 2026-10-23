#!/usr/local/autopkg/python
"""
Script to update GitHub download recipes with prerelease handling.
Supports both plist and yaml recipe formats.
Requires AutoPkg's Python installation.
"""

import contextlib
import os
import plistlib
import shutil
import sys
import yaml
from pathlib import Path
import re
import traceback
from enum import Enum
from xml.parsers.expat import ExpatError

# Make linter_common importable when run directly (a no-op under
# autopkg-linter.py, which already has this directory on sys.path).
# Kept as one if-statement so the import below isn't flagged E402.
if (_LINTERS_DIR := os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))) not in sys.path:
    sys.path.insert(0, _LINTERS_DIR)
from linter_common import clean_path, verify_environment

GITHUB_PROCESSOR_RE = re.compile(
    r'^(\s*)(- +)?Processor: *([\'"]?)GitHubReleasesInfoProvider\3'
    r' *(#.*)?$')
ARGUMENTS_KEY = 'Arguments:'
RECIPE_ENCODING = 'utf-8'
PRERELEASE_ARGUMENT = 'include_prereleases: "%PRERELEASE%"'
PLIST_GITHUB_STRING = '<string>GitHubReleasesInfoProvider</string>'
PRERELEASE_KEY = 'include_prereleases'
# Characters YAML's parser treats as line breaks, which a literal block
# can't keep as written. A raw '\r' is already normalised on read, so '\r'
# only matches one escaped in a quoted value
YAML_LINE_BREAKS = ('\r', '\x85', '\u2028', '\u2029')
PRERELEASE_DESCRIPTION = [
    'Set PRERELEASE to a non-empty string to download prereleases, either',
    'via Input in an override or via the -k option,',
    'i.e.: `-k PRERELEASE=yes`',
]


class RecipeResult(Enum):
    """The result of processing one recipe."""

    MODIFIED = 'modified'
    UNCHANGED = 'unchanged'
    FAILED = 'failed'


def _yaml_needs_prereleases(recipe: object) -> bool:
    """Check whether any step of a parsed yaml recipe lacks the argument."""
    needs_modification = False
    if not isinstance(recipe, dict):
        return needs_modification
    for process_step in recipe.get('Process') or []:
        if not isinstance(process_step, dict):
            continue
        if process_step.get('Processor') == (
                'GitHubReleasesInfoProvider'):
            print(
                "DEBUG: Found GitHubReleasesInfoProvider "
                "processor in YAML recipe")
            args = process_step.get('Arguments') or {}
            if PRERELEASE_KEY not in args:
                print("DEBUG: include_prereleases key missing")
                needs_modification = True
    return needs_modification


def _yaml_needs_prerelease_input(recipe: object) -> bool:
    """Check whether a recipe with a GitHub step lacks the PRERELEASE input."""
    if not isinstance(recipe, dict):
        return False
    has_github_step = any(
        isinstance(step, dict) and
        step.get('Processor') == 'GitHubReleasesInfoProvider'
        for step in recipe.get('Process') or [])
    return has_github_step and 'PRERELEASE' not in (recipe.get('Input') or {})


def _indent_of(line: str) -> int:
    """Return the number of leading spaces on a line."""
    return len(line) - len(line.lstrip(' '))


def _entry_indent(following: list[str], parent_indent: int) -> int:
    """Return the indent for a new entry under a key at parent_indent.

    That is the indent of the first entry in following, skipping blank and
    comment lines, or two more spaces than the key if it has no entries.
    """
    first = next((ln for ln in following
                  if ln.strip() and not ln.lstrip().startswith('#')), '')
    indent = _indent_of(first)
    return indent if indent > parent_indent else parent_indent + 2


def _yaml_step_bounds(modified_lines: list[str], i: int,
                      key_indent: int) -> tuple[int, int]:
    """Return the step holding line i as a (start, end) range, end exclusive.

    The step starts at the nearest '- ' line above with an indent below
    key_indent, so list items nested within the step's keys are skipped.
    It ends before the next non-blank line with an indent below key_indent.
    """
    start = i
    while start > 0 and not (
            modified_lines[start].lstrip().startswith('- ') and
            _indent_of(modified_lines[start]) < key_indent):
        start -= 1
    end = i + 1
    while end < len(modified_lines):
        line = modified_lines[end]
        if line.strip() and _indent_of(line) < key_indent:
            break
        end += 1
    return start, end


def _find_yaml_arguments(modified_lines: list[str], start: int, end: int,
                         key_indent: int) -> int | None:
    """Find the Arguments line of a step, or None."""
    for j in range(start, end):
        stripped = modified_lines[j].strip()
        if j == start and stripped.startswith('- '):
            is_arguments = re.sub(r'^- +', '', stripped).startswith(
                ARGUMENTS_KEY)
        else:
            is_arguments = (stripped.startswith(ARGUMENTS_KEY) and
                            _indent_of(modified_lines[j]) == key_indent)
        if is_arguments:
            return j
    return None


def _add_yaml_step_prereleases(modified_lines: list[str], i: int,
                               match: re.Match[str]) -> None:
    """Add include_prereleases to the step whose Processor is on line i."""
    key_indent = len(match.group(1)) + len(match.group(2) or '')
    start, end = _yaml_step_bounds(modified_lines, i, key_indent)
    step = modified_lines[start:end]
    if any(ln.strip().startswith('include_prereleases:') for ln in step):
        return
    args_idx = _find_yaml_arguments(modified_lines, start, end, key_indent)
    pad = ' ' * key_indent
    if (args_idx is not None and not re.sub(
            r'\s+#.*$', '', modified_lines[args_idx]).rstrip().endswith(
                ARGUMENTS_KEY)):
        # Inline Arguments value, such as {}, so leave for a manual edit
        return
    if args_idx is not None:
        entry_indent = _entry_indent(
            modified_lines[args_idx + 1:end], key_indent)
        modified_lines.insert(
            args_idx + 1, f'{" " * entry_indent}{PRERELEASE_ARGUMENT}')
    elif match.group(2):
        # List item opened by Processor, so open it with Arguments instead
        modified_lines[i:i + 1] = [
            f'{match.group(1)}{match.group(2)}{ARGUMENTS_KEY}',
            f'{pad}  {PRERELEASE_ARGUMENT}',
            f'{pad}{modified_lines[i][key_indent:]}',
        ]
    else:
        modified_lines[i:i] = [f'{pad}{ARGUMENTS_KEY}',
                               f'{pad}  {PRERELEASE_ARGUMENT}']


def _add_yaml_include_prereleases(modified_lines: list[str]) -> None:
    """Add include_prereleases to each GitHubReleasesInfoProvider step."""
    # Work upwards, so inserted lines don't shift steps not yet handled
    for i in range(len(modified_lines) - 1, -1, -1):
        match = GITHUB_PROCESSOR_RE.match(modified_lines[i])
        if match:
            _add_yaml_step_prereleases(modified_lines, i, match)


def _add_yaml_prerelease_input(modified_lines: list[str]) -> None:
    """Add PRERELEASE to the Input section if missing.

    The entry is indented as given by _entry_indent.
    """
    if any(ml.strip().startswith('PRERELEASE:') for ml in modified_lines):
        return
    for i, line in enumerate(modified_lines):
        if line.strip() == 'Input:':
            entry_indent = _entry_indent(
                modified_lines[i + 1:], _indent_of(line))
            modified_lines.insert(
                i + 1, f'{" " * entry_indent}PRERELEASE: ""')
            return


def _yaml_description_range(
        modified_lines: list[str]) -> tuple[int, int] | None:
    """Return the top-level Description's lines as (start, end), or None.

    end is exclusive, and trailing blank lines are left out. If there is
    no top-level Description, None is returned. A
    Description with an anchor or alias, or a '#' anywhere in its lines,
    gives None, as a rewrite would drop a comment. That also declines a
    '#' within the text, which is left for a manual edit.
    """
    for i, line in enumerate(modified_lines):
        if not line.startswith('Description:'):
            continue
        j = i + 1
        while j < len(modified_lines) and (
                modified_lines[j].startswith(' ') or
                not modified_lines[j].strip()):
            j += 1
        while j > i + 1 and not modified_lines[j - 1].strip():
            j -= 1
        value = line[len('Description:'):].lstrip()
        has_extra = (value[:1] in ('&', '*') or
                     any('#' in ml for ml in modified_lines[i:j]))
        return None if has_extra else (i, j)
    return None


def _has_prerelease_note(desc: object) -> bool:
    """Check whether a Description already has the PRERELEASE note."""
    return isinstance(desc, str) and PRERELEASE_DESCRIPTION[0] in desc


def _add_yaml_prerelease_description(modified_lines: list[str]) -> None:
    """Append PRERELEASE instructions to the top-level Description.

    The parsed value is rewritten as a literal block, so every scalar
    style, quoted, plain or block, keeps its text apart from trailing
    whitespace, as the plist path does, unless declined below.
    Does nothing if there is no Description, as on the plist path, or it
    already has the note. Also does nothing, and _yaml_edits_complete
    then reports the recipe for a manual edit, if the edited yaml doesn't
    parse, the Description isn't a string, starts with whitespace or
    holds a character in YAML_LINE_BREAKS, or _yaml_description_range
    declines it.
    """
    try:
        recipe = yaml.safe_load('\n'.join(modified_lines))
    except yaml.YAMLError:
        return
    desc = recipe.get('Description') if isinstance(recipe, dict) else None
    if (not isinstance(desc, str) or _has_prerelease_note(desc) or
            desc[:1].isspace() or any(c in desc for c in YAML_LINE_BREAKS)):
        return
    description_range = _yaml_description_range(modified_lines)
    if description_range:
        start, end = description_range
        text_lines = desc.rstrip().split('\n') + [''] if desc.strip() else []
        value_lines = text_lines + PRERELEASE_DESCRIPTION
        modified_lines[start:end] = ['Description: |'] + [
            f'  {value}' if value else '' for value in value_lines]


def _yaml_edits_complete(new_content: str,
                         original_description: object) -> bool:
    """Check edited yaml parses and has every PRERELEASE edit.

    That is the PRERELEASE input, the note in the Description if there
    is one, and include_prereleases in every GitHubReleasesInfoProvider
    step. If the original Description was a string, the new one must
    start with its text, ignoring trailing whitespace.
    """
    try:
        recipe = yaml.safe_load(new_content)
    except yaml.YAMLError as err:
        print(f"⚠️  Edited YAML no longer parses: {err}")
        return False
    problem = None
    desc = recipe.get('Description') if isinstance(recipe, dict) else None
    if not isinstance(recipe, dict):
        problem = "Edited YAML is not a recipe"
    elif 'PRERELEASE' not in (recipe.get('Input') or {}):
        problem = "Could not add PRERELEASE to the Input section"
    elif 'Description' in recipe and not _has_prerelease_note(desc):
        problem = "Could not add the PRERELEASE note to the Description"
    elif (isinstance(original_description, str) and
          not desc.startswith(original_description.rstrip())):
        problem = "Rewriting the Description would change its text"
    elif _yaml_needs_prereleases(recipe):
        problem = ("Could not add include_prereleases to every "
                   "GitHubReleasesInfoProvider step")
    if problem:
        print(f"⚠️  {problem}")
    return problem is None


def modify_yaml_recipe(content: str) -> str | None:
    """Modify yaml recipe content while preserving formatting.

    Uses parsed YAML to detect what needs changing, then performs
    text-based edits to preserve formatting. Returns the modified
    content, content as it was if no change is needed, or None if the
    edits couldn't be completed, so the recipe needs a manual edit.
    """
    print("DEBUG: Processing YAML recipe")
    recipe = yaml.safe_load(content)

    # As on the plist path, skip only if both the argument and input exist
    if not (_yaml_needs_prereleases(recipe) or
            _yaml_needs_prerelease_input(recipe)):
        return content

    print("DEBUG: YAML recipe needs modification")
    # Split on '\n' only, as splitlines() also breaks on characters such
    # as U+2028, which the join below would turn into real line breaks
    modified_lines = content.removesuffix('\n').split('\n')

    # 1. Add include_prereleases to each GitHubReleasesInfoProvider step
    _add_yaml_include_prereleases(modified_lines)

    # 2. Add PRERELEASE to Input section if missing
    _add_yaml_prerelease_input(modified_lines)

    # 3. Update Description with PRERELEASE instructions
    _add_yaml_prerelease_description(modified_lines)

    new_content = '\n'.join(modified_lines) + '\n'
    if not _yaml_edits_complete(new_content, recipe.get('Description')):
        print("⚠️  Could not complete the PRERELEASE edits, so leaving "
              "this recipe for a manual edit")
        return None
    return new_content


def _leading_ws(line: str) -> str:
    """Return a line's leading whitespace."""
    return line[:len(line) - len(line.lstrip())]


def _is_plist_github_processor(lines: list[str], i: int) -> bool:
    """Check whether line i is the Processor key of a GitHub step."""
    return (lines[i].strip() == '<key>Processor</key>' and
            i + 1 < len(lines) and
            lines[i + 1].strip() == PLIST_GITHUB_STRING)


def _plist_step_bounds(lines: list[str], i: int) -> tuple[int, int] | None:
    """Return the step dict holding key line i as (start, end), or None.

    start is the step's <dict> line and end its </dict> line, the nearest
    ones with an indent shallower than the key's.
    """
    indent = len(_leading_ws(lines[i]))
    start = next((j for j in range(i - 1, -1, -1)
                  if lines[j].strip() == '<dict>' and
                  len(_leading_ws(lines[j])) < indent), None)
    end = next((j for j in range(i + 1, len(lines))
                if lines[j].strip() == '</dict>' and
                len(_leading_ws(lines[j])) < indent), None)
    if start is None or end is None:
        return None
    return start, end


def _plist_sorted_position(lines: list[str], first: int, close: int) -> int:
    """Return where include_prereleases sorts among a dict's keys.

    The dict's entries are lines first to close, end exclusive. Keys sort
    ignoring case, as RecipeAlphabetiser sorts them.
    """
    entry_ws = _leading_ws(lines[first])
    return next(
        (j for j in range(first, close)
         if _leading_ws(lines[j]) == entry_ws and
         lines[j].strip().startswith('<key>') and
         lines[j].strip()[5:-6].lower() > PRERELEASE_KEY), close)


def _insert_plist_argument(lines: list[str], args: int, end: int,
                           entry: list[str]) -> None:
    """Insert entry into the Arguments dict whose key is line args.

    It goes where it sorts, indented as the existing entries, if any. A
    dict whose </dict> isn't found before end is left alone.
    """
    pad = _leading_ws(lines[args])
    close = next((j for j in range(args + 2, end + 1)
                  if lines[j] == f'{pad}</dict>'), None)
    if close is None:
        return
    first_ws = _leading_ws(lines[args + 2])
    if close > args + 2 and len(first_ws) > len(pad):
        entry = [f'{first_ws}{line.lstrip()}' for line in entry]
    position = _plist_sorted_position(lines, args + 2, close)
    lines[position:position] = entry


def _add_plist_step_prereleases(lines: list[str], i: int) -> None:
    """Add include_prereleases to the step whose Processor key is line i.

    Any other keys in the step, such as Comment, are left in place. A step
    whose Arguments isn't a <dict> block is left for a manual edit.
    """
    bounds = _plist_step_bounds(lines, i)
    pad = _leading_ws(lines[i])
    entry_pad = pad + ('\t' if pad.startswith('\t') else '    ')
    entry = [f'{entry_pad}<key>include_prereleases</key>',
             f'{entry_pad}<string>%PRERELEASE%</string>']
    if bounds is None or any('<key>include_prereleases</key>' in ln
                             for ln in lines[bounds[0]:bounds[1]]):
        return
    start, end = bounds
    args = next((j for j in range(start + 1, end)
                 if lines[j] == f'{pad}<key>Arguments</key>'), None)
    if args is None:
        # Arguments sorts first, so open the step with it
        lines[start + 1:start + 1] = [f'{pad}<key>Arguments</key>',
                                      f'{pad}<dict>', *entry, f'{pad}</dict>']
    elif lines[args + 1].strip() == '<dict/>':
        lines[args + 1:args + 2] = [f'{pad}<dict>', *entry, f'{pad}</dict>']
    elif lines[args + 1].strip() == '<dict>':
        _insert_plist_argument(lines, args, end, entry)


def _add_plist_include_prereleases(content: str) -> str:
    """Add include_prereleases to each GitHubReleasesInfoProvider step."""
    lines = content.split('\n')
    # Work upwards, so inserted lines don't shift steps not yet handled
    for i in range(len(lines) - 1, -1, -1):
        if _is_plist_github_processor(lines, i):
            _add_plist_step_prereleases(lines, i)
    return '\n'.join(lines)


def modify_plist_content(content: str) -> str:
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

    # Add include_prereleases to each GitHubReleasesInfoProvider step
    content = _add_plist_include_prereleases(content)

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


def _write_recipe(recipe_path: Path, recipe_dir: str, content: str,
                  original: bytes) -> bool:
    """Write content to recipe_path, keeping its line endings.

    The content is written to a temporary file beside the recipe's
    target, read back to verify it, and only then moved over the target,
    so an error or interrupt at any point leaves the recipe as it was.
    A symlinked recipe has its target written, and is refused if that
    target is outside recipe_dir. A recipe with only CRLF line endings
    is written with CRLF line endings.
    """
    real_dir = os.path.realpath(recipe_dir)
    real_path = os.path.realpath(recipe_path)
    # Joining '' adds a trailing separator, except to '/', which has one
    if not real_path.startswith(os.path.join(real_dir, '')):
        print(f"❌ {recipe_path} resolves outside {recipe_dir}, so leaving "
              f"it unchanged")
        return False
    crlf_only = original.count(b'\r\n') == original.count(b'\n') > 0
    newline = '\r\n' if crlf_only else '\n'
    tmp_path = os.path.join(os.path.dirname(real_path),
                            f'.{os.path.basename(real_path)}.tmp')
    try:
        with open(tmp_path, 'w', encoding=RECIPE_ENCODING,
                  newline=newline) as file:
            file.write(content)
        with open(tmp_path, 'r', encoding=RECIPE_ENCODING) as file:
            verified = file.read() == content
        if verified:
            shutil.copymode(real_path, tmp_path)
            os.replace(tmp_path, real_path)
            print(f"✓ Successfully modified and verified: {recipe_path}")
        else:
            print(f"❌ Warning: File write verification failed for "
                  f"{recipe_path}, so leaving it unchanged")
        return verified
    except (OSError, ValueError) as err:
        print(f"❌ Could not write {recipe_path}, so leaving it "
              f"unchanged: {err}")
        return False
    finally:
        with contextlib.suppress(OSError):
            os.unlink(tmp_path)


def _plist_prerelease_state(content: str) -> tuple[bool, bool] | None:
    """Return whether a plist has GitHub steps, and has every edit.

    The second value is True if there is a GitHubReleasesInfoProvider
    step, the PRERELEASE input exists, and every such step has an
    include_prereleases argument, whatever its value. Returns None, and
    says so, if the plist doesn't parse.
    """
    try:
        recipe = plistlib.loads(content.encode(RECIPE_ENCODING))
    # ValueError covers plistlib.InvalidFileException
    except (ExpatError, ValueError) as err:
        print(f"⚠️  Recipe doesn't parse as a plist: {err}")
        return None
    steps = recipe.get('Process') if isinstance(recipe, dict) else None
    github_steps = [
        step for step in steps or [] if isinstance(step, dict) and
        step.get('Processor') == 'GitHubReleasesInfoProvider']
    # github_steps is empty unless recipe is a dict, so check it first
    complete = (bool(github_steps) and
                'PRERELEASE' in (recipe.get('Input') or {}) and
                all(PRERELEASE_KEY in (step.get('Arguments') or {})
                    for step in github_steps))
    return bool(github_steps), complete


def _edit_plist_recipe(original_content: str) -> str | None:
    """Return a plist recipe with the PRERELEASE edits, or None.

    None is returned if the edits are incomplete afterwards, as
    _plist_prerelease_state finds, so the recipe needs a manual edit.
    """
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
        start_idx = original_content.find(PLIST_GITHUB_STRING)
        if start_idx != -1:
            print("Original:", original_content[start_idx:start_idx+200])
            print("Modified:", modified_content[start_idx:start_idx+200])
    if _plist_prerelease_state(modified_content) != (True, True):
        print("⚠️  Could not add include_prereleases and PRERELEASE, so "
              "leaving this recipe for a manual edit")
        return None
    return modified_content


def _modify_plist_recipe(recipe_path: Path,
                         original_content: str) -> str | None:
    """Return a plist recipe's modified content, or None if it needs a
    manual edit.

    A recipe without a GitHubReleasesInfoProvider step, or that already has
    the PRERELEASE input and include_prereleases in every such step, is
    returned as it was. Each step is checked, not the file as a whole.
    """
    state = _plist_prerelease_state(original_content)
    if state is None:
        return None
    has_github_steps, complete = state
    if has_github_steps:
        print(f"\nFound GitHubReleasesInfoProvider in: {recipe_path}")
    if complete or not has_github_steps:
        if complete:
            print(f"Skipping {recipe_path.name} - already has required keys")
        return original_content
    return _edit_plist_recipe(original_content)


def process_recipe(recipe_path: Path, recipe_dir: str) -> RecipeResult:
    """Process a single recipe file and make necessary modifications.

    Returns MODIFIED, UNCHANGED if no change was needed, or FAILED if a
    needed change couldn't be made or written, or the recipe couldn't be
    processed.
    """
    status = RecipeResult.UNCHANGED
    try:
        is_yaml = recipe_path.suffix == '.yaml'
        print(f"\nDEBUG: Processing {recipe_path}")
        print(f"DEBUG: File type: {'YAML' if is_yaml else 'plist'}")

        # Read original content and store it for comparison, and its
        # bytes to find its line endings
        original_bytes = recipe_path.read_bytes()
        with open(recipe_path, 'r', encoding=RECIPE_ENCODING) as file:
            original_content = file.read()
            print(
                f"DEBUG: Original content length: "
                f"{len(original_content)}")

        # Both return None if the recipe needs a manual edit
        if is_yaml:
            modified_content = modify_yaml_recipe(original_content)
        else:
            modified_content = _modify_plist_recipe(
                recipe_path, original_content)

        if modified_content is None:
            status = RecipeResult.FAILED
        elif modified_content != original_content:
            print(f"DEBUG: Writing changes to: {recipe_path}")
            written = _write_recipe(recipe_path, recipe_dir,
                                    modified_content, original_bytes)
            status = (RecipeResult.MODIFIED if written
                      else RecipeResult.FAILED)
        elif is_yaml:
            print(f"No modifications needed for: {recipe_path}")

    except Exception as e:
        print(f"❌ Error processing {recipe_path}: {str(e)}")
        print("DEBUG: Full error details:")
        print(traceback.format_exc())
        status = RecipeResult.FAILED
    return status


def _scan_recipes(recipe_dir: str,
                  results: dict[RecipeResult, list[Path]]) -> None:
    """Process every download recipe in recipe_dir, recording each result.

    results is filled in as it goes, so it holds the recipes processed so
    far if a recipe is interrupted.
    """
    for recipe_path in Path(recipe_dir).rglob("*.download.recipe*"):
        if recipe_path.suffix in ['.recipe', '.yaml']:
            results[process_recipe(recipe_path, recipe_dir)].append(
                recipe_path)


def _print_summary(results: dict[RecipeResult, list[Path]],
                   complete: bool) -> None:
    """Print the counts, then the modified and failed recipes."""
    modified_files = results[RecipeResult.MODIFIED]
    failed_files = results[RecipeResult.FAILED]
    recipe_count = sum(len(paths) for paths in results.values())
    print(f"\n{'=' * 50}")
    print("Processing complete!" if complete else "Processing stopped early!")
    print(f"Recipes processed: {recipe_count}")
    print(f"Recipes modified: {len(modified_files)}")
    print(f"Recipes failed: {len(failed_files)}")
    print("=" * 50)

    if modified_files:
        print("\nModified files:")
        for file in modified_files:
            print(f"  ✓ {file}")

        print(
            "\nPlease verify these files in your version control "
            "system.")

    if failed_files:
        print("\nFailed files, which need checking by hand:")
        for file in failed_files:
            print(f"  ❌ {file}")


def main() -> None:
    """Prompt for a recipe directory and add PRERELEASE support.

    Exits with status 1 if any recipe failed or the scan did not
    complete.
    """
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

    results: dict[RecipeResult, list[Path]] = {
        result: [] for result in RecipeResult}
    scanning = complete = False
    try:
        recipe_dir = clean_path(input())
        recipe_dir = os.path.abspath(recipe_dir)

        if os.path.isdir(recipe_dir):
            print(f"\nScanning recipes in: {recipe_dir}")
            scanning = True
            _scan_recipes(recipe_dir, results)
            complete = True
        else:
            print(f"Error: '{recipe_dir}' is not a valid directory")
            print(
                "Make sure the path exists and you have permission to "
                "access it.")

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
        print("DEBUG: Full error details:")
        print(traceback.format_exc())

    # Also after a cancel or error, so files already rewritten are listed
    if scanning:
        _print_summary(results, complete)
    # Outside the try, as the linter runner's sys.exit raises an Exception
    if results[RecipeResult.FAILED] or not complete:
        sys.exit(1)


if __name__ == "__main__":
    main()

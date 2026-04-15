#!/usr/local/autopkg/python
"""
Script to alphabetize keys in AutoPkg recipes.
Alphabetizes the Input dict with dependency-awareness (keys referenced in
other keys' values are ordered first), pkginfo dict (in munki recipes).
Preserves Process array order but alphabetizes keys within each processor.
Ensures 'Processor' key is always last in processor dicts.
Supports both plist and YAML recipe formats.
Requires AutoPkg's Python installation.

Key Feature: Dependency-Aware Input Sorting
AutoPkg processes Input keys sequentially. If key A's value contains %KEY_B%,
then KEY_B must be defined before KEY_A. This script uses topological sorting
to ensure correct dependency order while maintaining alphabetical sorting for
keys with no dependencies.

Example:
  If MUNKI_REPO_SUBDIR = '%CATEGORY%/%NAME%'
  Then CATEGORY and NAME will be placed before MUNKI_REPO_SUBDIR
"""

import os
import sys
from pathlib import Path
import plistlib
import re
import traceback


class AutoPkgYAMLDumper:
    """Custom YAML dumper for AutoPkg recipes with proper indentation."""

    @staticmethod
    def represent_none(dumper, _):
        """Represent None as empty string instead of 'null'."""
        return dumper.represent_scalar('tag:yaml.org,2002:null', '')

    @staticmethod
    def get_dumper():
        """Get configured YAML dumper.

        Returns:
            YAML Dumper class configured for AutoPkg recipes
        """
        try:
            import yaml

            class CustomDumper(yaml.SafeDumper):
                pass

            # Represent None as empty instead of 'null'
            CustomDumper.add_representer(
                type(None),
                AutoPkgYAMLDumper.represent_none
            )

            return CustomDumper
        except ImportError:
            return None


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


def alphabetize_dict_with_processor_last(d):
    """Alphabetize dict keys, but keep 'Processor' key last.

    Args:
        d: Dictionary to alphabetize

    Returns:
        New dict with sorted keys (Processor last if present)
    """
    if not isinstance(d, dict):
        return d

    # Separate Processor key if present
    has_processor = 'Processor' in d
    processor_value = d.get('Processor')

    # Get all keys except Processor and sort them (case-insensitive)
    keys = [k for k in d.keys() if k != 'Processor']
    sorted_keys = sorted(keys, key=str.lower)

    # Build new dict
    result = {}
    for key in sorted_keys:
        result[key] = d[key]

    # Add Processor at the end if it existed
    if has_processor:
        result['Processor'] = processor_value

    return result


def alphabetize_dict_with_processor_first(d):
    """Alphabetize dict keys, but keep 'Processor' key first.

    For YAML recipes, Processor must be first or the recipe is invalid.

    Args:
        d: Dictionary to alphabetize

    Returns:
        New dict with sorted keys (Processor first if present)
    """
    if not isinstance(d, dict):
        return d

    # Separate Processor key if present
    has_processor = 'Processor' in d
    processor_value = d.get('Processor')

    # Get all keys except Processor and sort them (case-insensitive)
    keys = [k for k in d.keys() if k != 'Processor']
    sorted_keys = sorted(keys, key=str.lower)

    # Build new dict with Processor first
    result = {}
    if has_processor:
        result['Processor'] = processor_value

    for key in sorted_keys:
        result[key] = d[key]

    return result


def alphabetize_dict(d):
    """Alphabetize dict keys recursively.

    Args:
        d: Dictionary to alphabetize

    Returns:
        New dict with sorted keys
    """
    if not isinstance(d, dict):
        return d

    sorted_dict = {}
    for key in sorted(d.keys(), key=str.lower):
        value = d[key]
        # Recursively alphabetize nested dicts
        if isinstance(value, dict):
            sorted_dict[key] = alphabetize_dict(value)
        else:
            sorted_dict[key] = value

    return sorted_dict


def extract_variable_references(value):
    """Extract AutoPkg variable references from a string value.

    Args:
        value: String value that may contain %VARIABLE% references

    Returns:
        Set of variable names referenced (without % symbols)
    """
    if not isinstance(value, str):
        return set()

    # Match %VARIABLE_NAME% references
    pattern = r'%(\w+)%'
    matches = re.findall(pattern, value)
    return set(matches)


def topological_sort_input_keys(input_dict):
    """Sort Input dict keys respecting variable dependencies.

    AutoPkg processes Input keys sequentially. If key A's value references
    %KEY_B%, then KEY_B must be defined before KEY_A.

    Args:
        input_dict: Input dictionary (excluding pkginfo)

    Returns:
        List of keys in dependency-respecting order
    """
    # Build dependency graph
    dependencies = {}  # key -> set of keys it depends on

    for key, value in input_dict.items():
        deps = extract_variable_references(value)
        # Only include dependencies that are actually in this Input dict
        deps = deps.intersection(set(input_dict.keys()))
        dependencies[key] = deps

    # Topological sort using Kahn's algorithm
    # Calculate in-degree (number of dependencies)
    in_degree = dict.fromkeys(input_dict.keys(), 0)
    for key, deps in dependencies.items():
        for _ in deps:
            in_degree[key] += 1

    # Queue: keys with no dependencies, alphabetized
    queue = [
        key for key, degree in in_degree.items()
        if degree == 0
    ]
    queue.sort(key=str.lower)

    result = []

    while queue:
        # Pop key with no remaining dependencies
        current = queue.pop(0)
        result.append(current)

        # Find keys that depend on current key
        for key, deps in dependencies.items():
            if current in deps:
                in_degree[key] -= 1
                if in_degree[key] == 0:
                    queue.append(key)

        # Keep queue sorted for consistent output (case-insensitive)
        queue.sort(key=str.lower)

    # Check for circular dependencies
    if len(result) != len(input_dict):
        # Circular dependency detected, fall back to alphabetical
        print("  Warning: Circular dependency detected in Input keys, "
              "using alphabetical order")
        return sorted(input_dict.keys(), key=str.lower)

    return result


def _sort_input_section(original_input):
    """Sort Input section with dependency awareness.

    Args:
        original_input: Original Input dict

    Returns:
        Tuple of (modified: bool, changes: list, new_input: dict)
    """
    changes = []
    modified = False

    # Get all keys in Input except pkginfo
    input_keys_dict = {
        k: v for k, v in original_input.items()
        if k != 'pkginfo'
    }

    # Sort with dependency awareness
    sorted_input_keys = topological_sort_input_keys(input_keys_dict)
    original_keys_list = [
        k for k in original_input.keys()
        if k != 'pkginfo'
    ]

    # Check if Input needs reordering
    if original_keys_list != sorted_input_keys:
        modified = True
        changes.append("Sorted Input dict (dependency-aware)")

    # Build new Input dict with sorted keys
    new_input = {}
    for key in sorted_input_keys:
        new_input[key] = original_input[key]

    # Handle pkginfo separately if it exists
    if 'pkginfo' in original_input:
        pkginfo_original = original_input['pkginfo']
        pkginfo_sorted = alphabetize_dict(pkginfo_original)

        # Check if pkginfo changed
        if list(pkginfo_original.keys()) != list(pkginfo_sorted.keys()):
            modified = True
            changes.append("Alphabetized pkginfo dict")

        # Add pkginfo in alphabetical position
        new_input['pkginfo'] = pkginfo_sorted

    return modified, changes, new_input


def _sort_process_array(process_array, processor_position='last'):
    """Sort keys within each processor in Process array.

    Args:
        process_array: Process array from recipe
        processor_position: 'first' for YAML, 'last' for plist

    Returns:
        Tuple of (modified: bool, changes: list)
    """
    changes = []
    modified = False

    # Choose the appropriate sorting function
    if processor_position == 'first':
        sort_func = alphabetize_dict_with_processor_first
    else:
        sort_func = alphabetize_dict_with_processor_last

    for i, processor in enumerate(process_array):
        if not isinstance(processor, dict):
            continue

        original_keys = list(processor.keys())
        processor_name = processor.get('Processor', f'step {i+1}')

        # Alphabetize processor dict
        sorted_processor = sort_func(processor)

        # Check if order changed
        if original_keys != list(sorted_processor.keys()):
            modified = True
            changes.append(
                f"Alphabetized processor: {processor_name}"
            )

        # Recursively alphabetize Arguments if present
        if 'Arguments' in sorted_processor:
            args_original = sorted_processor['Arguments']
            if isinstance(args_original, dict):
                args_sorted = alphabetize_dict(args_original)
                if (list(args_original.keys()) !=
                        list(args_sorted.keys())):
                    modified = True
                    changes.append(
                        f"Alphabetized Arguments in {processor_name}"
                    )
                sorted_processor['Arguments'] = args_sorted

        process_array[i] = sorted_processor

    return modified, changes


def _build_ordered_recipe(recipe_data):
    """Build recipe dict with standardized key order.

    Args:
        recipe_data: Recipe data dict

    Returns:
        Ordered recipe dict
    """
    ordered_recipe = {}

    # Standard order for recipe keys
    key_order = [
        'Comment',
        'Description',
        'Identifier',
        'Input',
        'MinimumVersion',
        'ParentRecipe',
        'Process'
    ]

    # Add keys in preferred order if they exist
    for key in key_order:
        if key in recipe_data:
            ordered_recipe[key] = recipe_data[key]

    # Add any remaining keys not in our standard list
    for key in recipe_data:
        if key not in ordered_recipe:
            ordered_recipe[key] = recipe_data[key]

    return ordered_recipe


def _detect_indentation(recipe_path):
    """Detect whether file uses tabs or spaces for indentation.

    Args:
        recipe_path: Path to the recipe file

    Returns:
        'tabs' if file uses tabs, 'spaces' if file uses spaces
    """
    try:
        with open(recipe_path, 'r', encoding='utf-8') as f:
            for line in f:
                # Look for lines with leading whitespace
                if line.startswith('\t'):
                    return 'tabs'
                elif line.startswith('    '):
                    return 'spaces'
    except Exception:
        pass

    # Default to spaces if unclear
    return 'spaces'


def _fix_plist_formatting(recipe_path, original_indent_type='spaces'):
    """Fix HTML entities and preserve indentation format.

    Args:
        recipe_path: Path to the recipe file
        original_indent_type: 'tabs' or 'spaces' - format to preserve
    """
    # Read back and fix HTML entities
    with open(recipe_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Unescape quotes that plistlib unnecessarily escapes
    content = content.replace('&quot;', '"')
    content = content.replace('&apos;', "'")

    lines = content.splitlines(keepends=True)

    # Convert indentation to match original format
    converted_lines = []
    for line in lines:
        if original_indent_type == 'spaces':
            # Convert tabs to spaces (original behavior)
            leading_tabs = len(line) - len(line.lstrip('\t'))
            if leading_tabs > 0:
                # Replace leading tabs with 4 spaces per tab
                line = ('    ' * leading_tabs) + line.lstrip('\t')
        # If original_indent_type == 'tabs', leave tabs as-is
        # plistlib.dump() outputs with tabs by default
        converted_lines.append(line)

    with open(recipe_path, 'w', encoding='utf-8') as f:
        f.writelines(converted_lines)


def process_plist_recipe(recipe_path):
    """Process a plist recipe file and alphabetize appropriate sections.

    Args:
        recipe_path: Path to the recipe file

    Returns:
        Tuple of (modified: bool, changes: list)
    """
    try:
        # Detect original indentation format before modifying
        original_indent_type = _detect_indentation(recipe_path)

        with open(recipe_path, 'rb') as f:
            recipe_data = plistlib.load(f)

        changes = []
        modified = False

        # Alphabetize Input dict if it exists
        if 'Input' in recipe_data:
            input_modified, input_changes, new_input = \
                _sort_input_section(recipe_data['Input'])
            if input_modified:
                modified = True
                changes.extend(input_changes)
            recipe_data['Input'] = new_input

        # Process the Process array
        if 'Process' in recipe_data:
            process_modified, process_changes = \
                _sort_process_array(
                    recipe_data['Process'],
                    processor_position='last'
                )
            if process_modified:
                modified = True
                changes.extend(process_changes)

        if modified:
            ordered_recipe = _build_ordered_recipe(recipe_data)

            # Write back to file
            with open(recipe_path, 'wb') as f:
                plistlib.dump(ordered_recipe, f, sort_keys=False)

            _fix_plist_formatting(recipe_path, original_indent_type)

        return modified, changes

    except Exception as e:
        print(f"Error processing {recipe_path}: {e}")
        traceback.print_exc()
        return False, []


def process_yaml_recipe(recipe_path):
    """Process a YAML recipe file and alphabetize appropriate sections.

    Args:
        recipe_path: Path to the recipe file

    Returns:
        Tuple of (modified: bool, changes: list)
    """
    try:
        import yaml

        with open(recipe_path, 'r', encoding='utf-8') as f:
            recipe_data = yaml.safe_load(f)

        changes = []
        modified = False

        # Alphabetize Input dict if it exists
        if 'Input' in recipe_data:
            input_modified, input_changes, new_input = \
                _sort_input_section(recipe_data['Input'])
            if input_modified:
                modified = True
                changes.extend(input_changes)
            recipe_data['Input'] = new_input

        # Process the Process array
        if 'Process' in recipe_data:
            process_modified, process_changes = \
                _sort_process_array(
                    recipe_data['Process'],
                    processor_position='first'
                )
            if process_modified:
                modified = True
                changes.extend(process_changes)

        if modified:
            ordered_recipe = _build_ordered_recipe(recipe_data)

            # Write back to file with proper formatting
            dumper = AutoPkgYAMLDumper.get_dumper()
            with open(recipe_path, 'w', encoding='utf-8') as f:
                yaml.dump(
                    ordered_recipe, f,
                    Dumper=dumper,
                    default_flow_style=False,
                    allow_unicode=True,
                    sort_keys=False,
                    indent=2,
                    width=120
                )

        return modified, changes

    except ImportError:
        print(f"Error: PyYAML not available for processing {recipe_path}")
        print("YAML recipes will be skipped")
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


def _collect_recipes(recipe_dir):
    """Collect all recipe files from directory.

    Args:
        recipe_dir: Path to recipe directory

    Returns:
        List of recipe paths
    """
    all_recipes = []
    for recipe_path in Path(recipe_dir).rglob("*.recipe*"):
        if recipe_path.suffix in ['.recipe', '.yaml']:
            all_recipes.append(recipe_path)
    return all_recipes


def _get_batch_size(all_recipes):
    """Get batch size from user input.

    Args:
        all_recipes: List of all recipe paths

    Returns:
        Batch size as integer
    """
    print("\nBatch processing options:")
    print("  1. Process all files at once")
    print(
        "  2. Process in batches "
        "(you'll be prompted between batches)"
    )
    print("Enter your choice (1-2): ", end='', flush=True)

    batch_choice = input().strip()

    if batch_choice == '2':
        print(
            "\nEnter batch size "
            "(number of files to process before pausing): ",
            end='', flush=True
        )
        try:
            batch_size = int(input().strip())
            if batch_size < 1:
                print("Invalid batch size. Using batch size of 10.")
                batch_size = 10
        except ValueError:
            print("Invalid input. Using batch size of 10.")
            batch_size = 10
    else:
        batch_size = len(all_recipes)

    return batch_size


def _process_batch(batch, recipe_count):
    """Process a batch of recipes.

    Args:
        batch: List of recipe paths to process
        recipe_count: Current recipe count

    Returns:
        Tuple of (updated_count, modified_list)
    """
    batch_modified = []
    count = recipe_count

    for recipe_path in batch:
        count += 1
        modified, changes = process_recipe(recipe_path)

        if modified:
            batch_modified.append((recipe_path, changes))
            print(f"\n✓ Alphabetized {recipe_path.name}")
            for change in changes:
                print(f"  - {change}")
        else:
            print(
                f"Skipping {recipe_path.name} - already alphabetized"
            )

    return count, batch_modified


def _print_summary(recipe_count, modified_count, modified_files):
    """Print final summary of processing.

    Args:
        recipe_count: Total recipes processed
        modified_count: Number of recipes modified
        modified_files: List of (path, changes) tuples
    """
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
            "\nPlease verify these files in your "
            "version control system."
        )
    else:
        print("\n✓ All recipes are already properly alphabetized!")


def main():
    verify_environment()

    print("RecipeAlphabetiser - AutoPkg Recipe Key Sorter")
    print("=" * 50)
    print("This script will:")
    print("1. Alphabetize keys in the Input dict")
    print("2. Alphabetize keys in the pkginfo dict (munki recipes)")
    print("3. Alphabetize keys in each Process step")
    print("4. Keep 'Processor' key last in each processor")
    print("5. Preserve Process array order")
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
            print(
                "Make sure the path exists and you have "
                "permission to access it."
            )
            return

        print(f"\nScanning recipes in: {recipe_dir}")

        all_recipes = _collect_recipes(recipe_dir)

        if not all_recipes:
            print("No recipe files found.")
            return

        print(f"Found {len(all_recipes)} recipe file(s)")

        batch_size = _get_batch_size(all_recipes)

        modified_count = 0
        recipe_count = 0
        modified_files = []
        batch_num = 0

        # Process recipes in batches
        for i in range(0, len(all_recipes), batch_size):
            batch = all_recipes[i:i + batch_size]
            batch_num += 1

            if batch_size < len(all_recipes):
                print(f"\n{'=' * 50}")
                print(
                    f"Processing batch {batch_num} "
                    f"({len(batch)} file(s))"
                )
                print("=" * 50)

            recipe_count, batch_modified = _process_batch(
                batch, recipe_count
            )
            modified_count += len(batch_modified)
            modified_files.extend(batch_modified)

            # If there are more batches, ask if they want to continue
            if i + batch_size < len(all_recipes):
                print(f"\n{'=' * 50}")
                print(
                    f"Batch {batch_num} complete: "
                    f"{len(batch_modified)} file(s) modified"
                )
                print(
                    f"Remaining: "
                    f"{len(all_recipes) - i - batch_size} file(s)"
                )
                print("=" * 50)
                print("\nReview the changes above, then:")
                print("  Press ENTER to continue to next batch")
                print("  Type 'q' or 'quit' to stop")
                print("Your choice: ", end='', flush=True)

                user_input = input().strip().lower()
                if user_input in ['q', 'quit']:
                    print("\nStopping at user request.")
                    break

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

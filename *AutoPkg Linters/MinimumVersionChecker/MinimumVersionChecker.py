#!/usr/local/autopkg/python
"""
Script to check and set MinimumVersion based on processors used in recipes.
Analyzes all processors and sets MinimumVersion to highest required version.
Supports both plist and yaml recipe formats.
Requires AutoPkg's Python installation.
"""

import os
import sys
import yaml
from pathlib import Path
import re
import traceback
import urllib.request


# URL to fetch the latest processor versions from pre-commit-macadmin
PROCESSOR_VERSIONS_URL = (
    "https://raw.githubusercontent.com/homebysix/"
    "pre-commit-macadmin/main/pre_commit_macadmin_hooks/"
    "check_autopkg_recipes.py"
)

# Fallback processor versions if fetching fails
# Source: homebysix/pre-commit-macadmin validate_minimumversion function
FALLBACK_PROCESSOR_VERSIONS = {
    'AppDmgVersioner': '0.0',
    'AppPkgCreator': '1.0',
    'BrewCaskInfoProvider': '0.2.5',
    'CodeSignatureVerifier': '0.3.1',
    'Copier': '0.0',
    'CURLDownloader': '0.5.1',
    'CURLTextSearcher': '0.5.1',
    'DeprecationWarning': '1.1',
    'DmgCreator': '0.0',
    'DmgMounter': '0.0',
    'EndOfCheckPhase': '0.1.0',
    'FileCreator': '0.0',
    'FileFinder': '0.2.3',
    'FileMover': '0.2.9',
    'FindAndReplace': '2.7.6',
    'FlatPkgPacker': '0.2.4',
    'FlatPkgUnpacker': '0.1.0',
    'GitHubReleasesInfoProvider': '0.5.0',
    'Installer': '0.4.0',
    'InstallFromDMG': '0.4.0',
    'MunkiCatalogBuilder': '0.1.0',
    'MunkiImporter': '0.1.0',
    'MunkiInfoCreator': '0.0',
    'MunkiInstallsItemsCreator': '0.1.0',
    'MunkiOptionalReceiptEditor': '2.7',
    'MunkiPkginfoMerger': '0.1.0',
    'MunkiSetDefaultCatalog': '0.4.2',
    'PackageRequired': '0.5.1',
    'PathDeleter': '0.1.0',
    'PkgCopier': '0.1.0',
    'PkgCreator': '0.0',
    'PkgExtractor': '0.1.0',
    'PkgInfoCreator': '0.0',
    'PkgPayloadUnpacker': '0.1.0',
    'PkgRootCreator': '0.0',
    'PlistEditor': '0.1.0',
    'PlistReader': '0.2.5',
    'SignToolVerifier': '2.3',
    'SparkleUpdateInfoProvider': '0.1.0',
    'StopProcessingIf': '0.1.0',
    'Symlinker': '0.1.0',
    'Unarchiver': '0.1.0',
    'URLDownloader': '0.0',
    'URLDownloaderPython': '2.4.1',
    'URLTextSearcher': '0.2.9',
    'Versioner': '0.1.0',
}

# Message constant
FALLBACK_MESSAGE = "Using fallback processor versions"


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


def fetch_processor_versions():
    """Fetch the latest processor versions from pre-commit-macadmin.

    Returns:
        Dictionary of processor names to minimum versions
    """
    print("\nFetching latest processor versions from GitHub...")

    try:
        with urllib.request.urlopen(
                PROCESSOR_VERSIONS_URL, timeout=10) as response:
            content = response.read().decode('utf-8')

        # Extract the PROCESSOR_NAMES dictionary from the Python file
        # Look for the pattern: PROCESSOR_NAMES = {
        match = re.search(
            r'PROCESSOR_NAMES\s*=\s*\{([^}]+)\}',
            content,
            re.DOTALL
        )

        if not match:
            print("Warning: Could not find PROCESSOR_NAMES in source file")
            print(FALLBACK_MESSAGE)
            return FALLBACK_PROCESSOR_VERSIONS

        dict_content = match.group(1)

        # Parse the dictionary entries
        # Pattern: "ProcessorName": "version",
        processor_versions = {}
        pattern = r'"([^"]+)":\s*"([^"]+)"'

        for match in re.finditer(pattern, dict_content):
            processor_name = match.group(1)
            version = match.group(2)
            processor_versions[processor_name] = version

        if processor_versions:
            print(f"Successfully fetched {len(processor_versions)} "
                  f"processor versions")
            return processor_versions
        else:
            print("Warning: No processor versions found in source file")
            print(FALLBACK_MESSAGE)
            return FALLBACK_PROCESSOR_VERSIONS

    except urllib.error.URLError as e:
        print(f"Warning: Failed to fetch processor versions: {e}")
        print(FALLBACK_MESSAGE)
        return FALLBACK_PROCESSOR_VERSIONS
    except Exception as e:
        print(f"Warning: Error parsing processor versions: {e}")
        print(FALLBACK_MESSAGE)
        return FALLBACK_PROCESSOR_VERSIONS


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


def get_highest_version(versions):
    """Get the highest version from a list of version strings."""
    if not versions:
        return None

    highest = versions[0]
    for version in versions[1:]:
        if compare_versions(version, highest) > 0:
            highest = version

    return highest


def extract_processors_from_yaml(content):
    """Extract all core processor names from YAML recipe content.

    Ignores shared/custom processors (those with slashes or domain patterns).
    Only returns core AutoPkg processors.
    """
    try:
        recipe = yaml.safe_load(content)
    except yaml.YAMLError as e:
        print(f"DEBUG: Error parsing YAML: {e}")
        return []

    processors = []
    if 'Process' in recipe and isinstance(recipe['Process'], list):
        for step in recipe['Process']:
            if isinstance(step, dict) and 'Processor' in step:
                processor_name = step['Processor']
                # Skip shared/custom processors (contain / or domain patterns)
                if '/' in processor_name or '.' in processor_name:
                    print(
                        f"DEBUG: Skipping shared/custom processor: "
                        f"{processor_name}")
                    continue
                processors.append(processor_name)

    return processors


def extract_processors_from_plist(content):
    """Extract all core processor names from plist recipe content.

    Ignores shared/custom processors (those with slashes or domain patterns).
    Only returns core AutoPkg processors.
    """
    processors = []

    # Find all Processor key-string pairs
    processor_pattern = (r'<key>Processor</key>\s*\n\s*'
                         r'<string>(.*?)</string>')

    matches = re.finditer(processor_pattern, content, re.DOTALL)
    for match in matches:
        processor_name = match.group(1).strip()
        # Skip shared/custom processors (contain / or domain patterns)
        if '/' in processor_name or '.' in processor_name:
            print(
                f"DEBUG: Skipping shared/custom processor: "
                f"{processor_name}")
            continue
        processors.append(processor_name)

    return processors


def get_current_minimum_version(content, is_yaml):
    """Get the current MinimumVersion from recipe content."""
    if is_yaml:
        try:
            recipe = yaml.safe_load(content)
            return recipe.get('MinimumVersion', None)
        except yaml.YAMLError:
            return None
    else:
        # Extract from plist
        pattern = (r'<key>MinimumVersion</key>\s*\n\s*'
                   r'<string>(.*?)</string>')
        match = re.search(pattern, content, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None


def update_yaml_minimum_version(content, new_version):
    """Update MinimumVersion in YAML content."""
    try:
        recipe = yaml.safe_load(content)
        recipe['MinimumVersion'] = new_version

        # Use yaml.dump to update, but preserve as much formatting as possible
        # by doing line-by-line replacement
        lines = content.splitlines()
        new_lines = []
        updated = False

        for line in lines:
            if line.strip().startswith('MinimumVersion:'):
                indent = len(line) - len(line.lstrip())
                new_lines.append(
                    ' ' * indent + f'MinimumVersion: {new_version}')
                updated = True
            else:
                new_lines.append(line)

        if not updated:
            # Add MinimumVersion at the beginning (after any comments)
            insert_index = 0
            for i, line in enumerate(lines):
                if line.strip() and not line.strip().startswith('#'):
                    insert_index = i
                    break

            lines.insert(insert_index, f'MinimumVersion: {new_version}')
            return '\n'.join(lines) + '\n', True

        return '\n'.join(new_lines) + '\n', True

    except yaml.YAMLError as e:
        print(f"DEBUG: Error updating YAML: {e}")
        return content, False


def update_plist_minimum_version(content, new_version):
    """Update MinimumVersion in plist content."""
    # Pattern that captures the entire MinimumVersion key-value pair
    # preserving all whitespace
    pattern = (r'(<key>MinimumVersion</key>\s*\n\s*)'
               r'<string>.*?</string>')

    match = re.search(pattern, content, re.DOTALL)

    if match:
        # Update existing MinimumVersion
        # Preserve everything up to and including whitespace before <string>
        prefix = match.group(1)
        replacement = prefix + f'<string>{new_version}</string>'
        content = content.replace(match.group(0), replacement)
        return content, True
    else:
        # Add MinimumVersion - position depends on recipe type
        # Try to find ParentRecipe key first
        # Match only the line with ParentRecipe, capturing indent
        parent_pattern = r'\n(\s*)<key>ParentRecipe</key>'
        parent_match = re.search(parent_pattern, content)

        if parent_match:
            # Insert before ParentRecipe (after the newline before it)
            indent = parent_match.group(1)
            insertion = (f'{indent}<key>MinimumVersion</key>\n'
                         f'{indent}<string>{new_version}</string>\n')
            # Insert after the newline, before the indentation and key
            insert_pos = parent_match.start() + 1  # +1 to skip the \n
            content = content[:insert_pos] + insertion + content[insert_pos:]
            return content, True

        # No ParentRecipe, so likely a download recipe
        # Insert before Process key
        process_pattern = r'\n(\s*)<key>Process</key>'
        process_match = re.search(process_pattern, content)

        if process_match:
            # Insert before Process (after the newline before it)
            indent = process_match.group(1)
            insertion = (f'{indent}<key>MinimumVersion</key>\n'
                         f'{indent}<string>{new_version}</string>\n')
            # Insert after the newline, before the indentation and key
            insert_pos = process_match.start() + 1  # +1 to skip the \n
            content = content[:insert_pos] + insertion + content[insert_pos:]
            return content, True

        # Fallback: insert after opening <dict> (original behavior)
        dict_pattern = (r'(<\?xml.*?>\s*<!DOCTYPE.*?>\s*'
                        r'<plist.*?>\s*<dict>)')
        dict_match = re.search(dict_pattern, content, re.DOTALL)

        if dict_match:
            indent = '    '
            insertion = (f'\n{indent}<key>MinimumVersion</key>\n'
                         f'{indent}<string>{new_version}</string>')

            content = content.replace(
                dict_match.group(1),
                dict_match.group(1) + insertion
            )
            return content, True

    return content, False


def process_recipe(recipe_path, processor_versions):
    """Process a single recipe file and check MinimumVersion.

    Args:
        recipe_path: Path to the recipe file
        processor_versions: Dictionary of processor version requirements
    """
    try:
        is_yaml = recipe_path.suffix == '.yaml'
        print(f"\nDEBUG: Processing {recipe_path}")
        print(f"DEBUG: File type: {'YAML' if is_yaml else 'plist'}")

        # Read original content
        with open(recipe_path, 'r', encoding='utf-8') as file:
            original_content = file.read()
            print(f"DEBUG: Original content length: {len(original_content)}")

        # Extract processors
        if is_yaml:
            processors = extract_processors_from_yaml(original_content)
        else:
            processors = extract_processors_from_plist(original_content)

        if not processors:
            print(f"Skipping {recipe_path.name} - no processors found")
            return False, None, None

        print(
            f"DEBUG: Found {len(processors)} processor(s): "
            f"{', '.join(processors)}")

        # Get required versions for all processors
        required_versions = []
        for processor in processors:
            if processor in processor_versions:
                version = processor_versions[processor]
                required_versions.append(version)
                print(f"DEBUG: {processor} requires version {version}")

        if not required_versions:
            print(
                f"Skipping {recipe_path.name} - no version requirements "
                f"found")
            return False, None, None

        # Get highest required version
        highest_required = get_highest_version(required_versions)
        print(f"DEBUG: Highest required version: {highest_required}")

        # Get current MinimumVersion
        current_version = get_current_minimum_version(original_content,
                                                      is_yaml)
        print(f"DEBUG: Current MinimumVersion: {current_version}")

        # Compare versions
        if current_version:
            comparison = compare_versions(current_version, highest_required)
            if comparison >= 0:
                print(
                    f"No modification needed - current version "
                    f"{current_version} >= required {highest_required}")
                return False, current_version, highest_required

        # Update MinimumVersion
        print(f"DEBUG: Updating MinimumVersion to {highest_required}")

        if is_yaml:
            modified_content, was_modified = update_yaml_minimum_version(
                original_content, highest_required)
        else:
            modified_content, was_modified = update_plist_minimum_version(
                original_content, highest_required)

        if not was_modified:
            print(f"Failed to update MinimumVersion in {recipe_path.name}")
            return False, current_version, highest_required

        # Write the changes
        print(f"DEBUG: Writing changes to: {recipe_path}")
        with open(recipe_path, 'w', encoding='utf-8') as file:
            file.write(modified_content)

        # Verify the changes
        with open(recipe_path, 'r', encoding='utf-8') as file:
            verification_content = file.read()

        if verification_content != modified_content:
            print(
                f"❌ Warning: File write verification failed for "
                f"{recipe_path}")
            return False, current_version, highest_required

        # Verify new version is set correctly
        new_version = get_current_minimum_version(verification_content,
                                                  is_yaml)
        if new_version != highest_required:
            print(
                f"❌ Warning: Verification failed - MinimumVersion is "
                f"{new_version}, expected {highest_required}")
            return False, current_version, highest_required

        print(f"✓ Successfully updated MinimumVersion: {recipe_path}")
        return True, current_version, highest_required

    except Exception as e:
        print(f"❌ Error processing {recipe_path}: {str(e)}")
        print("DEBUG: Full error details:")
        print(traceback.format_exc())
        return False, None, None


def main():
    verify_environment()

    print("MinimumVersionChecker - AutoPkg Recipe Version Validator")
    print("=" * 50)
    print("This script will:")
    print("1. Fetch latest processor versions from GitHub")
    print("2. Analyze all processors used in recipes")
    print("3. Determine highest required AutoPkg version")
    print("4. Set MinimumVersion to required version")
    print("5. Skip recipes already meeting requirements")
    print("=" * 50)

    # Fetch the latest processor versions
    processor_versions = fetch_processor_versions()

    print("\nEnter the path to your recipe directory")
    print("(You can drag and drop the folder here): ", end='', flush=True)

    try:
        recipe_dir = clean_path(input())
        recipe_dir = os.path.abspath(recipe_dir)

        if not os.path.isdir(recipe_dir):
            print(f"Error: '{recipe_dir}' is not a valid directory")
            print(
                "Make sure the path exists and you have permission "
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
                success, old_version, new_version = process_recipe(
                    recipe_path, processor_versions)
                if success:
                    modified_count += 1
                    modified_files.append((recipe_path, old_version,
                                          new_version))

        print(f"\n{'=' * 50}")
        print("Processing complete!")
        print(f"Recipes processed: {recipe_count}")
        print(f"Recipes modified: {modified_count}")
        print("=" * 50)

        if modified_files:
            print("\nModified files:")
            for file, old_ver, new_ver in modified_files:
                old_display = old_ver if old_ver else "not set"
                print(f"  ✓ {file}")
                print(f"    {old_display} → {new_ver}")

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

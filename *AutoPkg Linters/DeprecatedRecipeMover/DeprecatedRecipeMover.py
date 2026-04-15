#!/usr/local/autopkg/python
"""
Script to move deprecated AutoPkg recipes based on deprecation age.
Checks for DeprecationWarning processor and last commit date.
Moves recipes (and parent folders if all recipes are deprecated) to a
'*Deprecated and to be deleted' folder.
Requires AutoPkg's Python installation and git repository.
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
import re
import traceback

# Constants
YAML_EXTENSION = '.yaml'
DEPRECATED_FOLDER_NAME = '*Deprecated and to be deleted'


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


def is_git_repository(path):
    """Check if the path is within a git repository."""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--git-dir'],
            cwd=path,
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode == 0
    except Exception:
        return False


def get_last_commit_date(file_path, repo_path):
    """Get the last commit date for a specific file.

    Args:
        file_path: Path to the file
        repo_path: Path to the git repository root

    Returns:
        datetime object of last commit, or None if not in git
    """
    try:
        result = subprocess.run(
            ['git', 'log', '-1', '--format=%ct', '--', str(file_path)],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode == 0 and result.stdout.strip():
            timestamp = int(result.stdout.strip())
            return datetime.fromtimestamp(timestamp)
        return None
    except Exception as e:
        print(f"Warning: Could not get commit date for {file_path}: {e}")
        return None


def has_deprecation_warning_plist(content):
    """Check if plist recipe has DeprecationWarning processor."""
    try:
        # Look for DeprecationWarning processor in the Process array
        pattern = r'<key>Processor</key>\s*<string>DeprecationWarning</string>'
        return bool(re.search(pattern, content))
    except Exception:
        return False


def has_deprecation_warning_yaml(content):
    """Check if YAML recipe has DeprecationWarning processor."""
    try:
        # Look for Processor: DeprecationWarning
        pattern = r'Processor:\s*DeprecationWarning'
        return bool(re.search(pattern, content))
    except Exception:
        return False


def has_deprecation_warning(file_path):
    """Check if recipe has DeprecationWarning processor.

    Args:
        file_path: Path to the recipe file

    Returns:
        Boolean indicating if DeprecationWarning is present
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if file_path.suffix == YAML_EXTENSION:
            return has_deprecation_warning_yaml(content)
        else:
            return has_deprecation_warning_plist(content)
    except Exception as e:
        print(f"Error checking {file_path}: {e}")
        return False


def get_time_period_choice():
    """Prompt user to select a time period for deprecation age."""
    print("\nSelect deprecation age threshold:")
    print("1. 1 month")
    print("2. 3 months")
    print("3. 6 months")
    print("4. 12 months (1 year)")
    print("5. Custom (enter number of months)")
    print("\nEnter your choice (1-5): ", end='', flush=True)

    try:
        choice = input().strip()

        if choice == '1':
            return 1
        elif choice == '2':
            return 3
        elif choice == '3':
            return 6
        elif choice == '4':
            return 12
        elif choice == '5':
            print("Enter number of months: ", end='', flush=True)
            months = int(input().strip())
            if months < 1:
                print("Error: Must be at least 1 month")
                return None
            return months
        else:
            print("Error: Invalid choice")
            return None
    except ValueError:
        print("Error: Invalid input")
        return None
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return None


def should_move_recipe(file_path, repo_path, months_threshold):
    """Determine if a recipe should be moved.

    Args:
        file_path: Path to the recipe file
        repo_path: Path to the git repository root
        months_threshold: Number of months for deprecation threshold

    Returns:
        Tuple of (should_move: bool, reason: str, commit_date: datetime)
    """
    # Check if recipe has DeprecationWarning
    if not has_deprecation_warning(file_path):
        return False, "No DeprecationWarning processor", None

    # Get last commit date
    commit_date = get_last_commit_date(file_path, repo_path)
    if commit_date is None:
        return False, "No commit history found", None

    # Calculate age
    age = datetime.now() - commit_date
    threshold = timedelta(days=months_threshold * 30)

    if age >= threshold:
        months_old = age.days // 30
        return True, f"Deprecated for {months_old} months", commit_date
    else:
        months_old = age.days // 30
        return False, f"Only deprecated for {months_old} months", commit_date


def get_all_recipes_in_folder(folder_path):
    """Get all recipe files in a folder (non-recursive).

    Args:
        folder_path: Path to the folder

    Returns:
        List of recipe file paths
    """
    recipes = []
    for item in folder_path.iterdir():
        if item.is_file() and item.suffix in ['.recipe', YAML_EXTENSION]:
            recipes.append(item)
    return recipes


def should_move_folder(folder_path, repo_path, months_threshold):
    """Check if entire folder should be moved (all recipes deprecated).

    Args:
        folder_path: Path to the folder
        repo_path: Path to the git repository root
        months_threshold: Number of months for deprecation threshold

    Returns:
        Tuple of (should_move: bool, recipe_count: int)
    """
    recipes = get_all_recipes_in_folder(folder_path)

    if not recipes:
        return False, 0

    # Check if all recipes should be moved
    all_should_move = True
    for recipe in recipes:
        should_move, _, _ = should_move_recipe(recipe, repo_path,
                                               months_threshold)
        if not should_move:
            all_should_move = False
            break

    return all_should_move, len(recipes)


def move_recipe(recipe_path, repo_path):
    """Move a recipe to '*Deprecated and to be deleted' folder
    maintaining structure.

    Args:
        recipe_path: Path to the recipe file
        repo_path: Path to the git repository root

    Returns:
        Path to the new location, or None if failed
    """
    try:
        # Calculate relative path from repo root
        relative_path = recipe_path.relative_to(repo_path)

        # Create destination path in '*Deprecated and to be deleted' folder
        deprecated_folder = Path(repo_path) / DEPRECATED_FOLDER_NAME
        dest_path = deprecated_folder / relative_path

        # Create parent directories if needed
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        # Move the file
        recipe_path.rename(dest_path)

        return dest_path
    except Exception as e:
        print(f"Error moving {recipe_path}: {e}")
        return None


def move_folder(folder_path, repo_path):
    """Move an entire folder to '*Deprecated and to be deleted'
    maintaining structure.

    Args:
        folder_path: Path to the folder
        repo_path: Path to the git repository root

    Returns:
        Path to the new location, or None if failed
    """
    try:
        # Calculate relative path from repo root
        relative_path = folder_path.relative_to(repo_path)

        # Create destination path in '*Deprecated and to be deleted' folder
        deprecated_folder = Path(repo_path) / DEPRECATED_FOLDER_NAME
        dest_path = deprecated_folder / relative_path

        # Move the entire folder
        folder_path.rename(dest_path)

        return dest_path
    except Exception as e:
        print(f"Error moving folder {folder_path}: {e}")
        return None


def scan_recipes(repo_path, months_threshold):
    """Scan repository for deprecated recipes to move.

    Args:
        repo_path: Path to the git repository root
        months_threshold: Number of months for deprecation threshold

    Returns:
        Dict with recipes_to_move, folders_to_move lists
    """
    recipes_to_move = []
    folders_to_move = []
    folders_processed = set()

    # Find all recipe files
    for recipe_path in Path(repo_path).rglob("*.recipe*"):
        if recipe_path.suffix not in ['.recipe', YAML_EXTENSION]:
            continue

        # Skip if already in '*Deprecated and to be deleted'
        if DEPRECATED_FOLDER_NAME in recipe_path.parts:
            continue

        # Check if parent folder should be moved (if not already processed)
        parent_folder = recipe_path.parent
        if parent_folder not in folders_processed:
            folders_processed.add(parent_folder)

            should_move, recipe_count = should_move_folder(
                parent_folder, repo_path, months_threshold
            )

            if should_move and recipe_count > 1:
                # Move entire folder
                folders_to_move.append((parent_folder, recipe_count))
                continue

        # Check individual recipe
        should_move, reason, commit_date = should_move_recipe(
            recipe_path, repo_path, months_threshold
        )

        if should_move:
            recipes_to_move.append((recipe_path, reason, commit_date))

    return {
        'recipes': recipes_to_move,
        'folders': folders_to_move
    }


def confirm_moves(recipes, folders):
    """Ask user to confirm the moves.

    Args:
        recipes: List of (recipe_path, reason, commit_date) tuples
        folders: List of (folder_path, recipe_count) tuples

    Returns:
        Boolean indicating if user confirmed
    """
    total_count = len(recipes) + sum(count for _, count in folders)

    if total_count == 0:
        print("\nNo recipes found that meet the criteria.")
        return False

    print(f"\nFound {total_count} deprecated recipe(s) to move:")
    print("=" * 50)

    if folders:
        print("\nFolders to move (all recipes deprecated):")
        for folder, count in folders:
            print(f"  📁 {folder.name}/ ({count} recipes)")

    if recipes:
        print("\nIndividual recipes to move:")
        for recipe, reason, commit_date in recipes:
            date_str = (
                commit_date.strftime('%Y-%m-%d') if commit_date
                else 'Unknown'
            )
            print(
                f"  📄 {recipe.name} - {reason} (Last commit: {date_str})"
            )

    print("\n" + "=" * 50)
    print(
        "These will be moved to a '*Deprecated and to be deleted' folder "
        "maintaining their structure."
    )
    print("\nProceed with moving these recipes? (y/n): ", end='',
          flush=True)

    try:
        response = input().strip().lower()
        return response in ['y', 'yes']
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return False


def main():
    verify_environment()

    print("DeprecatedRecipeMover - AutoPkg Recipe Organizer")
    print("=" * 50)
    print("This script will:")
    print("1. Find recipes with DeprecationWarning processor")
    print("2. Check their last commit date")
    print("3. Move old deprecated recipes to '*Deprecated and to be deleted'")
    print("4. Move entire folders if all recipes are deprecated")
    print("=" * 50)
    print("\nEnter the path to your recipe repository")
    print("(You can drag and drop the folder here): ", end='', flush=True)

    try:
        repo_path = clean_path(input())
        repo_path = os.path.abspath(repo_path)

        if not os.path.isdir(repo_path):
            print(f"Error: '{repo_path}' is not a valid directory")
            print("Make sure the path exists and you have permission "
                  "to access it.")
            return

        # Verify this is a git repository
        if not is_git_repository(repo_path):
            print(f"\nError: '{repo_path}' is not a git repository")
            print("This script requires git history to determine "
                  "deprecation age.")
            return

        print(f"\n✓ Git repository found: {repo_path}")

        # Get time period selection
        months = get_time_period_choice()
        if months is None:
            return

        print(f"\n✓ Will move recipes deprecated for {months} month(s) "
              f"or longer")
        print("\nScanning repository for deprecated recipes...")

        # Scan for recipes to move
        results = scan_recipes(repo_path, months)

        # Confirm with user
        if not confirm_moves(results['recipes'], results['folders']):
            print("\nOperation cancelled - no files were moved")
            return

        # Perform moves
        print("\nMoving files...")
        moved_count = 0
        failed_count = 0

        # Move folders first
        for folder, count in results['folders']:
            new_path = move_folder(folder, repo_path)
            if new_path:
                print(f"✓ Moved folder: {folder.name}/ → "
                      f"{new_path.relative_to(repo_path)}")
                moved_count += count
            else:
                print(f"✗ Failed to move folder: {folder.name}/")
                failed_count += count

        # Move individual recipes
        for recipe, reason, commit_date in results['recipes']:
            new_path = move_recipe(recipe, repo_path)
            if new_path:
                print(f"✓ Moved: {recipe.name} → "
                      f"{new_path.relative_to(repo_path)}")
                moved_count += 1
            else:
                print(f"✗ Failed to move: {recipe.name}")
                failed_count += 1

        print(f"\n{'=' * 50}")
        print("Move operation complete!")
        print(f"Recipes moved: {moved_count}")
        if failed_count > 0:
            print(f"Failed moves: {failed_count}")
        print("=" * 50)

        print("\nIMPORTANT: Review the changes and commit them to git:")
        print(f"  cd {repo_path}")
        print("  git status")
        print("  git add .")
        print('  git commit -m "Move deprecated recipes to _Deprecated"')

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

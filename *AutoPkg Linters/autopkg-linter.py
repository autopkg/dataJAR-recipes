#!/usr/local/autopkg/python
"""
AutoPkg Recipe Linter Suite - Command Line Tool

Runs individual or all AutoPkg recipe linters in sequence.
Provides a unified interface to all linting tools.

Available linters:
1. GitHubPreReleaseChecker - Add pre-release support to GitHub recipes
2. DeprecationChecker - Validate deprecated recipe configuration
3. DetabChecker - Convert tabs to spaces and fix whitespace
4. CommentKeyChecker - Convert HTML comments to Comment keys
5. UninstallScriptChecker - Validate uninstall_script configuration
6. MinimumVersionChecker - Set correct MinimumVersion
7. DeprecatedRecipeMover - Move old deprecated recipes
8. RecipeAlphabetiser - Alphabetize recipe keys
9. MunkiPathDeleterChecker - Ensure PathDeleter cleanup
10. MunkiInstallsItemsCreatorChecker
    - Validate MunkiInstallsItemsCreator config
11. FindAndReplaceChecker - Convert shared FindAndReplace to core
12. AutoPkgXMLEscapeChecker - Ensure proper XML character escaping
13. ChecksumVerifierChanger - Update ChecksumVerifier pathname argument
14. NAMEChecker - Remove spaces from NAME input variable values
15. MissingKeyValueChecker - Check for empty values in pkginfo dict
16. DuplicateKeyChecker - Detect duplicate keys and fix duplicates
17. zshChecker - Ensure zsh shebangs include --no-rcs flag
18. OverridePkgReceiptChecker - Ensure uninstall scripts forget pkg receipts

Usage:
    Run all linters:
        /usr/local/autopkg/python autopkg-linter.py --all /path/to/recipes

    Run specific linters:
        /usr/local/autopkg/python autopkg-linter.py
            --linters 3,6,8 /path/to/recipes

    Interactive mode:
        /usr/local/autopkg/python autopkg-linter.py
"""

import os
import sys
import argparse
from pathlib import Path
import importlib.util


def verify_environment():
    """Verify we're running in AutoPkg's Python environment."""
    autopkg_python = '/usr/local/autopkg/python'
    if not sys.executable.startswith('/usr/local/autopkg'):
        print("Error: This script should be run using AutoPkg's "
              "Python installation.")
        print(f"Please run this script using: {autopkg_python} "
              "<script_name.py>")
        sys.exit(1)


def get_script_dir():
    """Get the directory where this script is located."""
    return Path(__file__).parent.absolute()


def get_available_linters():
    """Get list of available linters with their details.

    Returns:
        List of tuples: (number, name, directory, script_file, description)
    """
    script_dir = get_script_dir()

    linters = [
        (1, "GitHubPreReleaseChecker", "GitHubPreReleaseChecker",
         "GitHubPreReleaseChecker.py",
         "Add include_prereleases support to GitHub recipes"),
        (2, "DeprecationChecker", "DeprecationChecker",
         "DeprecationChecker.py",
         "Validate deprecated recipe configuration"),
        (3, "DetabChecker", "DetabChecker",
         "DetabChecker.py",
         "Convert tabs to spaces and fix whitespace"),
        (4, "CommentKeyChecker", "CommentKeyChecker",
         "CommentKeyChecker.py",
         "Convert HTML comments to Comment keys"),
        (5, "UninstallScriptChecker", "UninstallScriptChecker",
         "UninstallScriptChecker.py",
         "Validate uninstall_script configuration"),
        (6, "MinimumVersionChecker", "MinimumVersionChecker",
         "MinimumVersionChecker.py",
         "Set correct MinimumVersion based on processors"),
        (7, "DeprecatedRecipeMover", "DeprecatedRecipeMover",
         "DeprecatedRecipeMover.py",
         "Move old deprecated recipes to archive folder"),
        (8, "RecipeAlphabetiser", "RecipeAlphabetiser",
         "RecipeAlphabetiser.py",
         "Alphabetize Input, pkginfo, and processor keys"),
        (9, "MunkiPathDeleterChecker", "MunkiPathDeleterChecker",
         "MunkiPathDeleterChecker.py",
         "Ensure PathDeleter cleanup for unpacking"),
        (10, "MunkiInstallsItemsCreatorChecker",
         "MunkiInstallsItemsCreatorChecker",
         "MunkiInstallsItemsCreatorChecker.py",
         "Validate MunkiInstallsItemsCreator configuration"),
        (11, "FindAndReplaceChecker", "FindAndReplaceChecker",
         "FindAndReplaceChecker.py",
         "Convert shared FindAndReplace to core processor"),
        (12, "AutoPkgXMLEscapeChecker", "AutoPkgXMLEscapeChecker",
         "AutoPkgXMLEscapeChecker.py",
         "Ensure proper XML character escaping (&, <, >)"),
        (13, "ChecksumVerifierChanger", "ChecksumVerifierChanger",
         "ChecksumVerifierChanger.py",
         "Change pathname to checksum_pathname in ChecksumVerifier"),
        (14, "NAMEChecker", "NAMEChecker",
         "NAMEChecker.py",
         "Remove spaces from NAME input variable values"),
        (15, "MissingKeyValueChecker", "MissingKeyValueChecker",
         "MissingKeyValueChecker.py",
         "Check for empty values in pkginfo dict (.munki recipes)"),
        (16, "DuplicateKeyChecker", "DuplicateKeyChecker",
         "DuplicateKeyChecker.py",
         "Detect duplicate keys and fix duplicate unattended_install"),
        (17, "zshChecker", "zshChecker",
         "zshChecker.py",
         "Ensure zsh shebangs include --no-rcs flag"),
        (18, "OverridePkgReceiptChecker", "OverridePkgReceiptChecker",
         "OverridePkgReceiptChecker.py",
         "Ensure uninstall scripts forget pkg receipts from EAs"),
    ]

    # Verify each linter exists
    available = []
    for num, name, directory, script, desc in linters:
        linter_path = script_dir / directory / script
        if linter_path.exists():
            available.append((num, name, directory, script, desc))
        else:
            print(f"Warning: Linter {name} not found at {linter_path}")

    return available


def load_linter_module(linter_path):
    """Load a linter module dynamically.

    Args:
        linter_path: Path to the linter script

    Returns:
        Loaded module or None if failed
    """
    try:
        spec = importlib.util.spec_from_file_location("linter", linter_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        print(f"Error loading linter: {e}")
        return None


def _get_bulk_response(call_num, linter_name, prompt,
                       recipe_dir):
    """Determine automatic response for bulk mode.

    Args:
        call_num: The input call sequence number
        linter_name: Name of the current linter
        prompt: The prompt text from the linter
        recipe_dir: Path to recipe directory

    Returns:
        String response to provide to the linter
    """
    if call_num == 1:
        return recipe_dir

    prompt_lower = prompt.lower()

    # Special handling for OverridePkgReceiptChecker (needs private-recipes path)
    # Call 1: overrides directory (handled by call_num == 1 above)
    # Call 2: private-recipes directory (handled here)
    if linter_name == "OverridePkgReceiptChecker" and call_num == 2:
        # Try to find private-recipes as a sibling directory
        from pathlib import Path
        recipe_path = Path(recipe_dir)
        parent_dir = recipe_path.parent

        # Look for private-recipes in parent directory
        private_recipes = parent_dir / "private-recipes"
        if private_recipes.exists() and private_recipes.is_dir():
            return str(private_recipes)

        # If not found, print warning and skip this linter
        print("\n" + "=" * 70)
        print("⚠️  WARNING: Could not auto-locate private-recipes directory")
        print(f"    Looked for: {private_recipes}")
        print("    This linter requires BOTH directories to function.")
        print("    Please re-run with interactive mode (option 1) or")
        print("    run this linter standalone with both paths.")
        print("=" * 70)
        # Raise to skip linter rather than calling sys.exit
        # (sys.exit is mocked and would be caught by the
        # linter's own exception handler instead of ours)
        raise _LinterExit(1)

    # Batch mode selection (RecipeAlphabetiser)
    is_alphabetiser = (
        call_num == 2
        and linter_name == "RecipeAlphabetiser"
    )
    if is_alphabetiser or "(1-2)" in prompt:
        return "1"

    # Threshold choice (DeprecatedRecipeMover)
    is_mover_threshold = (
        call_num == 2
        and linter_name == "DeprecatedRecipeMover"
    )
    if is_mover_threshold or "choice (1-5)" in prompt_lower:
        return "3"

    # Confirmation prompts
    is_mover_confirm = (
        call_num == 3
        and linter_name == "DeprecatedRecipeMover"
    )
    is_proceed = (
        "proceed" in prompt_lower
        and "(y/n)" in prompt_lower
    )
    if (is_mover_confirm or is_proceed
            or "stopprocessingif" in prompt_lower):
        return "y"

    # Default: skip optional operations
    return "n"


class _LinterExit(BaseException):
    """Raised when a linter calls sys.exit().

    Extends BaseException (like SystemExit) so it is not caught
    by generic 'except Exception' handlers within linter scripts.
    """

    def __init__(self, code):
        self.code = code
        super().__init__(code)


def _execute_linter(module, name):
    """Execute a linter module's main function.

    Temporarily overrides sys.exit to avoid catching
    SystemExit directly.

    Args:
        module: The loaded linter module
        name: Name of the linter

    Returns:
        Boolean indicating success
    """
    original_exit = sys.exit

    def _mock_exit(code=0):
        raise _LinterExit(code)

    sys.exit = _mock_exit
    try:
        module.main()
        print(
            f"\n✓ {name} completed successfully"
        )
        return True
    except _LinterExit as e:
        if e.code == 0:
            print(
                f"\n✓ {name} completed "
                "successfully"
            )
            return True
        print(
            f"\n✗ {name} exited with "
            f"code {e.code}"
        )
        return False
    except Exception as e:
        print(
            f"\n✗ {name} failed with error: {e}"
        )
        import traceback
        traceback.print_exc()
        return False
    finally:
        sys.exit = original_exit


def run_linter(linter_info, recipe_dir, run_mode='bulk'):
    """Run a single linter.

    Args:
        linter_info: Tuple of (num, name, directory, script, desc)
        recipe_dir: Path to recipe directory
        run_mode: 'bulk' or 'interactive' mode

    Returns:
        Boolean indicating success
    """
    num, name, directory, script, desc = linter_info
    script_dir = get_script_dir()
    linter_path = script_dir / directory / script

    print("\n" + "=" * 70)
    print(f"Running Linter #{num}: {name}")
    print(f"Description: {desc}")
    print("=" * 70)

    try:
        module = load_linter_module(linter_path)
        if not module:
            print(f"✗ Failed to load {name}")
            return False

        if not hasattr(module, 'main'):
            print(
                f"✗ {name} does not have a main() "
                "function"
            )
            return False

        original_argv = sys.argv
        sys.argv = [str(linter_path)]
        original_input = __builtins__.input

        if run_mode == 'bulk':
            input_calls = [0]

            def mock_input(prompt=""):
                print(prompt, end='', flush=True)
                input_calls[0] += 1
                response = _get_bulk_response(
                    input_calls[0], name,
                    prompt, recipe_dir
                )
                print(response)
                return response

            __builtins__.input = mock_input
        else:
            input_calls = [0]

            def partial_mock_input(prompt=""):
                print(prompt, end='', flush=True)
                input_calls[0] += 1
                if input_calls[0] == 1:
                    print(recipe_dir)
                    __builtins__.input = original_input
                    return recipe_dir
                # Fallback to original input
                return original_input(prompt)

            __builtins__.input = partial_mock_input

        try:
            success = _execute_linter(module, name)
        finally:
            sys.argv = original_argv
            __builtins__.input = original_input

        return success

    except Exception as e:
        print(f"\n✗ Error running {name}: {e}")
        import traceback
        traceback.print_exc()
        return False


def display_linter_menu(linters):
    """Display available linters in a menu.

    Args:
        linters: List of linter tuples
    """
    print("\nAvailable Linters:")
    print("=" * 70)
    for num, name, _, _, desc in linters:
        print(f"{num:2d}. {name}")
        print(f"    {desc}")
    print("=" * 70)


def _clean_recipe_dir(raw_path):
    """Clean and validate a recipe directory path.

    Args:
        raw_path: Raw path string (may include escapes)

    Returns:
        Cleaned absolute path string
    """
    path = raw_path.strip().strip('"').strip("'")
    path = path.replace(r'\ ', ' ')
    path = path.replace(r'\*', '*')
    path = path.rstrip(' ').rstrip('/')
    path = os.path.expanduser(path)
    path = os.path.abspath(path)
    if not os.path.isdir(path):
        print(
            f"Error: '{path}' is not a valid directory"
        )
        sys.exit(1)
    return path


def _parse_linter_numbers(text, linters):
    """Parse comma-separated linter numbers.

    Args:
        text: Comma-separated number string
        linters: Available linter list

    Returns:
        List of selected linter tuples
    """
    try:
        nums = [
            int(x.strip()) for x in text.split(',')
        ]
    except ValueError:
        return None

    selected = [
        linter for linter in linters
        if linter[0] in nums
    ]
    return selected if selected else None


def _run_and_summarize(selected_linters, recipe_dir,
                       run_mode):
    """Run linters and display summary.

    Args:
        selected_linters: List of linter tuples to run
        recipe_dir: Path to recipe directory
        run_mode: 'bulk' or 'interactive'
    """
    results = []
    for linter in selected_linters:
        success = run_linter(
            linter, recipe_dir, run_mode
        )
        results.append((linter[1], success))

    print("\n" + "=" * 70)
    print("LINTER SUITE SUMMARY")
    print("=" * 70)

    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status:8s} {name}")

    print("=" * 70)

    passed = sum(1 for _, s in results if s)
    total = len(results)
    print(
        f"\nResults: {passed}/{total} linters "
        "completed successfully"
    )

    if passed < total:
        sys.exit(1)


def _ask_run_mode():
    """Ask user for run mode preference.

    Returns:
        'interactive' or 'bulk'
    """
    print("\nRun mode:")
    print("  1. Interactive (linter prompts)")
    print("  2. Bulk (automatic responses)")
    print(
        "\nYour choice (1 or 2): ",
        end='', flush=True
    )
    mode_choice = input().strip()
    if mode_choice == '1':
        return 'interactive'
    return 'bulk'


def interactive_mode():
    """Run in interactive mode."""
    verify_environment()

    print("AutoPkg Recipe Linter Suite")
    print("=" * 70)

    linters = get_available_linters()
    if not linters:
        print("Error: No linters found")
        sys.exit(1)

    display_linter_menu(linters)

    print("\nOptions:")
    print("  - Enter 'all' to run all linters")
    print("  - Enter linter numbers (e.g., 3,6,8)")
    print("  - Enter 'q' to quit")
    print("\nYour choice: ", end='', flush=True)

    choice = input().strip().lower()

    if choice == 'q':
        print("Exiting...")
        sys.exit(0)

    if choice == 'all':
        selected_linters = linters
        run_mode = 'bulk'
    else:
        selected_linters = _parse_linter_numbers(
            choice, linters
        )
        if not selected_linters:
            print(
                "Error: Invalid input. "
                "Use numbers separated by commas"
            )
            sys.exit(1)

        if len(selected_linters) == 1:
            run_mode = _ask_run_mode()
        else:
            run_mode = 'bulk'

    print("\nEnter the path to your recipe directory")
    print(
        "(You can drag and drop the folder here): ",
        end='', flush=True
    )
    recipe_dir = _clean_recipe_dir(input())

    count = len(selected_linters)
    print(
        f"\nRunning {count} linter(s) "
        f"in {run_mode} mode on: {recipe_dir}"
    )

    _run_and_summarize(
        selected_linters, recipe_dir, run_mode
    )


def command_line_mode(args):
    """Run in command line mode with arguments.

    Args:
        args: Parsed command line arguments
    """
    verify_environment()

    linters = get_available_linters()
    if not linters:
        print("Error: No linters found")
        sys.exit(1)

    recipe_dir = os.path.abspath(args.recipe_dir)
    if not os.path.isdir(recipe_dir):
        print(
            f"Error: '{recipe_dir}' is not a "
            "valid directory"
        )
        sys.exit(1)

    if args.all:
        selected_linters = linters
    elif args.linters:
        selected_linters = _parse_linter_numbers(
            args.linters, linters
        )
        if not selected_linters:
            print(
                "Error: Invalid linter numbers. "
                "Use format: 1,3,5"
            )
            sys.exit(1)
    else:
        print("Error: Must specify --all or --linters")
        print("Use --help for usage information")
        sys.exit(1)

    print("AutoPkg Recipe Linter Suite")
    print("=" * 70)
    count = len(selected_linters)
    print(
        f"Running {count} linter(s) on: {recipe_dir}"
    )

    _run_and_summarize(
        selected_linters, recipe_dir, 'bulk'
    )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description=(
            'AutoPkg Recipe Linter Suite'
            ' - Run recipe validation tools'
        ),
        formatter_class=(
            argparse.RawDescriptionHelpFormatter
        ),
        epilog="""
Examples:
  # Interactive mode
  %(prog)s

  # Run all linters
  %(prog)s --all /path/to/recipes

  # Run specific linters (by number)
  %(prog)s --linters 3,6,8 /path/to/recipes

  # List available linters
  %(prog)s --list

Available Linters:
  1. GitHubPreReleaseChecker
  2. DeprecationChecker
  3. DetabChecker
  4. CommentKeyChecker
  5. UninstallScriptChecker
  6. MinimumVersionChecker
  7. DeprecatedRecipeMover
  8. RecipeAlphabetiser
  9. MunkiPathDeleterChecker
  10. MunkiInstallsItemsCreatorChecker
  11. FindAndReplaceChecker
        """
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='Run all available linters'
    )

    parser.add_argument(
        '--linters',
        type=str,
        help=(
            'Comma-separated list of linter '
            'numbers to run (e.g., 1,3,5)'
        )
    )

    parser.add_argument(
        '--list',
        action='store_true',
        help='List available linters and exit'
    )

    parser.add_argument(
        'recipe_dir',
        nargs='?',
        help='Path to recipe directory'
    )

    args = parser.parse_args()

    if args.list:
        verify_environment()
        linters = get_available_linters()
        display_linter_menu(linters)
        sys.exit(0)

    if len(sys.argv) == 1:
        interactive_mode()
    else:
        if not args.recipe_dir:
            parser.error(
                "recipe_dir is required when "
                "using --all or --linters"
            )
        command_line_mode(args)


if __name__ == '__main__':
    main()

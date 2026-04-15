# AutoPkg Recipe Linter Suite

A comprehensive command-line tool for validating and fixing AutoPkg recipes. Run individual linters or the entire suite with a single command.

## Features

- **Unified Interface**: Run all 16 linters through one command
- **Flexible Execution**: Run all linters at once or select specific ones
- **Interactive Mode**: Easy-to-use menu for selecting linters
- **Batch Processing**: Process entire recipe repositories efficiently
- **Clear Reporting**: Detailed summary of all linter results

## Available Linters

The suite includes 16 specialized linters:

1. **GitHubPreReleaseChecker** - Add `include_prereleases` support to GitHub recipes
2. **DeprecationChecker** - Validate deprecated recipe configuration
3. **DetabChecker** - Convert tabs to spaces and fix whitespace issues
4. **CommentKeyChecker** - Convert HTML comments to proper Comment keys
5. **UninstallScriptChecker** - Validate `uninstall_script` configuration
6. **MinimumVersionChecker** - Set correct MinimumVersion based on processors
7. **DeprecatedRecipeMover** - Move old deprecated recipes to archive folder
8. **RecipeAlphabetiser** - Alphabetize Input, pkginfo, and processor keys (dependency-aware)
9. **MunkiPathDeleterChecker** - Ensure PathDeleter cleanup for unpacking
10. **MunkiInstallsItemsCreatorChecker** - Validate MunkiInstallsItemsCreator configuration
11. **FindAndReplaceChecker** - Convert shared FindAndReplace to core processor
12. **AutoPkgXMLEscapeChecker** - Ensure proper XML character escaping
13. **ChecksumVerifierChanger** - Update ChecksumVerifier pathname argument
14. **NAMEChecker** - Remove spaces from NAME input variable values
15. **MissingKeyValueChecker** - Check for empty values in pkginfo dict
16. **DuplicateKeyChecker** - Detect duplicate keys and auto-fix duplicate unattended_install

## Installation

1. Ensure AutoPkg is installed with Python at `/usr/local/autopkg/python`
2. Place all linter directories in the same parent folder
3. Place `autopkg-linter.py` in the parent folder alongside the linter directories

Directory structure:
```
AutoPkg Linters/
├── autopkg-linter.py                    # Main suite runner
├── GItHubPreReleaseChecker/
│   ├── GItHubPreReleaseChecker.py
│   └── README.md
├── DeprecationChecker/
│   ├── DeprecationChecker.py
│   └── README.md
├── DetabChecker/
│   ├── DetabChecker.py
│   └── README.md
├── CommentKeyChecker/
│   ├── CommentKeyChecker.py
│   └── README.md
├── UninstallScriptChecker/
│   ├── UninstallScriptChecker.py
│   └── README.md
├── MinimumVersionChecker/
│   ├── MinimumVersionChecker.py
│   └── README.md
├── DeprecatedRecipeMover/
│   ├── DeprecatedRecipeMover.py
│   └── README.md
├── RecipeAlphabetiser/
│   ├── RecipeAlphabetiser.py
│   └── README.md
├── MunkiPathDeleterChecker/
│   ├── MunkiPathDeleterChecker.py
│   └── README.md
├── MunkiInstallsItemsCreatorChecker/
│   ├── MunkiInstallsItemsCreatorChecker.py
│   └── README.md
├── FindAndReplaceChecker/
│   ├── FindAndReplaceChecker.py
│   └── README.md
├── AutoPkgXMLEscapeChecker/
│   ├── AutoPkgXMLEscapeChecker.py
│   └── README.md
├── ChecksumVerifierChanger/
│   ├── ChecksumVerifierChanger.py
│   └── README.md
├── NAMEChecker/
│   ├── NAMEChecker.py
│   └── README.md
├── MissingKeyValueChecker/
│   ├── MissingKeyValueChecker.py
│   └── README.md
├── DuplicateKeyChecker/
│   ├── DuplicateKeyChecker.py
│   └── README.md
└── zshChecker/
    ├── zshChecker.py
    └── README.md
```

## Usage

### Interactive Mode

Run without arguments for an interactive menu:

```bash
/usr/local/autopkg/python autopkg-linter.py
```

You'll be prompted to:
1. Select which linters to run (by number or 'all')
2. Provide the path to your recipe directory

### Command Line Mode

#### Run All Linters

```bash
/usr/local/autopkg/python autopkg-linter.py --all /path/to/recipes
```

#### Run Specific Linters

Run selected linters by number (comma-separated):

```bash
# Run DetabChecker, MinimumVersionChecker, and RecipeAlphabetiser
/usr/local/autopkg/python autopkg-linter.py --linters 3,6,8 /path/to/recipes
```

#### List Available Linters

```bash
/usr/local/autopkg/python autopkg-linter.py --list
```

### Drag and Drop Support

You can drag and drop your recipe directory into the terminal when prompted for the path.

## Examples

### Quick Cleanup Before Committing

Run the essential formatting and validation linters:

```bash
# DetabChecker + MinimumVersionChecker + RecipeAlphabetiser
/usr/local/autopkg/python autopkg-linter.py --linters 3,6,8 ~/autopkg-recipes
```

### New Recipe Repository Setup

Add all enhancements to a new recipe repo:

```bash
/usr/local/autopkg/python autopkg-linter.py --all ~/new-recipe-repo
```

### Munki-Specific Validation

Run Munki-focused linters:

```bash
# UninstallScriptChecker + MunkiPathDeleterChecker + MunkiInstallsItemsCreator
/usr/local/autopkg/python autopkg-linter.py --linters 5,9,10 ~/munki-recipes
```

### Pre-Commit Workflow

Quick validation before committing:

```bash
# CommentKeyChecker + DetabChecker + RecipeAlphabetiser
/usr/local/autopkg/python autopkg-linter.py --linters 4,3,8 ~/autopkg-recipes
```

## Output

The tool provides detailed output for each linter and a summary at the end:

```
======================================================================
Running Linter #3: DetabChecker
Description: Convert tabs to spaces and fix whitespace
======================================================================

Scanning recipes in: /Users/username/recipes
Processing: Firefox.munki.recipe
  ✓ Converted 2 tabs to spaces
  ✓ Removed trailing whitespace from 3 lines
  ✓ Added final newline

✓ DetabChecker completed successfully

======================================================================
LINTER SUITE SUMMARY
======================================================================
✓ PASS   GitHubPreReleaseChecker
✓ PASS   DetabChecker
✗ FAIL   MinimumVersionChecker
✓ PASS   RecipeAlphabetiser
======================================================================

Results: 3/4 linters completed successfully
```

## Recommended Usage Order

For best results, run linters in this recommended order:

1. **DetabChecker** (3) - Fix formatting first
2. **CommentKeyChecker** (4) - Convert comments
3. **DeprecationChecker** (2) - Add deprecation warnings
4. **MinimumVersionChecker** (6) - Set version requirements
5. **GitHubPreReleaseChecker** (1) - Add pre-release support
6. **UninstallScriptChecker** (5) - Validate uninstall config
7. **MunkiPathDeleterChecker** (9) - Add PathDeleter cleanup
8. **MunkiInstallsItemsCreator** (10) - Validate installs creator
9. **RecipeAlphabetiser** (8) - Alphabetize keys (run last)
10. **DeprecatedRecipeMover** (7) - Archive old recipes (manual)

The suite runs linters in the order specified, so you can control the sequence.

## Integration with Git

### Pre-Commit Hook

Create a pre-commit hook to automatically lint recipes:

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Get list of modified .recipe and .yaml files
RECIPES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(recipe|yaml)$')

if [ -n "$RECIPES" ]; then
    echo "Running AutoPkg linters on modified recipes..."

    # Run essential linters
    /usr/local/autopkg/python ~/Scripts/autopkg-linter.py \
        --linters 3,6,8 \
        "$(pwd)"

    if [ $? -ne 0 ]; then
        echo "Linting failed. Please fix errors before committing."
        exit 1
    fi

    # Re-stage modified files
    git add $RECIPES
fi

exit 0
```

Make it executable:
```bash
chmod +x .git/hooks/pre-commit
```

### Batch Processing Multiple Repositories

Process all your recipe repositories:

```bash
#!/bin/bash
# lint-all-repos.sh

REPOS=(
    ~/autopkg-recipes
    ~/munki-recipes
    ~/company-recipes
)

for repo in "${REPOS[@]}"; do
    echo "Processing $repo..."
    /usr/local/autopkg/python ~/Scripts/autopkg-linter.py \
        --linters 3,6,8 \
        "$repo"
done
```

## CI/CD Integration

### GitHub Actions

Add to `.github/workflows/lint-recipes.yml`:

```yaml
name: Lint AutoPkg Recipes

on:
  pull_request:
    paths:
      - '**.recipe'
      - '**.yaml'

jobs:
  lint:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v2

      - name: Install AutoPkg
        run: |
          curl -L https://github.com/autopkg/autopkg/releases/latest/download/autopkg-latest.pkg -o /tmp/autopkg.pkg
          sudo installer -pkg /tmp/autopkg.pkg -target /

      - name: Clone Linter Suite
        run: |
          git clone https://github.com/your-org/autopkg-linters.git ~/linters

      - name: Run Linters
        run: |
          /usr/local/autopkg/python ~/linters/autopkg-linter.py \
            --linters 3,6,8 \
            "${{ github.workspace }}"
```

## Special Considerations

### DeprecatedRecipeMover

The **DeprecatedRecipeMover** (linter #7) requires interactive input for the deprecation threshold and is skipped in batch mode. Run it individually when needed:

```bash
cd DeprecatedRecipeMover
/usr/local/autopkg/python DeprecatedRecipeMover.py
```

### Order Matters for Some Linters

- Run **DetabChecker** before **RecipeAlphabetiser** to ensure consistent formatting
- Run **MinimumVersionChecker** after adding new processors
- Run **RecipeAlphabetiser** last to ensure all keys are properly ordered

### Dry Run Testing

Each individual linter can be run separately for testing:

```bash
cd DetabChecker
/usr/local/autopkg/python DetabChecker.py
```

This is useful for:
- Testing changes before running the full suite
- Understanding what each linter does
- Troubleshooting specific issues

## Exit Codes

- `0` - All selected linters completed successfully
- `1` - One or more linters failed
- `1` - Invalid arguments or configuration

Use exit codes in scripts:

```bash
if /usr/local/autopkg/python autopkg-linter.py --linters 3,6,8 ~/recipes; then
    echo "Linting passed!"
    git commit -m "Updated recipes"
else
    echo "Linting failed, please review"
fi
```

## Troubleshooting

### Linter Not Found

```
Warning: Linter DetabChecker not found at /path/to/DetabChecker/DetabChecker.py
```

**Solution**: Ensure all linter directories are in the same parent folder as `autopkg-linter.py`

### Wrong Python Version

```
Error: This script should be run using AutoPkg's Python installation.
```

**Solution**: Use `/usr/local/autopkg/python` to run the script:
```bash
/usr/local/autopkg/python autopkg-linter.py --all ~/recipes
```

### Permission Denied

```
Error: Permission denied when writing to recipes
```

**Solution**: Ensure you have write permissions to the recipe directory:
```bash
chmod -R u+w ~/recipes
```

### Import Errors

```
Error loading linter: No module named 'yaml'
```

**Solution**: Install required modules in AutoPkg's Python:
```bash
/usr/local/autopkg/python -m pip install PyYAML
```

## Performance

- **Single Recipe**: < 1 second per linter
- **100 Recipes**: 30-60 seconds for all linters
- **1000 Recipes**: 5-10 minutes for all linters

Performance tips:
- Run only needed linters with `--linters`
- Process subdirectories separately for large repositories
- Use file patterns to limit scope (modify linters to accept file patterns)

## Best Practices

1. **Start Small**: Test on a single recipe before processing entire repos
2. **Version Control**: Always commit before running linters
3. **Review Changes**: Check git diff after running linters
4. **Regular Use**: Integrate into your workflow, not just one-time cleanup
5. **Selective Running**: Don't run all linters if you only need specific fixes
6. **Documentation**: Read individual linter READMEs for detailed behavior

## Limitations

- **DeprecatedRecipeMover** requires manual interaction
- Some linters modify recipe files in place
- No rollback mechanism (use version control)
- Processes entire directory, not individual files
- All linters must be present (no partial suite)

## Individual Linter Documentation

Each linter has detailed documentation in its own README:

- [GitHubPreReleaseChecker/README.md](GItHubPreReleaseChecker/README.md)
- [DeprecationChecker/README.md](DeprecationChecker/README.md)
- [DetabChecker/README.md](DetabChecker/README.md)
- [CommentKeyChecker/README.md](CommentKeyChecker/README.md)
- [UninstallScriptChecker/README.md](UninstallScriptChecker/README.md)
- [MinimumVersionChecker/README.md](MinimumVersionChecker/README.md)
- [DeprecatedRecipeMover/README.md](DeprecatedRecipeMover/README.md)
- [RecipeAlphabetiser/README.md](RecipeAlphabetiser/README.md)
- [MunkiPathDeleterChecker/README.md](MunkiPathDeleterChecker/README.md)
- [MunkiInstallsItemsCreatorChecker/README.md](MunkiInstallsItemsCreatorChecker/README.md)
- [FindAndReplaceChecker/README.md](FindAndReplaceChecker/README.md)
- [AutoPkgXMLEscapeChecker/README.md](AutoPkgXMLEscapeChecker/README.md)
- [ChecksumVerifierChanger/README.md](ChecksumVerifierChanger/README.md)
- [NAMEChecker/README.md](NAMEChecker/README.md)
- [MissingKeyValueChecker/README.md](MissingKeyValueChecker/README.md)
- [DuplicateKeyChecker/README.md](DuplicateKeyChecker/README.md)
- [zshChecker/README.md](zshChecker/README.md)

## Contributing

When adding new linters to the suite:

1. Create linter directory with script and README
2. Add entry to `get_available_linters()` in `autopkg-linter.py`
3. Ensure linter has a `main()` function
4. Test with `--list` to verify it appears
5. Update this README with new linter information

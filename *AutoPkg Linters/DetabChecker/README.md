# DetabChecker

An AutoPkg utility script that automatically converts tab characters to spaces in recipe files, removes trailing whitespace from lines, and ensures files end with a single newline. This script ensures all recipes follow AutoPkg formatting standards.

## Features

- **Automatic Tab Detection**: Scans all recipe files for tab characters
- **Consistent Conversion**: Converts all tabs to exactly 4 spaces
- **Trailing Whitespace Removal**: Strips trailing spaces from the end of lines
- **Final Newline Enforcement**: Ensures files end with a single newline character
- **Multi-Format Support**: Handles both plist (`.recipe`) and YAML (`.yaml`) recipe formats
- **Batch Processing**: Processes multiple recipes in a single run
- **Detailed Reporting**: Shows exactly what issues were fixed in each file
- **Safe Modifications**: Preserves all content and formatting except whitespace issues

## Why Use 4 Spaces and Clean Whitespace?

Following AutoPkg and Python community standards:

- **Consistency**: Ensures recipes look the same in all editors
- **Version Control**: Reduces noise in diffs caused by mixed indentation and whitespace
- **PEP 8 Compliance**: Follows Python's official style guide
- **Editor Independence**: Avoids tab width configuration issues
- **Readability**: Predictable formatting across all environments
- **Clean Files**: No invisible trailing spaces that cause diff noise

## What It Does

The script performs three important formatting tasks:

1. **Tab Conversion**: Reads each recipe file, detects tab characters (`\t`), and replaces each with 4 spaces
2. **Trailing Whitespace**: Removes any spaces or tabs at the end of lines
3. **Final Newline**: Ensures the file ends with exactly one newline character
4. Writes the corrected content back to the file
5. Verifies the changes were successful

### Before
```xml
<dict>
→   <key>Processor</key>···
→   <string>URLDownloader</string>
</dict>[EOF]
```
*(→ represents a tab, · represents trailing space, [EOF] indicates no final newline)*

### After
```xml
<dict>
    <key>Processor</key>
    <string>URLDownloader</string>
</dict>
```
*(4 spaces, no trailing whitespace, ends with newline)*

## Requirements

- **AutoPkg**: Must be installed with its bundled Python environment at `/usr/local/autopkg/python`
- **Python 3**: Included with AutoPkg installation
- **No external dependencies**: Uses only Python standard library

## Installation

1. Download `DetabChecker.py` to a convenient location
2. Make the script executable (optional):
   ```bash
   chmod +x DetabChecker.py
   ```

## Usage

### Running the Script

Execute the script using AutoPkg's Python installation:

```bash
/usr/local/autopkg/python DetabChecker.py
```

### Interactive Prompt

When run, the script will prompt for a recipe directory:

```
DetabChecker - AutoPkg Recipe Whitespace Fixer
==================================================
This script will:
1. Scan recipes for tab characters
2. Convert all tabs to 4 spaces
3. Remove trailing whitespace from lines
4. Ensure files end with a newline
==================================================

Enter the path to your recipe directory
(You can drag and drop the folder here):
```

You can either:
- Type the full path to your recipe directory
- Drag and drop a folder from Finder

### Example Session

```
Enter the path to your recipe directory
(You can drag and drop the folder here): /Users/username/autopkg/recipes

Scanning recipes in: /Users/username/autopkg/recipes

Found issues in /Users/username/autopkg/recipes/App.download.recipe: 45 tab(s), trailing whitespace, missing final newline
DEBUG: Converting 45 tab character(s)
DEBUG: Removing trailing whitespace
DEBUG: Adding final newline
✓ Fixed App.download.recipe: converted 45 tab(s) to spaces, removed trailing whitespace, added final newline

==================================================
Processing complete!
Recipes processed: 10
Recipes modified: 3
==================================================

Modified files:
  ✓ App.download.recipe: converted 45 tab(s) to spaces, removed trailing whitespace, added final newline
  ✓ Another.pkg.recipe: removed trailing whitespace, added final newline
  ✓ Third.munki.recipe: converted 2 tab(s) to spaces

Please verify these files in your version control system.
```

## Output Details

The script provides comprehensive information:

- **Per-file issue detection**: Lists all issues found (tabs, trailing whitespace, missing newline)
- **Fix summary**: Shows what corrections were applied to each file
- **Verification status**: Confirms each file was successfully updated
- **Skip notifications**: Indicates which files have no issues (already correct)

## When to Use DetabChecker

### Ideal Use Cases

- ✅ **After importing recipes** from external sources
- ✅ **Before committing** changes to version control
- ✅ **Regular maintenance** to ensure consistency
- ✅ **After manual editing** in different editors
- ✅ **Repository cleanup** projects
- ✅ **Pre-release checks** to ensure clean whitespace
- ✅ **CI/CD integration** for automated validation

### Preventive Measures

After running DetabChecker, configure your editor to use spaces:

**VS Code**:
```json
{
    "editor.insertSpaces": true,
    "editor.tabSize": 4,
    "files.trimTrailingWhitespace": true,
    "files.insertFinalNewline": true
}
```

**Sublime Text**:
```json
{
    "translate_tabs_to_spaces": true,
    "tab_size": 4,
    "trim_trailing_white_space_on_save": true,
    "ensure_newline_at_eof_on_save": true
}
```

**Atom**:
```coffeescript
"*":
  editor:
    tabType: "soft"
    tabLength: 4
  whitespace:
    removeTrailingWhitespace: true
    ensureSingleTrailingNewline: true
```

## Safety Features

- **Non-Destructive**: Only modifies files with whitespace issues
- **Verification**: Validates file writes to ensure accuracy
- **Skip Logic**: Automatically skips files without issues
- **Environment Check**: Ensures it runs in AutoPkg's Python environment
- **Error Handling**: Clear error messages with full tracebacks
- **Content Preservation**: Only changes whitespace, nothing else
- **Line Ending Preservation**: Maintains existing line endings (LF or CRLF)

## Integration with Other Tools

DetabChecker works well alongside:

- **GitHubPreReleaseChecker**: Run DetabChecker after to ensure proper spacing
- **DeprecationChecker**: Run DetabChecker after to clean up any tab issues
- **Pre-commit hooks**: Add DetabChecker to automated workflows
- **CI/CD pipelines**: Validate recipes before merging

## Troubleshooting

### Script Won't Run

**Error**: `This script should be run using AutoPkg's Python installation`

**Solution**: Use the full path to AutoPkg's Python:
```bash
/usr/local/autopkg/python DetabChecker.py
```

### No Issues Found

If no recipes are modified:
- ✅ Your recipes already have clean whitespace (good!)
- Check that you're scanning the correct directory
- Verify files have `.recipe` or `.yaml` extensions

### File Write Failed

If verification fails:
1. Check file permissions
2. Ensure the file isn't locked by another process
3. Verify disk space is available

### Mixed Indentation Issues

If recipes have both tabs AND irregular spacing:
1. Run DetabChecker first to remove tabs and fix whitespace
2. Manually review indentation levels if needed
3. Consider using an XML/YAML formatter for complex cases

### Trailing Whitespace Detection

DetabChecker finds trailing whitespace by:
- Checking each line for spaces/tabs at the end
- Preserving line endings (LF or CRLF)
- Only removing the actual trailing whitespace characters

## Command Line Tips

Drag and drop folder from Finder:
```
Enter the path to your recipe directory
(You can drag and drop the folder here): [drag folder here]
```

The script automatically handles:
- Spaces in directory names
- Escaped characters
- Trailing slashes
- Home directory shortcuts (`~`)

## Pre-Commit Hook Example

Automate whitespace checking with a git pre-commit hook:

```bash
#!/bin/bash
# .git/hooks/pre-commit

RECIPES=$(git diff --cached --name-only --diff-filter=ACM | grep '\.recipe')

if [ -n "$RECIPES" ]; then
    for recipe in $RECIPES; do
        # Check for tabs
        if grep -q $'\t' "$recipe"; then
            echo "Error: Tabs found in $recipe"
            echo "Run DetabChecker.py to fix this issue"
            exit 1
        fi
        
        # Check for trailing whitespace
        if grep -q '[[:space:]]$' "$recipe"; then
            echo "Error: Trailing whitespace found in $recipe"
            echo "Run DetabChecker.py to fix this issue"
            exit 1
        fi
        
        # Check for final newline
        if [ -n "$(tail -c 1 "$recipe")" ]; then
            echo "Error: Missing final newline in $recipe"
            echo "Run DetabChecker.py to fix this issue"
            exit 1
        fi
    done
fi
```

## Statistics and Reporting

The script tracks:

- **Total recipes scanned**: All `.recipe` and `.yaml` files found
- **Recipes modified**: Files that had whitespace issues
- **Issues fixed**: Tabs converted, trailing whitespace removed, final newlines added
- **Per-file details**: Individual fixes applied to each file

This helps identify:
- Which files had the most formatting issues
- Overall repository code quality
- Progress in maintaining standards
- Common whitespace problems in your workflow

## File Format Support

| Format | Extension | Support |
|--------|-----------|---------|
| Plist | `.recipe` | ✅ Full |
| YAML | `.recipe.yaml` | ✅ Full |
| Other | `.yaml` | ✅ Full |

## Best Practices

1. **Run Before Committing**: Always check for whitespace issues before pushing changes
2. **Configure Your Editor**: Set up your editor to use spaces and trim whitespace automatically
3. **Regular Maintenance**: Run periodically to catch any issues
4. **Review Changes**: Check diffs in version control after running
5. **Team Standards**: Share this tool with collaborators
6. **Automate Checks**: Add to pre-commit hooks or CI/CD pipelines

## Performance

DetabChecker is highly efficient:

- **Fast Processing**: Simple string operations
- **Low Memory**: Processes one file at a time
- **No Dependencies**: No external libraries to install
- **Instant Results**: Provides immediate feedback
- **Multi-Issue Detection**: Checks tabs, trailing whitespace, and newlines in one pass

Typical performance:
- ~100 recipes: < 5 seconds
- ~1000 recipes: < 30 seconds

## Limitations

- Only processes `.recipe` and `.yaml` files
- Converts all tabs to 4 spaces (not configurable)
- Does not fix other indentation issues (only tabs and trailing whitespace)
- Does not validate XML/YAML syntax
- Preserves existing line endings (doesn't normalize LF vs CRLF)

## Advanced Usage

### Process Specific File Types Only

Modify the glob pattern in the script:
```python
# Only .recipe files
for recipe_path in Path(recipe_dir).rglob("*.recipe"):

# Only .yaml files
for recipe_path in Path(recipe_dir).rglob("*.yaml"):
```

### Different Space Count

Modify the `spaces_per_tab` parameter:
```python
modified_content = convert_tabs_to_spaces(original_content, spaces_per_tab=2)
```

## Related Tools

- **EditorConfig**: Define consistent coding styles across editors
- **Prettier**: Code formatter for various file types
- **autopkg-linter**: Additional recipe validation tools
- **xmllint**: XML syntax validation and formatting

## Contributing

When modifying this script:

1. Test with both plist and YAML recipes
2. Verify all whitespace detection works correctly
3. Ensure 4-space conversion is accurate
4. Test trailing whitespace removal
5. Verify final newline enforcement
6. Test with files containing various content and line endings
7. Update this README with changes

## References

- [PEP 8 - Style Guide for Python Code](https://www.python.org/dev/peps/pep-0008/)
- [AutoPkg Documentation](https://github.com/autopkg/autopkg/wiki)
- [EditorConfig](https://editorconfig.org/)

## Author

Paul Cossey

## Version History

- **Current**: Tab-to-space conversion, trailing whitespace removal, and final newline enforcement

---

For more information about AutoPkg recipe formatting standards, visit [https://github.com/autopkg/autopkg](https://github.com/autopkg/autopkg)

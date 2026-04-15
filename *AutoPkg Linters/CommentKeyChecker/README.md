# CommentKeyChecker

An AutoPkg utility script that converts HTML-style comments (`<!-- -->`) to proper `Comment` key-string pairs in recipe files. This ensures recipes follow AutoPkg standards while preserving inline documentation.

## Features

- **Automatic Comment Detection**: Finds all HTML-style comments in recipes
- **Proper Key-String Conversion**: Converts to standard Comment format
- **Multi-Format Support**: Handles both plist (`.recipe`) and YAML (`.yaml`) formats
- **Indentation Preservation**: Maintains original indentation level
- **4-Space Standard**: Ensures spaces (not tabs) are used
- **Batch Processing**: Processes multiple recipes in a single run
- **Detailed Reporting**: Shows exactly how many comments were converted

## Why Convert HTML Comments?

HTML-style comments in AutoPkg recipes have several issues:

- **Not Standard**: AutoPkg recipes should use key-string pairs
- **Processing Issues**: Can interfere with plist/XML parsing in some tools
- **Inconsistent**: Mixing comment styles reduces code clarity
- **Best Practice**: Using `Comment` keys is the recommended approach
- **Tool Compatibility**: Ensures compatibility with all AutoPkg tools

## What It Does

The script performs a precise conversion:

1. Scans recipe files for HTML-style comments
2. Extracts the comment text
3. Creates a proper `Comment` key-string pair
4. Maintains the exact indentation and location
5. Uses 4 spaces for indentation

### Plist Format

#### Before
```xml
<dict>
    <key>Processor</key>
    <string>URLDownloader</string>
    <!-- This downloads the latest version -->
    <key>Arguments</key>
    <dict>
```

#### After
```xml
<dict>
    <key>Processor</key>
    <string>URLDownloader</string>
    <key>Comment</key>
    <string>This downloads the latest version</string>
    <key>Arguments</key>
    <dict>
```

### YAML Format

#### Before
```yaml
Process:
  - Processor: URLDownloader
    <!-- This downloads the latest version -->
    Arguments:
      url: https://example.com
```

#### After
```yaml
Process:
  - Processor: URLDownloader
    Comment: This downloads the latest version
    Arguments:
      url: https://example.com
```

## Requirements

- **AutoPkg**: Must be installed with its bundled Python environment at `/usr/local/autopkg/python`
- **Python 3**: Included with AutoPkg installation
- **No external dependencies**: Uses only Python standard library

## Installation

1. Download `CommentKeyChecker.py` to a convenient location
2. Make the script executable (optional):
   ```bash
   chmod +x CommentKeyChecker.py
   ```

## Usage

### Running the Script

Execute the script using AutoPkg's Python installation:

```bash
/usr/local/autopkg/python CommentKeyChecker.py
```

### Interactive Prompt

When run, the script will prompt for a recipe directory:

```
CommentKeyChecker - AutoPkg Recipe Comment Converter
==================================================
This script will:
1. Find HTML-style comments (<!-- -->)
2. Convert them to Comment key-string pairs
3. Use 4 spaces for indentation
4. Preserve comment location and formatting
==================================================

Enter the path to your recipe directory
(You can drag and drop the folder here):
```

### Example Session

```
Enter the path to your recipe directory
(You can drag and drop the folder here): /Users/username/autopkg/recipes

Scanning recipes in: /Users/username/autopkg/recipes

Found HTML comments in: /Users/username/autopkg/recipes/App.download.recipe
DEBUG: Converting comment: This processor downloads the application...
DEBUG: Converting comment: Set the base URL for downloads...
DEBUG: Converted 2 comment(s)
✓ Successfully converted 2 comment(s): /Users/username/autopkg/recipes/App.download.recipe

==================================================
Processing complete!
Recipes processed: 10
Recipes modified: 1
Total comments converted: 2
==================================================

Modified files:
  ✓ /Users/username/autopkg/recipes/App.download.recipe (2 comment(s) converted)

Please verify these files in your version control system.
```

## Comment Placement

Comments are converted in-place, maintaining their exact position in the recipe structure:

### Inside Processor Dicts
```xml
<dict>
    <key>Processor</key>
    <string>URLDownloader</string>
    <key>Comment</key>
    <string>Downloads from vendor site</string>
    <key>Arguments</key>
```

### Between Processors
```xml
</dict>
<key>Comment</key>
<string>End of download phase</string>
<dict>
    <key>Processor</key>
```

### In Arguments Section
```xml
<key>Arguments</key>
<dict>
    <key>Comment</key>
    <string>URL changes quarterly</string>
    <key>url</key>
```

## YAML Special Character Handling

The script automatically quotes YAML values when necessary:

### Automatic Quoting
```yaml
# Comment contains special characters
Comment: "Check https://example.com for updates"

# Comment contains colons
Comment: "Note: This will change in version 2.0"

# Comment starts with list marker
Comment: "- Remember to update annually"
```

### No Quoting Needed
```yaml
# Simple comments don't need quotes
Comment: This is a simple comment
Comment: Downloads the latest version
```

## Safety Features

- **Non-Destructive**: Only modifies files with HTML comments
- **Verification**: Validates changes and ensures no comments remain
- **Skip Logic**: Automatically skips files without HTML comments
- **Environment Check**: Ensures it runs in AutoPkg's Python environment
- **Error Handling**: Clear error messages with full tracebacks
- **Content Preservation**: Only changes comment format, nothing else
- **Tab Conversion**: Converts any tabs to 4 spaces in the process

## Integration with Other Tools

CommentKeyChecker works well alongside:

- **DetabChecker**: Run after CommentKeyChecker to ensure spacing
- **GitHubPreReleaseChecker**: Can be run in any order
- **DeprecationChecker**: Can be run in any order
- **Pre-commit hooks**: Add to automated validation workflows

## Troubleshooting

### Script Won't Run

**Error**: `This script should be run using AutoPkg's Python installation`

**Solution**: Use the full path to AutoPkg's Python:
```bash
/usr/local/autopkg/python CommentKeyChecker.py
```

### No Comments Found

If no recipes are modified:
- ✅ Your recipes are already using proper Comment keys (good!)
- Check that you're scanning the correct directory
- Verify files have `.recipe` or `.yaml` extensions
- Look for `<!-- -->` style comments manually

### Comments Still Present After Conversion

If verification fails:
1. Check for malformed HTML comments (missing `<!--` or `-->`)
2. Look for nested comments
3. Check for multi-line comments (not supported)
4. Verify file permissions

### Multi-line Comments

This script handles single-line comments only:

**Supported:**
```xml
<!-- This is a single-line comment -->
```

**Not Supported:**
```xml
<!--
This is a multi-line comment
spanning multiple lines
-->
```

For multi-line comments, either:
- Split into multiple single-line comments first
- Manually convert to Comment key-string format

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

## Best Practices

1. **Run Before Committing**: Check recipes before pushing to repositories
2. **Review Changes**: Verify conversions in version control diffs
3. **Consistent Style**: Use Comment keys for all inline documentation
4. **Meaningful Comments**: Ensure comments add value and context
5. **Regular Cleanup**: Run periodically on recipe repositories

## Use Cases

### Repository Migration

When importing recipes from external sources:
1. Run CommentKeyChecker to standardize comments
2. Run DetabChecker to fix indentation
3. Review and commit changes

### Recipe Maintenance

For ongoing recipe upkeep:
1. Run after manual edits to clean up added comments
2. Use in pre-commit hooks for automatic enforcement
3. Include in CI/CD pipelines

### Team Standardization

When working with multiple contributors:
1. Establish Comment key usage as standard
2. Run CommentKeyChecker on pull requests
3. Document the standard in contribution guidelines

## File Format Support

| Format | Extension | Support |
|--------|-----------|---------|
| Plist | `.recipe` | ✅ Full |
| YAML | `.recipe.yaml` | ✅ Full |
| YAML | `.yaml` | ✅ Full |

## Output Details

The script provides comprehensive information:

- **Per-file comment count**: Shows exactly how many comments were converted
- **Total conversion count**: Reports the total number across all files
- **Debug output**: Shows first 50 characters of each comment being converted
- **Verification status**: Confirms no HTML comments remain
- **Skip notifications**: Indicates which files have no HTML comments

## Performance

CommentKeyChecker is highly efficient:

- **Fast Processing**: Simple regex-based line processing
- **Low Memory**: Processes one file at a time
- **No Dependencies**: No external libraries to install
- **Instant Results**: Provides immediate feedback

Typical performance:
- ~100 recipes: < 5 seconds
- ~1000 recipes: < 30 seconds

## Limitations

- Only processes `.recipe` and `.yaml` files
- Handles single-line HTML comments only
- Does not support nested comments
- Does not validate comment content
- Assumes well-formed HTML comment syntax

## Advanced Usage

### Finding Recipes with HTML Comments

Before running the converter:
```bash
grep -r "<!--" /path/to/recipes --include="*.recipe*"
```

### Verifying No Comments Remain

After running:
```bash
grep -r "<!--" /path/to/recipes --include="*.recipe*"
# Should return no results
```

### Pre-Commit Hook Example

Prevent HTML comments from being committed:
```bash
#!/bin/bash
# .git/hooks/pre-commit

RECIPES=$(git diff --cached --name-only --diff-filter=ACM | \
          grep '\.recipe')

if [ -n "$RECIPES" ]; then
    for recipe in $RECIPES; do
        if grep -q "<!--" "$recipe"; then
            echo "Error: HTML comments found in $recipe"
            echo "Run CommentKeyChecker.py to fix this issue"
            exit 1
        fi
    done
fi
```

## Comment Style Guidelines

### Good Comment Usage

✅ Explain why, not what:
```xml
<key>Comment</key>
<string>URL format changed in 2024 - keep both patterns for compatibility</string>
```

✅ Document edge cases:
```xml
<key>Comment</key>
<string>Special handling required for beta versions</string>
```

✅ Note external dependencies:
```xml
<key>Comment</key>
<string>Requires munkitools to be installed first</string>
```

### Avoid Excessive Comments

❌ Don't state the obvious:
```xml
<key>Comment</key>
<string>This is a URLDownloader processor</string>
```

❌ Don't duplicate key names:
```xml
<key>url</key>
<string>https://example.com</string>
<key>Comment</key>
<string>The URL</string>
```

## Related Tools

- **xmllint**: Validate XML syntax after conversion
- **yamllint**: Validate YAML syntax after conversion
- **autopkg-linter**: Additional recipe validation
- **DetabChecker**: Ensure proper spacing after conversion

## Contributing

When modifying this script:

1. Test with both plist and YAML recipes
2. Verify indentation is exactly 4 spaces
3. Test with various comment contents
4. Handle YAML special characters correctly
5. Update this README with changes

## References

- [AutoPkg Recipe Format](https://github.com/autopkg/autopkg/wiki/Recipe-Format)
- [XML Comments](https://www.w3.org/TR/xml/#sec-comments)
- [YAML Specification](https://yaml.org/spec/1.2/spec.html)

## Author

Paul Cossey

## Version History

- **Current**: Initial release with plist and YAML support, automatic quoting

---

For more information about AutoPkg recipe standards, visit [https://github.com/autopkg/autopkg](https://github.com/autopkg/autopkg)

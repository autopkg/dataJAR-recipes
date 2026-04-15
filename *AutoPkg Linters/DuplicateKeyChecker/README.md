# DuplicateKeyChecker

An AutoPkg utility script that detects duplicate keys in recipe files. Duplicate keys in plist files can cause parsing issues and unexpected behavior. This script identifies all duplicates and automatically fixes the common case where `unattended_install` appears twice when `unattended_uninstall` is missing.

## Features

- **Duplicate Key Detection**: Scans all `<dict>` sections for duplicate keys
- **Automatic Fix**: Converts second `unattended_install` to `unattended_uninstall` when appropriate
- **Comprehensive Warnings**: Reports all duplicate keys found
- **Multi-Format Support**: Handles both plist (`.recipe`) and YAML (`.yaml`) formats
- **Batch Processing**: Processes entire recipe repositories
- **Detailed Reporting**: Shows exactly what was found and fixed

## Why Check for Duplicate Keys?

Duplicate keys in plist files can cause several issues:

- **Parsing Errors**: Some XML parsers reject duplicate keys
- **Unpredictable Behavior**: Which value is used varies by parser
- **Common Typo**: `unattended_install` often duplicated instead of adding `unattended_uninstall`
- **Data Loss**: Second value may silently override the first
- **Munki Issues**: Munki expects distinct `unattended_install` and `unattended_uninstall` keys

## What It Does

### Detection

The script scans all `<dict>` sections and identifies any keys that appear more than once:

```xml
<dict>
    <key>name</key>
    <string>Firefox</string>
    <key>unattended_install</key>
    <true/>
    <key>unattended_install</key>  <!-- DUPLICATE! -->
    <true/>
</dict>
```

### Automatic Fix

When the script finds:
- Two occurrences of `unattended_install`
- No `unattended_uninstall` key

It automatically fixes it:

#### Before
```xml
<key>pkginfo</key>
<dict>
    <key>catalogs</key>
    <array>
        <string>testing</string>
    </array>
    <key>description</key>
    <string>Firefox web browser</string>
    <key>name</key>
    <string>Firefox</string>
    <key>unattended_install</key>
    <true/>
    <key>unattended_install</key>
    <true/>
</dict>
```

#### After
```xml
<key>pkginfo</key>
<dict>
    <key>catalogs</key>
    <array>
        <string>testing</string>
    </array>
    <key>description</key>
    <string>Firefox web browser</string>
    <key>name</key>
    <string>Firefox</string>
    <key>unattended_install</key>
    <true/>
    <key>unattended_uninstall</key>
    <true/>
</dict>
```

### Warnings Only

For other duplicate keys, the script reports warnings but does not auto-fix:

```
⚠ Found duplicate 'developer' key (2 occurrences)
```

You'll need to manually review and fix these cases.

## Usage

### Standalone

```bash
cd DuplicateKeyChecker
/usr/local/autopkg/python DuplicateKeyChecker.py
```

You'll be prompted to enter the path to your recipe directory.

### Via Linter Suite

```bash
# Run with other linters
/usr/local/autopkg/python autopkg-linter.py --linters 16 /path/to/recipes

# Run all linters including DuplicateKeyChecker
/usr/local/autopkg/python autopkg-linter.py --all /path/to/recipes
```

### Drag and Drop

You can drag and drop your recipe directory into the terminal when prompted for the path.

## Output Example

```
DuplicateKeyChecker - AutoPkg Recipe Duplicate Key Detector
======================================================================
This script will:
1. Scan recipes for duplicate keys in dict sections
2. Warn about any duplicate keys found
3. Auto-fix duplicate 'unattended_install' when possible
   (changes 2nd occurrence to 'unattended_uninstall')
======================================================================

Enter the path to your recipe directory
(You can drag and drop the folder here): /Users/admin/recipes

Scanning recipes in: /Users/admin/recipes
Found 50 recipe file(s)

✓ Firefox.munki.recipe
  ⚠ Found duplicate 'unattended_install' key (will attempt to fix)
  ✓ Changed second 'unattended_install' to 'unattended_uninstall'

⚠ Chrome.munki.recipe
  ⚠ Found duplicate 'developer' key (2 occurrences)

======================================================================
Scan complete!
Recipes scanned: 50
Recipes with issues: 2
Recipes fixed: 1
======================================================================

Fixed files:

  ✓ Firefox.munki.recipe:
    - Changed second 'unattended_install' to 'unattended_uninstall'

Warnings (not auto-fixed):

  ⚠ Chrome.munki.recipe:
    - Found duplicate 'developer' key (2 occurrences)

Please review and manually fix recipes with warnings.
Please verify fixed files in your version control system.
```

## YAML Support

For YAML recipes, the script detects duplicate keys at the same indentation level but only reports warnings (no auto-fix):

```yaml
Input:
  NAME: Firefox
  NAME: Chrome  # Duplicate detected, warning shown
```

YAML parsers typically use the last value when duplicates are found, but it's still worth fixing.

## Integration

### Pre-Commit Hook

Add to your git pre-commit hook:

```bash
#!/bin/bash
# Check for duplicate keys before committing

/usr/local/autopkg/python ~/Scripts/DuplicateKeyChecker/DuplicateKeyChecker.py \
    "$(pwd)" | grep -q "⚠"

if [ $? -eq 0 ]; then
    echo "Warning: Duplicate keys found in recipes"
    echo "Run DuplicateKeyChecker to review"
    exit 1
fi
```

### CI/CD Pipeline

Include in your recipe validation workflow to catch duplicate keys early.

## Common Scenarios

### Scenario 1: Copy-Paste Error

**Issue**: Copied `unattended_install` line twice instead of adding `unattended_uninstall`

**Detection**: Script finds duplicate `unattended_install`, no `unattended_uninstall`

**Fix**: Automatic - second occurrence changed to `unattended_uninstall`

### Scenario 2: Merge Conflict

**Issue**: Git merge created duplicate keys

**Detection**: Script finds duplicate keys of any type

**Fix**: Manual review required - script shows warnings

### Scenario 3: Parent Recipe Override

**Issue**: Child recipe accidentally duplicates parent recipe key

**Detection**: Script finds duplicate in combined recipe

**Fix**: Manual - remove duplicate from child recipe

## Limitations

- **Auto-fix only for unattended_install**: Other duplicates require manual review
- **Plist format only for fixes**: YAML duplicates are detected but not fixed
- **Single dict scope**: Doesn't check across different dict levels
- **Requires exact match**: Keys must be identical (case-sensitive)

## Best Practices

1. **Run before committing**: Catch duplicates before they enter version control
2. **Review auto-fixes**: Verify the fix is correct for your use case
3. **Check warnings**: Manually fix any non-auto-fixed duplicates
4. **Use with RecipeAlphabetiser**: Run after fixing duplicates for clean formatting
5. **Regular scans**: Include in your recipe maintenance workflow

## Exit Codes

- `0` - Success (no issues or all issues auto-fixed)
- `0` - Success with warnings (duplicates found but not auto-fixed)

## Technical Details

### Detection Algorithm

1. Parse plist file content
2. Find all `<dict>...</dict>` blocks
3. Extract all `<key>` tags within each dict
4. Track positions of each key name
5. Report keys with multiple positions

### Auto-Fix Logic

1. Check if `unattended_install` appears exactly twice
2. Check if `unattended_uninstall` is missing
3. If both conditions met, replace second `unattended_install` with `unattended_uninstall`
4. Write modified content back to file

### YAML Detection

1. Parse line by line
2. Track indentation level
3. Extract key names from `key:` patterns
4. Report duplicates at same indentation level

## Troubleshooting

### "No recipe files found"

**Solution**: Verify the path points to a directory containing `.recipe` or `.yaml` files

### "Error processing recipe"

**Solution**: Check that recipe files are valid XML/YAML format

### Auto-fix didn't work

**Possible reasons**:
- More than 2 occurrences of `unattended_install`
- `unattended_uninstall` already exists
- Key appears in different dict contexts

**Solution**: Review the recipe manually

## Related Linters

- **RecipeAlphabetiser**: Run after DuplicateKeyChecker to organize keys
- **MissingKeyValueChecker**: Checks for empty values in pkginfo
- **DetabChecker**: Fixes whitespace and formatting issues

## Version History

- **v1.0** - Initial release
  - Duplicate key detection
  - Auto-fix for duplicate unattended_install
  - YAML support (warnings only)

## License

Same as AutoPkg - Apache 2.0

## Support

For issues or questions:
- Check this README
- Review the main suite README
- Verify you're using AutoPkg's Python (`/usr/local/autopkg/python`)

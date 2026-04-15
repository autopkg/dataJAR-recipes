# FindAndReplaceChecker

A Python script that updates AutoPkg recipes to use the core FindAndReplace processor instead of the shared processor reference.

## Purpose

As of AutoPkg version 2.7.6, FindAndReplace became a core processor. This script:
- Converts shared processor references (`com.github.homebysix.FindAndReplace/FindAndReplace`) to the core processor (`FindAndReplace`)
- Updates `MinimumVersion` to 2.7.6 or higher

## Background

Previously, FindAndReplace was a shared processor that needed to be referenced with its full path:
```xml
<key>Processor</key>
<string>com.github.homebysix.FindAndReplace/FindAndReplace</string>
```

Since AutoPkg 2.7.6, it's a core processor and should be referenced simply as:
```xml
<key>Processor</key>
<string>FindAndReplace</string>
```

## Features

- **Automatic Detection**: Finds all recipes using the shared FindAndReplace processor
- **Format Support**: Handles both plist (.recipe) and YAML (.yaml) formats
- **Version Update**: Sets MinimumVersion to 2.7.6 if lower
- **Indentation Preservation**: Maintains original file formatting
- **Safe Processing**: Verifies changes before confirming success
- **Recursive Search**: Processes all recipes in directory tree

## Requirements

- AutoPkg's bundled Python 3 (`/usr/local/autopkg/python`)
- Read/write access to recipe directories

## Usage

### Basic Usage

```bash
/usr/local/autopkg/python /path/to/FindAndReplaceChecker.py
```

When prompted, enter or drag-and-drop your recipe directory.

### Example Session

```
FindAndReplaceChecker - AutoPkg Recipe Updater
==================================================
This script will:
1. Find recipes using shared FindAndReplace processor
2. Convert to core FindAndReplace processor
3. Update MinimumVersion to 2.7.6
==================================================

Enter the path to your recipe directory
(You can drag and drop the folder here): /Users/username/autopkg-recipes

Scanning recipes in: /Users/username/autopkg-recipes

Found shared FindAndReplace in: /Users/username/autopkg-recipes/App/App.download.recipe
DEBUG: Converting com.github.homebysix.FindAndReplace/FindAndReplace to FindAndReplace
DEBUG: Updating MinimumVersion from 1.0 to 2.7.6
✓ Successfully modified: /Users/username/autopkg-recipes/App/App.download.recipe

==================================================
Processing complete!
Recipes processed: 150
Recipes modified: 12
==================================================

Modified files:
  ✓ /Users/username/autopkg-recipes/App/App.download.recipe
  ✓ /Users/username/autopkg-recipes/Tool/Tool.pkg.recipe
  ...

Please verify these files in your version control system.
```

## What It Modifies

### Plist Format

**Before:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>MinimumVersion</key>
    <string>1.0</string>
    <key>Process</key>
    <array>
        <dict>
            <key>Processor</key>
            <string>com.github.homebysix.FindAndReplace/FindAndReplace</string>
            <key>Arguments</key>
            <dict>
                <key>find</key>
                <string>old_text</string>
                <key>replace</key>
                <string>new_text</string>
            </dict>
        </dict>
    </array>
</dict>
</plist>
```

**After:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>MinimumVersion</key>
    <string>2.7.6</string>
    <key>Process</key>
    <array>
        <dict>
            <key>Processor</key>
            <string>FindAndReplace</string>
            <key>Arguments</key>
            <dict>
                <key>find</key>
                <string>old_text</string>
                <key>replace</key>
                <string>new_text</string>
            </dict>
        </dict>
    </array>
</dict>
</plist>
```

### YAML Format

**Before:**
```yaml
MinimumVersion: 1.0
Process:
    - Processor: com.github.homebysix.FindAndReplace/FindAndReplace
      Arguments:
          find: old_text
          replace: new_text
```

**After:**
```yaml
MinimumVersion: 2.7.6
Process:
    - Processor: FindAndReplace
      Arguments:
          find: old_text
          replace: new_text
```

## Detected Patterns

The script detects both common shared processor reference patterns:
- `com.github.homebysix.FindAndReplace/FindAndReplace`
- `com.github.homebysix.FindAndReplace`

## Safety Features

1. **Verification**: Confirms file writes completed successfully
2. **Backup Recommendation**: Only modifies files; keep backups or use version control
3. **Detailed Output**: Shows which recipes are modified and why
4. **Graceful Errors**: Continues processing if individual recipes fail
5. **Skip Logic**: Only processes recipes that actually need updates

## When to Use

Run this script when:
- Migrating recipes to AutoPkg 2.7.6 or later
- Cleaning up recipes that use the old shared processor reference
- Standardizing recipe processor references across a repository
- Preparing recipes for distribution with correct modern references

## Best Practices

1. **Version Control**: Commit or backup recipes before running
2. **Review Changes**: Use `git diff` or similar to review modifications
3. **Test Recipes**: Run updated recipes to ensure they work correctly
4. **Batch Processing**: Can process entire recipe repositories at once
5. **Run After Updates**: Use after upgrading to AutoPkg 2.7.6+

## Limitations

- Only updates FindAndReplace processor references
- Requires AutoPkg 2.7.6+ to use updated recipes
- Does not modify processor arguments or logic
- Does not handle custom FindAndReplace implementations

## Related Scripts

- **MinimumVersionChecker**: Sets MinimumVersion based on all processors used
- **DeprecationChecker**: Handles deprecated recipe warnings
- **RecipeAlphabetiser**: Alphabetizes recipe keys for consistency

## Troubleshooting

### "Error: This script should be run using AutoPkg's Python installation"
**Solution**: Run with AutoPkg's Python:
```bash
/usr/local/autopkg/python FindAndReplaceChecker.py
```

### "Permission denied"
**Solution**: Ensure you have write access:
```bash
chmod +w /path/to/recipes/*.recipe
```

### Recipe Still Has Shared Reference
**Problem**: Recipe wasn't modified
**Solutions**:
- Check the processor name spelling matches exactly
- Verify file is writable
- Check DEBUG output for errors

### MinimumVersion Not Updated
**Problem**: Version requirement not set correctly
**Possible Causes**:
- Recipe already has MinimumVersion >= 2.7.6
- File write failed (check permissions)

## Version History

- **1.0** (2025-11-27): Initial release
  - Converts shared FindAndReplace to core processor
  - Updates MinimumVersion to 2.7.6
  - Supports plist and YAML formats

## Exit Codes

- `0`: Success
- `1`: Error (invalid directory, permission issues, etc.)

## Author

Created for AutoPkg recipe maintenance and modernization.

## License

Use freely for AutoPkg recipe management.

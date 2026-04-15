# MissingKeyValueChecker

An AutoPkg utility script that checks for empty or whitespace-only values in the `pkginfo` dict of Munki recipes. This helps identify incomplete recipe configurations that could cause issues with Munki imports.

## Features

- **Munki-Focused**: Only checks `.munki` recipes (skips other recipe types)
- **Empty Value Detection**: Finds keys with empty strings or whitespace-only values
- **Multi-Format Support**: Handles both plist (`.munki.recipe`) and YAML (`.munki.yaml`) formats
- **Batch Processing**: Scans entire recipe directories
- **Non-Destructive**: Reports issues without modifying files
- **Detailed Reporting**: Shows which keys are empty and on which lines

## Why This Matters

Empty or whitespace-only values in `pkginfo` can cause issues:

- **Munki Import Failures**: Empty required fields may prevent Munki imports
- **Incomplete Metadata**: Missing descriptions or categories make catalogs unclear
- **Catalog Issues**: Empty values may not filter correctly in Managed Software Center
- **Recipe Quality**: Empty values indicate incomplete recipe development
- **Maintenance**: Helps identify recipes needing attention

## What It Does

The script examines the `pkginfo` dict in Munki recipes and reports:

1. Keys with completely empty `<string>` values
2. Keys with whitespace-only values (spaces, tabs, newlines)
3. The line number where each empty key is found

### Example Issues Found

**Empty String**:
```xml
<key>category</key>
<string></string>
```

**Whitespace Only**:
```xml
<key>description</key>
<string>    </string>
```

**Valid (Not Reported)**:
```xml
<key>category</key>
<string>Utilities</string>
```

## Requirements

- **AutoPkg**: Must be installed with its bundled Python environment at `/usr/local/autopkg/python`
- **Python 3**: Included with AutoPkg installation
- **PyYAML**: For YAML recipe support (usually included with AutoPkg)
- **No external dependencies**: Uses only Python standard library

## Installation

1. Download `MissingKeyValueChecker.py` to a convenient location
2. Make the script executable (optional):
   ```bash
   chmod +x MissingKeyValueChecker.py
   ```

## Usage

### Running the Script

Execute the script using AutoPkg's Python installation:

```bash
/usr/local/autopkg/python MissingKeyValueChecker.py
```

### Interactive Prompt

When run, the script will prompt for a recipe directory:

```
MissingKeyValueChecker - Empty pkginfo Value Detector
==================================================
This script checks .munki recipes for empty values
in the pkginfo dict.
==================================================

Enter the path to your recipe directory
(You can drag and drop the folder here):
```

You can either:
- Type the full path to your recipe directory
- Drag and drop a folder from Finder

### Bulk Mode

Run against a directory without prompts:

```bash
# Using autopkg-linter.py suite runner
/usr/local/autopkg/python autopkg-linter.py --linters 15 /path/to/recipes
```

## What Gets Checked

The script only examines Munki recipes:

✅ **Checks**:
- `.munki.recipe` files (plist format)
- `.munki.yaml` files (YAML format)
- Only the `pkginfo` dict within Input
- String values for emptiness or whitespace

❌ **Skips**:
- Non-Munki recipes (`.recipe`, `.download`, `.pkg`)
- Keys outside the `pkginfo` dict
- Non-string values (arrays, dicts, booleans)
- Keys with actual content

## Common Empty Keys

Keys that are often found empty and should be filled:

### Required by Munki
- `name` - Package name (critical!)
- `version` - Version string (critical!)
- `display_name` - Human-readable name

### Important for Users
- `description` - Package description
- `category` - Managed Software Center category
- `developer` - Software vendor/developer

### Optional but Useful
- `unattended_install` - Boolean, but may be empty string
- `unattended_uninstall` - Boolean, but may be empty string
- `blocking_applications` - Array, but may have empty strings
- `update_for` - Array of package names

## Examples

### Example 1: Empty Category

**Input** (plist):
```xml
<key>pkginfo</key>
<dict>
    <key>category</key>
    <string></string>
    <key>description</key>
    <string>A useful application</string>
</dict>
```

**Output**:
```
⚠ Found empty keys in MyApp.munki.recipe:
  - category (line 42)
```

### Example 2: Whitespace-Only Description

**Input** (YAML):
```yaml
Input:
  pkginfo:
    category: Utilities
    description: '   '
    display_name: My App
```

**Output**:
```
⚠ Found empty keys in MyApp.munki.yaml:
  - description
```

### Example 3: Multiple Empty Keys

**Input**:
```xml
<key>pkginfo</key>
<dict>
    <key>category</key>
    <string></string>
    <key>description</key>
    <string>   </string>
    <key>developer</key>
    <string></string>
</dict>
```

**Output**:
```
⚠ Found empty keys in IncompleteApp.munki.recipe:
  - category (line 38)
  - description (line 40)
  - developer (line 42)
```

## Output

The script provides clear feedback:

```
MissingKeyValueChecker - Empty pkginfo Value Detector
==================================================

Processing 25 Munki recipes...

⚠ Found empty keys in Firefox.munki.recipe:
  - category (line 45)

⚠ Found empty keys in Chrome.munki.recipe:
  - description (line 52)
  - category (line 48)

✓ Slack.munki.recipe - all pkginfo values populated
✓ Teams.munki.recipe - all pkginfo values populated

==================================================
Processing complete!
Recipes checked: 25
Recipes with empty values: 2
==================================================
```

## Common Use Cases

1. **Recipe Development**: Identify incomplete recipes during development
2. **Quality Assurance**: Validate recipes before publishing
3. **Recipe Import**: Check recipes imported from other sources
4. **Maintenance**: Find recipes needing metadata updates
5. **Pre-Commit Check**: Validate completeness before version control commits

## Fixing Empty Values

After the script identifies empty keys, manually edit the recipes:

### Add Missing Category

```xml
<key>category</key>
<string>Productivity</string>
```

### Add Missing Description

```xml
<key>description</key>
<string>A powerful text editor with IDE features</string>
```

### Add Missing Developer

```xml
<key>developer</key>
<string>Microsoft Corporation</string>
```

## Integration with autopkg-linter.py

This linter is integrated into the AutoPkg Linter Suite as **Linter #15**:

```bash
# Run as part of the suite
/usr/local/autopkg/python autopkg-linter.py --linters 15 ~/recipes

# Include in a batch with other Munki linters
/usr/local/autopkg/python autopkg-linter.py --linters 9,10,15 ~/recipes

# Run with all linters
/usr/local/autopkg/python autopkg-linter.py --all ~/recipes
```

## Troubleshooting

### Script Won't Run

**Error**: `This script should be run using AutoPkg's Python installation`

**Solution**: Use AutoPkg's Python:
```bash
/usr/local/autopkg/python MissingKeyValueChecker.py
```

### No Recipes Checked

If the script reports "0 recipes checked":
- Ensure you're scanning a directory with `.munki.recipe` or `.munki.yaml` files
- This script only checks Munki recipes, not `.recipe`, `.download`, or `.pkg` recipes
- Check paths to ensure you're scanning the right directory

### YAML Errors

**Error**: `PyYAML not available`

**Solution**: Install PyYAML in AutoPkg's Python:
```bash
/usr/local/autopkg/python -m pip install PyYAML
```

## Technical Details

### Plist Processing

- Uses regex to find and extract `pkginfo` dict
- Parses `<key>` and `<string>` pairs
- Tracks line numbers for reporting
- Detects empty strings and whitespace-only values

### YAML Processing

- Uses PyYAML library for parsing
- Navigates to `Input.pkginfo` dict
- Checks string values for emptiness
- Reports key names (line numbers not available in YAML)

### Empty Value Detection

Considers a value empty if:
- Completely empty string: `""`
- Whitespace only: spaces, tabs, newlines
- Python's `str.strip()` returns empty string

## Best Practices

- **Fill Required Fields**: Always provide `name`, `version`, `display_name`
- **Meaningful Descriptions**: Write clear descriptions for Managed Software Center
- **Use Categories**: Categorize packages for user navigation
- **Include Developer**: Help users identify software vendors
- **Review Regularly**: Check recipes periodically for empty values

## Related Linters

- **MunkiPathDeleterChecker** (#9): Validates PathDeleter cleanup
- **MunkiInstallsItemsCreatorChecker** (#10): Validates install tracking
- **UninstallScriptChecker** (#5): Validates uninstall configuration
- **RecipeAlphabetiser** (#8): Alphabetizes pkginfo keys

## Munki pkginfo Reference

Common `pkginfo` keys:

### Required
- `name` - Unique package identifier
- `version` - Version string

### Display
- `display_name` - User-friendly name
- `description` - Package description
- `category` - Category for Managed Software Center

### Install Behavior
- `unattended_install` - Boolean for silent install
- `unattended_uninstall` - Boolean for silent uninstall
- `blocking_applications` - Array of apps to quit

### Dependencies
- `requires` - Array of required packages
- `update_for` - Array of packages this updates

For complete pkginfo reference, see: https://github.com/munki/munki/wiki/Pkginfo-Files

## Support

For issues, questions, or contributions, please refer to the main repository README.

## License

Part of the AutoPkg Recipe Linter Suite.

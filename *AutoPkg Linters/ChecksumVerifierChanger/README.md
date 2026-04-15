# ChecksumVerifierChanger

An AutoPkg utility script that updates ChecksumVerifier processor arguments from the incorrect `pathname` key to the correct `checksum_pathname` key. This fixes a common configuration error in AutoPkg recipes.

## Features

- **Automatic Detection**: Finds all ChecksumVerifier processors with incorrect arguments
- **Smart Renaming**: Renames `pathname` → `checksum_pathname` when present
- **Automatic Addition**: Adds missing `checksum_pathname` argument with default value
- **Multi-Format Support**: Handles both plist (`.recipe`) and YAML (`.yaml`) recipe formats
- **Batch Processing**: Processes entire recipe directories
- **Safe Modifications**: Only modifies ChecksumVerifier processor Arguments
- **Detailed Reporting**: Shows exactly what was changed in each file

## Why This Matters

The **ChecksumVerifier** processor uses the argument name `checksum_pathname`, not `pathname`:

- **Correct Usage**: `checksum_pathname` specifies the file to verify
- **Common Mistake**: Using `pathname` (which ChecksumVerifier doesn't recognize)
- **Silent Failures**: Recipes with incorrect arguments may fail checksum verification
- **AutoPkg Best Practices**: Ensures processor arguments match their definitions

## What It Does

The script performs two types of fixes:

### 1. Rename Incorrect Key

When a ChecksumVerifier has `pathname` but not `checksum_pathname`:

- Renames `pathname` → `checksum_pathname`
- Preserves the existing value
- Maintains all other Arguments

### 2. Add Missing Key

When a ChecksumVerifier is missing `checksum_pathname` entirely:

- Adds `checksum_pathname` to Arguments dict
- Sets default value to `%pathname%`
- Maintains proper indentation

### Before (Incorrect)
```xml
<dict>
    <key>Processor</key>
    <string>com.github.autopkg.example/ChecksumVerifier</string>
    <key>Arguments</key>
    <dict>
        <key>pathname</key>
        <string>%pathname%</string>
        <key>algorithm</key>
        <string>sha256</string>
    </dict>
</dict>
```

### After (Correct)
```xml
<dict>
    <key>Processor</key>
    <string>com.github.autopkg.example/ChecksumVerifier</string>
    <key>Arguments</key>
    <dict>
        <key>checksum_pathname</key>
        <string>%pathname%</string>
        <key>algorithm</key>
        <string>sha256</string>
    </dict>
</dict>
```

### YAML Example

**Before**:
```yaml
Processor: com.github.autopkg/ChecksumVerifier
Arguments:
  pathname: '%pathname%'
  algorithm: sha256
```

**After**:
```yaml
Processor: com.github.autopkg/ChecksumVerifier
Arguments:
  checksum_pathname: '%pathname%'
  algorithm: sha256
```

## Requirements

- **AutoPkg**: Must be installed with its bundled Python environment at `/usr/local/autopkg/python`
- **Python 3**: Included with AutoPkg installation
- **PyYAML**: For YAML recipe support (usually included with AutoPkg)
- **No external dependencies**: Uses only Python standard library

## Installation

1. Download `ChecksumVerifierChanger.py` to a convenient location
2. Make the script executable (optional):
   ```bash
   chmod +x ChecksumVerifierChanger.py
   ```

## Usage

### Running the Script

Execute the script using AutoPkg's Python installation:

```bash
/usr/local/autopkg/python ChecksumVerifierChanger.py
```

### Interactive Prompt

When run, the script will prompt for a recipe directory:

```
ChecksumVerifierChanger - Argument Key Updater
==================================================
This script updates ChecksumVerifier processors:
  - Renames 'pathname' → 'checksum_pathname'
  - Adds missing 'checksum_pathname' arguments
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
/usr/local/autopkg/python autopkg-linter.py --linters 13 /path/to/recipes
```

## What Gets Modified

The script only modifies ChecksumVerifier processors:

✅ **Changes**:
- Renames `pathname` → `checksum_pathname` in Arguments
- Adds `checksum_pathname` if missing entirely
- Preserves all other processor arguments
- Maintains file structure and formatting

✅ **Preserves**:
- All other processors unchanged
- All other arguments unchanged
- File formatting and indentation
- Comments and whitespace

❌ **Skips**:
- ChecksumVerifier processors that already have correct `checksum_pathname`
- All other processor types
- Recipes without ChecksumVerifier processors

## Examples

### Example 1: Simple Rename

**Before**:
```xml
<key>Arguments</key>
<dict>
    <key>pathname</key>
    <string>%pathname%</string>
</dict>
```

**After**:
```xml
<key>Arguments</key>
<dict>
    <key>checksum_pathname</key>
    <string>%pathname%</string>
</dict>
```

### Example 2: Missing checksum_pathname

**Before**:
```xml
<key>Arguments</key>
<dict>
    <key>algorithm</key>
    <string>sha256</string>
</dict>
```

**After**:
```xml
<key>Arguments</key>
<dict>
    <key>algorithm</key>
    <string>sha256</string>
    <key>checksum_pathname</key>
    <string>%pathname%</string>
</dict>
```

### Example 3: Custom Value Preserved

**Before**:
```xml
<key>Arguments</key>
<dict>
    <key>pathname</key>
    <string>%RECIPE_CACHE_DIR%/downloads/installer.pkg</string>
</dict>
```

**After**:
```xml
<key>Arguments</key>
<dict>
    <key>checksum_pathname</key>
    <string>%RECIPE_CACHE_DIR%/downloads/installer.pkg</string>
</dict>
```

## Output

The script provides clear feedback:

```
ChecksumVerifierChanger - Argument Key Updater
==================================================

Processing 30 recipes...

✓ Updated MyApp.recipe
  - Renamed pathname → checksum_pathname in 1 processor(s)

✓ Updated AnotherApp.recipe
  - Added checksum_pathname to 1 processor(s)

Skipping ValidApp.recipe - ChecksumVerifier already has checksum_pathname

==================================================
Processing complete!
Recipes processed: 30
Recipes modified: 2
==================================================

Modified files:
  ✓ MyApp.recipe:
    - Renamed pathname → checksum_pathname in 1 processor(s)
  ✓ AnotherApp.recipe:
    - Added checksum_pathname to 1 processor(s)

Please verify these files in your version control system.
```

## Common Use Cases

1. **Recipe Migration**: Fix recipes that used incorrect `pathname` argument
2. **New Recipes**: Add missing `checksum_pathname` to incomplete recipes
3. **Batch Updates**: Update entire recipe repositories at once
4. **Recipe Import**: Fix recipes imported from other sources
5. **Pre-Commit Check**: Validate ChecksumVerifier configuration before committing

## ChecksumVerifier Processor

The ChecksumVerifier processor verifies file checksums:

### Correct Arguments

- `checksum_pathname`: Path to file to verify (required)
- `algorithm`: Hash algorithm - `md5`, `sha1`, `sha256` (optional, default: `md5`)
- `checksum`: Expected checksum value (optional)

### Example Usage

```xml
<dict>
    <key>Processor</key>
    <string>com.github.autopkg/ChecksumVerifier</string>
    <key>Arguments</key>
    <dict>
        <key>checksum_pathname</key>
        <string>%pathname%</string>
        <key>algorithm</key>
        <string>sha256</string>
        <key>checksum</key>
        <string>abc123def456...</string>
    </dict>
</dict>
```

## Integration with autopkg-linter.py

This linter is integrated into the AutoPkg Linter Suite as **Linter #13**:

```bash
# Run as part of the suite
/usr/local/autopkg/python autopkg-linter.py --linters 13 ~/recipes

# Include in a batch with other linters
/usr/local/autopkg/python autopkg-linter.py --linters 6,8,13 ~/recipes

# Run with all linters
/usr/local/autopkg/python autopkg-linter.py --all ~/recipes
```

## Troubleshooting

### Script Won't Run

**Error**: `This script should be run using AutoPkg's Python installation`

**Solution**: Use AutoPkg's Python:
```bash
/usr/local/autopkg/python ChecksumVerifierChanger.py
```

### No Changes Made

If the script reports no changes:
- Your recipes may already have correct `checksum_pathname`
- Your recipes may not use ChecksumVerifier processor
- Check paths to ensure you're scanning the right directory

### YAML Errors

**Error**: `PyYAML not available`

**Solution**: Install PyYAML in AutoPkg's Python:
```bash
/usr/local/autopkg/python -m pip install PyYAML
```

## Technical Details

### Plist Processing

- Uses regex to find ChecksumVerifier processors
- Parses processor Arguments dict
- Renames keys or adds missing keys
- Maintains exact XML structure

### YAML Processing

- Uses PyYAML library for parsing
- Modifies processor Arguments dictionaries
- Preserves YAML formatting and structure
- Maintains key ordering

### Safety Features

- Only modifies ChecksumVerifier processors
- Validates changes before writing
- Preserves all other recipe content
- Handles nested dict structures correctly

## Best Practices

- **Test After Changes**: Run recipes with `autopkg run --check` after modification
- **Review Diffs**: Check git diffs to verify only ChecksumVerifier was modified
- **Combine with Other Linters**: Run alongside MinimumVersionChecker and RecipeAlphabetiser
- **Version Control**: Commit changes separately for clear history

## Related Linters

- **MinimumVersionChecker** (#6): Sets correct MinimumVersion for processors
- **RecipeAlphabetiser** (#8): Alphabetizes processor Arguments
- **DetabChecker** (#3): Fixes whitespace formatting

## Support

For issues, questions, or contributions, please refer to the main repository README.

## License

Part of the AutoPkg Recipe Linter Suite.

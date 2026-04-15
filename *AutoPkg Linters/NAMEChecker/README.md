# NAMEChecker

An AutoPkg utility script that validates and fixes the `NAME` input variable in AutoPkg recipes by removing spaces. This ensures `NAME` values follow AutoPkg conventions and prevents issues with file paths and package identifiers.

## Features

- **Automatic Space Removal**: Detects and removes spaces from `NAME` values
- **Multi-Format Support**: Handles both plist (`.recipe`) and YAML (`.yaml`) recipe formats
- **Batch Processing**: Processes entire recipe directories
- **Safe Modifications**: Only modifies the `NAME` value in Input dict
- **Format Preservation**: Uses text manipulation to preserve exact file formatting
- **Detailed Reporting**: Shows original and corrected NAME values

## Why This Matters

The `NAME` input variable should not contain spaces:

- **File Path Safety**: Spaces in NAME can cause issues with file paths
- **Package Identifiers**: NAME often used in package/bundle identifiers
- **AutoPkg Conventions**: Best practices recommend no spaces in NAME
- **Variable Substitution**: NAME used in many string substitutions throughout recipes
- **Consistency**: Ensures NAME works reliably across all contexts

## What It Does

The script finds `NAME` values with spaces and removes them:

- Detects `NAME` key in the Input dict
- Identifies if the value contains spaces
- Removes all spaces from the value
- Preserves capitalization and other characters

### Conversion Examples

| Before (Incorrect) | After (Correct) |
|-------------------|-----------------|
| `File Beat` | `FileBeat` |
| `Adobe Reader` | `AdobeReader` |
| `VS Code` | `VSCode` |
| `Microsoft Teams` | `MicrosoftTeams` |
| `Google Chrome` | `GoogleChrome` |

### Before
```xml
<key>Input</key>
<dict>
    <key>NAME</key>
    <string>Adobe Reader</string>
    <key>VENDOR</key>
    <string>Adobe</string>
</dict>
```

### After
```xml
<key>Input</key>
<dict>
    <key>NAME</key>
    <string>AdobeReader</string>
    <key>VENDOR</key>
    <string>Adobe</string>
</dict>
```

### YAML Example

**Before**:
```yaml
Input:
  NAME: File Beat
  VENDOR: Elastic
```

**After**:
```yaml
Input:
  NAME: FileBeat
  VENDOR: Elastic
```

## Requirements

- **AutoPkg**: Must be installed with its bundled Python environment at `/usr/local/autopkg/python`
- **Python 3**: Included with AutoPkg installation
- **PyYAML**: For YAML recipe support (usually included with AutoPkg)
- **No external dependencies**: Uses only Python standard library

## Installation

1. Download `NAMEChecker.py` to a convenient location
2. Make the script executable (optional):
   ```bash
   chmod +x NAMEChecker.py
   ```

## Usage

### Running the Script

Execute the script using AutoPkg's Python installation:

```bash
/usr/local/autopkg/python NAMEChecker.py
```

### Interactive Prompt

When run, the script will prompt for a recipe directory:

```
NAMEChecker - NAME Variable Space Remover
==================================================
This script removes spaces from NAME input variable values.
Example: "Adobe Reader" → "AdobeReader"
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
/usr/local/autopkg/python autopkg-linter.py --linters 14 /path/to/recipes
```

## What Gets Modified

The script only modifies the NAME value:

✅ **Changes**:
- Removes all spaces from NAME value in Input dict
- Preserves capitalization (e.g., "Adobe Reader" → "AdobeReader")
- Maintains file structure and formatting

✅ **Preserves**:
- All other Input keys unchanged
- All other recipe content unchanged
- File formatting and indentation
- Comments and whitespace (except within NAME value)

❌ **Skips**:
- Recipes where NAME has no spaces
- Recipes without a NAME key
- All other variables besides NAME

## Examples

### Example 1: Simple Two-Word Name

**Before**:
```xml
<key>NAME</key>
<string>VS Code</string>
```

**After**:
```xml
<key>NAME</key>
<string>VSCode</string>
```

### Example 2: Multi-Word Name

**Before**:
```xml
<key>NAME</key>
<string>Microsoft Visual Studio Code</string>
```

**After**:
```xml
<key>NAME</key>
<string>MicrosoftVisualStudioCode</string>
```

### Example 3: Name with Multiple Spaces

**Before**:
```xml
<key>NAME</key>
<string>Adobe   Creative   Cloud</string>
```

**After**:
```xml
<key>NAME</key>
<string>AdobeCreativeCloud</string>
```
*(All spaces removed, even multiple consecutive spaces)*

### Example 4: YAML Format

**Before**:
```yaml
Input:
  NAME: Google Chrome
  SEARCH_URL: https://google.com/chrome
```

**After**:
```yaml
Input:
  NAME: GoogleChrome
  SEARCH_URL: https://google.com/chrome
```

## Output

The script provides clear feedback:

```
NAMEChecker - NAME Variable Space Remover
==================================================

Processing 40 recipes...

✓ Modified AdobeReader.recipe
  - Changed NAME: "Adobe Reader" → "AdobeReader"

✓ Modified VSCode.recipe
  - Changed NAME: "VS Code" → "VSCode"

Skipping Firefox.recipe - NAME has no spaces
Skipping Slack.recipe - NAME has no spaces

==================================================
Processing complete!
Recipes processed: 40
Recipes modified: 2
==================================================

Modified files:
  ✓ AdobeReader.recipe
    - Changed NAME: "Adobe Reader" → "AdobeReader"
  ✓ VSCode.recipe
    - Changed NAME: "VS Code" → "VSCode"

Please verify these files in your version control system.
```

## Common Use Cases

1. **Recipe Creation**: Fix NAME after initial recipe creation
2. **Recipe Import**: Clean up recipes imported from other sources
3. **Standardization**: Ensure all recipes follow NAME conventions
4. **Pre-Commit Check**: Validate NAME format before version control commits
5. **Batch Cleanup**: Update entire recipe repositories at once

## NAME Variable Best Practices

### Recommended Formats

✅ **Good**:
- `Firefox` - Single word
- `GoogleChrome` - Camel case, no spaces
- `AdobeAcrobatDC` - Descriptive, no spaces
- `VSCode` - Abbreviation, no spaces

❌ **Avoid**:
- `Google Chrome` - Contains space
- `Adobe Reader DC` - Contains spaces
- `VS Code` - Contains space
- `Microsoft Teams` - Contains space

### Special Characters

The script only removes **spaces**. Other characters are preserved:
- Hyphens: `My-App` → `My-App` (unchanged)
- Underscores: `My_App` → `My_App` (unchanged)
- Numbers: `App123` → `App123` (unchanged)

## Integration with autopkg-linter.py

This linter is integrated into the AutoPkg Linter Suite as **Linter #14**:

```bash
# Run as part of the suite
/usr/local/autopkg/python autopkg-linter.py --linters 14 ~/recipes

# Include in a batch with other linters
/usr/local/autopkg/python autopkg-linter.py --linters 3,8,14 ~/recipes

# Run with all linters
/usr/local/autopkg/python autopkg-linter.py --all ~/recipes
```

## Troubleshooting

### Script Won't Run

**Error**: `This script should be run using AutoPkg's Python installation`

**Solution**: Use AutoPkg's Python:
```bash
/usr/local/autopkg/python NAMEChecker.py
```

### No Changes Made

If the script reports no changes:
- Your recipes may already have NAME values without spaces
- Check that recipes actually have a NAME variable defined
- Verify you're scanning the correct directory

### YAML Errors

**Error**: `PyYAML not available`

**Solution**: Install PyYAML in AutoPkg's Python:
```bash
/usr/local/autopkg/python -m pip install PyYAML
```

### Recipe Behavior Changes

If recipes behave differently after NAME change:
- Some recipes may use spaces in NAME intentionally (rare)
- Check if NAME is used in display names or descriptions
- Review git diffs to verify only NAME was changed

## Technical Details

### Plist Processing

- Uses regex to find NAME key in Input dict
- Extracts the value within `<string>` tags
- Removes all spaces using `str.replace(' ', '')`
- Performs text-based replacement to preserve formatting

### YAML Processing

- Uses PyYAML library for parsing
- Navigates to `Input.NAME` key
- Removes spaces from value
- Preserves YAML structure and formatting

### Format Preservation

The script uses text manipulation (not XML/YAML parsing) for plist files to:
- Preserve exact indentation
- Maintain comments
- Keep original formatting
- Only change the NAME value itself

## Best Practices

- **Run Early**: Check NAME when creating new recipes
- **Test Recipes**: Run `autopkg run --check` after modifying NAME
- **Review Changes**: Use git diff to verify only NAME was modified
- **Update Documentation**: If NAME changes, update recipe comments
- **Consistent Naming**: Use consistent NAME format across related recipes

## Impact on Recipe Variables

NAME is often used in variable substitutions:

```xml
<key>NAME</key>
<string>GoogleChrome</string>

<!-- Used throughout recipe -->
<string>%NAME%.app</string>         → GoogleChrome.app
<string>%NAME%.pkg</string>         → GoogleChrome.pkg
<string>com.example.%NAME%</string> → com.example.GoogleChrome
```

If NAME had spaces, these become:
```xml
<string>Google Chrome.app</string>  → ⚠️ Problems!
```

## Related Linters

- **RecipeAlphabetiser** (#8): Alphabetizes Input keys (including NAME)
- **DetabChecker** (#3): Fixes whitespace formatting
- **MinimumVersionChecker** (#6): Sets correct MinimumVersion

## Support

For issues, questions, or contributions, please refer to the main repository README.

## License

Part of the AutoPkg Recipe Linter Suite.

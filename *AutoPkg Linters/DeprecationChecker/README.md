# DeprecationChecker

An AutoPkg utility script that validates and fixes recipes containing the `DeprecationWarning` processor. This script ensures deprecated recipes are properly configured to warn users and optionally stop processing.

## Features

- **Automatic Position Correction**: Moves `DeprecationWarning` to the top of the Process array
- **Version Validation**: Ensures `MinimumVersion` is at least `1.1` (required for DeprecationWarning)
- **Optional Stop Processing**: Interactively asks to add `StopProcessingIf` processor to halt execution
- **Multi-Format Support**: Handles both plist (`.recipe`) and YAML (`.yaml`) recipe formats
- **Batch Processing**: Processes multiple recipes in a single run
- **Safe Modifications**: Preserves formatting with proper 4-space indentation

## What It Does

The script performs three main checks and fixes:

### 1. DeprecationWarning Position
Ensures `DeprecationWarning` is the **first processor** in the `Process` array. This guarantees users see the deprecation message before any other processing occurs.

### 2. MinimumVersion Check
Verifies that `MinimumVersion` is set to at least `1.1`. The `DeprecationWarning` processor requires AutoPkg version 1.1 or higher.

### 3. StopProcessingIf Addition (Optional)
Offers to add a `StopProcessingIf` processor immediately after `DeprecationWarning` to prevent further execution. This is useful when a recipe has been completely replaced.

## Example Transformation

### Before
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
            <string>URLDownloader</string>
        </dict>
        <dict>
            <key>Processor</key>
            <string>DeprecationWarning</string>
            <key>Arguments</key>
            <dict>
                <key>warning_message</key>
                <string>This recipe is deprecated.</string>
            </dict>
        </dict>
    </array>
</dict>
</plist>
```

### After
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>MinimumVersion</key>
    <string>1.1</string>
    <key>Process</key>
    <array>
        <dict>
            <key>Processor</key>
            <string>DeprecationWarning</string>
            <key>Arguments</key>
            <dict>
                <key>warning_message</key>
                <string>This recipe is deprecated.</string>
            </dict>
        </dict>
        <dict>
            <key>Processor</key>
            <string>StopProcessingIf</string>
            <key>Arguments</key>
            <dict>
                <key>predicate</key>
                <string>TRUEPREDICATE</string>
            </dict>
        </dict>
        <dict>
            <key>Processor</key>
            <string>URLDownloader</string>
        </dict>
    </array>
</dict>
</plist>
```

## Requirements

- **AutoPkg**: Must be installed with its bundled Python environment at `/usr/local/autopkg/python`
- **Python 3**: Included with AutoPkg installation
- **Required Python modules**: `yaml` (for YAML recipe support)

## Installation

1. Download `DeprecationChecker.py` to a convenient location
2. Make the script executable (optional):
   ```bash
   chmod +x DeprecationChecker.py
   ```

## Usage

### Running the Script

Execute the script using AutoPkg's Python installation:

```bash
/usr/local/autopkg/python DeprecationChecker.py
```

### Interactive Prompt

When run, the script will:

1. Prompt for a recipe directory path
2. Scan all `.recipe` and `.recipe.yaml` files
3. Process recipes containing `DeprecationWarning`
4. Ask interactively whether to add `StopProcessingIf` for each recipe

```
DeprecationChecker - AutoPkg Recipe Processor
==================================================
This script will:
1. Check for DeprecationWarning processor
2. Ensure it's at the top of the Process array
3. Ensure MinimumVersion is at least 1.1
4. Optionally add StopProcessingIf processor
==================================================

Enter the path to your recipe directory
(You can drag and drop the folder here):
```

### Example Session

```
Enter the path to your recipe directory
(You can drag and drop the folder here): /Users/username/autopkg/recipes

Scanning recipes in: /Users/username/autopkg/recipes

Found DeprecationWarning in: /Users/username/autopkg/recipes/OldApp.download.recipe

Recipe: OldApp.download.recipe
    Add StopProcessingIf processor after DeprecationWarning? (y/n): y
✓ Successfully modified and verified: /Users/username/autopkg/recipes/OldApp.download.recipe

==================================================
Processing complete!
Recipes processed: 10
Recipes modified: 1
==================================================

Modified files:
  ✓ /Users/username/autopkg/recipes/OldApp.download.recipe
```

## StopProcessingIf Processor

When you choose to add the `StopProcessingIf` processor, it's configured with:

```xml
<dict>
    <key>Processor</key>
    <string>StopProcessingIf</string>
    <key>Arguments</key>
    <dict>
        <key>predicate</key>
        <string>TRUEPREDICATE</string>
    </dict>
</dict>
```

- **`TRUEPREDICATE`**: Always evaluates to true, ensuring the recipe stops after showing the deprecation warning
- **Position**: Placed immediately after `DeprecationWarning`
- **Use Case**: Ideal for recipes that have been completely replaced and should not continue processing

## When to Add StopProcessingIf

### Add it when:
- ✅ The recipe has been completely replaced by another recipe
- ✅ You want to prevent any further processing after the warning
- ✅ The recipe should only display a message and exit

### Don't add it when:
- ❌ The recipe is still functional but deprecated (soft deprecation)
- ❌ You want users to see a warning but still allow the recipe to run
- ❌ The deprecation is informational only

## Formatting Standards

The script follows AutoPkg best practices:

- **Indentation**: 4 spaces per level (no tabs)
- **Consistency**: Matches existing recipe formatting
- **Structure**: Preserves all original content and comments

## Safety Features

- **Non-Destructive**: Only modifies recipes with `DeprecationWarning`
- **Interactive**: Asks before adding `StopProcessingIf`
- **Verification**: Validates file writes to ensure changes are correct
- **Environment Check**: Ensures it runs in AutoPkg's Python environment
- **Skip Logic**: Skips recipes that are already properly configured

## Output and Debugging

The script provides comprehensive output:

- **Progress indicators**: Shows which recipes are being processed
- **Debug information**: Detailed processing steps (prefixed with `DEBUG:`)
- **Modification summary**: Lists all modified files
- **Error handling**: Clear error messages with full tracebacks

## Troubleshooting

### Script Won't Run

**Error**: `This script should be run using AutoPkg's Python installation`

**Solution**: Use the full path to AutoPkg's Python:
```bash
/usr/local/autopkg/python DeprecationChecker.py
```

### No Recipes Found

The script only processes recipes that contain `DeprecationWarning`. If no recipes are found, verify:

1. You're pointing to the correct directory
2. The directory contains `.recipe` or `.recipe.yaml` files
3. Those recipes have a `DeprecationWarning` processor

### MinimumVersion Not Updated

If `MinimumVersion` already exists with a value >= 1.1, it won't be changed. The script only updates versions that are too low.

### DeprecationWarning Not Found

Check that the processor name is exactly `DeprecationWarning` (case-sensitive) in the recipe.

## Command Line Tips

You can drag and drop a folder from Finder into the terminal window when prompted for the path:

```
Enter the path to your recipe directory
(You can drag and drop the folder here): [drag folder here]
```

The script will automatically clean up the path, handling:
- Spaces in directory names
- Escaped characters
- Trailing slashes
- Home directory shortcuts (`~`)

## Use Cases

### Deprecated Recipe Migration

When migrating recipes to a new repository:

1. Run DeprecationChecker on old recipes
2. Add `StopProcessingIf` to prevent execution
3. Update `warning_message` to point users to new recipes

### Soft Deprecation

For recipes that still work but have better alternatives:

1. Run DeprecationChecker
2. Choose **not** to add `StopProcessingIf`
3. Users see the warning but can still use the recipe

## File Format Support

| Format | Extension | Support |
|--------|-----------|---------|
| Plist | `.recipe` | ✅ Full |
| YAML | `.recipe.yaml` | ✅ Full |

## Best Practices

1. **Review Changes**: Always check modified recipes in version control before committing
2. **Update Messages**: Ensure `warning_message` includes helpful information about alternatives
3. **Version Control**: Commit changes with clear messages about deprecation updates
4. **Test Recipes**: Run recipes after modification to verify they work correctly

## Limitations

- Only processes recipes that already contain `DeprecationWarning`
- Does not add `DeprecationWarning` to recipes that don't have it
- Requires interactive input for `StopProcessingIf` decisions
- Uses 4-space indentation (AutoPkg standard)

## Contributing

When modifying this script:

1. Test with both plist and YAML recipes
2. Verify indentation is exactly 4 spaces (no tabs)
3. Ensure `DeprecationWarning` remains at index 0
4. Test interactive prompts work correctly
5. Update this README with changes

## Related Processors

- **DeprecationWarning**: AutoPkg processor for displaying deprecation messages
- **StopProcessingIf**: AutoPkg processor for conditionally halting recipe execution
- **EndOfCheckPhase**: Alternative processor for stopping recipe processing

## References

- [AutoPkg Documentation](https://github.com/autopkg/autopkg/wiki)
- [DeprecationWarning Processor](https://github.com/autopkg/autopkg/wiki/Processor-DeprecationWarning)
- [StopProcessingIf Processor](https://github.com/autopkg/autopkg/wiki/Processor-StopProcessingIf)

## Author

Paul Cossey

## Version History

- **Current**: Initial release with plist and YAML support, interactive StopProcessingIf addition

---

For more information about AutoPkg processors and recipe management, visit [https://github.com/autopkg/autopkg](https://github.com/autopkg/autopkg)

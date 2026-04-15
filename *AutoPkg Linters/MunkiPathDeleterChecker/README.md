# MunkiPathDeleterChecker

An AutoPkg utility script that ensures Munki recipes properly clean up temporary directories created by unpacking processors. This script automatically adds or updates the `PathDeleter` processor to remove temporary files, and ensures it's positioned as the last processor in the Process array.

## Features

- **Automatic Detection**: Finds unpacking processors (`FlatPkgUnpacker`, `PkgPayloadUnpacker`, `Unarchiver`)
- **Path Extraction**: Extracts `destination_path` values from unpacking processors
- **PathDeleter Creation**: Adds PathDeleter processor if missing
- **Path Validation**: Ensures PathDeleter includes all necessary paths
- **Position Correction**: Moves PathDeleter to last position if misplaced
- **Munki-Specific**: Only processes `.munki` recipes
- **Multi-Format Support**: Handles both plist (`.recipe`) and YAML (`.yaml`) recipe formats
- **Batch Processing**: Processes multiple recipes in a single run
- **Detailed Reporting**: Shows exactly what was added or modified

## Why PathDeleter Matters

Unpacking processors create temporary directories to extract package contents. Without proper cleanup:

- **Disk Space**: Temporary files accumulate over time
- **Security**: Sensitive files may remain on disk
- **Clutter**: Unnecessary directories fill up system
- **Best Practice**: Proper resource management

The `PathDeleter` processor ensures these temporary directories are removed after the recipe completes.

## What It Does

The script performs several checks and corrections:

1. **Identifies Munki Recipes**: Only processes recipes with `.munki` in the identifier
2. **Finds Unpacking Processors**: Looks for:
   - `FlatPkgUnpacker` (unpacks flat packages)
   - `PkgPayloadUnpacker` (extracts package payloads)
   - `Unarchiver` (decompresses archives)
3. **Extracts Paths**: Collects all `destination_path` values from these processors
4. **Checks PathDeleter**: Verifies PathDeleter processor exists
5. **Validates Paths**: Ensures all destination paths are in PathDeleter's `path_list`
6. **Positions Correctly**: Moves PathDeleter to last position in Process array
7. **Adds If Missing**: Creates PathDeleter with correct paths if it doesn't exist

## Requirements

- **AutoPkg**: Must be installed with its bundled Python environment at `/usr/local/autopkg/python`
- **Python 3**: Included with AutoPkg installation
- **PyYAML**: Required only for YAML recipe support (usually pre-installed with AutoPkg)
- **No external dependencies**: Uses Python standard library (plistlib)

## Installation

1. Download `MunkiPathDeleterChecker.py` to a convenient location
2. Make the script executable (optional):
   ```bash
   chmod +x MunkiPathDeleterChecker.py
   ```

## Usage

### Running the Script

Execute the script using AutoPkg's Python installation:

```bash
/usr/local/autopkg/python MunkiPathDeleterChecker.py
```

### Interactive Prompt

When run, the script will prompt for a recipe directory:

```
MunkiPathDeleterChecker - AutoPkg Recipe Cleanup Validator
==================================================
This script will:
1. Find unpacking processors (FlatPkgUnpacker, etc.)
2. Extract their destination_path values
3. Ensure PathDeleter exists with those paths
4. Move PathDeleter to last position if needed
5. Add missing paths to existing PathDeleter
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

✓ Updated App.munki.recipe
  Added PathDeleter with 2 path(s)
    - %RECIPE_CACHE_DIR%/unpack
    - %RECIPE_CACHE_DIR%/payload

✓ Updated Another.munki.recipe
  Moved PathDeleter to last position

✓ Updated Third.munki.recipe
  Added 1 missing path(s) to PathDeleter
    - %RECIPE_CACHE_DIR%/expanded

Skipping Good.munki.recipe - PathDeleter already correct

==================================================
Processing complete!
Recipes scanned: 25
Munki recipes checked: 15
Recipes modified: 3
Recipes without unpacking: 8
==================================================

Modified files:

  ✓ App.munki.recipe:
    Added PathDeleter with 2 path(s)
      - %RECIPE_CACHE_DIR%/unpack
      - %RECIPE_CACHE_DIR%/payload

  ✓ Another.munki.recipe:
    Moved PathDeleter to last position

  ✓ Third.munki.recipe:
    Added 1 missing path(s) to PathDeleter
      - %RECIPE_CACHE_DIR%/expanded

Please verify these files in your version control system.
```

## Unpacking Processors Detected

The script recognizes three types of unpacking processors:

### 1. FlatPkgUnpacker

Unpacks flat packages (`.pkg` files):

```xml
<dict>
    <key>Arguments</key>
    <dict>
        <key>flat_pkg_path</key>
        <string>%pathname%</string>
        <key>destination_path</key>
        <string>%RECIPE_CACHE_DIR%/unpack</string>
    </dict>
    <key>Processor</key>
    <string>FlatPkgUnpacker</string>
</dict>
```

### 2. PkgPayloadUnpacker

Extracts package payloads:

```xml
<dict>
    <key>Arguments</key>
    <dict>
        <key>pkg_payload_path</key>
        <string>%RECIPE_CACHE_DIR%/unpack/Payload</string>
        <key>destination_path</key>
        <string>%RECIPE_CACHE_DIR%/payload</string>
    </dict>
    <key>Processor</key>
    <string>PkgPayloadUnpacker</string>
</dict>
```

### 3. Unarchiver

Decompresses archives (`.zip`, `.tar.gz`, `.dmg`, etc.):

```xml
<dict>
    <key>Arguments</key>
    <dict>
        <key>archive_path</key>
        <string>%pathname%</string>
        <key>destination_path</key>
        <string>%RECIPE_CACHE_DIR%/expanded</string>
    </dict>
    <key>Processor</key>
    <string>Unarchiver</string>
</dict>
```

## PathDeleter Processor

The script adds or updates the PathDeleter processor:

```xml
<dict>
    <key>Arguments</key>
    <dict>
        <key>path_list</key>
        <array>
            <string>%RECIPE_CACHE_DIR%/unpack</string>
            <string>%RECIPE_CACHE_DIR%/payload</string>
        </array>
    </dict>
    <key>Processor</key>
    <string>PathDeleter</string>
</dict>
```

### Key Requirements

- Must be the **last** processor in the Process array
- Must include **all** destination paths from unpacking processors
- Uses `path_list` array to specify paths to delete

## Example Scenarios

### Scenario 1: Missing PathDeleter

**Before:**
```xml
<key>Process</key>
<array>
    <dict>
        <key>Processor</key>
        <string>FlatPkgUnpacker</string>
        <key>Arguments</key>
        <dict>
            <key>destination_path</key>
            <string>%RECIPE_CACHE_DIR%/unpack</string>
        </dict>
    </dict>
    <dict>
        <key>Processor</key>
        <string>MunkiImporter</string>
    </dict>
</array>
```

**After:**
```xml
<key>Process</key>
<array>
    <dict>
        <key>Processor</key>
        <string>FlatPkgUnpacker</string>
        <key>Arguments</key>
        <dict>
            <key>destination_path</key>
            <string>%RECIPE_CACHE_DIR%/unpack</string>
        </dict>
    </dict>
    <dict>
        <key>Processor</key>
        <string>MunkiImporter</string>
    </dict>
    <dict>
        <key>Arguments</key>
        <dict>
            <key>path_list</key>
            <array>
                <string>%RECIPE_CACHE_DIR%/unpack</string>
            </array>
        </dict>
        <key>Processor</key>
        <string>PathDeleter</string>
    </dict>
</array>
```

**Result:** `Added PathDeleter with 1 path(s)`

### Scenario 2: PathDeleter in Wrong Position

**Before:**
```xml
<key>Process</key>
<array>
    <dict>
        <key>Processor</key>
        <string>FlatPkgUnpacker</string>
    </dict>
    <dict>
        <key>Processor</key>
        <string>PathDeleter</string>
        <!-- PathDeleter here is too early -->
    </dict>
    <dict>
        <key>Processor</key>
        <string>MunkiImporter</string>
    </dict>
</array>
```

**After:**
```xml
<key>Process</key>
<array>
    <dict>
        <key>Processor</key>
        <string>FlatPkgUnpacker</string>
    </dict>
    <dict>
        <key>Processor</key>
        <string>MunkiImporter</string>
    </dict>
    <dict>
        <key>Processor</key>
        <string>PathDeleter</string>
        <!-- PathDeleter moved to last position -->
    </dict>
</array>
```

**Result:** `Moved PathDeleter to last position`

### Scenario 3: Missing Paths in PathDeleter

**Before:**
```xml
<dict>
    <key>Processor</key>
    <string>FlatPkgUnpacker</string>
    <key>Arguments</key>
    <dict>
        <key>destination_path</key>
        <string>%RECIPE_CACHE_DIR%/unpack</string>
    </dict>
</dict>
<dict>
    <key>Processor</key>
    <string>PkgPayloadUnpacker</string>
    <key>Arguments</key>
    <dict>
        <key>destination_path</key>
        <string>%RECIPE_CACHE_DIR%/payload</string>
    </dict>
</dict>
<!-- ... -->
<dict>
    <key>Processor</key>
    <string>PathDeleter</string>
    <key>Arguments</key>
    <dict>
        <key>path_list</key>
        <array>
            <string>%RECIPE_CACHE_DIR%/unpack</string>
            <!-- Missing payload path! -->
        </array>
    </dict>
</dict>
```

**After:**
```xml
<!-- PathDeleter now includes both paths -->
<dict>
    <key>Processor</key>
    <string>PathDeleter</string>
    <key>Arguments</key>
    <dict>
        <key>path_list</key>
        <array>
            <string>%RECIPE_CACHE_DIR%/unpack</string>
            <string>%RECIPE_CACHE_DIR%/payload</string>
        </array>
    </dict>
</dict>
```

**Result:** `Added 1 missing path(s) to PathDeleter`

### Scenario 4: Multiple Unpacking Steps

Recipe that unpacks a flat package, then extracts the payload, then unarchives:

```xml
<key>Process</key>
<array>
    <dict>
        <key>Processor</key>
        <string>FlatPkgUnpacker</string>
        <key>Arguments</key>
        <dict>
            <key>destination_path</key>
            <string>%RECIPE_CACHE_DIR%/unpack</string>
        </dict>
    </dict>
    <dict>
        <key>Processor</key>
        <string>PkgPayloadUnpacker</string>
        <key>Arguments</key>
        <dict>
            <key>destination_path</key>
            <string>%RECIPE_CACHE_DIR%/payload</string>
        </dict>
    </dict>
    <dict>
        <key>Processor</key>
        <string>Unarchiver</string>
        <key>Arguments</key>
        <dict>
            <key>destination_path</key>
            <string>%RECIPE_CACHE_DIR%/expanded</string>
        </dict>
    </dict>
    <dict>
        <key>Processor</key>
        <string>MunkiImporter</string>
    </dict>
</array>
```

**Script adds PathDeleter with all three paths:**
```xml
<dict>
    <key>Arguments</key>
    <dict>
        <key>path_list</key>
        <array>
            <string>%RECIPE_CACHE_DIR%/unpack</string>
            <string>%RECIPE_CACHE_DIR%/payload</string>
            <string>%RECIPE_CACHE_DIR%/expanded</string>
        </array>
    </dict>
    <key>Processor</key>
    <string>PathDeleter</string>
</dict>
```

## Output Details

The script provides comprehensive information:

- **Per-recipe changes**: Lists what was added or modified
- **Path details**: Shows which paths were added to PathDeleter
- **Position changes**: Indicates when PathDeleter was moved
- **Recipe counts**: Reports total recipes scanned and modified
- **Skip reasons**: Shows how many recipes were skipped and why

## When to Use MunkiPathDeleterChecker

### Ideal Use Cases

- ✅ **After creating new recipes** with unpacking processors
- ✅ **Repository audits** to ensure all recipes clean up properly
- ✅ **Before committing** recipes to version control
- ✅ **Migration projects** when updating old recipes
- ✅ **Quality assurance** as part of recipe review process
- ✅ **Automated validation** in CI/CD pipelines

### Recipes That Need This

- Munki recipes that unpack flat packages
- Munki recipes that extract package payloads
- Munki recipes that decompress archives
- Any munki recipe with temporary directory creation

### Recipes That Don't Need This

- Download recipes (no munki import)
- Pkg recipes (no munki import)
- Recipes without unpacking processors
- Recipes that use variables for import (already cleaned by AutoPkg)

## Safety Features

- **Non-Destructive**: Only modifies Munki recipes with unpacking
- **Munki-Specific**: Won't modify download or pkg recipes
- **Existing PathDeleter**: Updates rather than replaces existing PathDeleter
- **Path Preservation**: Keeps existing paths, only adds missing ones
- **Environment Check**: Ensures it runs in AutoPkg's Python environment
- **Error Handling**: Clear error messages with full tracebacks

## Integration with Other Tools

MunkiPathDeleterChecker works well alongside:

- **DetabChecker**: Run DetabChecker after to fix any formatting
- **RecipeAlphabetiser**: Alphabetize keys after adding PathDeleter
- **DeprecationChecker**: Validate recipes before adding PathDeleter
- **MinimumVersionChecker**: Ensure version compatibility

## Recommended Workflow

1. **Create/Modify Recipe**: Add unpacking processors as needed
2. **MunkiPathDeleterChecker**: Ensure cleanup is configured
3. **RecipeAlphabetiser**: Organize keys consistently
4. **DetabChecker**: Fix whitespace issues
5. **Review**: Check the changes in version control
6. **Commit**: Push the complete recipe

## Troubleshooting

### Script Won't Run

**Error**: `This script should be run using AutoPkg's Python installation`

**Solution**: Use the full path to AutoPkg's Python:
```bash
/usr/local/autopkg/python MunkiPathDeleterChecker.py
```

### YAML Support Missing

**Error**: `PyYAML not available for processing`

**Solution**: Install PyYAML in AutoPkg's Python:
```bash
/usr/local/autopkg/python -m pip install PyYAML
```

### No Recipes Modified

If no recipes are modified:
- ✅ Your recipes already have correct PathDeleter (good!)
- Check that you're scanning munki recipes (not download/pkg)
- Verify recipes have unpacking processors
- Check if recipes are `.munki.recipe` format

### PathDeleter Not Added

If PathDeleter wasn't added when expected:

1. **Check Identifier**: Must contain `.munki`
2. **Check Processors**: Must have FlatPkgUnpacker, PkgPayloadUnpacker, or Unarchiver
3. **Check destination_path**: Unpacking processor must have this key
4. **Review Output**: Script shows why recipes were skipped

## Command Line Tips

### Check If Recipe Needs PathDeleter

```bash
# Look for unpacking processors
grep -A 5 "FlatPkgUnpacker\|PkgPayloadUnpacker\|Unarchiver" recipe.munki.recipe

# Check if PathDeleter exists
grep "PathDeleter" recipe.munki.recipe
```

### Find Recipes Without PathDeleter

```bash
# Find munki recipes with unpacking but no PathDeleter
grep -l "FlatPkgUnpacker" *.munki.recipe | while read recipe; do
    grep -q "PathDeleter" "$recipe" || echo "$recipe needs PathDeleter"
done
```

### Count Unpacking Processors

```bash
# Count FlatPkgUnpacker usage
grep -c "FlatPkgUnpacker" *.munki.recipe

# Count all unpacking processors
grep -c "FlatPkgUnpacker\|PkgPayloadUnpacker\|Unarchiver" *.munki.recipe
```

## Performance

MunkiPathDeleterChecker is highly efficient:

- **Fast Scanning**: Quick identifier check before processing
- **Targeted Processing**: Only handles munki recipes with unpacking
- **Low Memory**: Processes one file at a time
- **Minimal Dependencies**: Only plistlib and optionally PyYAML

Typical performance:
- ~100 recipes: < 10 seconds
- ~1000 recipes: < 60 seconds

## Best Practices

1. **Run After Unpacking Changes**: Anytime you modify unpacking processors
2. **Include in Review Process**: Check PathDeleter during recipe reviews
3. **Automate**: Add to pre-commit hooks or CI/CD
4. **Verify Changes**: Always review diffs before committing
5. **Document**: Note why specific paths are being deleted
6. **Test Recipes**: Run recipes after adding PathDeleter to verify cleanup

## Pre-Commit Hook Example

Automate PathDeleter validation with a git pre-commit hook:

```bash
#!/bin/bash
# .git/hooks/pre-commit

MUNKI_RECIPES=$(git diff --cached --name-only --diff-filter=ACM | grep '\.munki\.recipe')

if [ -n "$MUNKI_RECIPES" ]; then
    for recipe in $MUNKI_RECIPES; do
        # Check if recipe has unpacking but no PathDeleter
        if grep -q "FlatPkgUnpacker\|PkgPayloadUnpacker\|Unarchiver" "$recipe"; then
            if ! grep -q "PathDeleter" "$recipe"; then
                echo "Error: $recipe has unpacking but no PathDeleter"
                echo "Run MunkiPathDeleterChecker.py to fix this issue"
                exit 1
            fi
        fi
    done
fi
```

## Advanced Usage

### Verify PathDeleter Position

To check if PathDeleter is in the last position:

```bash
# Extract Process array and check last processor
plutil -extract Process xml1 -o - recipe.munki.recipe | \
    grep -A 1 "<key>Processor</key>" | \
    tail -2
```

### List All Destination Paths

To see all destination paths in a recipe:

```bash
# Extract destination_path values
plutil -extract Process xml1 -o - recipe.munki.recipe | \
    grep -A 1 "destination_path" | \
    grep "<string>" | \
    sed 's/.*<string>\(.*\)<\/string>.*/\1/'
```

## File Format Support

| Format | Extension | Support | Notes |
|--------|-----------|---------|-------|
| Plist | `.recipe` | ✅ Full | Native plistlib support |
| YAML | `.recipe.yaml` | ✅ Full | Requires PyYAML |
| YAML | `.yaml` | ✅ Full | Requires PyYAML |

## Common Destination Paths

Typical destination_path values used in recipes:

| Path | Purpose |
|------|---------|
| `%RECIPE_CACHE_DIR%/unpack` | Unpacked flat package |
| `%RECIPE_CACHE_DIR%/payload` | Extracted payload |
| `%RECIPE_CACHE_DIR%/expanded` | Unarchived contents |
| `%RECIPE_CACHE_DIR%/Scripts` | Extracted scripts |
| `%RECIPE_CACHE_DIR%/pkg` | Temporary package directory |

All of these should be included in PathDeleter's `path_list`.

## Limitations

- Only processes `.munki` recipes (by identifier)
- Only detects FlatPkgUnpacker, PkgPayloadUnpacker, and Unarchiver
- Requires `destination_path` key in processor Arguments
- Does not validate if paths actually exist at runtime
- Does not remove extra paths from PathDeleter (only adds missing ones)

## Contributing

When modifying this script:

1. Test with recipes using FlatPkgUnpacker
2. Test with recipes using PkgPayloadUnpacker  
3. Test with recipes using Unarchiver
4. Test with recipes using multiple unpacking processors
5. Test PathDeleter positioning logic
6. Test path addition to existing PathDeleter
7. Update this README with changes

## Related Tools

- **DetabChecker**: Fix tab and whitespace issues
- **RecipeAlphabetiser**: Organize dictionary keys
- **DeprecationChecker**: Add deprecation warnings
- **MinimumVersionChecker**: Validate AutoPkg version requirements

## References

- [PathDeleter Processor](https://github.com/autopkg/autopkg/wiki/Processor-PathDeleter)
- [FlatPkgUnpacker Processor](https://github.com/autopkg/autopkg/wiki/Processor-FlatPkgUnpacker)
- [PkgPayloadUnpacker Processor](https://github.com/autopkg/autopkg/wiki/Processor-PkgPayloadUnpacker)
- [Unarchiver Processor](https://github.com/autopkg/autopkg/wiki/Processor-Unarchiver)
- [AutoPkg Recipe Format](https://github.com/autopkg/autopkg/wiki/Recipe-Format)

## Author

Paul Cossey

## Version History

- **Current**: Initial release with automatic PathDeleter validation and correction

---

For more information about AutoPkg processor best practices, visit [https://github.com/autopkg/autopkg](https://github.com/autopkg/autopkg)

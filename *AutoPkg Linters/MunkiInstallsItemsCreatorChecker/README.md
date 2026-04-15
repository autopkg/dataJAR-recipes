# MunkiInstallsItemsCreator Validator

An AutoPkg utility script that ensures recipes using the `MunkiInstallsItemsCreator` processor are properly configured. This script validates and fixes five critical requirements for proper installs array generation and minimum OS version detection.

## Features

- **derive_minimum_os_version Key**: Ensures the key exists in MunkiInstallsItemsCreator Arguments
- **MunkiPkginfoMerger Validation**: Adds empty MunkiPkginfoMerger immediately after if missing
- **DERIVE_MIN_OS Input Variable**: Adds the required Input variable with default value
- **Description Instructions**: Adds usage instructions to recipe Description
- **MinimumVersion Update**: Ensures MinimumVersion is 2.7 or higher
- **Multi-Format Support**: Handles both plist (`.recipe`) and YAML (`.yaml`) recipe formats
- **Batch Processing**: Processes multiple recipes in a single run
- **Smart Detection**: Only modifies recipes that use MunkiInstallsItemsCreator

## Why This Matters

The `MunkiInstallsItemsCreator` processor is powerful but requires specific configuration:

1. **derive_minimum_os_version**: Without this key, the processor won't generate minimum_os_version in pkginfo
2. **MunkiPkginfoMerger**: Required immediately after to merge the generated installs array into pkginfo
3. **DERIVE_MIN_OS Variable**: Provides user control over whether to derive minimum OS version
4. **AutoPkg 2.7**: MunkiInstallsItemsCreator requires AutoPkg 2.7 or later
5. **Documentation**: Users need to know how to use the DERIVE_MIN_OS variable

## What It Does

The script performs five validation checks:

### 1. Add derive_minimum_os_version Key

Ensures MunkiInstallsItemsCreator has the `derive_minimum_os_version` argument:

**Before:**
```xml
<dict>
    <key>Arguments</key>
    <dict>
        <key>installs_item_paths</key>
        <array>
            <string>/Applications/App.app</string>
        </array>
    </dict>
    <key>Processor</key>
    <string>MunkiInstallsItemsCreator</string>
</dict>
```

**After:**
```xml
<dict>
    <key>Arguments</key>
    <dict>
        <key>installs_item_paths</key>
        <array>
            <string>/Applications/App.app</string>
        </array>
        <key>derive_minimum_os_version</key>
        <string>%DERIVE_MIN_OS%</string>
    </dict>
    <key>Processor</key>
    <string>MunkiInstallsItemsCreator</string>
</dict>
```

### 2. Add Empty MunkiPkginfoMerger

Ensures an empty `MunkiPkginfoMerger` processor immediately follows:

**Before:**
```xml
<array>
    <dict>
        <key>Processor</key>
        <string>MunkiInstallsItemsCreator</string>
    </dict>
    <dict>
        <key>Processor</key>
        <string>MunkiImporter</string>
    </dict>
</array>
```

**After:**
```xml
<array>
    <dict>
        <key>Processor</key>
        <string>MunkiInstallsItemsCreator</string>
    </dict>
    <dict>
        <key>Processor</key>
        <string>MunkiPkginfoMerger</string>
    </dict>
    <dict>
        <key>Processor</key>
        <string>MunkiImporter</string>
    </dict>
</array>
```

### 3. Add DERIVE_MIN_OS Input Variable

Adds the `DERIVE_MIN_OS` variable to the Input dict:

**Before:**
```xml
<key>Input</key>
<dict>
    <key>NAME</key>
    <string>AppName</string>
    <key>MUNKI_REPO_SUBDIR</key>
    <string>apps/%NAME%</string>
</dict>
```

**After:**
```xml
<key>Input</key>
<dict>
    <key>NAME</key>
    <string>AppName</string>
    <key>MUNKI_REPO_SUBDIR</key>
    <string>apps/%NAME%</string>
    <key>DERIVE_MIN_OS</key>
    <string>YES</string>
</dict>
```

### 4. Add Usage Instructions to Description

Appends instructions to the Description unless already present:

**Before:**
```xml
<key>Description</key>
<string>Downloads the latest version of JUCE and imports it into Munki.</string>
```

**After:**
```xml
<key>Description</key>
<string>Downloads the latest version of JUCE and imports it into Munki.

Set the DERIVE_MIN_OS variable to a non-empty string to set the minimum_os_version via MunkiInstallsItemsCreator.</string>
```

**Note:** If description already contains "Set the DERIVE_MIN_OS", it won't be modified.

### 5. Update MinimumVersion

Ensures MinimumVersion is at least 2.7:

**Before:**
```xml
<key>MinimumVersion</key>
<string>1.0</string>
```

**After:**
```xml
<key>MinimumVersion</key>
<string>2.7</string>
```

## Requirements

- **AutoPkg**: Must be installed with its bundled Python environment at `/usr/local/autopkg/python`
- **Python 3**: Included with AutoPkg installation
- **PyYAML**: Required only for YAML recipe support (usually pre-installed with AutoPkg)
- **No external dependencies**: Uses Python standard library (plistlib)

## Installation

1. Download `MunkiInstallsItemsCreator.py` to a convenient location
2. Make the script executable (optional):
   ```bash
   chmod +x MunkiInstallsItemsCreator.py
   ```

## Usage

### Running the Script

Execute the script using AutoPkg's Python installation:

```bash
/usr/local/autopkg/python MunkiInstallsItemsCreator.py
```

### Interactive Prompt

When run, the script will prompt for a recipe directory:

```
MunkiInstallsItemsCreator - Recipe Configuration Validator
==================================================
This script will:
1. Find MunkiInstallsItemsCreator processors
2. Add derive_minimum_os_version key if missing
3. Add empty MunkiPkginfoMerger after if missing
4. Add DERIVE_MIN_OS to Input dict
5. Add usage instructions to Description
6. Update MinimumVersion to 2.7 if needed
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

✓ Updated JUCE.munki.recipe
  - Added derive_minimum_os_version to MunkiInstallsItemsCreator
  - Added empty MunkiPkginfoMerger after MunkiInstallsItemsCreator
  - Added DERIVE_MIN_OS to Input dict
  - Added DERIVE_MIN_OS instructions to Description
  - Updated MinimumVersion from 1.0 to 2.7

✓ Updated AnotherApp.munki.recipe
  - Added derive_minimum_os_version to MunkiInstallsItemsCreator
  - Added DERIVE_MIN_OS to Input dict

Skipping GoodRecipe.munki.recipe - already configured correctly

==================================================
Processing complete!
Recipes scanned: 25
Recipes modified: 2
==================================================

Modified files:

  ✓ JUCE.munki.recipe:
    - Added derive_minimum_os_version to MunkiInstallsItemsCreator
    - Added empty MunkiPkginfoMerger after MunkiInstallsItemsCreator
    - Added DERIVE_MIN_OS to Input dict
    - Added DERIVE_MIN_OS instructions to Description
    - Updated MinimumVersion from 1.0 to 2.7

  ✓ AnotherApp.munki.recipe:
    - Added derive_minimum_os_version to MunkiInstallsItemsCreator
    - Added DERIVE_MIN_OS to Input dict

Please verify these files in your version control system.
```

## Complete Example Recipe

Here's a fully configured recipe after running the script:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Description</key>
    <string>Downloads the latest version of JUCE and imports it into Munki.

Set the DERIVE_MIN_OS variable to a non-empty string to set the minimum_os_version via MunkiInstallsItemsCreator.</string>
    <key>Identifier</key>
    <string>com.github.dataJAR-recipes.munki.JUCE</string>
    <key>Input</key>
    <dict>
        <key>MUNKI_REPO_SUBDIR</key>
        <string>apps/%NAME%</string>
        <key>NAME</key>
        <string>JUCE</string>
        <key>DERIVE_MIN_OS</key>
        <string>YES</string>
        <key>pkginfo</key>
        <dict>
            <key>catalogs</key>
            <array>
                <string>testing</string>
            </array>
            <key>description</key>
            <string>JUCE is an open-source cross-platform C++ application framework...</string>
            <key>developer</key>
            <string>Raw Material Software Limited</string>
            <key>display_name</key>
            <string>JUCE</string>
            <key>name</key>
            <string>%NAME%</string>
            <key>unattended_install</key>
            <true/>
            <key>unattended_uninstall</key>
            <true/>
        </dict>
    </dict>
    <key>MinimumVersion</key>
    <string>2.7</string>
    <key>ParentRecipe</key>
    <string>com.github.dataJAR-recipes.pkg.JUCE</string>
    <key>Process</key>
    <array>
        <dict>
            <key>Arguments</key>
            <dict>
                <key>faux_root</key>
                <string>%RECIPE_CACHE_DIR%</string>
                <key>installs_item_paths</key>
                <array>
                    <string>/Applications/JUCE/Projucer.app</string>
                    <string>/Applications/JUCE/DemoRunner.app</string>
                </array>
                <key>derive_minimum_os_version</key>
                <string>%DERIVE_MIN_OS%</string>
            </dict>
            <key>Processor</key>
            <string>MunkiInstallsItemsCreator</string>
        </dict>
        <dict>
            <key>Processor</key>
            <string>MunkiPkginfoMerger</string>
        </dict>
        <dict>
            <key>Arguments</key>
            <dict>
                <key>pkg_path</key>
                <string>%RECIPE_CACHE_DIR%/%NAME%-%version%.pkg</string>
                <key>repo_subdirectory</key>
                <string>%MUNKI_REPO_SUBDIR%</string>
            </dict>
            <key>Processor</key>
            <string>MunkiImporter</string>
        </dict>
    </array>
</dict>
</plist>
```

## How MunkiInstallsItemsCreator Works

### Purpose

The `MunkiInstallsItemsCreator` processor generates the installs array for Munki pkginfo by examining applications on disk and extracting their bundle information.

### derive_minimum_os_version Feature

When `derive_minimum_os_version` is set to a non-empty string:

1. Processor examines each application's `Info.plist`
2. Finds the `LSMinimumSystemVersion` key
3. Determines the highest minimum OS version required
4. Adds `minimum_os_version` to the pkginfo

This ensures Munki won't attempt to install software on incompatible OS versions.

### Why MunkiPkginfoMerger Is Required

The `MunkiInstallsItemsCreator` processor generates installs array data, but it needs `MunkiPkginfoMerger` immediately after to merge this data into the pkginfo that will be imported by `MunkiImporter`.

**Without MunkiPkginfoMerger:**
- Installs array is generated but not merged
- MunkiImporter doesn't receive the installs data
- Recipe appears to work but pkginfo is incomplete

**With MunkiPkginfoMerger:**
- Installs array is properly merged into pkginfo
- minimum_os_version is added if derived
- Complete pkginfo is passed to MunkiImporter

## User Control with DERIVE_MIN_OS

Users can control minimum OS version detection:

### Enable Minimum OS Detection

```xml
<key>DERIVE_MIN_OS</key>
<string>YES</string>
```

Result: `minimum_os_version` will be added to pkginfo based on application requirements.

### Disable Minimum OS Detection

```xml
<key>DERIVE_MIN_OS</key>
<string></string>
```

Result: No `minimum_os_version` will be added to pkginfo.

### Override via autopkg Command

```bash
autopkg run JUCE.munki --key DERIVE_MIN_OS=""
```

This allows users to disable minimum OS detection for specific runs.

## When to Use This Tool

### Ideal Use Cases

- ✅ **After adding MunkiInstallsItemsCreator** to a recipe
- ✅ **Repository audits** to ensure all recipes are properly configured
- ✅ **Before committing** new or modified recipes
- ✅ **When updating old recipes** to use MunkiInstallsItemsCreator
- ✅ **Quality assurance** as part of recipe review process

### Recipes That Need This

- Munki recipes using `MunkiInstallsItemsCreator`
- Recipes that need minimum OS version detection
- Recipes with multiple applications to track
- Recipes where manual installs array creation is error-prone

## Safety Features

- **Non-Destructive**: Only modifies recipes using MunkiInstallsItemsCreator
- **Additive Changes**: Adds missing configuration, doesn't remove existing
- **Description Preservation**: Won't modify description if instructions already present
- **Version Awareness**: Only updates MinimumVersion if too low
- **Environment Check**: Ensures it runs in AutoPkg's Python environment
- **Error Handling**: Clear error messages with full tracebacks

## Integration with Other Tools

MunkiInstallsItemsCreator validator works well alongside:

- **MinimumVersionChecker**: Run MinimumVersionChecker after to validate version
- **RecipeAlphabetiser**: Alphabetize keys after adding DERIVE_MIN_OS
- **DetabChecker**: Fix whitespace after modifications
- **DeprecationChecker**: Validate recipes before adding new features

## Recommended Workflow

1. **Add MunkiInstallsItemsCreator**: Configure processor in recipe
2. **Run Validator**: Use this tool to add required configuration
3. **RecipeAlphabetiser**: Organize Input dict keys
4. **Test Recipe**: Run recipe to verify installs array generation
5. **Review**: Check generated pkginfo has installs and minimum_os_version
6. **Commit**: Push the properly configured recipe

## Troubleshooting

### Script Won't Run

**Error**: `This script should be run using AutoPkg's Python installation`

**Solution**: Use the full path to AutoPkg's Python:
```bash
/usr/local/autopkg/python MunkiInstallsItemsCreator.py
```

### YAML Support Missing

**Error**: `PyYAML not available for processing`

**Solution**: Install PyYAML in AutoPkg's Python:
```bash
/usr/local/autopkg/python -m pip install PyYAML
```

### No Recipes Modified

If no recipes are modified:
- ✅ Your recipes are already configured correctly (good!)
- Check that recipes use MunkiInstallsItemsCreator processor
- Verify you're scanning the correct directory

### Installs Array Not Generated

If installs array isn't appearing in pkginfo after running:

1. **Check faux_root**: Ensure it points to extracted applications
2. **Check installs_item_paths**: Verify paths are correct
3. **Check MunkiPkginfoMerger**: Must be immediately after MunkiInstallsItemsCreator
4. **Check DERIVE_MIN_OS**: Ensure it's set to non-empty string
5. **Run with -vvv**: Use verbose mode to see processor output

### minimum_os_version Not Added

If minimum_os_version isn't appearing:

1. **Check DERIVE_MIN_OS**: Must be non-empty string ("YES", "True", etc.)
2. **Check LSMinimumSystemVersion**: Applications must have this key in Info.plist
3. **Check AutoPkg Version**: Must be 2.7 or higher

## Command Line Tips

### Check Recipe Configuration

```bash
# Check if recipe has MunkiInstallsItemsCreator
grep -A 10 "MunkiInstallsItemsCreator" recipe.munki.recipe

# Check if derive_minimum_os_version exists
grep "derive_minimum_os_version" recipe.munki.recipe

# Check if MunkiPkginfoMerger follows
grep -A 5 "MunkiInstallsItemsCreator" recipe.munki.recipe | grep "MunkiPkginfoMerger"
```

### Find Recipes Using MunkiInstallsItemsCreator

```bash
# Find all recipes with MunkiInstallsItemsCreator
grep -l "MunkiInstallsItemsCreator" *.munki.recipe

# Count recipes using it
grep -c "MunkiInstallsItemsCreator" *.munki.recipe
```

### Test Recipe with Verbose Output

```bash
# Run recipe with maximum verbosity
autopkg run -vvv recipe.munki.recipe

# Check pkginfo for installs array
autopkg run recipe.munki.recipe && \
    plutil -p ~/Library/AutoPkg/Cache/*/pkginfo.plist | grep -A 20 "installs"
```

## Performance

MunkiInstallsItemsCreator validator is highly efficient:

- **Fast Scanning**: Quick check for MunkiInstallsItemsCreator processor
- **Targeted Processing**: Only modifies relevant recipes
- **Low Memory**: Processes one file at a time
- **Minimal Dependencies**: Only plistlib and optionally PyYAML

Typical performance:
- ~100 recipes: < 10 seconds
- ~1000 recipes: < 60 seconds

## Best Practices

1. **Run After Adding Processor**: Always validate configuration immediately
2. **Test Recipe**: Run recipe after validation to verify it works
3. **Check pkginfo**: Verify installs array and minimum_os_version are present
4. **Document Changes**: Note why DERIVE_MIN_OS is needed in commit messages
5. **User Communication**: Explain DERIVE_MIN_OS variable to recipe users
6. **Version Control**: Review diffs before committing changes

## Common Scenarios

### Scenario 1: New Recipe with MunkiInstallsItemsCreator

**Action**: Create recipe with MunkiInstallsItemsCreator processor

**Result**: Script adds all five required configurations automatically

**Benefit**: Recipe is immediately ready for use

### Scenario 2: Updating Old Recipe

**Action**: Add MunkiInstallsItemsCreator to existing recipe

**Result**: Script adds derive_minimum_os_version, MunkiPkginfoMerger, DERIVE_MIN_OS, updates description and MinimumVersion

**Benefit**: Complete configuration with one run

### Scenario 3: Recipe Without MunkiPkginfoMerger

**Action**: Recipe has MunkiInstallsItemsCreator but missing merger

**Result**: Script inserts empty MunkiPkginfoMerger in correct position

**Benefit**: Installs array will now be properly merged

### Scenario 4: Low MinimumVersion

**Action**: Recipe has MinimumVersion 1.0 but uses MunkiInstallsItemsCreator

**Result**: Script updates MinimumVersion to 2.7

**Benefit**: Prevents errors on older AutoPkg versions

## File Format Support

| Format | Extension | Support | Notes |
|--------|-----------|---------|-------|
| Plist | `.recipe` | ✅ Full | Native plistlib support |
| YAML | `.recipe.yaml` | ✅ Full | Requires PyYAML |
| YAML | `.yaml` | ✅ Full | Requires PyYAML |

## Limitations

- Only processes recipes using MunkiInstallsItemsCreator
- Won't remove extra configurations (only adds missing ones)
- Description modification appends text (doesn't restructure)
- Assumes MunkiPkginfoMerger should be empty (no custom arguments)
- Does not validate installs_item_paths correctness

## Contributing

When modifying this script:

1. Test with recipes using MunkiInstallsItemsCreator
2. Verify all five checks work correctly
3. Test with recipes missing various combinations of config
4. Test Description modification logic
5. Test MinimumVersion comparison
6. Update this README with changes

## Related Tools

- **MinimumVersionChecker**: Validate MinimumVersion requirements
- **RecipeAlphabetiser**: Organize dictionary keys
- **DetabChecker**: Fix whitespace and formatting
- **DeprecationChecker**: Add deprecation warnings

## References

- [MunkiInstallsItemsCreator Processor](https://github.com/autopkg/autopkg/wiki/Processor-MunkiInstallsItemsCreator)
- [MunkiPkginfoMerger Processor](https://github.com/autopkg/autopkg/wiki/Processor-MunkiPkginfoMerger)
- [AutoPkg 2.7 Release Notes](https://github.com/autopkg/autopkg/releases/tag/v2.7)
- [Munki Installs Array](https://github.com/munki/munki/wiki/Supported-Pkginfo-Keys#installs)

## Author

Paul Cossey

## Version History

- **Current**: Initial release with MunkiInstallsItemsCreator configuration validation

---

For more information about AutoPkg processors, visit [https://github.com/autopkg/autopkg](https://github.com/autopkg/autopkg)

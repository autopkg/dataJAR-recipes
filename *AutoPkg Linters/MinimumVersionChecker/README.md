# MinimumVersionChecker

An AutoPkg utility script that automatically sets the correct `MinimumVersion` in recipes based on the processors they use. This ensures recipes declare their actual AutoPkg version requirements, preventing compatibility issues.

## Features

- **Dynamic Version Database**: Fetches latest processor versions from [pre-commit-macadmin](https://github.com/homebysix/pre-commit-macadmin) on every run
- **Always Up-to-Date**: No need to manually update processor versions
- **Automatic Processor Analysis**: Scans all processors used in each recipe
- **Highest Version Wins**: Sets MinimumVersion to the highest required version
- **Smart Updates**: Only updates when necessary (current version too low)
- **Multi-Format Support**: Handles both plist (`.recipe`) and YAML (`.yaml`) formats
- **Version Comparison**: Properly compares semantic versions (e.g., 1.0.1 vs 1.1.0)
- **Fallback Support**: Uses built-in versions if GitHub is unreachable
- **Batch Processing**: Processes multiple recipes in a single run

## Why MinimumVersion Matters

The `MinimumVersion` key tells AutoPkg users what version is required to run a recipe:

- **Prevents Errors**: Users won't try running recipes with unsupported processors
- **Clear Requirements**: Documents AutoPkg version dependencies
- **Safe Upgrades**: Helps users know when to update AutoPkg
- **Best Practice**: Required for recipes using newer processors

### The Problem

Recipes often have missing or incorrect `MinimumVersion`:

- ❌ Recipe uses `DeprecationWarning` (requires 1.1.0) but MinimumVersion is 0.2.0
- ❌ Recipe uses `PlistEditor` (requires 1.0.1) but no MinimumVersion set
- ❌ Recipe upgraded with new processors but MinimumVersion not updated

### The Solution

This script analyzes all processors and sets the correct MinimumVersion automatically.

## What It Does

The script performs intelligent version analysis:

1. **Extracts all processors** from the recipe's Process array
2. **Looks up version requirements** for each processor
3. **Determines highest required version** across all processors
4. **Compares with current MinimumVersion** (if present)
5. **Updates MinimumVersion** if current version is too low

### Plist Format

#### Before
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "...">
<plist version="1.0">
<dict>
    <key>Description</key>
    <string>Downloads App</string>
    <key>Process</key>
    <array>
        <dict>
            <key>Processor</key>
            <string>DeprecationWarning</string>
        </dict>
        <dict>
            <key>Processor</key>
            <string>URLDownloader</string>
        </dict>
    </array>
</dict>
</plist>
```

#### After
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "...">
<plist version="1.0">
<dict>
    <key>MinimumVersion</key>
    <string>1.1.0</string>
    <key>Description</key>
    <string>Downloads App</string>
    <key>Process</key>
    <array>
        <dict>
            <key>Processor</key>
            <string>DeprecationWarning</string>
        </dict>
        <dict>
            <key>Processor</key>
            <string>URLDownloader</string>
        </dict>
    </array>
</dict>
</plist>
```

*Note: DeprecationWarning requires 1.1.0, URLDownloader requires 0.2.0 → highest is 1.1.0*

### YAML Format

#### Before
```yaml
Description: Downloads App
Process:
  - Processor: PlistEditor
    Arguments:
      ...
  - Processor: URLDownloader
```

#### After
```yaml
MinimumVersion: 1.0.1
Description: Downloads App
Process:
  - Processor: PlistEditor
    Arguments:
      ...
  - Processor: URLDownloader
```

*Note: PlistEditor requires 1.0.1, URLDownloader requires 0.2.0 → highest is 1.0.1*

## Processor Version Database

The script **automatically fetches** the latest processor version requirements from the [homebysix/pre-commit-macadmin](https://github.com/homebysix/pre-commit-macadmin) project on every run. This ensures you always have the most current processor version information without needing to update the script.

### How It Works

1. On startup, the script fetches the latest `PROCESSOR_NAMES` dictionary from GitHub
2. Parses the processor versions from the source code
3. Uses these versions to validate recipes
4. Falls back to built-in versions if GitHub is unreachable

### Source

The processor versions are maintained by the MacAdmin community at:
```
https://github.com/homebysix/pre-commit-macadmin/blob/main/
pre_commit_macadmin_hooks/check_autopkg_recipes.py
```

This database is regularly updated as new processors are released or version requirements change.

### Common Processor Versions

Here are some frequently used processors and their requirements (as examples):

| Processor | Minimum Version |
|-----------|----------------|
| DeprecationWarning | 1.1.0 |
| PlistEditor | 1.0.1 |
| PackageRequired | 1.0.0 |
| FileCreator | 0.6.1 |
| GitHubReleasesInfoProvider | 0.5.0 |
| URLTextSearcher | 0.5.0 |
| StopProcessingIf | 0.4.0 |
| CodeSignatureVerifier | 0.4.2 |

*Note: These are examples. The script fetches the complete, up-to-date list automatically.*

## Requirements

- **AutoPkg**: Must be installed with its bundled Python environment at `/usr/local/autopkg/python`
- **Python 3**: Included with AutoPkg installation
- **Required modules**: `yaml`, `urllib` (standard library)
- **Network Access**: Required to fetch latest processor versions (falls back if offline)

## Installation

1. Download `MinimumVersionChecker.py` to a convenient location
2. Make the script executable (optional):
   ```bash
   chmod +x MinimumVersionChecker.py
   ```

## Usage

### Running the Script

Execute the script using AutoPkg's Python installation:

```bash
/usr/local/autopkg/python MinimumVersionChecker.py
```

### Interactive Prompt

When run, the script will prompt for a recipe directory:

```
MinimumVersionChecker - AutoPkg Recipe Version Validator
==================================================
This script will:
1. Fetch latest processor versions from GitHub
2. Analyze all processors used in recipes
3. Determine highest required AutoPkg version
4. Set MinimumVersion to required version
5. Skip recipes already meeting requirements
==================================================

Fetching latest processor versions from GitHub...
Successfully fetched 29 processor versions

Enter the path to your recipe directory
(You can drag and drop the folder here):
```

### Example Session

```
Enter the path to your recipe directory
(You can drag and drop the folder here): /Users/username/autopkg/recipes

Scanning recipes in: /Users/username/autopkg/recipes

DEBUG: Processing /Users/username/autopkg/recipes/App.download.recipe
DEBUG: Found 3 processor(s): URLDownloader, Unarchiver, CodeSignatureVerifier
DEBUG: URLDownloader requires version 0.2.0
DEBUG: Unarchiver requires version 0.2.0
DEBUG: CodeSignatureVerifier requires version 0.4.2
DEBUG: Highest required version: 0.4.2
DEBUG: Current MinimumVersion: 0.2.0
DEBUG: Updating MinimumVersion to 0.4.2
✓ Successfully updated MinimumVersion: /Users/username/autopkg/recipes/App.download.recipe

==================================================
Processing complete!
Recipes processed: 10
Recipes modified: 1
==================================================

Modified files:
  ✓ /Users/username/autopkg/recipes/App.download.recipe
    0.2.0 → 0.4.2

Please verify these files in your version control system.
```

## Version Comparison Logic

The script uses semantic version comparison:

- `1.0.1` > `1.0.0`
- `1.1.0` > `1.0.1`
- `2.0.0` > `1.9.9`
- `0.4.2` > `0.4.0`

### When Updates Happen

MinimumVersion is updated when:
- ✅ No MinimumVersion currently set
- ✅ Current version is lower than required version
- ✅ Current version missing patch/minor numbers (e.g., `1.0` vs `1.0.1`)

### When Skipped

Recipes are skipped when:
- ✅ Current MinimumVersion >= highest required version
- ✅ No processors with version requirements found
- ✅ No processors found in recipe

## Safety Features

- **Non-Destructive**: Only updates when necessary
- **Smart Comparison**: Properly handles all version formats
- **Verification**: Validates changes after writing
- **Skip Logic**: Won't downgrade MinimumVersion
- **Environment Check**: Ensures it runs in AutoPkg's Python environment
- **Shared Processor Handling**: Ignores custom processor versions

## Integration with Other Tools

MinimumVersionChecker works well alongside:

- **DeprecationChecker**: Run MinimumVersionChecker after to set correct version
- **DetabChecker**: Can be run in any order
- **Recipe Validation**: Use as part of CI/CD pipeline
- **Pre-commit hooks**: Ensure MinimumVersion is always correct

## Troubleshooting

### Script Won't Run

**Error**: `This script should be run using AutoPkg's Python installation`

**Solution**: Use the full path to AutoPkg's Python:
```bash
/usr/local/autopkg/python MinimumVersionChecker.py
```

### Version Not Updated

If MinimumVersion isn't updated:
- Check current version isn't already >= required version
- Verify processors are in the version database
- Check DEBUG output for version comparison results

### Custom Processors Ignored

The script only tracks core AutoPkg processors. Custom processors like:
- `com.github.username.CustomProcessor`
- Shared processors from recipe repos
- Your own custom processors

...are ignored because their version requirements aren't tracked in the database.

### Wrong Version Set

If the version seems incorrect:
1. Check DEBUG output for processor versions
2. Verify processor names are correct
3. Check the [source repository](https://github.com/homebysix/pre-commit-macadmin) for updates
4. Report issues to the pre-commit-macadmin project if versions are wrong

### Network Issues

If the script can't reach GitHub:
- ✅ The script will use built-in fallback versions
- ✅ A warning message will be displayed
- ✅ Processing continues normally with fallback data
- ⚠️ Fallback versions may be outdated

To resolve:
1. Check your internet connection
2. Verify GitHub is accessible
3. Check firewall/proxy settings
4. Run again when network is available for latest versions

## Processor Version Source

The processor versions are automatically fetched from the **pre-commit-macadmin** project, which is actively maintained by the MacAdmin community. This ensures:

- ✅ Always current version requirements
- ✅ Community-verified accuracy
- ✅ Regular updates as AutoPkg evolves
- ✅ No manual maintenance needed

If you find incorrect processor versions, please report them to:
https://github.com/homebysix/pre-commit-macadmin/issues

## Best Practices

### After Adding New Processors

When updating recipes with new processors:
1. Add the processor to your recipe
2. Run MinimumVersionChecker
3. Verify MinimumVersion was updated correctly
4. Test recipe with that AutoPkg version

### Before Publishing Recipes

Before sharing recipes publicly:
1. Run MinimumVersionChecker on all recipes
2. Verify MinimumVersion requirements
3. Document any version-specific features
4. Test on minimum required version

### Repository Maintenance

For recipe repository maintenance:
1. Run MinimumVersionChecker periodically
2. Update after adding processors
3. Include in pre-commit hooks
4. Document version requirements in README

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

Ensure MinimumVersion is always set correctly:

```bash
#!/bin/bash
# .git/hooks/pre-commit

RECIPES=$(git diff --cached --name-only --diff-filter=ACM | \
          grep '\.recipe')

if [ -n "$RECIPES" ]; then
    echo "Checking MinimumVersion in modified recipes..."
    /usr/local/autopkg/python /path/to/MinimumVersionChecker.py
    
    # If changes were made, fail the commit
    if ! git diff --quiet; then
        echo "MinimumVersion was updated. Please review and commit again."
        exit 1
    fi
fi
```

## Performance

MinimumVersionChecker is efficient:

- **Fast Processing**: Simple regex and dictionary lookups
- **Low Memory**: Processes one file at a time
- **Quick Analysis**: Version comparison is O(1)
- **Instant Results**: Immediate feedback

Typical performance:
- ~100 recipes: < 10 seconds
- ~1000 recipes: < 60 seconds

## File Format Support

| Format | Extension | Support |
|--------|-----------|---------|
| Plist | `.recipe` | ✅ Full |
| Plist | `.download.recipe` | ✅ Full |
| Plist | `.munki.recipe` | ✅ Full |
| YAML | `.yaml` | ✅ Full |
| YAML | `.recipe.yaml` | ✅ Full |

## Limitations

- Only tracks core AutoPkg processors
- Does not track custom/shared processor versions
- Assumes processor names are standard
- Does not validate processor compatibility
- Does not check recipe parent MinimumVersion

## Advanced Usage

### Check Single Recipe

To test a single recipe:
1. Create a temporary directory
2. Copy the recipe there
3. Run MinimumVersionChecker on that directory

### Export Version Report

Get a list of all processors and their versions:
```bash
grep "Processor" *.recipe | \
    sed "s/.*<string>\(.*\)<\/string>/\1/" | \
    sort -u
```

### Find Recipes Needing Updates

Before running MinimumVersionChecker:
```bash
# Find recipes without MinimumVersion
grep -L "MinimumVersion" *.recipe*

# Find recipes with old versions
grep -l "MinimumVersion.*0\.[0-3]" *.recipe*
```

## Version Increment Guidelines

When to bump MinimumVersion:

- **Major (1.0 → 2.0)**: Breaking changes, major new features
- **Minor (1.0 → 1.1)**: New processors, significant features
- **Patch (1.0.0 → 1.0.1)**: Bug fixes, minor improvements

## Related Documentation

- [AutoPkg Releases](https://github.com/autopkg/autopkg/releases)
- [AutoPkg Changelog](https://github.com/autopkg/autopkg/blob/master/CHANGELOG.md)
- [Recipe Format Documentation](https://github.com/autopkg/autopkg/wiki/Recipe-Format)

## Contributing

When modifying this script:

1. Test with both plist and YAML recipes
2. Verify version comparison logic
3. Test network error handling (offline mode)
4. Test with various version formats
5. Update this README with changes

**Note**: Processor versions are fetched from the [pre-commit-macadmin](https://github.com/homebysix/pre-commit-macadmin) project. To update processor versions, contribute to that project instead of modifying this script.

## Author

Paul Cossey

## Version History

- **Current**: Dynamic version fetching from pre-commit-macadmin, fallback support, semantic version comparison

---

For more information about AutoPkg versions and processors, visit:
- [AutoPkg Wiki](https://github.com/autopkg/autopkg/wiki)
- [AutoPkg Releases](https://github.com/autopkg/autopkg/releases)
- [pre-commit-macadmin](https://github.com/homebysix/pre-commit-macadmin) - Processor version source

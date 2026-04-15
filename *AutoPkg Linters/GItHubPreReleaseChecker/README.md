# GitHub PreRelease Checker

An AutoPkg utility script that automatically updates GitHub download recipes to support pre-release handling. This script modifies recipes that use the `GitHubReleasesInfoProvider` processor to add the ability to optionally download pre-release versions.

## Features

- **Automatic Recipe Detection**: Scans directories for `.download.recipe` files
- **Multi-Format Support**: Handles both plist (`.recipe`) and YAML (`.yaml`) recipe formats
- **Safe Modifications**: Preserves existing recipe formatting and structure
- **Batch Processing**: Processes multiple recipes in a single run
- **Verification**: Validates changes after writing to ensure accuracy

## What It Does

The script modifies recipes to:

1. Add `include_prereleases` argument to `GitHubReleasesInfoProvider` processor with value `%PRERELEASE%`
2. Add a `PRERELEASE` input variable (default empty string)
3. Update the recipe description with instructions for using the pre-release feature

### Before
```xml
<key>Processor</key>
<string>GitHubReleasesInfoProvider</string>
<key>Arguments</key>
<dict>
    <key>github_repo</key>
    <string>example/repo</string>
</dict>
```

### After
```xml
<key>Processor</key>
<string>GitHubReleasesInfoProvider</string>
<key>Arguments</key>
<dict>
    <key>include_prereleases</key>
    <string>%PRERELEASE%</string>
    <key>github_repo</key>
    <string>example/repo</string>
</dict>
```

## Requirements

- **AutoPkg**: Must be installed with its bundled Python environment at `/usr/local/autopkg/python`
- **Python 3**: Included with AutoPkg installation
- **Required Python modules**: `plistlib`, `yaml` (standard library)

## Installation

1. Download `GItHubPreReleaseChecker.py` to a convenient location
2. Make the script executable (optional):
   ```bash
   chmod +x GItHubPreReleaseChecker.py
   ```

## Usage

### Running the Script

Execute the script using AutoPkg's Python installation:

```bash
/usr/local/autopkg/python GItHubPreReleaseChecker.py
```

### Interactive Prompt

When run, the script will prompt you for a recipe directory:

```
Enter the path to your recipe directory
(You can drag and drop the folder here):
```

You can either:
- Type the full path to your recipe directory
- Drag and drop a folder from Finder

The script will:
1. Scan the directory (including subdirectories) for `.download.recipe` and `.download.recipe.yaml` files
2. Check each recipe for `GitHubReleasesInfoProvider` processor
3. Add pre-release support if not already present
4. Display a summary of modified files

### Example Session

```
Enter the path to your recipe directory
(You can drag and drop the folder here): /Users/username/autopkg/recipes

Scanning recipes in: /Users/username/autopkg/recipes

Found GitHubReleasesInfoProvider in: /Users/username/autopkg/recipes/App.download.recipe
✓ Successfully modified and verified: /Users/username/autopkg/recipes/App.download.recipe

Processing complete!
Recipes processed: 5
Recipes modified: 1

Modified files:
- /Users/username/autopkg/recipes/App.download.recipe
```

## Using Pre-Release Features

After running this script, your recipes will support pre-release downloads. To use this feature:

### In AutoPkg Override

Add to your override's Input section:

```xml
<key>Input</key>
<dict>
    <key>PRERELEASE</key>
    <string>yes</string>
    <!-- other inputs -->
</dict>
```

### Command Line

Use the `-k` option when running AutoPkg:

```bash
autopkg run App.download -k PRERELEASE=yes
```

### Default Behavior

When `PRERELEASE` is empty (default), only stable releases are downloaded, maintaining backward compatibility.

## Safety Features

- **Non-Destructive**: Only modifies recipes that need changes
- **Skip Logic**: Automatically skips recipes that already have pre-release support
- **Verification**: Reads back modified files to ensure changes were written correctly
- **Environment Check**: Validates that it's running in AutoPkg's Python environment
- **Error Handling**: Comprehensive error messages and debugging output

## Output

The script provides:

- **Debug information**: Detailed processing steps for troubleshooting
- **Progress updates**: Status for each recipe processed
- **Summary statistics**: Total recipes processed and modified
- **File list**: Complete list of modified files for verification

## Troubleshooting

### Script Won't Run

**Error**: `This script should be run using AutoPkg's Python installation`

**Solution**: Use the full path to AutoPkg's Python:
```bash
/usr/local/autopkg/python GItHubPreReleaseChecker.py
```

### Changes Not Appearing in Git

If modified files don't appear in GitHub Desktop or `git status`:

1. Refresh GitHub Desktop
2. Run `git status` in the terminal
3. Check file permissions
4. Verify the files were actually modified (check timestamp)

### Recipe Not Modified

The script will skip recipes if:
- No `GitHubReleasesInfoProvider` processor is found
- The recipe already has both `include_prereleases` and `PRERELEASE` keys
- The file format is unsupported

## Debug Mode

The script includes extensive debug output by default. Look for lines starting with `DEBUG:` to trace processing steps.

## File Format Support

| Format | Extension | Support |
|--------|-----------|---------|
| Plist | `.recipe` | ✅ Full |
| YAML | `.yaml` | ✅ Full |

## Limitations

- Only processes `.download.recipe` and `.download.recipe.yaml` files
- Requires `GitHubReleasesInfoProvider` processor to be present
- Must be run with AutoPkg's Python installation

## Contributing

When modifying this script:

1. Test with both plist and YAML recipes
2. Verify formatting preservation
3. Add debug output for new features
4. Update this README with changes

## License

This script is provided as-is for use with AutoPkg.

## Author

Paul Cossey

## Version History

- **Current**: Initial release with plist and YAML support

---

For more information about AutoPkg, visit [https://github.com/autopkg/autopkg](https://github.com/autopkg/autopkg)

# RecipeAlphabetiser

An AutoPkg utility script that automatically alphabetizes keys in recipe files for consistency and readability. This script organizes the `Input` dict, `pkginfo` dict (in Munki recipes), and processor keys while preserving the intentional order of processors in the `Process` array.

## Features

- **Dependency-Aware Input Sorting**: Sorts Input keys while respecting variable references
- **Input Dict Alphabetization**: Sorts all keys in the Input dictionary
- **pkginfo Dict Alphabetization**: Recursively sorts keys in pkginfo (Munki recipes)
- **Processor Key Sorting**: Alphabetizes keys within each processor step
- **Processor Key Positioning**: Ensures `Processor` key is always last in each processor
- **Process Array Preservation**: Maintains the intentional order of processors
- **Arguments Alphabetization**: Sorts keys within processor Arguments dicts
- **Multi-Format Support**: Handles both plist (`.recipe`) and YAML (`.yaml`) recipe formats
- **Batch Processing**: Processes multiple recipes in a single run
- **Detailed Reporting**: Shows exactly what was alphabetized in each file

## Why Alphabetize Recipe Keys?

Following consistent key ordering improves recipe maintainability:

- **Readability**: Easy to find specific keys in predictable locations
- **Consistency**: All recipes follow the same structure
- **Version Control**: Reduces diff noise from key reordering
- **Collaboration**: Makes it easier for multiple contributors
- **Standards**: Follows common AutoPkg community practices

## What It Does

The script performs targeted alphabetization:

### 1. Input Dict (Dependency-Aware)
Sorts Input keys while respecting variable dependencies. If a key's value references another key (e.g., `%NAME%`), the referenced key will be placed first:

**Before:**
```xml
<key>Input</key>
<dict>
    <key>MUNKI_REPO_SUBDIR</key>
    <string>%MUNKI_CATEGORY%/%MUNKI_DEVELOPER%/%NAME%</string>
    <key>NAME</key>
    <string>%aacp_name%</string>
    <key>aacp_name</key>
    <string>TestApp</string>
    <key>MUNKI_CATEGORY</key>
    <string>Software</string>
    <key>MUNKI_DEVELOPER</key>
    <string>Adobe</string>
</dict>
```

**After (dependencies first):**
```xml
<key>Input</key>
<dict>
    <key>MUNKI_CATEGORY</key>       <!-- No dependencies -->
    <string>Software</string>
    <key>MUNKI_DEVELOPER</key>      <!-- No dependencies -->
    <string>Adobe</string>
    <key>aacp_name</key>             <!-- No dependencies -->
    <string>TestApp</string>
    <key>NAME</key>                  <!-- Depends on aacp_name -->
    <string>%aacp_name%</string>
    <key>MUNKI_REPO_SUBDIR</key>    <!-- Depends on NAME, MUNKI_CATEGORY, MUNKI_DEVELOPER -->
    <string>%MUNKI_CATEGORY%/%MUNKI_DEVELOPER%/%NAME%</string>
</dict>
```

Keys with no dependencies are sorted alphabetically, followed by dependent keys in the order their dependencies allow.

### 2. pkginfo Dict (Munki Recipes)
Recursively alphabetizes all keys within `pkginfo`:
```xml
<key>pkginfo</key>
<dict>
    <key>catalogs</key>            <!-- Alphabetically sorted -->
    <key>description</key>
    <key>developer</key>
    <key>display_name</key>
    <key>name</key>
    <key>unattended_install</key>
    <key>unattended_uninstall</key>
</dict>
```

### 3. Processor Keys (Processor Last)
Within each processor step, alphabetizes keys but keeps `Processor` at the end:
```xml
<dict>
    <key>Arguments</key>           <!-- Alphabetically first -->
    <dict>
        <key>munkiimport_appname</key>
        <key>pkg_path</key>
        <key>repo_subdirectory</key>
    </dict>
    <key>Processor</key>           <!-- Always last -->
    <string>MunkiImporter</string>
</dict>
```

### 4. Process Array Order
**Preserves** the order of processors in the `Process` array:
```xml
<key>Process</key>
<array>
    <dict><!-- Processor 1 stays first --></dict>
    <dict><!-- Processor 2 stays second --></dict>
    <dict><!-- Processor 3 stays third --></dict>
</array>
```

## Before and After Example

### Before
```xml
<key>Input</key>
<dict>
    <key>NAME</key>
    <string>PrusaSlicer</string>
    <key>pkginfo</key>
    <dict>
        <key>name</key>
        <string>%NAME%</string>
        <key>display_name</key>
        <string>PrusaSlicer</string>
        <key>description</key>
        <string>PrusaSlicer takes 3D models...</string>
        <key>catalogs</key>
        <array>
            <string>testing</string>
        </array>
        <key>developer</key>
        <string>Prusa Research</string>
    </dict>
    <key>MUNKI_REPO_SUBDIR</key>
    <string>apps/%NAME%</string>
</dict>
```

### After
```xml
<key>Input</key>
<dict>
    <key>MUNKI_REPO_SUBDIR</key>
    <string>apps/%NAME%</string>
    <key>NAME</key>
    <string>PrusaSlicer</string>
    <key>pkginfo</key>
    <dict>
        <key>catalogs</key>
        <array>
            <string>testing</string>
        </array>
        <key>description</key>
        <string>PrusaSlicer takes 3D models...</string>
        <key>developer</key>
        <string>Prusa Research</string>
        <key>display_name</key>
        <string>PrusaSlicer</string>
        <key>name</key>
        <string>%NAME%</string>
    </dict>
</dict>
```

## Requirements

- **AutoPkg**: Must be installed with its bundled Python environment at `/usr/local/autopkg/python`
- **Python 3**: Included with AutoPkg installation
- **PyYAML**: Required only for YAML recipe support (usually pre-installed with AutoPkg)
- **No external dependencies**: Uses Python standard library (plistlib)

## Installation

1. Download `RecipeAlphabetiser.py` to a convenient location
2. Make the script executable (optional):
   ```bash
   chmod +x RecipeAlphabetiser.py
   ```

## Usage

### Running the Script

Execute the script using AutoPkg's Python installation:

```bash
/usr/local/autopkg/python RecipeAlphabetiser.py
```

### Interactive Prompt

When run, the script will prompt for a recipe directory:

```
RecipeAlphabetiser - AutoPkg Recipe Key Sorter
==================================================
This script will:
1. Alphabetize keys in the Input dict
2. Alphabetize keys in the pkginfo dict (munki recipes)
3. Alphabetize keys in each Process step
4. Keep 'Processor' key last in each processor
5. Preserve Process array order
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

✓ Alphabetized PrusaSlicer.munki.recipe
  - Alphabetized Input dict
  - Alphabetized pkginfo dict
  - Alphabetized processor: MunkiImporter
  - Alphabetized Arguments in MunkiImporter

Skipping App.download.recipe - already alphabetized

✓ Alphabetized Another.pkg.recipe
  - Alphabetized Input dict
  - Alphabetized processor: PkgCreator

==================================================
Processing complete!
Recipes processed: 15
Recipes modified: 3
==================================================

Modified files:

  ✓ PrusaSlicer.munki.recipe:
    - Alphabetized Input dict
    - Alphabetized pkginfo dict
    - Alphabetized processor: MunkiImporter
    - Alphabetized Arguments in MunkiImporter

  ✓ Another.pkg.recipe:
    - Alphabetized Input dict
    - Alphabetized processor: PkgCreator

Please verify these files in your version control system.
```

## What Gets Alphabetized

### ✅ Alphabetized

| Section | Description | Example Keys |
|---------|-------------|--------------|
| Input keys | Top-level keys in Input dict | `NAME`, `MUNKI_REPO_SUBDIR`, `pkginfo` |
| pkginfo keys | All keys in pkginfo dict | `catalogs`, `description`, `developer`, `display_name` |
| Processor keys | Keys in each processor dict | `Arguments`, `Comment`, `Processor` (last) |
| Arguments keys | Keys within Arguments dict | `pkg_path`, `repo_subdirectory`, etc. |

### ❌ NOT Alphabetized

| Section | Reason | Why |
|---------|--------|-----|
| Process array | Order matters | Processors must run in specific sequence |
| Top-level keys | Convention | `Description`, `Identifier`, `Input`, `Process`, etc. stay in standard order |
| Array values | Not dicts | Arrays like `catalogs` maintain their order |

## Special Handling

### Processor Key Always Last

The `Processor` key is special - it identifies the processor and should always be the last key in each processor dict for readability:

```xml
<dict>
    <key>Arguments</key>
    <dict>...</dict>
    <key>Comment</key>
    <string>Import into Munki</string>
    <key>Processor</key>        <!-- Always last -->
    <string>MunkiImporter</string>
</dict>
```

This makes it easy to scan the Process array and see which processor each step uses.

### Nested Dictionary Handling

The script recursively alphabetizes nested dictionaries:

```xml
<key>pkginfo</key>
<dict>
    <key>blocking_applications</key>
    <array>...</array>
    <key>installs</key>
    <array>
        <dict>
            <key>CFBundleIdentifier</key>  <!-- Nested dict also alphabetized -->
            <key>CFBundleName</key>
            <key>path</key>
        </dict>
    </array>
</dict>
```

## Output Details

The script provides comprehensive information:

- **Per-recipe changes**: Lists what was alphabetized in each file
- **Section identification**: Shows which dicts were modified (Input, pkginfo, processors)
- **Processor names**: Identifies which processors had keys alphabetized
- **Skip notifications**: Indicates which files are already properly ordered

## When to Use RecipeAlphabetiser

### Ideal Use Cases

- ✅ **Before committing** new or modified recipes
- ✅ **Repository cleanup** projects to standardize key ordering
- ✅ **After manual editing** to restore consistent ordering
- ✅ **When merging** recipes from different sources
- ✅ **Pre-release checks** to ensure consistency
- ✅ **Team standardization** to enforce consistent structure

### When NOT to Use

- ❌ **Process array reordering**: Never changes processor execution order
- ❌ **Value modification**: Only reorders keys, never changes values
- ❌ **Top-level recipe keys**: Doesn't reorder Description, Identifier, etc.

## Safety Features

- **Non-Destructive**: Only modifies files that need alphabetization
- **Preservation**: Maintains all data, only changes key order
- **Skip Logic**: Automatically skips files already properly ordered
- **Environment Check**: Ensures it runs in AutoPkg's Python environment
- **Error Handling**: Clear error messages with full tracebacks
- **Format Preservation**: Maintains plist/YAML formatting

## Integration with Other Tools

RecipeAlphabetiser works well alongside:

- **DetabChecker**: Run DetabChecker first to fix whitespace
- **MinimumVersionChecker**: Alphabetize after updating MinimumVersion
- **DeprecationChecker**: Alphabetize after adding deprecation
- **Pre-commit hooks**: Add RecipeAlphabetiser to automated workflows

## Recommended Workflow

1. **Create/Modify Recipe**: Edit recipe as needed
2. **DetabChecker**: Fix any tab/whitespace issues
3. **RecipeAlphabetiser**: Organize keys consistently
4. **Review**: Check the changes in your version control
5. **Commit**: Push the clean, organized recipe

## Troubleshooting

### Script Won't Run

**Error**: `This script should be run using AutoPkg's Python installation`

**Solution**: Use the full path to AutoPkg's Python:
```bash
/usr/local/autopkg/python RecipeAlphabetiser.py
```

### YAML Support Missing

**Error**: `PyYAML not available for processing`

**Solution**: Install PyYAML in AutoPkg's Python:
```bash
/usr/local/autopkg/python -m pip install PyYAML
```

### No Changes Made

If no recipes are modified:
- ✅ Your recipes are already properly alphabetized (good!)
- Check that you're scanning the correct directory
- Verify files have `.recipe` or `.yaml` extensions

### Unexpected Key Order

If keys aren't in the order you expect:
- Remember: Top-level recipe keys (Description, Identifier) are NOT alphabetized
- Process array order is preserved (processors stay in same sequence)
- Only Input, pkginfo, and processor keys are alphabetized

## Performance

RecipeAlphabetiser is highly efficient:

- **Fast Processing**: Dictionary operations are O(n log n)
- **Low Memory**: Processes one file at a time
- **Minimal Dependencies**: Only plistlib and optionally PyYAML
- **Instant Results**: Provides immediate feedback

Typical performance:
- ~100 recipes: < 10 seconds
- ~1000 recipes: < 60 seconds

## Best Practices

1. **Run Before Committing**: Always alphabetize before pushing changes
2. **Combine with Other Tools**: Use as part of a linting workflow
3. **Review Changes**: Check diffs to understand what changed
4. **Team Standards**: Share this tool with collaborators
5. **Regular Maintenance**: Run periodically on recipe repositories
6. **Automate**: Add to pre-commit hooks or CI/CD pipelines

## Pre-Commit Hook Example

Automate key ordering with a git pre-commit hook:

```bash
#!/bin/bash
# .git/hooks/pre-commit

RECIPES=$(git diff --cached --name-only --diff-filter=ACM | grep '\.recipe')

if [ -n "$RECIPES" ]; then
    # Run alphabetiser on staged recipes
    for recipe in $RECIPES; do
        /usr/local/autopkg/python RecipeAlphabetiser.py "$recipe"
    done
    
    # Re-add alphabetized files
    git add $RECIPES
fi
```

## Command Line Tips

### Check Current Key Order

View current key order in a recipe:

```bash
# Plist recipes
plutil -p recipe.recipe | grep "<key>"

# Count keys in Input
plutil -extract Input xml1 -o - recipe.recipe | grep "<key>" | wc -l
```

### Compare Before/After

```bash
# Create backup
cp recipe.recipe recipe.recipe.backup

# Run alphabetiser
/usr/local/autopkg/python RecipeAlphabetiser.py

# View changes
diff recipe.recipe.backup recipe.recipe

# Or use git
git diff recipe.recipe
```

## Advanced Usage

### Single File Processing

To process a single recipe file, modify the main loop or create a wrapper:

```python
from pathlib import Path
modified, changes = process_recipe(Path('/path/to/recipe.recipe'))
if modified:
    print("Changes:", changes)
```

### Custom Key Ordering

If you need custom ordering rules beyond alphabetical:

```python
# Modify alphabetize_dict() to use custom sort
def custom_sort_key(key):
    priority = {
        'name': 0,
        'display_name': 1,
        'description': 2,
    }
    return (priority.get(key, 999), key)

sorted(d.keys(), key=custom_sort_key)
```

## File Format Support

| Format | Extension | Support | Notes |
|--------|-----------|---------|-------|
| Plist | `.recipe` | ✅ Full | Native plistlib support |
| YAML | `.recipe.yaml` | ✅ Full | Requires PyYAML |
| YAML | `.yaml` | ✅ Full | Requires PyYAML |

## Limitations

- Only processes `.recipe` and `.yaml` files
- Does not reorder top-level recipe keys (Description, Identifier, Input, etc.)
- Does not change array value order (only dict keys)
- Does not modify comments or formatting beyond key order
- YAML output formatting may differ slightly from input

## Contributing

When modifying this script:

1. Test with both plist and YAML recipes
2. Verify Input dict alphabetization
3. Verify pkginfo nested alphabetization
4. Test Processor key positioning (always last)
5. Ensure Process array order is preserved
6. Test with various recipe types (download, munki, pkg)
7. Update this README with changes

## Examples

### Munki Recipe

**Before alphabetization:**
- Input keys: `NAME`, `pkginfo`, `MUNKI_REPO_SUBDIR`
- pkginfo keys: `name`, `display_name`, `description`, `catalogs`

**After alphabetization:**
- Input keys: `MUNKI_REPO_SUBDIR`, `NAME`, `pkginfo`
- pkginfo keys: `catalogs`, `description`, `display_name`, `name`

### Download Recipe

**Before alphabetization:**
- Input keys: `NAME`, `DOWNLOAD_URL`, `USER_AGENT`
- Processor keys: `Processor`, `Arguments`

**After alphabetization:**
- Input keys: `DOWNLOAD_URL`, `NAME`, `USER_AGENT`
- Processor keys: `Arguments`, `Processor`

## Related Tools

- **DetabChecker**: Fix tab and whitespace issues
- **MinimumVersionChecker**: Validate AutoPkg version requirements
- **DeprecationChecker**: Add deprecation warnings to recipes
- **autopkg-linter**: Additional recipe validation tools

## References

- [AutoPkg Recipe Format](https://github.com/autopkg/autopkg/wiki/Recipe-Format)
- [AutoPkg Style Guide](https://github.com/autopkg/autopkg/wiki/Recipe-Style-Guide)
- [Python plistlib](https://docs.python.org/3/library/plistlib.html)
- [PyYAML Documentation](https://pyyaml.org/wiki/PyYAMLDocumentation)

## Author

Paul Cossey

## Version History

- **Current**: Initial release with Input, pkginfo, and processor key alphabetization

---

For more information about AutoPkg recipe best practices, visit [https://github.com/autopkg/autopkg](https://github.com/autopkg/autopkg)

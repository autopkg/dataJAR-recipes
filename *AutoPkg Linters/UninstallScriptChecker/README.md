# UninstallScriptChecker

An AutoPkg utility script that validates and fixes uninstall script configuration in Munki recipes. This script ensures that recipes using `uninstall_script` also have the required `uninstall_method` key properly set.

## Features

- **Automatic Detection**: Finds recipes with `uninstall_script` key
- **Method Validation**: Ensures `uninstall_method` is set to `'uninstall_script'`
- **Auto-Correction**: Adds missing `uninstall_method` key
- **Value Fixing**: Corrects incorrect `uninstall_method` values
- **Multi-Format Support**: Handles both plist (`.recipe`) and YAML (`.yaml`) formats
- **4-Space Standard**: Maintains proper indentation
- **Batch Processing**: Processes multiple recipes in a single run

## Why This Matters

In Munki, the `uninstall_script` and `uninstall_method` keys work together:

- **`uninstall_script`**: Contains the actual uninstall script code
- **`uninstall_method`**: Tells Munki how to uninstall (must be set to `'uninstall_script'`)

### The Problem

If you have `uninstall_script` but no `uninstall_method`, Munki will:
- ❌ Not execute your uninstall script
- ❌ Fall back to default uninstall behavior
- ❌ Potentially leave files behind or fail to uninstall properly

### The Solution

This script ensures both keys are present and correctly configured.

## What It Does

The script performs three main checks:

1. **Finds `uninstall_script` keys** in recipe Input sections
2. **Checks for `uninstall_method` key** in the same section
3. **Adds or corrects `uninstall_method`** to be `'uninstall_script'`

### Plist Format

#### Before (Missing uninstall_method)
```xml
<key>Input</key>
<dict>
    <key>NAME</key>
    <string>AppName</string>
    <key>uninstall_script</key>
    <string>#!/bin/bash
rm -rf /Applications/App.app
    </string>
</dict>
```

#### After
```xml
<key>Input</key>
<dict>
    <key>NAME</key>
    <string>AppName</string>
    <key>uninstall_method</key>
    <string>uninstall_script</string>
    <key>uninstall_script</key>
    <string>#!/bin/bash
rm -rf /Applications/App.app
    </string>
</dict>
```

#### Before (Incorrect uninstall_method)
```xml
<key>uninstall_method</key>
<string>remove_app</string>
<key>uninstall_script</key>
<string>#!/bin/bash
...
```

#### After
```xml
<key>uninstall_method</key>
<string>uninstall_script</string>
<key>uninstall_script</key>
<string>#!/bin/bash
...
```

### YAML Format

#### Before
```yaml
Input:
  NAME: AppName
  uninstall_script: |
    #!/bin/bash
    rm -rf /Applications/App.app
```

#### After
```yaml
Input:
  NAME: AppName
  uninstall_method: uninstall_script
  uninstall_script: |
    #!/bin/bash
    rm -rf /Applications/App.app
```

## Requirements

- **AutoPkg**: Must be installed with its bundled Python environment at `/usr/local/autopkg/python`
- **Python 3**: Included with AutoPkg installation
- **Required modules**: `yaml` (for YAML recipe support)

## Installation

1. Download `UninstallScriptChecker.py` to a convenient location
2. Make the script executable (optional):
   ```bash
   chmod +x UninstallScriptChecker.py
   ```

## Usage

### Running the Script

Execute the script using AutoPkg's Python installation:

```bash
/usr/local/autopkg/python UninstallScriptChecker.py
```

### Interactive Prompt

When run, the script will prompt for a recipe directory:

```
UninstallScriptChecker - AutoPkg Recipe Uninstall Validator
==================================================
This script will:
1. Find recipes with uninstall_script key
2. Ensure uninstall_method key exists
3. Set uninstall_method to 'uninstall_script'
4. Use 4 spaces for indentation
==================================================

Enter the path to your recipe directory
(You can drag and drop the folder here):
```

### Example Session

```
Enter the path to your recipe directory
(You can drag and drop the folder here): /Users/username/autopkg/recipes

Scanning recipes in: /Users/username/autopkg/recipes

Found uninstall_script in: /Users/username/autopkg/recipes/App.munki.recipe
DEBUG: Found uninstall_script key
DEBUG: Adding uninstall_method key
✓ Successfully configured uninstall_method: /Users/username/autopkg/recipes/App.munki.recipe

==================================================
Processing complete!
Recipes processed: 15
Recipes modified: 1
==================================================

Modified files:
  ✓ /Users/username/autopkg/recipes/App.munki.recipe

Please verify these files in your version control system.
```

## Common Scenarios

### Scenario 1: Missing uninstall_method

**Recipe has**: `uninstall_script` only  
**Script does**: Adds `uninstall_method: uninstall_script` before `uninstall_script`  
**Result**: Properly configured uninstall

### Scenario 2: Incorrect uninstall_method Value

**Recipe has**: `uninstall_method: remove_app` with `uninstall_script`  
**Script does**: Changes value to `uninstall_script`  
**Result**: Script will now execute correctly

### Scenario 3: Already Correct

**Recipe has**: Both keys with correct values  
**Script does**: Skips the file (no modification needed)  
**Result**: No changes

## Key Placement

The script intelligently places `uninstall_method`:

- **Added before `uninstall_script`**: Maintains logical order
- **Same indentation level**: Preserves recipe structure
- **4 spaces**: Ensures consistent formatting

Example placement in Input section:
```xml
<key>Input</key>
<dict>
    <key>NAME</key>
    <string>AppName</string>
    <key>uninstall_method</key>      ← Added here
    <string>uninstall_script</string>
    <key>uninstall_script</key>      ← Before this
    <string>#!/bin/bash...</string>
</dict>
```

## Munki Uninstall Methods

For reference, valid `uninstall_method` values in Munki:

| Method | Description |
|--------|-------------|
| `removepackages` | Uses pkgutil to remove packages |
| `remove_app` | Removes application bundle |
| `remove_copied_items` | Removes items from installs array |
| `uninstall_script` | Executes custom uninstall script |

When using **`uninstall_script`**, the `uninstall_method` **must** be set to `'uninstall_script'` for Munki to execute your script.

## Safety Features

- **Non-Destructive**: Only modifies recipes with `uninstall_script`
- **Smart Detection**: Checks both presence and value of `uninstall_method`
- **Verification**: Validates changes after writing
- **Skip Logic**: Automatically skips properly configured recipes
- **Environment Check**: Ensures it runs in AutoPkg's Python environment
- **Content Preservation**: Only adds/modifies the necessary key

## Integration with Other Tools

UninstallScriptChecker works well alongside:

- **DetabChecker**: Run after to ensure spacing
- **CommentKeyChecker**: Can be run in any order
- **Recipe Linters**: Use as part of validation workflow
- **Pre-commit hooks**: Add to automated validation

## Troubleshooting

### Script Won't Run

**Error**: `This script should be run using AutoPkg's Python installation`

**Solution**: Use the full path to AutoPkg's Python:
```bash
/usr/local/autopkg/python UninstallScriptChecker.py
```

### No Recipes Found

If no recipes are modified:
- ✅ Check that recipes contain `uninstall_script` key
- ✅ Verify you're scanning Munki recipes (not download/pkg recipes)
- ✅ Confirm recipes are `.munki.recipe` or similar

### Verification Failed

If the script reports verification failure:
1. Check file permissions
2. Verify the recipe is valid XML/YAML
3. Look for syntax errors in the original recipe
4. Check for conflicting keys

### Script Not Working as Expected

**Recipe still doesn't uninstall properly?**

Check these common issues:
1. Script syntax errors in `uninstall_script` content
2. Incorrect paths in uninstall script
3. Missing permissions (uninstall script needs to run as root)
4. Munki version compatibility

## Best Practices

### Writing Uninstall Scripts

When creating `uninstall_script` content:

```yaml
uninstall_method: uninstall_script
uninstall_script: |
  #!/bin/bash
  # Always use absolute paths
  /bin/rm -rf "/Applications/MyApp.app"
  
  # Remove support files
  /bin/rm -rf "/Library/Application Support/MyApp"
  
  # Check if removal was successful
  if [ -e "/Applications/MyApp.app" ]; then
      echo "Failed to remove application"
      exit 1
  fi
  
  exit 0
```

### Testing Uninstall Scripts

After running UninstallScriptChecker:

1. Import recipe to Munki
2. Install the item on a test machine
3. Test uninstall functionality
4. Verify all files are removed
5. Check for any errors in Munki logs

### Recipe Review Checklist

- ✅ `uninstall_script` present and functional
- ✅ `uninstall_method` set to `'uninstall_script'`
- ✅ Script uses absolute paths
- ✅ Script includes error checking
- ✅ Script exits with appropriate exit codes (0 = success)

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

Prevent commits with misconfigured uninstall scripts:

```bash
#!/bin/bash
# .git/hooks/pre-commit

RECIPES=$(git diff --cached --name-only --diff-filter=ACM | \
          grep '\.recipe')

for recipe in $RECIPES; do
    # Check if recipe has uninstall_script
    if grep -q "uninstall_script" "$recipe"; then
        # Check if it has uninstall_method
        if ! grep -q "uninstall_method" "$recipe"; then
            echo "Error: $recipe has uninstall_script but no uninstall_method"
            echo "Run UninstallScriptChecker.py to fix this issue"
            exit 1
        fi
    fi
done
```

## Performance

UninstallScriptChecker is efficient:

- **Fast Processing**: Simple key detection and insertion
- **Low Memory**: Processes one file at a time
- **Minimal Dependencies**: Uses standard libraries
- **Quick Results**: Immediate feedback

Typical performance:
- ~100 recipes: < 10 seconds
- ~1000 recipes: < 60 seconds

## File Format Support

| Format | Extension | Support |
|--------|-----------|---------|
| Plist | `.recipe` | ✅ Full |
| Plist | `.munki.recipe` | ✅ Full |
| YAML | `.yaml` | ✅ Full |
| YAML | `.munki.recipe.yaml` | ✅ Full |

## Limitations

- Only processes `.recipe` and `.yaml` files
- Assumes `uninstall_script` is in Input section
- Does not validate script syntax or functionality
- Does not test actual uninstall behavior

## Advanced Usage

### Find Recipes with Uninstall Scripts

Before running the checker:
```bash
grep -r "uninstall_script" /path/to/recipes --include="*.recipe*"
```

### Verify Configuration After Running

```bash
# Find recipes with uninstall_script
grep -l "uninstall_script" *.recipe* | while read recipe; do
    # Check if uninstall_method is also present
    if ! grep -q "uninstall_method.*uninstall_script" "$recipe"; then
        echo "Issue in: $recipe"
    fi
done
```

## Related Documentation

- [Munki Uninstall Methods](https://github.com/munki/munki/wiki/Supported-Pkginfo-Keys#uninstall_method)
- [Writing Uninstall Scripts](https://github.com/munki/munki/wiki/Pkginfo-Files#uninstall_script)
- [AutoPkg Recipe Format](https://github.com/autopkg/autopkg/wiki/Recipe-Format)

## Common Patterns

### Simple Application Removal
```yaml
uninstall_method: uninstall_script
uninstall_script: |
  #!/bin/bash
  /bin/rm -rf "/Applications/MyApp.app"
```

### Complex Uninstall with Cleanup
```yaml
uninstall_method: uninstall_script
uninstall_script: |
  #!/bin/bash
  # Remove application
  /bin/rm -rf "/Applications/MyApp.app"
  
  # Remove preferences
  /bin/rm -rf "/Library/Preferences/com.company.myapp.plist"
  
  # Remove support files
  /bin/rm -rf "/Library/Application Support/MyApp"
  
  # Remove LaunchDaemons
  /bin/launchctl unload "/Library/LaunchDaemons/com.company.myapp.plist"
  /bin/rm -f "/Library/LaunchDaemons/com.company.myapp.plist"
```

## Contributing

When modifying this script:

1. Test with both plist and YAML recipes
2. Verify key placement is correct
3. Test with various uninstall_method values
4. Ensure proper indentation (4 spaces)
5. Update this README with changes

## Author

Paul Cossey

## Version History

- **Current**: Initial release with plist and YAML support

---

For more information about Munki and AutoPkg, visit:
- [Munki Wiki](https://github.com/munki/munki/wiki)
- [AutoPkg Documentation](https://github.com/autopkg/autopkg)

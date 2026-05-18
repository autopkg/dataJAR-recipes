# Override Pkg Receipt Checker

## Overview

This linter validates that recipe overrides using `uninstall_script` as their uninstall method properly forget pkg receipts. It cross-references extension attributes in your private-recipes repository to determine which pkg receipts should be forgotten, then checks if the uninstall script includes the appropriate `pkgutil --forget` commands.

## Problem This Solves

When creating recipe overrides with custom uninstall scripts, it's easy to forget to include `pkgutil --forget` commands for pkg receipts. This can leave orphaned receipts on systems after uninstallation, which can cause issues with:

- Package verification
- Installation detection
- System cleanup
- Extension attribute reporting

This linter automates the detection of missing `pkgutil --forget` commands by:

1. Finding overrides that use `uninstall_method: uninstall_script`
2. Locating the corresponding extension attribute in your private-recipes folder
3. Extracting pkg receipt IDs from the extension attribute's script
4. Verifying the uninstall script includes `pkgutil --forget` for each receipt
5. Optionally adding missing forget commands automatically

## What It Checks

The linter performs these validations:

- ✅ Identifies overrides with `uninstall_method = uninstall_script`
- ✅ Finds corresponding extension attributes (handles -arm64/-x86_64 suffixes)
- ✅ Extracts pkg receipt IDs from extension attribute scripts
- ✅ Checks for `pkgutil --forget` commands in uninstall scripts
- ✅ Reports missing forget commands with specific receipt IDs
- ✅ Can automatically add missing forget commands (fix mode)
- ✅ Checks that existing `pkgutil --forget` commands are actually reachable (not blocked by early `exit` statements)

## How It Works

### Extension Attribute Parsing

The linter looks for extension attribute bash scripts (`.sh` files) in the private-recipes directory with "Extension Attribute" in the filename. It extracts the pkg receipt ID from the `pkgID` variable:

```bash
pkgID="com.company.appname"
```

### Uninstall Script Validation

It then checks if the override's uninstall script contains matching forget commands:

```bash
/usr/sbin/pkgutil --forget "com.company.appname"
```

### Automatic Fix Mode

The linter automatically adds missing forget commands to the uninstall script:

- Inserts commands before any `exit` statement (if present)
- Adds them at the end of the script (if no exit)
- Includes a comment: `# Forget pkg receipt`

### Reachability Check

When a `pkgutil --forget` command is already present, the linter analyses the script's control flow to verify the command will actually execute. It detects common patterns where early `exit` statements prevent the receipt from being forgotten:

- **Unconditional exit before forget**: An `exit` at the top level of the script before the `pkgutil --forget` line
- **Conditional exit in guard clauses**: An `exit` inside an `if` block (e.g. checking if a directory exists) that runs before `pkgutil --forget`
- **Forget inside wrong branch**: `pkgutil --forget` placed inside an `else` block while the `if` block exits, meaning the receipt is only forgotten on failure

These are reported as warnings and require manual review to fix, since the correct restructuring depends on each script's logic.

## Usage

### Standalone Mode

Run the script directly with AutoPkg's Python:

```bash
cd OverridePkgReceiptChecker
/usr/local/autopkg/python OverridePkgReceiptChecker.py
```

You'll be prompted for:
1. **Overrides directory**: Path to your recipe overrides folder
2. **Private-recipes directory**: Path to your private-recipes repository

The linter automatically fixes any issues it finds.

### Via Suite Runner

Run via the linter suite as linter #18:

```bash
# Interactive mode (recommended) - you'll be prompted for both directories
/usr/local/autopkg/python autopkg-linter.py --linters 18 /path/to/overrides

# Bulk mode - auto-locates private-recipes as a sibling directory
/usr/local/autopkg/python autopkg-linter.py --linters 18 /path/to/overrides
# In bulk mode, expects: parent_folder/recipe_overrides and parent_folder/private-recipes
```

**Note:** Bulk mode requires `private-recipes` to exist in the same parent directory as your overrides folder. If not found, use interactive mode (option 1) or run standalone.

## Example Output

```
OverridePkgReceiptChecker - AutoPkg Override Pkg Receipt Checker
======================================================================
This script will:
1. Find overrides with uninstall_method=uninstall_script
2. Look up the corresponding extension attribute in private-recipes
3. Extract the pkg receipt ID from the extension attribute
4. Ensure the uninstall script includes 'pkgutil --forget' for that receipt
======================================================================

Scanning overrides in: /Users/user/autopkg/recipe_overrides
Using private-recipes from: /Users/user/private-recipes

📋 Checking: ExpressVPN.definition.recipe
  ✓ Added pkgutil --forget for com.pkg.express.vpn

📋 Checking: Zoom.munki.recipe
  ⚠️  Extension attribute not found for Zoom

======================================================================
Processing complete!
Overrides checked: 12
Overrides modified: 1
======================================================================

✅ Modified files:
  • ExpressVPN.definition.recipe
    - Added pkgutil --forget for com.pkg.express.vpn

⚠️  Warnings:
  • Zoom.munki.recipe: Extension attribute not found for Zoom

⚠️  Please review the modified files before committing!
```

## Before and After Examples

### Before (Missing Forget Command)

**Extension Attribute (Extension Attribute - ExpressVPN.sh):**

```bash
#!/bin/bash

pkgID="com.pkg.express.vpn"

if /usr/sbin/pkgutil --pkgs | /usr/bin/grep -E "${pkgID}"
then
    pkgVersion=$(/usr/sbin/pkgutil --pkg-info-plist "${pkgID}" | /usr/bin/plutil -extract pkg-version xml1 - -o - | /usr/bin/xmllint --xpath "//string/text()" -)
    /bin/echo "<result>${pkgVersion}</result>"
else
    /bin/echo "<result></result>"
fi
```

**Override (ExpressVPN.definition.recipe):**

```xml
<key>uninstall_method</key>
<string>uninstall_script</string>
<key>uninstall_script</key>
<string>#!/bin/zsh --no-rcs

# Uninstall ExpressVPN using the vendor's uninstaller

uninstaller_path="/Applications/ExpressVPN.app/Contents/Resources/vpn-installer.sh"

if [ -x "$uninstaller_path" ]; then
    "$uninstaller_path" uninstall
    exit $?
else
    echo "ExpressVPN uninstaller not found at: $uninstaller_path" &gt;&amp;2
    exit 1
fi</string>
```

### After (With Forget Command Added)

**Override (ExpressVPN.definition.recipe):**

```xml
<key>uninstall_method</key>
<string>uninstall_script</string>
<key>uninstall_script</key>
<string>#!/bin/zsh --no-rcs

# Uninstall ExpressVPN using the vendor's uninstaller

uninstaller_path="/Applications/ExpressVPN.app/Contents/Resources/vpn-installer.sh"

if [ -x "$uninstaller_path" ]; then
    "$uninstaller_path" uninstall

# Forget pkg receipt
/usr/sbin/pkgutil --forget "com.pkg.express.vpn"
    exit $?
else
    echo "ExpressVPN uninstaller not found at: $uninstaller_path" &gt;&amp;2
    exit 1
fi</string>
```

## Directory Structure Requirements

### Private-Recipes Repository Structure

The linter expects extension attributes to be organized as:

```
private-recipes/
├── AppName/
│   └── ExtensionAttributes/
│       └── AppName-EA.recipe
├── OtherApp/
│   └── Extension Attributes/  # (also supported)
│       └── OtherApp-EA.plist
```

Or directly in the recipe folder:

```
private-recipes/
├── AppName/
│   └── AppName-EA.recipe
```

### Architecture Suffix Handling

The linter automatically handles dual-architecture recipes:

- `AppName-arm64.munki.recipe` → looks for `AppName/` folder
- `AppName-x86_64.munki.recipe` → looks for `AppName/` folder
- `AppName.munki.recipe` → looks for `AppName/` folder

## Supported Formats

## Supported Formats

- ✅ Plist recipe overrides (`.recipe`)
- ✅ YAML recipe overrides (`.yaml`)
- ✅ Bash script extension attributes (`.sh` files)

## Technical Details

### Pkg Receipt Extraction

The linter looks for the `pkgID` variable in extension attribute bash scripts:

```bash
pkgID="com.pkg.express.vpn"
```

### Forget Command Format

Generated forget commands are inserted before any `exit` statement:

```bash
# Forget pkg receipt
/usr/sbin/pkgutil --forget "com.pkg.express.vpn"
```

## Requirements

- AutoPkg's Python environment (`/usr/local/autopkg/python`)
- Access to both overrides and private-recipes directories
- Extension attributes must be `.sh` bash scripts with `pkgID` variable
- Works with both `.recipe` (plist) and `.yaml` formats

### For Bulk Mode (Suite Runner)

When running via the suite in bulk mode, the linter expects this directory structure:

```
parent_folder/
├── recipe_overrides/     # Your override recipes
└── private-recipes/      # Your private recipes with extension attributes
```

If your directories are not siblings, use interactive mode (option 1) or run standalone.

## Features

- ✅ Automatically adds missing `pkgutil --forget` commands
- ✅ Preserves existing script structure and indentation
- ✅ Only processes overrides with `uninstall_method=uninstall_script`
- ✅ Handles both plist and YAML recipe formats
- ✅ Strips architecture suffixes when matching recipes to extension attributes

## Limitations

- Currently only looks for extension attributes in `<private-recipes>/<RecipeName>/` directory
- Extension attribute must be a `.sh` file with "Extension Attribute" in the filename
- Only extracts `pkgID` variable pattern (`pkgID="..."`)
- Does not handle multiple pkg receipts in a single extension attribute

## See Also

- [UninstallScriptChecker](../UninstallScriptChecker/README.md) - Validates uninstall script syntax
- [MunkiPathDeleterChecker](../MunkiPathDeleterChecker/README.md) - Checks for deprecated uninstall methods

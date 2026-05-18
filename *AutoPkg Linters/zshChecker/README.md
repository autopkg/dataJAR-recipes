# zshChecker

## Purpose

Ensures that all zsh shebangs in AutoPkg recipes include the `--no-rcs` flag. This flag prevents zsh from sourcing user configuration files (`.zshrc`, `.zprofile`, `.zshenv`, etc.), which ensures consistent and predictable behavior when recipes execute shell scripts across different environments.

## Problem

When AutoPkg recipes contain shell scripts with `#!/bin/zsh` shebangs, zsh will source user configuration files by default. This can lead to:

1. **Inconsistent behavior** - Different users or systems may have different zsh configurations
2. **Security concerns** - User configuration files might interfere with recipe execution
3. **Debugging difficulties** - Recipe failures that work on some systems but not others

## Solution

The linter automatically converts:
```bash
#!/bin/zsh
```

to:
```bash
#!/bin/zsh --no-rcs
```

The `--no-rcs` flag tells zsh to skip sourcing any startup files, ensuring the script runs in a clean, predictable environment.

## Examples

### Before (Plist Format)
```xml
<dict>
    <key>Arguments</key>
    <dict>
        <key>source_script</key>
        <string>#!/bin/zsh
echo "Hello World"
exit 0</string>
    </dict>
    <key>Processor</key>
    <string>com.github.grahampugh.recipes.postprocessors/LastRecipeRunResult</string>
</dict>
```

### After (Plist Format)
```xml
<dict>
    <key>Arguments</key>
    <dict>
        <key>source_script</key>
        <string>#!/bin/zsh --no-rcs
echo "Hello World"
exit 0</string>
    </dict>
    <key>Processor</key>
    <string>com.github.grahampugh.recipes.postprocessors/LastRecipeRunResult</string>
</dict>
```

### Before (YAML Format)
```yaml
- Processor: com.github.grahampugh.recipes.postprocessors/LastRecipeRunResult
  Arguments:
    source_script: |
      #!/bin/zsh
      echo "Hello World"
      exit 0
```

### After (YAML Format)
```yaml
- Processor: com.github.grahampugh.recipes.postprocessors/LastRecipeRunResult
  Arguments:
    source_script: |
      #!/bin/zsh --no-rcs
      echo "Hello World"
      exit 0
```

## Usage

### Standalone
```bash
cd zshChecker
/usr/local/autopkg/python zshChecker.py
# Prompts for recipe directory
```

### Via autopkg-linter.py Suite

List available linters:
```bash
/usr/local/autopkg/python autopkg-linter.py --list
```

Run just this linter (number 17):
```bash
/usr/local/autopkg/python autopkg-linter.py --linters 17 /path/to/recipes
```

Run as part of all linters:
```bash
/usr/local/autopkg/python autopkg-linter.py --all /path/to/recipes
```

## Technical Details

- **Supported formats**: `.recipe` (plist) and `.yaml` files
- **Pattern matching**: Uses regex to find `#!/bin/zsh` shebangs that don't already include `--no-rcs`
- **Preservation**: Maintains exact file structure, only modifying the shebang line
- **Safety**: Skips shebangs that already have the `--no-rcs` flag

## Requirements

- Must be run using AutoPkg's Python: `/usr/local/autopkg/python`
- Recipes must be in `.recipe` (plist) or `.yaml` format

## Notes

- The linter works on any text content within recipes, including inline scripts in processor arguments
- Changes are made in-place; always verify in version control after running
- The `--no-rcs` flag is a standard zsh option and has been available since early zsh versions

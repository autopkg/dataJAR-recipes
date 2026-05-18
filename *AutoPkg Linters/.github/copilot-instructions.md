# AutoPkg Recipe Linter Suite - AI Coding Agent Instructions

## Project Overview

This is a suite of Python linters for validating and fixing [AutoPkg](https://github.com/autopkg/autopkg) recipes. AutoPkg recipes are XML plist or YAML files that automate software packaging for macOS. Each linter is a standalone script in its own directory that detects and fixes specific issues in recipe files.

**Architecture**: Unified CLI runner (`autopkg-linter.py`) + 16 independent linter modules, each following the same pattern.

## Critical Environment Requirement

⚠️ **All scripts MUST run using AutoPkg's Python**: `/usr/local/autopkg/python`

Every script includes `verify_environment()` that checks `sys.executable.startswith('/usr/local/autopkg')`. This is not optional - AutoPkg recipes require AutoPkg's Python environment with its specific dependencies (plistlib, etc.).

## Linter Architecture Pattern

Each linter follows this structure:
```
LinterName/
├── LinterName.py          # Main script with main() function
├── README.md              # Detailed documentation
└── __pycache__/          # Python bytecode cache
```

### Standard Linter Structure

Every linter script contains:
1. **Shebang**: `#!/usr/local/autopkg/python`
2. **verify_environment()**: Validates Python path
3. **clean_path()**: Handles drag-and-drop paths with escaped spaces
4. **process_plist_recipe()**: Logic for XML plist recipes
5. **process_yaml_recipe()**: Logic for YAML recipes (if applicable)
6. **main()**: Interactive prompt for recipe directory, then scans/processes files

### Recipe Format Handling

- **Plist recipes** (`.recipe`): XML plist format using `plistlib`
- **YAML recipes** (`.yaml`): YAML format using `yaml` module
- Most linters support both formats with separate processing functions
- Some operations (e.g., XML escaping) only apply to plist format

## Suite Runner Integration

[autopkg-linter.py](autopkg-linter.py) dynamically loads and runs linters:

1. **get_available_linters()**: Returns list of (number, name, directory, script, description) tuples
2. **load_linter_module()**: Uses `importlib.util.spec_from_file_location()` to load scripts
3. **run_linter()**: Temporarily overrides `sys.argv` and `__builtins__.input` to inject recipe directory and auto-answer prompts in bulk mode
4. **Modes**: 
   - `bulk`: Auto-provides recipe directory + default answers to all prompts
   - `interactive`: Provides recipe directory, then allows user interaction

### Adding New Linters to Suite

Edit `get_available_linters()` in [autopkg-linter.py](autopkg-linter.py):
```python
linters = [
    (16, "NewLinterName", "NewLinterDirectory",
     "NewLinterScript.py",
     "Brief description of what it does"),
    # ... existing linters
]
```

Numbers should be sequential, directory must exist, script must have `main()` function.

## Common Patterns

### Path Handling
```python
def clean_path(path):
    """Handles drag-and-drop paths with backslash-escaped spaces"""
    path = path.strip().strip('"').strip("'")
    path = path.replace(r'\ ', ' ')
    path = path.rstrip(' ').rstrip('/')
    path = os.path.expanduser(path)
    return path
```

### Recipe Discovery
Standard pattern across all linters:
```python
recipe_files = []
for root, dirs, files in os.walk(recipe_dir):
    for file in files:
        if file.endswith(('.recipe', '.yaml')):
            recipe_files.append(Path(root) / file)
```

### Modification Tracking
Most linters return `(modified: bool, changes: list)` from processing functions to report what changed.

## Key Linter Examples

### DetabChecker Pattern (Whitespace Fixes)
- Uses string manipulation on raw file content
- Tracks line-by-line changes
- Processes both plist and YAML identically
- See [DetabChecker/DetabChecker.py](DetabChecker/DetabChecker.py)

### MinimumVersionChecker Pattern (Data Fetching)
- Fetches live data from GitHub (`PROCESSOR_VERSIONS_URL`)
- Maintains fallback data (`FALLBACK_PROCESSOR_VERSIONS`)
- Graceful degradation with try/except
- See [MinimumVersionChecker/MinimumVersionChecker.py](MinimumVersionChecker/MinimumVersionChecker.py)

### RecipeAlphabetiser Pattern (Structured Editing)
- Loads plist with `plistlib`, preserves structure
- Uses **dependency-aware topological sorting** for Input dict keys
- Critical: AutoPkg processes Input keys sequentially - if `KEY_A = %KEY_B%`, then `KEY_B` must be defined before `KEY_A`
- Uses `topological_sort_input_keys()` with Kahn's algorithm to respect dependencies
- Uses `alphabetize_dict_with_processor_last()` - special rule: `Processor` key always last in processor dicts
- Writes back with `plistlib.dump()`
- See [RecipeAlphabetiser/RecipeAlphabetiser.py](RecipeAlphabetiser/RecipeAlphabetiser.py)

### AutoPkgXMLEscapeChecker Pattern (Regex Surgery)
- Uses regex to find `<string>...</string>` blocks
- Escapes XML entities: `&` → `&amp;`, `<` → `&lt;`, `>` → `&gt;`
- Critical: Escape `&` first to avoid double-escaping
- Only for plist format (YAML doesn't need XML escaping)
- See [AutoPkgXMLEscapeChecker/AutoPkgXMLEscapeChecker.py](AutoPkgXMLEscapeChecker/AutoPkgXMLEscapeChecker.py)

### DuplicateKeyChecker Pattern (Duplicate Detection & Fix)
- Scans all `<dict>` sections for duplicate `<key>` tags
- Tracks positions of each key name, reports duplicates
- Auto-fixes specific case: duplicate `unattended_install` → changes 2nd to `unattended_uninstall`
- Returns `(modified, changes, warnings)` tuple - warnings for non-fixable duplicates
- See [DuplicateKeyChecker/DuplicateKeyChecker.py](DuplicateKeyChecker/DuplicateKeyChecker.py)

## Testing & Development Workflow

### Run Individual Linter (Development)
```bash
cd DetabChecker
/usr/local/autopkg/python DetabChecker.py
# Prompts for recipe directory interactively
```

### Run via Suite (Production)
```bash
# All linters
/usr/local/autopkg/python autopkg-linter.py --all /path/to/recipes

# Specific linters (by number)
/usr/local/autopkg/python autopkg-linter.py --linters 3,6,8 /path/to/recipes

# List available
/usr/local/autopkg/python autopkg-linter.py --list
```

### Test Recipe
[test-comp.recipe](test-comp.recipe) exists for testing purposes.

## Naming Conventions

- **Functions**: Snake_case (`process_plist_recipe`, `verify_environment`)
- **Variables**: Snake_case (`recipe_data`, `modified`)
- **Constants**: UPPER_SNAKE_CASE (`PROCESSOR_VERSIONS_URL`, `FALLBACK_PROCESSOR_VERSIONS`)
- **Indentation**: 4 spaces (DetabChecker enforces this)

## Documentation Requirements

Each linter's README.md should include:
- What problem it solves
- Before/after examples with actual XML/YAML snippets
- Usage instructions (standalone + via suite)
- Any special considerations

## Common Gotchas

1. **Don't use `python` command**: Always `/usr/local/autopkg/python`
2. **Processor key ordering**: In recipe processors, `Processor` key must be last
3. **Input key dependencies**: Variables referenced in values (e.g., `%NAME%`) must be defined before keys that reference them - use topological sorting
4. **XML escaping order**: Escape `&` before `<` and `>`
5. **Input dict with pkginfo**: `pkginfo` needs separate alphabetization (it's nested)
6. **YAML vs Plist**: Some operations (XML escaping) only apply to plist format
7. **Suite mock input**: When adding prompts to linters, update `mock_input()` in [autopkg-linter.py](autopkg-linter.py#L180-L217) for bulk mode

## AutoPkg Recipe Structure (Quick Reference)

```xml
<plist version="1.0">
<dict>
    <key>Comment</key>
    <string>Recipe description</string>
    <key>Identifier</key>
    <string>com.github.autopkg.recipe-name</string>
    <key>Input</key>
    <dict>
        <key>NAME</key>
        <string>AppName</string>
        <!-- pkginfo only in .munki recipes -->
    </dict>
    <key>MinimumVersion</key>
    <string>2.3</string>
    <key>Process</key>
    <array>
        <dict>
            <key>Arguments</key>
            <dict><!-- ... --></dict>
            <key>Processor</key>  <!-- Always last -->
            <string>URLDownloader</string>
        </dict>
    </array>
</dict>
</plist>
```

## Contact & Context

- AutoPkg GitHub: https://github.com/autopkg/autopkg
- Processor versions source: homebysix/pre-commit-macadmin
- Main README: [README.md](README.md) (comprehensive usage guide)

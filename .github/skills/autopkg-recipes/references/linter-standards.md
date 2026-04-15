# Linter Standards Reference

Rules enforced by the AutoPkg Linters suite that all recipes must comply with.

## Pre-commit Enforcement

This repository uses `.pre-commit-config.yaml` with [pre-commit-macadmin](https://github.com/homebysix/pre-commit-macadmin) hooks to enforce recipe standards automatically on every commit. The configured hooks are:

- **check-autopkg-recipes** — validates recipe structure and enforces the `com.github.dataJAR-recipes.` identifier prefix
- **forbid-autopkg-overrides** — prevents override files from being committed
- **forbid-autopkg-trust-info** — prevents trust info from being committed

Setup:
- Install pre-commit: `brew install pre-commit`
- Activate hooks: `pre-commit install`
- Hooks run automatically on `git commit`
- Manual check: `pre-commit run --all-files`

## Formatting Standards

### Indentation (DetabChecker)
- 4 spaces per indentation level — no tabs
- All indentation must be multiples of 4 spaces
- No trailing whitespace on any line
- File must end with a single newline

### XML Escaping (AutoPkgXMLEscapeChecker)
- `&` → `&amp;` (always escape first)
- `<` → `&lt;`
- `>` → `&gt;`
- Only applies within `<string>` tags in plist format
- Quotes (`"` and `'`) are NOT escaped

### Comments (CommentKeyChecker)
- Never use HTML comments (`<!-- comment -->`)
- Use Comment key pairs instead:
  ```xml
  <key>Comment</key>
  <string>Your comment here</string>
  ```

### Boolean Values
- Always use self-closing tags: `<true/>` and `<false/>`
- Never use long-form: `<true></true>` or `<false></false>`

## Naming Standards

### NAME Variable (NAMEChecker)
- NAME input variable must NOT contain spaces
- Example: `RingCentralPhone` not `RingCentral Phone`
- Applies to both plist and YAML formats

## Key Ordering Standards

### Recipe Alphabetisation (RecipeAlphabetiser)

**Input Dict**: Topological sort respecting variable dependencies
- If `KEY_A = %KEY_B%`, then `KEY_B` appears before `KEY_A`
- Falls back to alphabetical if no dependencies or circular dependencies
- AutoPkg processes Input keys sequentially, so order matters

**pkginfo Dict**: Pure alphabetical sorting of keys

**Processor Arguments**: Alphabetical order within each processor's Arguments dict

**Processor Dict Keys**: In plist format, the `Processor` key must be LAST in each processor dict. In YAML, `Processor` key is FIRST.

## Processor Standards

### MinimumVersion (MinimumVersionChecker)
- Must be set to the highest version required by any processor used
- Minimum 1.1 for basic recipes
- 2.7 when using MunkiInstallsItemsCreator with derive_minimum_os_version
- 2.7.6 when using core FindAndReplace processor

### MunkiInstallsItemsCreator (MunkiInstallsItemsCreatorChecker)
- Must include `derive_minimum_os_version` key in Arguments
- An empty MunkiPkginfoMerger must immediately follow MunkiInstallsItemsCreator
- DERIVE_MIN_OS input variable must exist (can be empty string for opt-out)
- Description must include DERIVE_MIN_OS usage instructions
- MinimumVersion must be ≥ 2.7

### PathDeleter (MunkiPathDeleterChecker)
- Must be the LAST processor in the Process array
- Must include all destination_path values from unpacking processors:
  - FlatPkgUnpacker
  - PkgPayloadUnpacker
  - Unarchiver
- Child paths are filtered (if parent path included, child is redundant)
- Only applies to munki recipes

### GitHubReleasesInfoProvider (GitHubPreReleaseChecker)
- Must include `include_prereleases` key with `%PRERELEASE%` value
- PRERELEASE input variable must exist (empty string by default)
- Description must include PRERELEASE usage instructions

### FindAndReplace (FindAndReplaceChecker)
- Use core `FindAndReplace` processor (not shared `com.github.homebysix.FindAndReplace`)
- Requires MinimumVersion 2.7.6

### ChecksumVerifier (ChecksumVerifierChanger)
- Use `checksum_pathname` key (not legacy `pathname`)

### DeprecationWarning (DeprecationChecker)
- Must be first processor in Process array when present
- StopProcessingIf with TRUEPREDICATE should follow DeprecationWarning
- MinimumVersion must be ≥ 1.1

## Script Standards

### All Scripts Must Use zsh (zshChecker)
- All scripts must use `#!/bin/zsh --no-rcs` — never `#!/bin/bash`, `#!/bin/sh`, or Python
- Correct: `#!/bin/zsh --no-rcs`
- Incorrect: `#!/bin/zsh`, `#!/bin/bash`, `#!/bin/sh`
- Prevents sourcing user configuration files for consistent cross-environment behavior

### Uninstall Scripts (UninstallScriptChecker)
- When `uninstall_script` key exists, `uninstall_method` must be set to `uninstall_script`
- The `uninstall_method` key must appear before `uninstall_script`

### Override Package Receipts (OverridePkgReceiptChecker)
- Override recipes with `uninstall_method: uninstall_script` must include `pkgutil --forget` for package receipts
- The `pkgutil --forget` command must be guarded with `pkgutil --pkg-info` to avoid non-zero exits when the receipt is missing
- The `pkgutil --forget` command must be reachable (not blocked by early exits)

## Data Integrity

### Duplicate Keys (DuplicateKeyChecker)
- No duplicate `<key>` tags within any `<dict>` block
- Special case: two `unattended_install` keys auto-corrects second to `unattended_uninstall`

### Missing Values (MissingKeyValueChecker)
- Reports empty or whitespace-only values in pkginfo dicts
- Applies only to munki recipes
- Reporting only — no auto-fix

## Quick Checklist

Before submitting a recipe, verify:

- [ ] 4-space indentation, no tabs, no trailing whitespace
- [ ] NAME variable has no spaces
- [ ] Processor arguments in alphabetical order
- [ ] Processor key is last in each dict (plist) or first (YAML)
- [ ] MinimumVersion is at least 1.1 (or higher based on processor requirements)
- [ ] PathDeleter is last processor when used
- [ ] MunkiPkginfoMerger follows MunkiInstallsItemsCreator
- [ ] DERIVE_MIN_OS variable present when using derive_minimum_os_version
- [ ] PRERELEASE variable present when using GitHubReleasesInfoProvider
- [ ] XML entities properly escaped in string values
- [ ] No HTML comments
- [ ] All scripts use `#!/bin/zsh --no-rcs` (never bash, sh, or Python)
- [ ] uninstall_method set when uninstall_script exists
- [ ] No duplicate keys in any dict
- [ ] File ends with single newline
- [ ] Custom processor Python passes Flake8 and SonarQube
- [ ] Pre-commit hooks pass: `pre-commit run --files <recipe files>`

## Custom Processor Python Standards

When writing a custom AutoPkg processor, the Python code must meet SonarQube and Flake8 standards.

### Shebang and Encoding
```python
#!/usr/local/autopkg/python
```
Always use the AutoPkg Python interpreter. No encoding declaration needed (Python 3 defaults to UTF-8).

### Flake8 Rules
- **Line length**: Maximum 120 characters (E501)
- **Imports**: One per line, grouped in order: stdlib, third-party, local (E401, I)
- **Whitespace**: No trailing whitespace (W291), no blank lines with whitespace (W293)
- **Indentation**: 4 spaces, no tabs (E101, W191)
- **Naming**: snake_case for functions and variables, PascalCase for classes (N801, N802, N806)
- **Unused imports/variables**: Remove all (F401, F841)
- **Bare except**: Always specify exception type (E722)
- **Comparisons**: Use `is None` / `is not None`, not `== None` (E711)
- **Boolean comparisons**: Use `if flag:` not `if flag == True:` (E712)

### SonarQube Rules
- **No hardcoded credentials or secrets** (S2068)
- **No commented-out code** — remove it (S125)
- **No duplicate string literals** — use constants (S1192)
- **Functions should not be too complex** — keep cyclomatic complexity low (S1541)
- **No mutable default arguments** — use `None` with internal default (S5765)
- **Use context managers** for file operations — `with open(...)` (S5713)
- **Log exceptions properly** — include the exception in the log message
- **No wildcard imports** — `from module import *` (S2208)

### AutoPkg Processor Structure
```python
#!/usr/local/autopkg/python
"""Short description of what this processor does."""

from autopkglib import Processor, ProcessorError


__all__ = ["MyProcessorName"]


class MyProcessorName(Processor):
    """Short description of what this processor does."""

    description = __doc__
    input_variables = {
        "input_var": {
            "required": True,
            "description": "Description of the input.",
        },
    }
    output_variables = {
        "output_var": {
            "description": "Description of the output.",
        },
    }

    def main(self):
        """Main process."""
        input_val = self.env.get("input_var")
        if not input_val:
            raise ProcessorError("input_var is required")

        # Processing logic here

        self.env["output_var"] = result
        self.output(f"Output: {result}")


if __name__ == "__main__":
    PROCESSOR = MyProcessorName()
    PROCESSOR.execute_shell()
```

### Key Requirements
- Inherit from `autopkglib.Processor`
- Raise `ProcessorError` for failures (not `Exception` or `SystemExit`)
- Define `input_variables` and `output_variables` dicts
- Use `self.env` to read inputs and write outputs
- Use `self.output()` for informational messages
- Include `__all__` list with the processor class name
- Include the `if __name__ == "__main__"` block

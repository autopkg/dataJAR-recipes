# AutoPkgXMLEscapeChecker

An AutoPkg utility script that ensures proper XML character escaping in plist recipe files. This script finds and escapes special characters (&, <, >) within `<string>` tags to comply with XML standards and prevent parsing errors.

## Features

- **Automatic XML Escaping**: Detects unescaped special characters in string values
- **Smart Entity Detection**: Avoids double-escaping already-escaped entities
- **Plist-Only Processing**: Only processes `.recipe` files (YAML recipes don't need XML escaping)
- **Batch Processing**: Scans entire recipe directories
- **Safe Modifications**: Only modifies `<string>` content, preserves all structure
- **Detailed Reporting**: Shows which files were modified

## Why XML Escaping Matters

AutoPkg recipe files in plist format are XML documents and must follow XML standards:

- **Parser Compatibility**: Unescaped special characters can cause XML parsing failures
- **Data Integrity**: Ensures string values are interpreted correctly
- **Standards Compliance**: Follows XML 1.0 specification
- **Cross-Platform**: Ensures recipes work on all systems

## What It Does

The script escapes three critical XML characters within `<string>` tags:

1. **Ampersand (`&`)**: Converts to `&amp;`
2. **Less Than (`<`)**: Converts to `&lt;`
3. **Greater Than (`>`)**: Converts to `&gt;`

Characters that **don't** need escaping:
- Double quotes (`"`)
- Single quotes/apostrophes (`'`)

### Smart Escaping

The script includes intelligent pattern matching:
- **Avoids Double-Escaping**: Detects existing entities like `&amp;`, `&lt;`, `&gt;`, `&quot;`, `&apos;`
- **Escape Order**: Processes `&` first to prevent double-escaping
- **Tag-Aware**: Only escapes content within `<string>` tags, not XML structure

### Before
```xml
<key>re_pattern</key>
<string>Version: (\d+\.\d+) & newer</string>
<key>match_message</key>
<string>Found version < %match%</string>
```

### After
```xml
<key>re_pattern</key>
<string>Version: (\d+\.\d+) &amp; newer</string>
<key>match_message</key>
<string>Found version &lt; %match%</string>
```

## Requirements

- **AutoPkg**: Must be installed with its bundled Python environment at `/usr/local/autopkg/python`
- **Python 3**: Included with AutoPkg installation
- **No external dependencies**: Uses only Python standard library

## Installation

1. Download `AutoPkgXMLEscapeChecker.py` to a convenient location
2. Make the script executable (optional):
   ```bash
   chmod +x AutoPkgXMLEscapeChecker.py
   ```

## Usage

### Running the Script

Execute the script using AutoPkg's Python installation:

```bash
/usr/local/autopkg/python AutoPkgXMLEscapeChecker.py
```

### Interactive Prompt

When run, the script will prompt for a recipe directory:

```
AutoPkgXMLEscapeChecker - XML Character Escaper
==================================================
This script will escape XML special characters in recipe string values.
Only processes plist (.recipe) files.
==================================================

Enter the path to your recipe directory
(You can drag and drop the folder here):
```

You can either:
- Type the full path to your recipe directory
- Drag and drop a folder from Finder

### Bulk Mode

Run against a directory without prompts:

```bash
# Using autopkg-linter.py suite runner
/usr/local/autopkg/python autopkg-linter.py --linters 12 /path/to/recipes
```

## What Gets Modified

The script processes only plist recipe files (`.recipe`) and:

✅ **Escapes**:
- `&` → `&amp;` (when not already part of an entity)
- `<` → `&lt;` (when not part of XML tags)
- `>` → `&gt;` (when not part of XML tags)

✅ **Preserves**:
- Existing XML entities (`&amp;`, `&lt;`, `&gt;`, `&quot;`, `&apos;`)
- XML structure and tags
- All whitespace and formatting
- Comments and processing instructions

❌ **Skips**:
- YAML recipes (`.yaml`) - don't need XML escaping
- Already properly escaped content

## Examples

### Example 1: Escaping Ampersands

**Before**:
```xml
<key>description</key>
<string>Download & install Firefox</string>
```

**After**:
```xml
<key>description</key>
<string>Download &amp; install Firefox</string>
```

### Example 2: Escaping Comparison Operators

**Before**:
```xml
<key>predicate</key>
<string>pkg_uploaded_version < "1.0"</string>
```

**After**:
```xml
<key>predicate</key>
<string>pkg_uploaded_version &lt; "1.0"</string>
```

### Example 3: Already Escaped (No Change)

**Before**:
```xml
<string>Price: &amp;pound;50 &lt; &amp;pound;100</string>
```

**After**:
```xml
<string>Price: &amp;pound;50 &lt; &amp;pound;100</string>
```
*(No changes - already properly escaped)*

## Output

The script provides clear feedback:

```
AutoPkgXMLEscapeChecker - XML Character Escaper
==================================================

Processing 45 recipes...

✓ Modified MyApp.recipe
  - Escaped XML characters on 2 line(s)

✓ Modified AnotherApp.recipe
  - Escaped XML characters on 1 line(s)

Skipping ValidApp.recipe - no unescaped characters
Skipping CleanRecipe.recipe - no unescaped characters

==================================================
Processing complete!
Recipes processed: 45
Recipes modified: 2
==================================================
```

## Common Use Cases

1. **Recipe Import**: Escape special characters after importing recipes from external sources
2. **Pre-Commit Check**: Validate XML escaping before committing to version control
3. **Regex Patterns**: Ensure comparison operators in regex patterns are properly escaped
4. **Description Fields**: Fix ampersands and other special characters in descriptions
5. **Conditional Logic**: Escape operators in predicate strings

## Integration with autopkg-linter.py

This linter is integrated into the AutoPkg Linter Suite as **Linter #12**:

```bash
# Run as part of the suite
/usr/local/autopkg/python autopkg-linter.py --linters 12 ~/recipes

# Include in a batch with other linters
/usr/local/autopkg/python autopkg-linter.py --linters 3,8,12 ~/recipes

# Run with all linters
/usr/local/autopkg/python autopkg-linter.py --all ~/recipes
```

## Troubleshooting

### Script Won't Run

**Error**: `This script should be run using AutoPkg's Python installation`

**Solution**: Use AutoPkg's Python:
```bash
/usr/local/autopkg/python AutoPkgXMLEscapeChecker.py
```

### No Changes Made

If the script reports no changes:
- Your recipes may already have proper XML escaping
- You may be scanning YAML recipes (which don't need XML escaping)
- Check that you're scanning `.recipe` files

### Double-Escaped Entities

If you see `&amp;amp;`:
- This shouldn't happen with the smart entity detection
- File an issue if you encounter this

## Technical Details

### Regex Patterns

The script uses sophisticated regex patterns:

1. **String Tag Matching**: `(<string>)(.*?)(</string>)` with DOTALL flag
2. **Entity Detection**: `&(?!(quot|apos|lt|gt|amp);)` - negative lookahead
3. **Tag-Aware Escaping**: Only processes content within string tags

### Processing Order

Critical: `&` must be escaped first to avoid double-escaping:

1. Escape `&` → `&amp;` (except existing entities)
2. Escape `<` → `&lt;`
3. Escape `>` → `&gt;`

## Best Practices

- **Run Before Committing**: Ensure XML compliance before version control commits
- **Combine with Other Linters**: Run alongside DetabChecker and RecipeAlphabetiser
- **Test Changes**: Verify recipes still work with `autopkg run --check` after escaping
- **Review Diffs**: Check git diffs to understand what changed

## Related Linters

- **DetabChecker** (#3): Fixes whitespace formatting
- **RecipeAlphabetiser** (#8): Alphabetizes recipe keys
- **MinimumVersionChecker** (#6): Sets correct MinimumVersion

## Support

For issues, questions, or contributions, please refer to the main repository README.

## License

Part of the AutoPkg Recipe Linter Suite.

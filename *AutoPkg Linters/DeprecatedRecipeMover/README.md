# DeprecatedRecipeMover

An AutoPkg utility script that automatically moves deprecated recipes to a `*Deprecated and to be deleted` folder based on their deprecation age. This script helps keep recipe repositories organized by relocating recipes that have been deprecated for a specified period of time.

## Features

- **Age-Based Moving**: Select time thresholds (1, 3, 6, or 12 months, or custom)
- **Git Integration**: Uses git commit history to determine deprecation age
- **Intelligent Folder Handling**: Moves entire folders when all recipes are deprecated
- **Structure Preservation**: Maintains directory structure within `*Deprecated and to be deleted` folder
- **Safety Confirmations**: Shows what will be moved before making any changes
- **Detailed Reporting**: Lists all recipes and folders to be moved with their ages
- **Multi-Format Support**: Handles both plist (`.recipe`) and YAML (`.yaml`) recipe formats

## Requirements

- **AutoPkg**: Must be installed with its bundled Python environment at `/usr/local/autopkg/python`
- **Git Repository**: Recipe directory must be a git repository with commit history
- **DeprecationWarning Processor**: Recipes must have the `DeprecationWarning` processor
- **Python 3**: Included with AutoPkg installation
- **No external dependencies**: Uses only Python standard library

## How It Works

The script performs several checks to identify which recipes should be moved:

1. **Scans Repository**: Finds all recipe files (`.recipe` and `.yaml`)
2. **Checks for DeprecationWarning**: Only considers recipes with `DeprecationWarning` processor
3. **Determines Age**: Uses `git log` to find the last commit date for each recipe
4. **Compares Threshold**: Compares recipe age against your selected time period
5. **Identifies Folders**: Checks if entire folders can be moved (all recipes deprecated)
6. **Confirms Action**: Shows you what will be moved and asks for confirmation
7. **Moves Files**: Relocates recipes/folders to `*Deprecated and to be deleted` maintaining structure

## What Gets Moved

### Individual Recipes

A recipe is moved if:
- ✅ Contains `DeprecationWarning` processor in its Process array
- ✅ Last commit date is older than the selected threshold
- ✅ Not already in `*Deprecated and to be deleted` folder

### Entire Folders

A folder is moved if:
- ✅ Contains 2 or more recipe files
- ✅ **ALL** recipes in the folder meet the above criteria
- ✅ Not already in `*Deprecated and to be deleted` folder

### Directory Structure

The `*Deprecated and to be deleted` folder preserves the original structure:

**Before:**
```
MyRecipes/
├── AppName/
│   ├── AppName.download.recipe
│   ├── AppName.pkg.recipe
│   └── AppName.munki.recipe
├── OtherApp/
│   └── OtherApp.download.recipe
└── SingleRecipe.recipe
```

**After (if AppName folder is fully deprecated):**
```
MyRecipes/
├── OtherApp/
│   └── OtherApp.download.recipe
├── SingleRecipe.recipe
└── *Deprecated and to be deleted/
    └── AppName/
        ├── AppName.download.recipe
        ├── AppName.pkg.recipe
        └── AppName.munki.recipe
```

## Installation

1. Download `DeprecatedRecipeMover.py` to a convenient location
2. Make the script executable (optional):
   ```bash
   chmod +x DeprecatedRecipeMover.py
   ```

## Usage

### Running the Script

Execute the script using AutoPkg's Python installation:

```bash
/usr/local/autopkg/python DeprecatedRecipeMover.py
```

### Interactive Workflow

#### Step 1: Select Repository

```
DeprecatedRecipeMover - AutoPkg Recipe Organizer
==================================================
This script will:
1. Find recipes with DeprecationWarning processor
2. Check their last commit date
3. Move old deprecated recipes to '*Deprecated and to be deleted'
4. Move entire folders if all recipes are deprecated
==================================================

Enter the path to your recipe repository
(You can drag and drop the folder here):
```

Drag and drop your recipe repository folder, or type the path.

#### Step 2: Choose Time Period

```
Select deprecation age threshold:
1. 1 month
2. 3 months
3. 6 months
4. 12 months (1 year)
5. Custom (enter number of months)

Enter your choice (1-5):
```

Select how long a recipe must have been deprecated before moving it.

#### Step 3: Review and Confirm

```
Found 15 deprecated recipe(s) to move:
==================================================

Folders to move (all recipes deprecated):
  📁 OldApp/ (3 recipes)
  📁 AbandonedTool/ (2 recipes)

Individual recipes to move:
  📄 Legacy.download.recipe - Deprecated for 8 months (Last commit: 2025-03-15)
  📄 Obsolete.munki.recipe - Deprecated for 10 months (Last commit: 2025-01-20)

==================================================
These will be moved to a '*Deprecated and to be deleted' folder maintaining their structure.

Proceed with moving these recipes? (y/n):
```

Review the list and confirm to proceed.

#### Step 4: Move Complete

```
Moving files...
✓ Moved folder: OldApp/ → *Deprecated and to be deleted/OldApp
✓ Moved folder: AbandonedTool/ → *Deprecated and to be deleted/AbandonedTool
✓ Moved: Legacy.download.recipe → *Deprecated and to be deleted/Legacy.download.recipe
✓ Moved: Obsolete.munki.recipe → *Deprecated and to be deleted/Obsolete.munki.recipe

==================================================
Move operation complete!
Recipes moved: 15
==================================================

IMPORTANT: Review the changes and commit them to git:
  cd /path/to/recipes
  git status
  git add .
  git commit -m "Move deprecated recipes to _Deprecated"
```

## Time Period Options

| Option | Duration | Use Case |
|--------|----------|----------|
| 1 month | ~30 days | Very aggressive cleanup |
| 3 months | ~90 days | Standard cleanup cycle |
| 6 months | ~180 days | Conservative approach |
| 12 months | ~365 days | Archive very old deprecations |
| Custom | Your choice | Specific organizational needs |

### Choosing the Right Threshold

**1 Month**: Use when:
- Recipes are quickly replaced with alternatives
- You want to keep the repository lean
- Users are actively monitoring deprecation notices

**3 Months**: Use when:
- You want a balanced approach
- Most users have time to transition
- Standard deprecation cycle

**6 Months**: Use when:
- You want to be cautious
- Recipes may still be in use
- Corporate environments with slower adoption

**12 Months**: Use when:
- Archiving very old recipes
- Keeping recipes accessible longer
- First-time cleanup of large repositories

## Git Integration

### Why Git History?

The script uses git commit history because:
- **Accurate Dating**: Last commit shows when deprecation was added
- **Reliable**: Doesn't depend on file modification times
- **Transparent**: You can verify dates with `git log`
- **Standard**: Works with any git workflow

### Checking Deprecation Date

To manually check when a recipe was deprecated:

```bash
# View last commit date for a recipe
git log -1 --format="%ci" path/to/recipe.recipe

# View commit that added DeprecationWarning
git log --all --grep="DeprecationWarning" -- path/to/recipe.recipe
```

### No Git History?

If a recipe has no git history:
- ❌ It will **not** be moved (script skips it)
- 💡 This is safe: prevents moving recipes without known dates
- 💡 Solution: Commit the recipe first, then wait for threshold period

## Safety Features

- **Read-Only Scanning**: Initial scan doesn't modify anything
- **Confirmation Required**: Must explicitly confirm before moving files
- **Skip Existing**: Won't re-process files already in `*Deprecated and to be deleted`
- **Error Handling**: Reports failed moves without stopping entire operation
- **Git Verification**: Ensures repository is valid before proceeding
- **Structure Preservation**: Maintains folder hierarchy for easy navigation

## Example Scenarios

### Scenario 1: Cleaning Up Old Deprecations

You deprecated several recipes 6 months ago and users have migrated:

1. Run script and select "6 months"
2. Review the list of 15 recipes to move
3. Confirm and move them to `_Deprecated`
4. Commit the changes to git
5. Repository is now cleaner for active recipes

### Scenario 2: Quarterly Maintenance

Every 3 months, move recipes deprecated that long:

1. Run script quarterly
2. Select "3 months" option
3. Move batches of deprecated recipes
4. Keep repository organized over time

### Scenario 3: Entire Product Line Deprecated

An entire product line is deprecated (folder with multiple recipes):

1. All recipes in folder have `DeprecationWarning`
2. All were committed 8 months ago
3. Select "6 months" threshold
4. Script detects entire folder can be moved
5. Moves folder as a unit to `*Deprecated and to be deleted`

### Scenario 4: Mixed Deprecation Ages

Folder has 5 recipes:
- 3 deprecated 8 months ago
- 2 still active

Result:
- Folder is **not** moved (not all recipes deprecated)
- Only the 3 old deprecated recipes are moved individually
- 2 active recipes remain in original location

## Output Details

### What You'll See

**During Scan:**
```
Scanning repository for deprecated recipes...
```

**Folders to Move:**
```
📁 AppName/ (5 recipes)
```
- Indicates entire folder will be moved
- Shows recipe count

**Individual Recipes:**
```
📄 Legacy.download.recipe - Deprecated for 8 months (Last commit: 2025-03-15)
```
- Recipe name
- How long it's been deprecated
- Last commit date

**Move Progress:**
```
✓ Moved folder: AppName/ → *Deprecated and to be deleted/AppName
✓ Moved: Legacy.download.recipe → *Deprecated and to be deleted/Legacy.download.recipe
```
- Confirms successful moves
- Shows new location

## Troubleshooting

### Not a Git Repository

**Error:** `Error: '/path' is not a git repository`

**Solution:**
```bash
cd /path/to/recipes
git init
git add .
git commit -m "Initial commit"
```

### No Commit History

**Warning:** `No commit history found`

**Cause:** Recipe was never committed to git

**Solution:** Commit the recipe first:
```bash
git add path/to/recipe.recipe
git commit -m "Add recipe with DeprecationWarning"
```

### No Recipes Found

**Output:** `No recipes found that meet the criteria.`

**Possible Reasons:**
- ✓ No recipes have `DeprecationWarning` processor (good!)
- ✓ All deprecated recipes are too new for threshold
- ✓ All deprecated recipes already in `*Deprecated and to be deleted`

### Permission Errors

**Error:** `Error moving /path/recipe.recipe: [Errno 13] Permission denied`

**Solutions:**
1. Check file permissions
2. Ensure you own the files
3. Close any applications with files open
4. Run with appropriate permissions

### Failed Moves

If some moves fail:
- Script continues with remaining moves
- Reports which files failed
- Successful moves are still completed
- Review errors and retry failed files manually

## Integration with Other Tools

### Recommended Workflow

1. **DeprecationChecker**: Add deprecation warnings to recipes
2. **Wait**: Allow users time to migrate (your threshold period)
3. **DeprecatedRecipeMover**: Move old deprecated recipes
4. **DetabChecker**: Clean up formatting in active recipes
5. **Git**: Commit the organized repository

### Pre-Move Checklist

Before running DeprecatedRecipeMover:

- ✅ Ensure recipes have `DeprecationWarning` processor
- ✅ Verify git repository is up to date
- ✅ Check that deprecation notices were added with git commits
- ✅ Communicate to users that recipes will be archived
- ✅ Have backups or be prepared to revert if needed

### Post-Move Actions

After moving deprecated recipes:

```bash
# Review changes
git status
git diff --stat

# View moved files
ls -R '*Deprecated and to be deleted/'

# Commit the organization
git add .
git commit -m "Archive recipes deprecated for X months"
git push
```

## Command Line Tips

### Check Last Commit Date

```bash
# Single recipe
git log -1 --format="%ci" AppName/AppName.download.recipe

# All recipes in folder
git log -1 --format="%ci" AppName/*.recipe
```

### Find Deprecated Recipes

```bash
# Search for DeprecationWarning in plist recipes
grep -r "DeprecationWarning" --include="*.recipe" .

# Search for DeprecationWarning in YAML recipes
grep -r "Processor: DeprecationWarning" --include="*.yaml" .
```

### Count Deprecated Recipes

```bash
# Count recipes with DeprecationWarning
grep -r "DeprecationWarning" --include="*.recipe" . | wc -l
```

## Best Practices

1. **Regular Schedule**: Run quarterly or semi-annually
2. **Communicate**: Notify users before moving large batches
3. **Start Conservative**: Use longer thresholds (6-12 months) initially
4. **Review First**: Always review the list before confirming
5. **Commit Immediately**: Commit moves to git right away
6. **Document**: Note why recipes were moved in commit messages
7. **Keep Accessible**: `_Deprecated` folder remains in repository for reference

## Advanced Usage

### Dry Run Workflow

To see what would be moved without actually moving:

1. Run the script normally
2. Review the list when prompted
3. Select "n" when asked to confirm
4. No files are moved
5. Repeat with different thresholds to compare

### Batch Processing Multiple Repos

Create a wrapper script:

```bash
#!/bin/bash
REPOS=(
    "/path/to/recipes1"
    "/path/to/recipes2"
    "/path/to/recipes3"
)

for repo in "${REPOS[@]}"; do
    echo "Processing $repo"
    echo "$repo" | /usr/local/autopkg/python DeprecatedRecipeMover.py
done
```

### Custom Time Periods

When selecting option 5 (Custom), you can specify any number of months:

- 2 months for aggressive cleanup
- 9 months for specific organizational policy
- 18 months for long-term archives

## Maintenance Strategies

### Strategy 1: Aggressive (1-3 months)

**Goal:** Keep repository very lean

**Process:**
- Add `DeprecationWarning` with alternatives
- Wait 1-3 months
- Move deprecated recipes
- Users must migrate quickly

**Best For:**
- Active development environments
- Frequently updated recipes
- Small teams

### Strategy 2: Balanced (3-6 months)

**Goal:** Give users time to migrate

**Process:**
- Add `DeprecationWarning` with clear migration path
- Wait 3-6 months
- Send reminder before moving
- Move deprecated recipes

**Best For:**
- Most organizations
- Medium-sized user bases
- Standard workflows

### Strategy 3: Conservative (6-12+ months)

**Goal:** Maintain long-term availability

**Process:**
- Add `DeprecationWarning` with extensive documentation
- Wait 6-12 months
- Multiple reminders
- Move only very old deprecations

**Best For:**
- Enterprise environments
- Large user bases
- Critical infrastructure

## Related Tools

- **DeprecationChecker**: Add `DeprecationWarning` processor to recipes
- **GitHubPreReleaseChecker**: Update recipes before deprecating
- **MinimumVersionChecker**: Ensure compatibility before deprecating
- **DetabChecker**: Clean up formatting of active recipes

## Frequently Asked Questions

**Q: What happens to recipes in `*Deprecated and to be deleted`?**

A: They remain in the repository but are separated from active recipes. Users can still access them if needed, though the folder name indicates they are candidates for deletion.

**Q: Can I undo the moves?**

A: Yes! Use git to revert:
```bash
git reset --hard HEAD~1  # Revert last commit
# Or manually move files back
```

**Q: Will this break AutoPkg?**

A: No. Recipes in `_Deprecated` won't be automatically discovered, but can still be run with explicit paths.

**Q: Should I delete recipes after moving?**

A: That's up to your organization's policy. The folder name `*Deprecated and to be deleted` indicates these are candidates for eventual deletion, but many organizations keep them indefinitely for reference.

**Q: What if a recipe has no `DeprecationWarning`?**

A: It won't be moved. Use DeprecationChecker first to add warnings.

**Q: What if I want to bring a recipe back?**

A: Simply move it back from `*Deprecated and to be deleted` to its original location (or anywhere else).

## Statistics and Reporting

The script tracks:

- **Total recipes scanned**: All recipe files found in repository
- **Deprecated recipes found**: Recipes with `DeprecationWarning`
- **Age distribution**: How long recipes have been deprecated
- **Folders vs. individual moves**: Optimization of move operations
- **Success rate**: Recipes successfully moved vs. failed

## Performance

DeprecatedRecipeMover is efficient:

- **Fast Scanning**: Regex-based deprecation detection
- **Optimized Git Queries**: Only checks recipes with `DeprecationWarning`
- **Smart Folder Detection**: Minimizes individual file moves
- **Low Memory**: Processes incrementally

Typical performance:
- ~100 recipes: < 10 seconds
- ~1000 recipes: < 60 seconds
- Git operations dominate timing

## Limitations

- Requires git repository with commit history
- Uses approximate month calculation (30 days)
- Only detects `DeprecationWarning` processor (not comments)
- Moves files (doesn't copy or delete)
- Doesn't update recipe relationships or identifiers

## Contributing

When modifying this script:

1. Test with git repositories
2. Verify commit date extraction works
3. Test folder and individual recipe moves
4. Ensure structure preservation
5. Test with various time thresholds
6. Update this README with changes

## References

- [AutoPkg Processor Reference](https://github.com/autopkg/autopkg/wiki/Processor-Reference)
- [Git Log Documentation](https://git-scm.com/docs/git-log)
- [DeprecationWarning Processor](https://github.com/autopkg/autopkg/wiki/Processor-DeprecationWarning)

## Author

Paul Cossey

## Version History

- **Current**: Initial release with age-based recipe moving and folder handling

---

For more information about AutoPkg recipe management, visit [https://github.com/autopkg/autopkg](https://github.com/autopkg/autopkg)

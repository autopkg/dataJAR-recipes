---
name: autopkg-recipes
description: 'Create, review, or fix AutoPkg recipes for the dataJAR-recipes repository. USE FOR: creating download recipes, munki recipes, pkg recipes; fixing recipe formatting; validating recipe structure; applying dataJAR naming conventions; architecture-specific downloads; URL scraping patterns; code signature verification; MunkiInstallsItemsCreator usage; minimum OS version detection. DO NOT USE FOR: running AutoPkg itself; managing Munki repositories; macOS packaging unrelated to AutoPkg.'
---

# AutoPkg Recipe Creation

Create, review, and fix AutoPkg recipes following dataJAR-recipes conventions.

## When to Use

- Creating new AutoPkg download, munki, or pkg recipes
- Reviewing existing recipes for standards compliance
- Fixing formatting, naming, or structural issues in recipes
- Adding architecture support to existing recipes
- Adding minimum OS version detection to munki recipes

## Information Gathering

Before creating recipes, collect these details from the user:

1. **Application name** (as shown in Finder)
2. **Developer name**
3. **Download method** (Direct URL / Sparkle / GitHub Releases / Web Scraping)
4. **Download URL or source**
5. **File format** (.dmg / .pkg / .zip / .app)
6. **Architecture** (Universal / Intel / Apple Silicon / Separate downloads)
7. **Recipe types needed** (download / munki / pkg)
8. **Bundle ID** (if known)
9. **Code signature info** (if known)
10. **Special requirements** (dependencies, scripts, etc.)

## Procedure

### Step 1: Derive App Name from URL

Before searching for existing recipes, derive the actual app name from the download URL and any available metadata. This mirrors Recipe Robot's flow — it downloads and inspects the app to get `CFBundleName` before searching.

**URL Analysis:**
- Parse the filename from the URL (e.g., `TheUnarchiver.dmg` → `TheUnarchiver`)
- Look for bundle ID patterns in URL path segments (e.g., `com.macpaw.site.theunarchiver`)
- If the URL points to a Sparkle appcast, fetch it to extract the app name and download URL
- If the user provided an app name, use it — but also check variations (with/without spaces, articles like "The")

**Normalise the app name** for searching by stripping spaces, dots, commas, and hyphens, then lowercasing. For example:
- "The Unarchiver" → `theunarchiver`
- "Visual Studio Code" → `visualstudiocode`
- "BBEdit" → `bbedit`

### Step 2: Check for Existing Recipes

Search for existing AutoPkg recipes using the app name derived in Step 1. Recipes may already exist in community repositories that can be used as-is, overridden, or used as parent recipes.

**Search the autopkg/index** — this is the same index Recipe Robot uses. Download and parse locally for faster searching:

```zsh
curl -s "https://raw.githubusercontent.com/autopkg/index/main/v1/index.json" -o /tmp/autopkg-index.json
```

The index has a `shortnames` dictionary mapping recipe shortnames to identifier IDs, and an `identifiers` dictionary mapping IDs to `{repo, path}`.

**Important:** Do NOT use `grep` on the raw JSON — shortname keys contain dots (e.g., `OmniFocus.munki`) which makes `grep` unreliable. Always use the Python search script below.

Search by normalising the app name (strip spaces, dots, commas, hyphens, and lowercasing) and doing **substring matching** against normalised shortnames. **Only show download, munki, and pkg recipes** — filter out install, jamf, jss, filewave, intune, fleet, and other deployment-specific types.

```zsh
python3 << 'PYEOF'
import json, sys
with open("/tmp/autopkg-index.json") as f:
    data = json.load(f)
shortnames = data.get("shortnames", {})
identifiers = data.get("identifiers", {})
search = "APPNAME".lower().replace(" ","").replace("-","").replace(".","").replace(",","")
for key in sorted(shortnames):
    normalized = key.lower().replace("-","").replace(" ","").replace(".","").replace(",","")
    if search not in normalized:
        continue
    for id_ref in shortnames[key]:
        info = identifiers.get(id_ref, {})
        path = info.get("path", "")
        rtype = path.rsplit(".", 1)[-1] if "." in path else ""
        if rtype in ("download", "munki", "pkg"):
            repo = info.get("repo", "?")
            print(f"{key} ({rtype}) - {repo}")
            print(f"  https://github.com/autopkg/{repo}/blob/master/{path}")
PYEOF
```

Replace `APPNAME` with the normalised app name from Step 1.

The index includes all recipes from autopkg organization repos (including dataJAR-recipes), so if nothing is found in the index, no recipes exist.

**Present findings to the user before continuing.** For each existing recipe found, provide:
- The recipe type (download/munki/pkg)
- The repository it lives in
- A direct GitHub URL to the recipe file so the user can review it

**Then STOP and ask the user how to proceed.** Do not create any recipes until the user responds. The options are:

1. **Existing recipes are suitable** — no new recipes needed, the user can use or override the existing ones. End here.
2. **Use existing download/pkg as a parent** — create only a munki recipe that references the existing download recipe as its `ParentRecipe`. Continue to Step 3.
3. **Existing recipes are not suitable** — proceed to create new recipes from scratch (continue to Step 3). Only do this when the user explicitly says the existing recipes won't work.

**Important:** Even if the user's download URL differs from existing recipes, do not assume the existing recipes are unsuitable — the existing recipe may use a better source (e.g., Sparkle feed, GitHub Releases) that automatically resolves to the latest version. Always let the user decide.

**Do not skip this step.** Always check for existing recipes first.

### Step 3: Set Up Recipe Folder and Download Dependencies

Create a proper folder structure for the recipe(s) in the repository root (the current working directory):

```zsh
mkdir -p "App Name"
cd "App Name"
```

**If using an existing parent recipe:**
1. Download the parent recipe file(s) to this folder for testing:
   ```zsh
   curl -s "https://raw.githubusercontent.com/autopkg/REPO_NAME/master/PATH/TO/RECIPE.download.recipe" -o "App Name.download.recipe"
   ```
2. Add the parent recipe's repo if not already added:
   ```zsh
   autopkg repo-add REPO_NAME
   ```

**If creating all recipes from scratch:**
- All recipes (download, munki, pkg) will be created in this folder

This folder structure allows you to:
- Keep related recipes together
- Run and test recipes locally
- Inspect the recipe cache folder (`~/Library/AutoPkg/Cache/com.github...`) when debugging processor errors
- Easily compare with existing recipes

### Step 3b: Initial URL Investigation

Before creating recipes, investigate the download URL to understand what gets downloaded and how.

**Always use `-L` (follow redirects) when inspecting URLs:**

```zsh
# Check where a URL redirects to
curl -I -L "https://vendor.com/download" 2>&1 | grep -i "^location:" | tail -1

# Download a small sample to inspect
curl -L -o "/tmp/sample.zip" "https://vendor.com/download"
```

**Critical:** Many download pages use redirects (302/301). Without `-L`, curl stops at the redirect and you won't see the actual download URL or filename. Always include `-L` in initial investigation commands.

**Detect versioned vs static URLs:**

Before proceeding, check whether the download URL contains version numbers embedded in the filename or path:
- **Versioned URL**: `https://vendor.com/app-1-8-1-macos.zip` or `https://cdn.example.com/v2.3.4/App.dmg`
- **Static URL**: `https://vendor.com/download/latest/App.dmg` or `https://cdn.example.com/App.zip`

If the URL contains a version (hyphens, dots, or underscores between digit groups), it will change with every release — **do not hardcode it**. Instead:
1. Ask the user for a **search URL** — the vendor's download page where the versioned link appears
2. Use `URLTextSearcher` to scrape the download path from that page
3. Use a **named capture group** `(?P<variable_name>...)` in the regex to simultaneously extract the version

If the URL is static (no version numbers), it can be used directly in URLDownloader.

**Immediately inspect downloaded archives:**

After downloading a ZIP or other archive, **inspect its contents before proceeding**:

```zsh
# For ZIP files
unzip -l /tmp/sample.zip

# Extract and check what's inside
cd /tmp && unzip -q sample.zip && ls -la
```

**Why this matters:**
- A ZIP might contain a `.pkg` (not a direct `.app`) — changes CodeSignatureVerifier format
- A ZIP might contain an installer app (not the actual application)
- Understanding the contents early determines the correct processor flow

**Example discoveries:**
- `LightkeyInstaller.zip` → contains `LightkeyInstaller.pkg` → use `expected_authority_names` in CodeSignatureVerifier
- `App.zip` → contains `App.app` → use `requirement` in CodeSignatureVerifier
- `Installer.zip` → contains `Installer.app` that downloads the real app at runtime → may not be suitable for AutoPkg

### Step 4: Determine Recipe Types

- **Download recipe**: Always required for new applications
- **Munki recipe**: Required for Munki deployment (can reference existing parent)
- **Pkg recipe**: When a standalone installer package is needed (see [pkg recipe reference](./references/pkg-recipe.md))

### Step 4b: Validate Version Info

After downloading and inspecting the file, verify that usable version information exists. Without a reliable on-disk version, Munki cannot detect when a newer version is installed, which leads to **looping installs** (Munki reinstalls on every run because it can never confirm the installed version matches).

**Check these sources in order:**

1. **App Info.plist** — `CFBundleShortVersionString` or `CFBundleVersion` (extract from DMG, ZIP, or PKG payload):
   ```zsh
   /usr/libexec/PlistBuddy -c "Print :CFBundleShortVersionString" -c "Print :CFBundleVersion" "/path/to/App.app/Contents/Info.plist"
   ```
2. **PKG receipt version** — the `version` attribute in `PackageInfo`:
   ```zsh
   cat /path/to/expanded/PackageName.pkg/PackageInfo | grep 'version='
   ```

**Version is usable** if at least one source provides a real version string (not `0.0.0`, `0`, or empty).

**If no usable version exists**, **STOP and warn the user:**
> ⚠️ **No usable version info found.** The app's Info.plist reports version `X` and the PKG receipt version is `Y`. Without a reliable on-disk version, Munki cannot detect updates — this will cause looping installs (Munki reinstalls on every run).

Then ask the user how to proceed:
1. **Stop** — do not create recipes for this application
2. **Continue anyway** — create the recipes understanding that version detection will not work reliably and manual intervention may be needed
3. **Extract version from URL** — if the download URL contains a version string (e.g., `app-1-8-1-macos.zip`), extract it using `URLTextSearcher` with a named capture group and convert it with the core `FindAndReplace` processor (MinimumVersion 2.7.6). This requires:
   - A search URL (vendor download page) where the versioned link appears
   - A **pkg recipe** in the chain (download → pkg → munki) to house the `FindAndReplace` processor and build a versioned package
   - The munki recipe parents the pkg recipe (not the download recipe) and merges the version into pkginfo via `MunkiPkginfoMerger`

**Do not silently proceed** when version info is missing or unusable.

### Step 5: Create Download Recipe

Follow the structure in [download recipe reference](./references/download-recipe.md).

Key rules:
- INPUT should ideally only contain NAME variable (no spaces in the value)
- Include EndOfCheckPhase after URLDownloader
- Include CodeSignatureVerifier with hardcoded app names (not `%NAME%.app`)
- **No versioning steps in download recipes** — Versioner belongs in the munki recipe
- **No FlatPkgUnpacker or PkgPayloadUnpacker in download recipes** — PKG unpacking belongs in the munki recipe
- Use URLTextSearcher to scrape URLs rather than hardcoding where possible

**Download recipe should be lean** — its job is only to download, unarchive (if ZIP), and verify the code signature:
- For DMG: URLDownloader → EndOfCheckPhase → CodeSignatureVerifier (on the .app with `requirement`)
- For ZIP containing .app: URLDownloader → EndOfCheckPhase → Unarchiver → CodeSignatureVerifier (on the .app with `requirement`)
- For ZIP containing .pkg: URLDownloader → EndOfCheckPhase → Unarchiver → CodeSignatureVerifier (on the .pkg with `expected_authority_names`)
- For direct .pkg: URLDownloader → EndOfCheckPhase → CodeSignatureVerifier (on the .pkg with `expected_authority_names`)

**GitHub Releases pre-release check:** When the download URL points to a GitHub Releases page, check whether the releases are marked as pre-releases before creating the recipe:

```zsh
curl -s "https://api.github.com/repos/OWNER/REPO/releases" | python3 -c "import sys,json; [print(f'{r[\"tag_name\"]}: prerelease={r[\"prerelease\"]}') for r in json.load(sys.stdin)]"
```

Pre-releases are considered beta versions. If there is a mix of normal releases and pre-releases, just continue — `GitHubReleasesInfoProvider` will use the latest normal release by default (with `PRERELEASE` as an empty string).

If **all** releases are pre-releases (no normal releases exist), **STOP and ask the user** whether they want to continue. Explain that all releases are pre-releases (beta versions) and the recipe would need `PRERELEASE` set to `True` to find them. Only proceed if the user confirms. If approved, set `PRERELEASE` to `True` in the Input section.

**CodeSignatureVerifier format depends on what you're verifying:**
- `.app` bundles → use `requirement` key with the designated requirement string (from `codesign -dr -`)
- `.pkg` files → use `expected_authority_names` array with the certificate chain (from `pkgutil --check-signature`)

### Step 6: Create Munki Recipe

Follow the structure in [munki recipe reference](./references/munki-recipe.md).

Key rules:
- ParentRecipe must point to the download recipe
- **Input key ordering matters** — keys that reference other variables must come after those variables are declared. Since `MUNKI_REPO_SUBDIR` references `%NAME%`, always declare `NAME` before `MUNKI_REPO_SUBDIR` in the Input dict
- MUNKI_REPO_SUBDIR set to `apps/%NAME%`
- Complete pkginfo with catalogs, description, developer, display_name, name, unattended_install, unattended_uninstall
- Include `blocking_applications` in pkginfo (e.g., `AppName.app`)
- For standard DMGs with .app: use simple MunkiImporter approach — do NOT use MunkiInstallsItemsCreator (MunkiImporter auto-generates the installs array for drag-and-drop .app bundles)
- For .pkg files or ZIP-wrapped PKGs: the **munki recipe** handles all PKG unpacking — FlatPkgUnpacker → PkgPayloadUnpacker → MunkiInstallsItemsCreator → MunkiPkginfoMerger → Versioner → MunkiPkginfoMerger (version) → MunkiImporter → PathDeleter. MinimumVersion must be 2.7 and DERIVE_MIN_OS must be added to Input.
- For archives (zip/tbz) containing .app: use Unarchiver + DmgCreator to convert to DMG, then import with `%dmg_path%`
- For unsigned DMGs with .app: consider AppDmgVersioner as a simpler alternative to Versioner
- When using `CFBundleVersion` instead of `CFBundleShortVersionString`, add `version_comparison_key` to MunkiImporter

### Step 6b: Create Pkg Recipe (if needed)

Follow the structure in [pkg recipe reference](./references/pkg-recipe.md).

Key rules:
- ParentRecipe always points to the download recipe (not the munki recipe)
- For downloads that are already `.pkg`: use PkgCopier
- For DMGs/archives containing `.app`: use AppPkgCreator
- For non-app bundles (prefpane, plugin, etc.): use PkgRootCreator + Copier + PkgCreator
- For apps with **no version in Info.plist** (version extracted from URL): use the core `FindAndReplace` processor (MinimumVersion 2.7.6) + PkgRootCreator + Copier + PkgCreator (see [Approach 6 in pkg reference](./references/pkg-recipe.md#approach-6-app-bundle-with-version-from-url))
- When using `PkgCreator` with a custom `PKG_ID`, include an `uninstall_script` in the munki recipe's pkginfo (see [uninstall scripts in munki reference](./references/munki-recipe.md#uninstall-scripts))
- Output pkg named `%NAME%-%version%.pkg` when version is available

### Step 7: Test the Recipe

**Always test the full chain** by running the munki recipe (or the last recipe in the chain). Never test individual download or pkg recipes in isolation — running the munki recipe automatically runs all parent recipes, validating the complete flow:

```zsh
autopkg run -vvv "App Name.munki.recipe"
```

**If the recipe fails:**
1. Review the verbose output for processor errors
2. Inspect the cache folder for intermediate files (the default cache location is shown below — check `autopkg info` if a custom `CACHE_DIR` is configured):
   ```zsh
   open ~/Library/AutoPkg/Cache/com.github.dataJAR-recipes.munki.AppName/
   ```
3. Common issues to check:
   - CodeSignatureVerifier `input_path` — must point to the .app inside the DMG (e.g., `%pathname%/Typora.app`), not the DMG itself
   - Download URL returning 403/404 — may need custom headers
   - Version not detected — check if app uses `CFBundleVersion` instead of `CFBundleShortVersionString`
4. Fix the recipe and re-run until successful

**If the recipe succeeds:**
- Verify the downloaded file in the cache folder
- Check the generated pkginfo in the cache folder
- Confirm all expected keys are present (minimum_os_version, installs array, etc.)

**Clean up after successful test:**
If you downloaded parent recipes for testing (Step 3), delete them now - they're not needed in the repo:
```zsh
rm "App Name.download.recipe"  # or .pkg.recipe if applicable
```
Only keep the new dataJAR recipes you created.

### Step 8: Validate Against Linter Standards

Apply all rules from the [linter standards reference](./references/linter-standards.md):

- 4-space indentation, no tabs, no trailing whitespace
- NAME variable has no spaces
- Input keys ordered with dependency awareness (if KEY_A references %KEY_B%, then KEY_B must come before KEY_A)
- Processor arguments in alphabetical order
- Processor key is last within each processor dict (plist)
- MinimumVersion must be at least 1.1, or higher if processors require it (e.g., 2.7 if using MunkiInstallsItemsCreator derive_minimum_os_version)
- PathDeleter is last in Process array when used
- MunkiPkginfoMerger immediately follows MunkiInstallsItemsCreator
- All scripts must use `#!/bin/zsh --no-rcs` — never bash or sh
- XML entities properly escaped (`&amp;`, `&lt;`, `&gt;`)
- No HTML comments (use Comment key instead)
- DERIVE_MIN_OS input variable when using derive_minimum_os_version
- PRERELEASE input variable when using GitHubReleasesInfoProvider

### Step 9: Run Linter Verification (Mandatory)

**Always run the linter after creating or modifying recipes.** Do not consider a recipe complete until it passes linting with no warnings or errors for the recipe files you created.

Run the linter against the created recipes:
```zsh
/usr/local/autopkg/python "*AutoPkg Linters/autopkg-linter.py"
```

The linter scans the entire repo. Filter the output for your recipe to check for issues:
```zsh
/usr/local/autopkg/python "*AutoPkg Linters/autopkg-linter.py" 2>&1 | grep -i "AppName"
```

**If the linter reports issues**, fix them and re-run until clean. Common linter catches:
- Input key ordering (variables referenced before they are declared)
- Missing PRERELEASE description text
- Missing PathDeleter for unpacked files
- Processor arguments not in alphabetical order
- FindAndReplace used as shared processor instead of core

**Do not skip this step.** Linting errors indicate recipe issues that will cause problems in production.

### Step 10: Pre-commit Hook Enforcement (Mandatory)

This repository uses a `.pre-commit-config.yaml` with [pre-commit-macadmin](https://github.com/homebysix/pre-commit-macadmin) hooks to enforce recipe standards on every commit. The hooks include:

- **check-autopkg-recipes** — validates recipe structure and enforces the `com.github.dataJAR-recipes.` identifier prefix
- **forbid-autopkg-overrides** — prevents override files from being committed
- **forbid-autopkg-trust-info** — prevents trust info from being committed

**Ensure pre-commit is installed and hooks are active:**
```zsh
pre-commit install
```

**Run pre-commit manually against your changed files:**
```zsh
pre-commit run --files "App Name/App Name.download.recipe" "App Name/App Name.munki.recipe"
```

**Or run against all files:**
```zsh
pre-commit run --all-files
```

**If pre-commit reports issues**, fix them and re-run until clean. Common pre-commit catches:
- Recipe identifier not using the `com.github.dataJAR-recipes.` prefix
- Override files accidentally staged
- Trust info left in recipe files

**Do not skip this step.** Pre-commit hooks are enforced in this repository. Commits that fail pre-commit checks will be rejected.

## Naming Conventions

| Element | Format | Example |
|---------|--------|---------|
| App name | Full Finder name | `RingCentral Phone` |
| NAME variable | No spaces | `RingCentralPhone` |
| Identifier | `com.github.dataJAR-recipes.[type].[App Name]` | `com.github.dataJAR-recipes.download.RingCentral Phone` |
| File name | `[App Name].[type].recipe` | `RingCentral Phone.download.recipe` |
| Munki catalog | `testing` | `testing` |
| MUNKI_REPO_SUBDIR | `apps/%NAME%` | `apps/%NAME%` |
| Version-specific | Include version in name | `Digital Pigeon 4` / `DigitalPigeon4` |

## Architecture Support

See [architecture reference](./references/architecture.md) for patterns covering:
- DOWNLOAD_ARCH variable in download recipes
- SUPPORTED_ARCH variable in munki recipes
- URL scraping with architecture variables
- GitHubReleasesInfoProvider with architecture-specific assets
- Common vendor architecture naming conventions

## Discovery Guidance

When creating recipes for an application, gather key facts:

### Finding Sparkle Feed URLs
Check the app's `Info.plist` for Sparkle feed keys:
```zsh
defaults read "/Applications/Application Name.app/Contents/Info" SUFeedURL
defaults read "/Applications/Application Name.app/Contents/Info" SUOriginalFeedURL
```
Also check for `DevMateKit.framework` in Frameworks — DevMate apps use Sparkle under the hood.

### Extracting Code Signature Info
Get the designated requirement for CodeSignatureVerifier:
```zsh
codesign --display --verbose=2 -r- "/Applications/Application Name.app" 2>&1 | grep '^designated'
```
This outputs the `designated =>` line containing the requirement string.

### Choosing a Version Key
Prefer `CFBundleShortVersionString` when it contains a valid version (e.g., `1.2.3`). Fall back to `CFBundleVersion` when `CFBundleShortVersionString` is missing, empty, or contains a non-version string. Check both:
```zsh
defaults read "/Applications/Application Name.app/Contents/Info" CFBundleShortVersionString
defaults read "/Applications/Application Name.app/Contents/Info" CFBundleVersion
```
When using `CFBundleVersion`, add `version_comparison_key` to MunkiImporter and use MunkiPkginfoMerger for the version.

### Identifying Blocking Applications
For pkg-based installs, expand the package to find user-facing apps:
```zsh
/usr/sbin/pkgutil --expand "/path/to/package.pkg" /tmp/expanded_pkg
find /tmp/expanded_pkg -name "*.app" -maxdepth 4
```
Exclude utility apps (Autoupdate.app, Install.app, Uninstaller.app).

## Processor Reference

See [processor reference](./references/processors.md) for:
- Core AutoPkg processor list and priority order
- URL scraping patterns (direct capture, version-first, multi-step, custom headers)
- Named capture groups in URLTextSearcher for extracting multiple values
- FindAndReplace processor usage (version conversion, string manipulation)
- Code signature verification patterns
- Installs array generation approaches
- Minimum OS version detection methods
- Package unpacking and payload handling
- Sparkle, AppDmgVersioner, DmgCreator, PkgCopier, AppPkgCreator patterns
- Non-app bundle handling and version key selection

## Common Anti-Patterns to Avoid

1. **Never invent processors** — only use documented, existing processors
2. **Never invent processor keys** — only use documented arguments
3. **Never use `%NAME%.app`** in CodeSignatureVerifier — hardcode the app name
4. **Never use wrong CodeSignatureVerifier format** — .app bundles (DMG/ZIP) require `requirement` key; .pkg files require `expected_authority_names` array. Never mix these formats.
5. **Never hardcode minimum_os_version** — use dynamic detection
6. **Never put versioning in download recipes** — version detection belongs in munki recipes
7. **Never use tabs** — always 4 spaces
8. **Never use DOWNLOAD_URL in INPUT** unless needed for architecture variants
9. **Never use bundle items** in installs arrays — use plist items for .definitions support
10. **Never use bash or sh** — all scripts must use `#!/bin/zsh --no-rcs`, never `#!/bin/bash`, `#!/bin/sh`, or `#!/bin/zsh` without `--no-rcs`
11. **Never use HTML comments** — use Comment key pairs instead
12. **Never use generic asset_regex** — for GitHubReleasesInfoProvider, use as much of the actual filename as possible, replacing only the version with a capture group. Never use `.*\.dmg$` or similar broad patterns
13. **Never use fixed-length version capture groups** — use flexible patterns like `([0-9]+(-[0-9]+)+)` or `([0-9]+(\.[0-9]+)+)` that match any number of version components. Never use `(\d+)-(\d+)-(\d+)` or `([0-9]+)\.([0-9]+)\.([0-9]+)` which break when versions have more or fewer components
14. **Never make up processor keys** — always verify processor arguments against the [AutoPkg wiki](https://github.com/autopkg/autopkg/wiki). For `FindAndReplace`, the only accepted keys are `input_string`, `find`, `replace`, and `result_output_var_name`
15. **Never use FindAndReplace as a shared processor** — `FindAndReplace` is a core processor since AutoPkg 2.7.6. Use `<string>FindAndReplace</string>`, never `<string>com.github.homebysix.FindAndReplace/FindAndReplace</string>`
16. **Never hardcode versioned download URLs** — if a URL contains version numbers (e.g., `app-1-8-1.zip`), scrape the vendor page with `URLTextSearcher` instead of hardcoding the URL
17. **Never use 0777 permissions in pkgdirs** — use `0755` for application directories (`root/Applications`) and other standard paths. Mode `0777` makes directories world-writable, which is insecure and can cause undesirable permission changes during install

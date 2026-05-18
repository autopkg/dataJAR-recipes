# Munki Recipe Reference

## Structure Template (Simple DMG Import)

For standard DMG files containing a .app bundle — the preferred approach:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Description</key>
    <string>Downloads the latest version of [APP NAME] and imports it into Munki.</string>
    <key>Identifier</key>
    <string>com.github.dataJAR-recipes.munki.[App Name With Spaces]</string>
    <key>Input</key>
    <dict>
        <key>NAME</key>
        <string>[NameNoSpaces]</string>
        <key>MUNKI_REPO_SUBDIR</key>
        <string>apps/%NAME%</string>
        <key>pkginfo</key>
        <dict>
            <key>blocking_applications</key>
            <array>
                <string>[App Display Name].app</string>
            </array>
            <key>catalogs</key>
            <array>
                <string>testing</string>
            </array>
            <key>description</key>
            <string>[App description]</string>
            <key>developer</key>
            <string>[Developer Name]</string>
            <key>display_name</key>
            <string>[App Display Name]</string>
            <key>name</key>
            <string>%NAME%</string>
            <key>unattended_install</key>
            <true/>
            <key>unattended_uninstall</key>
            <true/>
        </dict>
    </dict>
    <key>MinimumVersion</key>
    <string>1.1</string>
    <key>ParentRecipe</key>
    <string>com.github.dataJAR-recipes.download.[App Name With Spaces]</string>
    <key>Process</key>
    <array>
        <dict>
            <key>Arguments</key>
            <dict>
                <key>pkg_path</key>
                <string>%pathname%</string>
                <key>repo_subdirectory</key>
                <string>%MUNKI_REPO_SUBDIR%</string>
            </dict>
            <key>Processor</key>
            <string>MunkiImporter</string>
        </dict>
    </array>
</dict>
</plist>
```

## Structure Template (PKG / Complex Processing with Installs Array)

For .pkg files or complex installations where MunkiImporter cannot auto-detect the installs array (not for simple drag-and-drop .app in DMG):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Description</key>
    <string>Downloads the latest version of [APP NAME] and imports it into Munki.

Set the DERIVE_MIN_OS variable to a non-empty string to set the minimum_os_version via MunkiInstallsItemsCreator. This requires a minimum AutoPkg version of 2.7 please update if you're not already running it.</string>
    <key>Identifier</key>
    <string>com.github.dataJAR-recipes.munki.[App Name With Spaces]</string>
    <key>Input</key>
    <dict>
        <key>DERIVE_MIN_OS</key>
        <string>YES</string>
        <key>NAME</key>
        <string>[NameNoSpaces]</string>
        <key>MUNKI_REPO_SUBDIR</key>
        <string>apps/%NAME%</string>
        <key>pkginfo</key>
        <dict>
            <key>blocking_applications</key>
            <array>
                <string>[App Display Name].app</string>
            </array>
            <key>catalogs</key>
            <array>
                <string>testing</string>
            </array>
            <key>description</key>
            <string>[App description]</string>
            <key>developer</key>
            <string>[Developer Name]</string>
            <key>display_name</key>
            <string>[App Display Name]</string>
            <key>name</key>
            <string>%NAME%</string>
            <key>unattended_install</key>
            <true/>
            <key>unattended_uninstall</key>
            <true/>
        </dict>
    </dict>
    <key>MinimumVersion</key>
    <string>2.7</string>
    <key>ParentRecipe</key>
    <string>com.github.dataJAR-recipes.download.[App Name With Spaces]</string>
    <key>Process</key>
    <array>
        <!-- Processors for unpacking, installs array generation, importing -->
    </array>
</dict>
</plist>
```

## Processing Approaches

### Approach 1: Simple DMG Import (Preferred)

Use for standard DMG files containing a drag-and-drop .app bundle. **Do NOT use MunkiInstallsItemsCreator** — MunkiImporter automatically generates the installs array and detects the version for .app bundles in a DMG.

```xml
<dict>
    <key>Arguments</key>
    <dict>
        <key>pkg_path</key>
        <string>%pathname%</string>
        <key>repo_subdirectory</key>
        <string>%MUNKI_REPO_SUBDIR%</string>
    </dict>
    <key>Processor</key>
    <string>MunkiImporter</string>
</dict>
```

### Approach 2: PKG Unpacking with Installs Array and Version Extraction

Use for .pkg files that need installs array generation and version extraction. This is the standard flow:

1. Unpack the flat package
2. Extract the payload to match installation directory structure
3. Generate installs array with MunkiInstallsItemsCreator
4. Merge installs info with MunkiPkginfoMerger
5. Extract version with Versioner
6. Merge version into pkginfo
7. Import into Munki
8. Clean up unpacked files

```xml
<!-- 1. Unpack the flat package -->
<dict>
    <key>Arguments</key>
    <dict>
        <key>destination_path</key>
        <string>%RECIPE_CACHE_DIR%/unpacked</string>
        <key>flat_pkg_path</key>
        <string>%pathname%</string>
        <key>purge_destination</key>
        <true/>
    </dict>
    <key>Processor</key>
    <string>FlatPkgUnpacker</string>
</dict>
<!-- 2. Extract payload to match installation path (/Applications) -->
<dict>
    <key>Arguments</key>
    <dict>
        <key>destination_path</key>
        <string>%RECIPE_CACHE_DIR%/Applications</string>
        <key>pkg_payload_path</key>
        <string>%RECIPE_CACHE_DIR%/unpacked/%NAME%.pkg/Payload</string>
        <key>purge_destination</key>
        <true/>
    </dict>
    <key>Processor</key>
    <string>PkgPayloadUnpacker</string>
</dict>
<!-- 3. Generate installs array (faux_root one level above /Applications) -->
<dict>
    <key>Arguments</key>
    <dict>
        <key>derive_minimum_os_version</key>
        <string>%DERIVE_MIN_OS%</string>
        <key>faux_root</key>
        <string>%RECIPE_CACHE_DIR%</string>
        <key>installs_item_paths</key>
        <array>
            <string>/Applications/%NAME%.app</string>
        </array>
    </dict>
    <key>Processor</key>
    <string>MunkiInstallsItemsCreator</string>
</dict>
<!-- 4. Merge installs info (required immediately after MunkiInstallsItemsCreator) -->
<dict>
    <key>Processor</key>
    <string>MunkiPkginfoMerger</string>
</dict>
<!-- 5. Extract version from the unpacked app bundle -->
<dict>
    <key>Arguments</key>
    <dict>
        <key>input_plist_path</key>
        <string>%RECIPE_CACHE_DIR%/Applications/%NAME%.app/Contents/Info.plist</string>
        <key>plist_version_key</key>
        <string>CFBundleVersion</string>
    </dict>
    <key>Processor</key>
    <string>Versioner</string>
</dict>
<!-- 6. Merge extracted version into pkginfo -->
<dict>
    <key>Arguments</key>
    <dict>
        <key>additional_pkginfo</key>
        <dict>
            <key>version</key>
            <string>%version%</string>
        </dict>
    </dict>
    <key>Processor</key>
    <string>MunkiPkginfoMerger</string>
</dict>
<!-- 7. Import into Munki -->
<dict>
    <key>Arguments</key>
    <dict>
        <key>pkg_path</key>
        <string>%pathname%</string>
        <key>repo_subdirectory</key>
        <string>%MUNKI_REPO_SUBDIR%</string>
    </dict>
    <key>Processor</key>
    <string>MunkiImporter</string>
</dict>
<!-- 8. Clean up unpacked files (must be last) -->
<dict>
    <key>Arguments</key>
    <dict>
        <key>path_list</key>
        <array>
            <string>%RECIPE_CACHE_DIR%/unpacked</string>
            <string>%RECIPE_CACHE_DIR%/Applications</string>
        </array>
    </dict>
    <key>Processor</key>
    <string>PathDeleter</string>
</dict>
```

**Key points for this flow:**
- `destination_path` in PkgPayloadUnpacker creates the `/Applications` directory structure so `faux_root` = `%RECIPE_CACHE_DIR%` finds the app at `/Applications/%NAME%.app`
- The sub-package name in `pkg_payload_path` (e.g., `%NAME%.pkg`) must match the actual package name inside the flat pkg — examine with `pkgutil --expand` if unsure
- Versioner uses `plist_version_key` to select which plist key provides the version (commonly `CFBundleVersion` or `CFBundleShortVersionString`)
- The second MunkiPkginfoMerger sets the top-level `version` key from the Versioner output
- PathDeleter paths must match all `destination_path` values from FlatPkgUnpacker and PkgPayloadUnpacker

### Approach 3: DMG with .app Needing Installs Array

For .app files from DMG that need custom installs array handling:

```xml
<!-- 1. Copy app to staging area -->
<dict>
    <key>Arguments</key>
    <dict>
        <key>destination_path</key>
        <string>%RECIPE_CACHE_DIR%/%NAME%/Applications/%NAME%.app</string>
        <key>source_path</key>
        <string>%pathname%/ActualAppName.app</string>
    </dict>
    <key>Processor</key>
    <string>Copier</string>
</dict>
<!-- 2. Generate installs array -->
<dict>
    <key>Arguments</key>
    <dict>
        <key>derive_minimum_os_version</key>
        <string>%DERIVE_MIN_OS%</string>
        <key>faux_root</key>
        <string>%RECIPE_CACHE_DIR%/%NAME%</string>
        <key>installs_item_paths</key>
        <array>
            <string>/Applications/%NAME%.app</string>
        </array>
    </dict>
    <key>Processor</key>
    <string>MunkiInstallsItemsCreator</string>
</dict>
<dict>
    <key>Processor</key>
    <string>MunkiPkginfoMerger</string>
</dict>
<!-- 3. Create DMG and import -->
<dict>
    <key>Arguments</key>
    <dict>
        <key>dmg_path</key>
        <string>%RECIPE_CACHE_DIR%/%NAME%.dmg</string>
        <key>dmg_root</key>
        <string>%pathname%</string>
    </dict>
    <key>Processor</key>
    <string>DmgCreator</string>
</dict>
<dict>
    <key>Arguments</key>
    <dict>
        <key>pkg_path</key>
        <string>%dmg_path%</string>
        <key>repo_subdirectory</key>
        <string>%MUNKI_REPO_SUBDIR%</string>
    </dict>
    <key>Processor</key>
    <string>MunkiImporter</string>
</dict>
<!-- 4. Clean up -->
<dict>
    <key>Arguments</key>
    <dict>
        <key>path_list</key>
        <array>
            <string>%RECIPE_CACHE_DIR%/%NAME%</string>
        </array>
    </dict>
    <key>Processor</key>
    <string>PathDeleter</string>
</dict>
```

### Approach 4: Archive (zip) with DMG Conversion

For zip/archive downloads, extract the archive, create a DMG, then import. Use `%dmg_path%` (not `%pathname%`) for the MunkiImporter:

```xml
<!-- 1. Unarchive if not already done in download recipe -->
<dict>
    <key>Arguments</key>
    <dict>
        <key>archive_path</key>
        <string>%pathname%</string>
        <key>destination_path</key>
        <string>%RECIPE_CACHE_DIR%/%NAME%</string>
        <key>purge_destination</key>
        <true/>
    </dict>
    <key>Processor</key>
    <string>Unarchiver</string>
</dict>
<!-- 2. Create DMG from extracted contents -->
<dict>
    <key>Arguments</key>
    <dict>
        <key>dmg_path</key>
        <string>%RECIPE_CACHE_DIR%/%NAME%.dmg</string>
        <key>dmg_root</key>
        <string>%RECIPE_CACHE_DIR%/%NAME%</string>
    </dict>
    <key>Processor</key>
    <string>DmgCreator</string>
</dict>
<!-- 3. Import the DMG into Munki -->
<dict>
    <key>Arguments</key>
    <dict>
        <key>pkg_path</key>
        <string>%dmg_path%</string>
        <key>repo_subdirectory</key>
        <string>%MUNKI_REPO_SUBDIR%</string>
    </dict>
    <key>Processor</key>
    <string>MunkiImporter</string>
</dict>
```

**Key point:** MunkiImporter uses `%dmg_path%` (from DmgCreator output) not `%pathname%` when importing from an archive-based download.

If the archive download gets Unarchiver + CodeSignatureVerifier in the download recipe (for signed apps), skip the Unarchiver step in the munki recipe — it's already extracted.

### Approach 5: Unsigned DMG with AppDmgVersioner

For unsigned apps in DMG where the version key is `CFBundleShortVersionString`, use `AppDmgVersioner` — it's simpler than `Versioner`:

```xml
<dict>
    <key>Arguments</key>
    <dict>
        <key>dmg_path</key>
        <string>%pathname%</string>
    </dict>
    <key>Processor</key>
    <string>AppDmgVersioner</string>
</dict>
<dict>
    <key>Arguments</key>
    <dict>
        <key>pkg_path</key>
        <string>%pathname%</string>
        <key>repo_subdirectory</key>
        <string>%MUNKI_REPO_SUBDIR%</string>
    </dict>
    <key>Processor</key>
    <string>MunkiImporter</string>
</dict>
```

Use `Versioner` instead of `AppDmgVersioner` when:
- The version key is `CFBundleVersion` (not `CFBundleShortVersionString`)
- The bundle type is not `.app` (e.g., `.prefpane`)
- The download is not a DMG

### Approach 6: Non-Default Version Key (CFBundleVersion)

When an app uses `CFBundleVersion` instead of `CFBundleShortVersionString`, add `version_comparison_key` to MunkiImporter and merge the version explicitly:

```xml
<!-- Extract version -->
<dict>
    <key>Arguments</key>
    <dict>
        <key>input_plist_path</key>
        <string>%pathname%/ActualAppName.app/Contents/Info.plist</string>
        <key>plist_version_key</key>
        <string>CFBundleVersion</string>
    </dict>
    <key>Processor</key>
    <string>Versioner</string>
</dict>
<!-- Merge version into pkginfo -->
<dict>
    <key>Arguments</key>
    <dict>
        <key>additional_pkginfo</key>
        <dict>
            <key>version</key>
            <string>%version%</string>
        </dict>
    </dict>
    <key>Processor</key>
    <string>MunkiPkginfoMerger</string>
</dict>
<!-- Import with version_comparison_key -->
<dict>
    <key>Arguments</key>
    <dict>
        <key>pkg_path</key>
        <string>%pathname%</string>
        <key>repo_subdirectory</key>
        <string>%MUNKI_REPO_SUBDIR%</string>
        <key>version_comparison_key</key>
        <string>CFBundleVersion</string>
    </dict>
    <key>Processor</key>
    <string>MunkiImporter</string>
</dict>
```

## Required pkginfo Keys

All munki recipes must include these in the pkginfo dict:

| Key | Value | Notes |
|-----|-------|-------|
| catalogs | `["testing"]` | Default catalog |
| description | App description text | Brief description |
| developer | Developer name | Company/person |
| display_name | App display name | Human-readable |
| name | `%NAME%` | Variable reference |
| unattended_install | `true` | Boolean |
| unattended_uninstall | `true` | Boolean |

## Optional pkginfo Keys

| Key | Purpose | Example |
|-----|---------|---------|
| blocking_applications | Apps to quit before install | `["App.app"]` |
| requires | Dependencies | `["MicrosoftPowerPoint365"]` |
| update_for | What this updates | `["ParentApp"]` |
| supported_architectures | Architecture restriction | `["%SUPPORTED_ARCH%"]` |
| minimum_os_version | Minimum OS (prefer dynamic) | `%min_os_ver%` |
| uninstall_method | Custom uninstall | `uninstall_script` |
| uninstall_script | Uninstall script content | Shell script |

## Uninstall Scripts

When a pkg recipe builds a package with `PkgCreator` (using a custom `PKG_ID`), Munki cannot automatically uninstall it — you must provide an `uninstall_script` in the munki recipe's pkginfo.

**When to include an uninstall script:**
- The pkg recipe uses `PkgCreator` with a custom package receipt ID (`PKG_ID`)
- The app was installed via a custom-built package (not a vendor `.pkg`)

**Required keys:**
- `uninstall_method` must be set to `uninstall_script` and must appear **before** `uninstall_script` in the pkginfo dict
- `uninstall_script` contains the shell script

**Script rules:**
- Always use `#!/bin/zsh --no-rcs` shebang
- Check the app bundle exists before deleting with `[[ -d ... ]]`
- Use `%PKG_ID%` variable (not hardcoded) so overrides are respected
- Always `pkgutil --forget` the package receipt, but **guard it** with `pkgutil --pkg-info` first — `--forget` exits non-zero if the receipt is missing, which causes Munki to report uninstall failure
- Use full paths for commands (`/bin/rm`, `/usr/sbin/pkgutil`)

### Example: Simple App Uninstall with Package Receipt

```xml
<key>uninstall_method</key>
<string>uninstall_script</string>
<key>uninstall_script</key>
<string>#!/bin/zsh --no-rcs

if [[ -d "/Applications/Application Name.app" ]]; then
    /bin/rm -rf "/Applications/Application Name.app"
fi

if /usr/sbin/pkgutil --pkg-info "%PKG_ID%" &amp;&gt; /dev/null; then
    /usr/sbin/pkgutil --forget "%PKG_ID%"
fi
</string>
```

**Note:** `%PKG_ID%` is inherited from the parent pkg recipe's `Input` dict — do not duplicate it in the munki recipe's `Input`.

## Input Variable Inheritance

AutoPkg child recipes inherit all `Input` variables from their parent recipes. **Do not duplicate input variables** that are already defined in a parent recipe:

- Variables like `NAME`, `PKG_ID`, etc. defined in the download or pkg recipe are automatically available in the munki recipe
- Only add variables to the munki recipe's `Input` that are **new to the munki recipe** (e.g., `MUNKI_REPO_SUBDIR`, `MUNKI_CATEGORY`, `pkginfo`, `DERIVE_MIN_OS`)
- Duplicating a parent's input variable creates confusion about which recipe "owns" it and where overrides should be applied

## Payload Unpacking Rules

- Match unpacked directory structure to actual installation paths
- For apps in /Applications: `destination_path` = `%RECIPE_CACHE_DIR%/Applications`
- For plugins in /Library: `destination_path` = `%RECIPE_CACHE_DIR%/Library/Audio/Plug-Ins/VST`
- Set `faux_root` = `%RECIPE_CACHE_DIR%` so MunkiInstallsItemsCreator finds files at correct paths
- When unpacking multiple packages: `purge_destination` = true for FIRST only, false for subsequent
- Never use placeholder names in installs_item_paths — examine actual package contents first

## Minimum OS Version Detection

### Method 1: MunkiInstallsItemsCreator (Preferred, requires MinimumVersion 2.7)
Use `derive_minimum_os_version` key with `%DERIVE_MIN_OS%` variable.

### Method 2: PlistReader (for .pkg files)
Read LSMinimumSystemVersion from Info.plist, merge via MunkiPkginfoMerger.

### Method 3: Distribution File Parsing
Use URLTextSearcher on `file://localhost/%RECIPE_CACHE_DIR%/unpack/Distribution`.

### Method 4: Vendor Website Scraping
Use URLTextSearcher on vendor's download/release page.

## Dependency Management

```xml
<key>requires</key>
<array>
    <string>MicrosoftPowerPoint365</string>
</array>

<key>blocking_applications</key>
<array>
    <string>Microsoft PowerPoint</string>
</array>
```

Use exact package names in requires array (matching name keys in Munki repository).

### Identifying Blocking Applications

For pkg-based installs, examine the apps inside the package payload to identify blocking applications. Expand the package to inspect:
```zsh
/usr/sbin/pkgutil --expand "/path/to/package.pkg" /tmp/expanded_pkg
find /tmp/expanded_pkg -name "*.app" -maxdepth 4
```

Exclude utility apps that should NOT be blocking applications:
- `Autoupdate.app`
- `Install.app` / `Installer.app`
- `Uninstall.app` / `Uninstaller.app`

All remaining user-facing apps found in the payload should be listed as blocking applications.

## Non-App Bundle Types

For preference panes, plugins, screen savers, and other non-app bundles, MunkiImporter needs `additional_makepkginfo_options` to specify the item name and destination:

```xml
<dict>
    <key>Arguments</key>
    <dict>
        <key>additional_makepkginfo_options</key>
        <array>
            <string>--destinationpath</string>
            <string>/Library/PreferencePanes</string>
            <string>--itemname</string>
            <string>MyPrefPane.prefpane</string>
        </array>
        <key>pkg_path</key>
        <string>%pathname%</string>
        <key>repo_subdirectory</key>
        <string>%MUNKI_REPO_SUBDIR%</string>
    </dict>
    <key>Processor</key>
    <string>MunkiImporter</string>
</dict>
```

Standard destinations for non-app bundle types:

| Bundle Type | Destination Path |
|-------------|-----------------|
| `.prefpane` | `/Library/PreferencePanes` |
| `.plugin` | `/Library/Internet Plug-Ins` |
| `.qlgenerator` | `/Library/QuickLook` |
| `.saver` | `/Library/Screen Savers` |

## MunkiImporter pkg_path by Download Format

The `pkg_path` argument to MunkiImporter depends on the download format:

| Download Format | pkg_path Value | Notes |
|----------------|---------------|-------|
| DMG | `%pathname%` | Direct reference to downloaded DMG |
| PKG | `%pathname%` | Direct reference to downloaded PKG |
| ZIP/Archive | `%dmg_path%` | After DmgCreator converts extracted contents |

## Architecture Support in Munki Recipes

```xml
<!-- In Description -->
<string>Downloads the latest version of [APP] and imports it into Munki.

For Intel use: "x86_64" in the SUPPORTED_ARCH variable
For Apple Silicon use: "arm64" in the SUPPORTED_ARCH variable</string>

<!-- In Input -->
<key>SUPPORTED_ARCH</key>
<string>arm64</string>

<!-- In pkginfo -->
<key>supported_architectures</key>
<array>
    <string>%SUPPORTED_ARCH%</string>
</array>
```

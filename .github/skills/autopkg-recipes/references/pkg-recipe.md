# Pkg Recipe Reference

Pkg recipes create installer packages (.pkg) from downloads. The parent recipe is always a download recipe.

## Template Structure

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Description</key>
    <string>Downloads the latest version of APPLICATION_NAME and creates a package.</string>
    <key>Identifier</key>
    <string>com.github.dataJAR-recipes.pkg.APPLICATION NAME</string>
    <key>Input</key>
    <dict>
        <key>NAME</key>
        <string>ApplicationName</string>
    </dict>
    <key>MinimumVersion</key>
    <string>1.1</string>
    <key>ParentRecipe</key>
    <string>com.github.dataJAR-recipes.download.APPLICATION NAME</string>
    <key>Process</key>
    <array>
        <!-- Processors go here -->
    </array>
</dict>
</plist>
```

## Approach Selection

Choose the approach based on what the download recipe provides:

| Download Format | Contents | Approach |
|----------------|----------|----------|
| PKG | Already a package (version from Sparkle/GitHub) | 1: PkgCopier (simple) |
| PKG | Already a package (no version in download) | 2: PkgCopier with version extraction |
| DMG | Contains `.app` bundle | 3: AppPkgCreator |
| ZIP/Archive | Contains `.app` bundle | 4: AppPkgCreator (archive) |
| DMG | Contains non-app bundle (`.prefpane`, `.plugin`, etc.) | 5: PkgRootCreator + Copier + PkgCreator |
| DMG/Archive | Contains `.app` with no version in Info.plist | 6: FindAndReplace + PkgRootCreator + Copier + PkgCreator |

---

## Approach 1: PkgCopier (Simple)

When the download is already a `.pkg` and version is available from Sparkle or GitHub:

```xml
<key>Process</key>
<array>
    <dict>
        <key>Arguments</key>
        <dict>
            <key>pkg_path</key>
            <string>%RECIPE_CACHE_DIR%/%NAME%-%version%.pkg</string>
            <key>source_pkg</key>
            <string>%pathname%</string>
        </dict>
        <key>Processor</key>
        <string>PkgCopier</string>
    </dict>
</array>
```

When no version is available (no Sparkle, no GitHub):

```xml
<dict>
    <key>Arguments</key>
    <dict>
        <key>pkg_path</key>
        <string>%RECIPE_CACHE_DIR%/%NAME%.pkg</string>
        <key>source_pkg</key>
        <string>%pathname%</string>
    </dict>
    <key>Processor</key>
    <string>PkgCopier</string>
</dict>
```

### PKG Inside DMG

When the download is a DMG containing a `.pkg` file:

```xml
<dict>
    <key>Arguments</key>
    <dict>
        <key>pkg_path</key>
        <string>%RECIPE_CACHE_DIR%/%NAME%-%version%.pkg</string>
        <key>source_pkg</key>
        <string>%pathname%/ApplicationName.pkg</string>
    </dict>
    <key>Processor</key>
    <string>PkgCopier</string>
</dict>
```

Hardcode the actual `.pkg` filename (not `%NAME%.pkg`) in source_pkg when the path includes the DMG mount point.

---

## Approach 2: PkgCopier with Version Extraction

When the download is a `.pkg` with no version from Sparkle or GitHub, extract the version from an app inside the package payload:

```xml
<key>Process</key>
<array>
    <dict>
        <key>Arguments</key>
        <dict>
            <key>destination_path</key>
            <string>%RECIPE_CACHE_DIR%/unpacked</string>
            <key>flat_pkg_path</key>
            <string>%pathname%</string>
        </dict>
        <key>Processor</key>
        <string>FlatPkgUnpacker</string>
    </dict>
    <dict>
        <key>Arguments</key>
        <dict>
            <key>destination_path</key>
            <string>%RECIPE_CACHE_DIR%/payload</string>
            <key>pkg_payload_path</key>
            <string>%RECIPE_CACHE_DIR%/unpacked/PackageName.pkg/Payload</string>
            <key>purge_destination</key>
            <true/>
        </dict>
        <key>Processor</key>
        <string>PkgPayloadUnpacker</string>
    </dict>
    <dict>
        <key>Arguments</key>
        <dict>
            <key>input_plist_path</key>
            <string>%RECIPE_CACHE_DIR%/payload/Applications/Application Name.app/Contents/Info.plist</string>
            <key>plist_version_key</key>
            <string>CFBundleShortVersionString</string>
        </dict>
        <key>Processor</key>
        <string>Versioner</string>
    </dict>
    <dict>
        <key>Arguments</key>
        <dict>
            <key>pkg_path</key>
            <string>%RECIPE_CACHE_DIR%/%NAME%-%version%.pkg</string>
            <key>source_pkg</key>
            <string>%pathname%</string>
        </dict>
        <key>Processor</key>
        <string>PkgCopier</string>
    </dict>
    <dict>
        <key>Arguments</key>
        <dict>
            <key>path_list</key>
            <array>
                <string>%RECIPE_CACHE_DIR%/payload</string>
                <string>%RECIPE_CACHE_DIR%/unpacked</string>
            </array>
        </dict>
        <key>Processor</key>
        <string>PathDeleter</string>
    </dict>
</array>
```

Key points:
- `PackageName.pkg` must be the actual sub-package name inside the flat package (inspect with `pkgutil --expand`)
- The app path in `input_plist_path` must match the actual payload structure
- PathDeleter cleans up both unpacked and payload directories
- PathDeleter must be the last processor in the array

---

## Approach 3: AppPkgCreator (DMG Download)

When the download is a DMG containing an `.app` bundle:

```xml
<key>Process</key>
<array>
    <dict>
        <key>Processor</key>
        <string>AppPkgCreator</string>
    </dict>
</array>
```

AppPkgCreator with no arguments automatically finds the `.app` in the mounted DMG and creates a package.

When the `.app` is in a subdirectory of the DMG:

```xml
<dict>
    <key>Arguments</key>
    <dict>
        <key>app_path</key>
        <string>%pathname%/Subfolder/Application Name.app</string>
    </dict>
    <key>Processor</key>
    <string>AppPkgCreator</string>
</dict>
```

---

## Approach 4: AppPkgCreator (Archive Download)

When the download is a zip or other archive containing an `.app` bundle. If the download recipe already unarchives (for CodeSignatureVerifier), use the extracted path directly:

```xml
<key>Process</key>
<array>
    <dict>
        <key>Arguments</key>
        <dict>
            <key>app_path</key>
            <string>%RECIPE_CACHE_DIR%/%NAME%/Application Name.app</string>
        </dict>
        <key>Processor</key>
        <string>AppPkgCreator</string>
    </dict>
</array>
```

If the download recipe does not unarchive (unsigned app), add Unarchiver first:

```xml
<key>Process</key>
<array>
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
    <dict>
        <key>Arguments</key>
        <dict>
            <key>app_path</key>
            <string>%RECIPE_CACHE_DIR%/%NAME%/Application Name.app</string>
        </dict>
        <key>Processor</key>
        <string>AppPkgCreator</string>
    </dict>
</array>
```

---

## Approach 5: PkgRootCreator + Copier + PkgCreator (Non-App Bundles)

For preference panes, plugins, Quick Look generators, screen savers, and other non-app bundles.

### DMG Download Example (Preference Pane)

```xml
<key>Process</key>
<array>
    <dict>
        <key>Arguments</key>
        <dict>
            <key>pkgdirs</key>
            <dict>
                <key>Library</key>
                <string>0775</string>
                <key>Library/PreferencePanes</key>
                <string>0775</string>
            </dict>
            <key>pkgroot</key>
            <string>%RECIPE_CACHE_DIR%/pkgroot</string>
        </dict>
        <key>Processor</key>
        <string>PkgRootCreator</string>
    </dict>
    <dict>
        <key>Arguments</key>
        <dict>
            <key>destination_path</key>
            <string>%pkgroot%/Library/PreferencePanes/MyPrefPane.prefpane</string>
            <key>source_path</key>
            <string>%pathname%/MyPrefPane.prefpane</string>
        </dict>
        <key>Processor</key>
        <string>Copier</string>
    </dict>
    <dict>
        <key>Arguments</key>
        <dict>
            <key>pkg_request</key>
            <dict>
                <key>chown</key>
                <array>
                    <dict>
                        <key>group</key>
                        <string>admin</string>
                        <key>path</key>
                        <string>Library/PreferencePanes</string>
                        <key>user</key>
                        <string>root</string>
                    </dict>
                </array>
                <key>id</key>
                <string>com.example.myprefpane</string>
                <key>pkgname</key>
                <string>%NAME%-%version%</string>
                <key>pkgroot</key>
                <string>%pkgroot%</string>
                <key>version</key>
                <string>%version%</string>
            </dict>
        </dict>
        <key>Processor</key>
        <string>PkgCreator</string>
    </dict>
</array>
```

### pkgdirs by Bundle Type

The `pkgdirs` dictionary must include all parent directories leading to the destination:

| Bundle Type | pkgdirs Keys |
|-------------|-------------|
| `.prefpane` | `Library` → `Library/PreferencePanes` |
| `.plugin` | `Library` → `Library/Internet Plug-Ins` |
| `.qlgenerator` | `Library` → `Library/QuickLook` |
| `.saver` | `Library` → `Library/Screen Savers` |

All values should be `0775`.

### pkg_request Dictionary

| Key | Value | Description |
|-----|-------|-------------|
| `chown` | Array of dicts | Sets ownership on install paths (root:admin) |
| `id` | String | Bundle identifier of the item being packaged |
| `pkgname` | `%NAME%-%version%` | Output package filename (without .pkg) |
| `pkgroot` | `%pkgroot%` | Root directory for package contents |
| `version` | `%version%` | Version string from the Versioner or parent recipe |

The `chown` path must NOT have a leading slash (it is relative to pkgroot).

---

## Approach 6: App Bundle with Version from URL

When the download is a DMG or archive containing an `.app` bundle, but the app has **no version in its Info.plist** (`CFBundleShortVersionString` and `CFBundleVersion` are both missing or unusable). The version is extracted from the download URL by the download recipe using `URLTextSearcher` with a named capture group, producing a hyphenated version (e.g., `1-8-1`).

This approach uses `FindAndReplace` to convert the hyphenated version to dotted notation, then builds a package with `PkgRootCreator` + `Copier` + `PkgCreator`.

**Requirements:**
- `MinimumVersion` must be `2.7.6` (for core `FindAndReplace` processor)
- Download recipe must set `%version_hyphenated%` via named capture group
- An overridable `PKG_ID` input variable for the package receipt identifier

```xml
<key>Input</key>
<dict>
    <key>NAME</key>
    <string>ApplicationName</string>
    <key>PKG_ID</key>
    <string>com.pkg.vendor.ApplicationName</string>
</dict>
<key>MinimumVersion</key>
<string>2.7.6</string>
<key>Process</key>
<array>
    <dict>
        <key>Arguments</key>
        <dict>
            <key>find</key>
            <string>-</string>
            <key>input_string</key>
            <string>%version_hyphenated%</string>
            <key>replace</key>
            <string>.</string>
            <key>result_output_var_name</key>
            <string>version</string>
        </dict>
        <key>Processor</key>
        <string>FindAndReplace</string>
    </dict>
    <dict>
        <key>Arguments</key>
        <dict>
            <key>pkgdirs</key>
            <dict>
                <key>root/Applications</key>
                <string>0755</string>
                <key>scripts</key>
                <string>0755</string>
            </dict>
            <key>pkgroot</key>
            <string>%RECIPE_CACHE_DIR%/payload</string>
        </dict>
        <key>Processor</key>
        <string>PkgRootCreator</string>
    </dict>
    <dict>
        <key>Arguments</key>
        <dict>
            <key>destination_path</key>
            <string>%pkgroot%/root/Applications/Application Name.app</string>
            <key>source_path</key>
            <string>%found_filename%/Application Name.app</string>
        </dict>
        <key>Processor</key>
        <string>Copier</string>
    </dict>
    <dict>
        <key>Arguments</key>
        <dict>
            <key>pkg_request</key>
            <dict>
                <key>id</key>
                <string>%PKG_ID%</string>
                <key>pkgname</key>
                <string>%NAME%-%version%</string>
                <key>pkgroot</key>
                <string>%RECIPE_CACHE_DIR%/payload/root</string>
                <key>version</key>
                <string>%version%</string>
            </dict>
        </dict>
        <key>Processor</key>
        <string>PkgCreator</string>
    </dict>
</array>
```

Key points:
- `FindAndReplace` converts `%version_hyphenated%` (e.g., `1-8-1`) to `%version%` (e.g., `1.8.1`)
- `PkgRootCreator` creates `root/Applications` (0755) and `scripts` (0755) directories
- `Copier` source uses `%found_filename%` from the download recipe's `FileFinder` (for DMG inside extracted archive)
- `PkgCreator` uses `pkgroot` pointing to the `root` subdirectory (not the payload directory itself)
- `pkgname` must be present in `pkg_request` — PkgCreator requires it
- `PKG_ID` is overridable so users can set their own package receipt identifier
- The munki recipe parents this pkg recipe and merges `%version%` into pkginfo via `MunkiPkginfoMerger`
- The munki recipe must include an `uninstall_script` that deletes the app and forgets `%PKG_ID%` (see [uninstall scripts](../references/munki-recipe.md#uninstall-scripts))
- The munki recipe inherits `PKG_ID` from this recipe — do not duplicate it in the munki recipe's `Input`

---

## Important Rules

1. **ParentRecipe always points to the download recipe** — pkg recipes depend on the download, not the munki recipe
2. **Use `%NAME%-%version%.pkg`** for pkg_path when version is available
3. **Use `%NAME%.pkg`** for pkg_path when no version is available
4. **Hardcode actual filenames** in source_pkg and source_path (not `%NAME%.app`)
5. **PathDeleter must be last** in the Process array when used
6. **All path_list entries use `%RECIPE_CACHE_DIR%/`** prefix for cleanup
7. **Arguments in alphabetical order** within each processor dict
8. **Processor key is last** within each processor dict

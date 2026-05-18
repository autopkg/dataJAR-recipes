# Processor Reference

## Core Processor Priority

Always prioritize core AutoPkg processors over custom processors. Core processors are maintained by the AutoPkg team, widely tested, and available in all AutoPkg installations.

**Priority order:**
1. Core AutoPkg processors — use first
2. Existing custom processors — only when core cannot handle requirement
3. New custom processors — last resort

**Never invent processors.** Always verify existence before including.
**Never invent processor keys or arguments.** Only use documented arguments.

## Available Core Processors

| Processor | Purpose | MinimumVersion |
|-----------|---------|----------------|
| AppDmgVersioner | Extract version from .app inside mounted DMG | 0.0 |
| AppPkgCreator | Create .pkg from .app bundle | 1.0 |
| CodeSignatureVerifier | Verify code signatures | 0.3.1 |
| Copier | Copy files/directories | 0.0 |
| CURLDownloader | Download with cURL (advanced options) | 0.5.1 |
| CURLTextSearcher | Search text with cURL | 0.5.1 |
| DmgCreator | Create DMG disk images | 0.0 |
| DmgMounter | Mount DMG files | 0.0 |
| EndOfCheckPhase | Mark end of check-only phase | 0.1.0 |
| FileCreator | Create files with content | 0.0 |
| FileFinder | Find files by glob pattern | 0.2.3 |
| FileMover | Move files | 0.2.9 |
| FindAndReplace | Find and replace in files | 2.7.6 |
| FlatPkgPacker | Repack a flat .pkg | 0.2.4 |
| FlatPkgUnpacker | Unpack flat .pkg files | 0.1.0 |
| GitHubReleasesInfoProvider | Get info from GitHub releases | 0.5.0 |
| Installer | Install a .pkg on the local machine | 0.4.0 |
| MunkiCatalogBuilder | Rebuild Munki catalogs | 0.1.0 |
| MunkiImporter | Import into Munki repository | 0.1.0 |
| MunkiInstallsItemsCreator | Generate Munki installs arrays | 0.1.0 |
| MunkiOptionalReceiptEditor | Edit optional receipt fields | 2.7 |
| MunkiPkginfoMerger | Merge additional pkginfo data | 0.1.0 |
| MunkiSetDefaultCatalog | Set default catalog for pkginfo | 0.4.2 |
| PathDeleter | Delete files/directories | 0.1.0 |
| PkgCopier | Copy a .pkg with optional rename | 0.1.0 |
| PkgCreator | Create .pkg packages | 0.0 |
| PkgExtractor | Extract contents of a .pkg | 0.1.0 |
| PkgPayloadUnpacker | Extract package payloads | 0.1.0 |
| PkgRootCreator | Create directory structure for PkgCreator | 0.0 |
| PlistEditor | Edit plist files | 0.1.0 |
| PlistReader | Read plist values | 0.2.5 |
| SignToolVerifier | Verify with signtool | 2.3 |
| SparkleUpdateInfoProvider | Get info from Sparkle appcasts | 0.1.0 |
| StopProcessingIf | Conditionally stop processing | 0.1.0 |
| Unarchiver | Extract archives (.zip, .tar, etc.) | 0.1.0 |
| URLDownloader | Download files from URLs | 0.0 |
| URLTextSearcher | Scrape text/URLs from web pages using regex | 0.2.9 |
| Versioner | Extract version from app bundle | 0.1.0 |

## URL Scraping Patterns

### Pattern 1: Direct URL Capture
```xml
<dict>
    <key>Arguments</key>
    <dict>
        <key>re_pattern</key>
        <string>href=\"(https://vendor\.com/downloads/app-([0-9\.]+)\.dmg)\"</string>
        <key>result_output_var_name</key>
        <string>DOWNLOAD_URL</string>
        <key>url</key>
        <string>https://vendor.com/download-page</string>
    </dict>
    <key>Processor</key>
    <string>URLTextSearcher</string>
</dict>
```

### Pattern 2: Version-First, Then URL Construction
```xml
<dict>
    <key>Arguments</key>
    <dict>
        <key>re_pattern</key>
        <string>version\":\"(4\..*?)\"</string>
        <key>url</key>
        <string>https://builds.vendor.com/app/mac.jsonp</string>
    </dict>
    <key>Processor</key>
    <string>URLTextSearcher</string>
</dict>
<dict>
    <key>Arguments</key>
    <dict>
        <key>filename</key>
        <string>%NAME%.dmg</string>
        <key>url</key>
        <string>https://cdn.vendor.com/App%20%match%.dmg</string>
    </dict>
    <key>Processor</key>
    <string>URLDownloader</string>
</dict>
```

### Pattern 3: Multi-Step URL Construction
Multiple URLTextSearcher processors to capture different URL components.

### Pattern 4: With Custom Request Headers
For sites that block non-browser requests — add `request_headers` to match browser behavior:

**Basic headers** (Referer + user-agent):
```xml
<dict>
    <key>Arguments</key>
    <dict>
        <key>re_pattern</key>
        <string>href="(https://vendor\.com/downloads/app-([0-9\.]+)\.dmg)"</string>
        <key>request_headers</key>
        <dict>
            <key>Accept</key>
            <string>text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8</string>
            <key>Referer</key>
            <string>https://help.sketchup.com/;auto</string>
            <key>Sec-Fetch-Mode</key>
            <string>navigate</string>
            <key>Sec-Fetch-Site</key>
            <string>same-site</string>
            <key>user-agent</key>
            <string>Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15</string>
        </dict>
        <key>result_output_var_name</key>
        <string>DOWNLOAD_URL</string>
        <key>url</key>
        <string>https://vendor.com/download-page</string>
    </dict>
    <key>Processor</key>
    <string>URLTextSearcher</string>
</dict>
```

**Cookie persistence with curl_opts** (for multi-step or session-based downloads):
```xml
<dict>
    <key>Arguments</key>
    <dict>
        <key>curl_opts</key>
        <array>
            <string>--cookie-jar</string>
            <string>%RECIPE_CACHE_DIR%/cookies.txt</string>
            <string>--cookie</string>
            <string>%RECIPE_CACHE_DIR%/cookies.txt</string>
        </array>
        <key>request_headers</key>
        <dict>
            <key>Accept</key>
            <string>text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8</string>
            <key>Accept-Encoding</key>
            <string>gzip, deflate, br</string>
            <key>Accept-Language</key>
            <string>en-GB,en;q=0.9</string>
            <key>Priority</key>
            <string>u=0, i</string>
            <key>Sec-Fetch-Dest</key>
            <string>document</string>
            <key>Sec-Fetch-Mode</key>
            <string>navigate</string>
            <key>Sec-Fetch-Site</key>
            <string>none</string>
            <key>user-agent</key>
            <string>Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15</string>
        </dict>
        <key>url</key>
        <string>https://vendor.com/download-page</string>
    </dict>
    <key>Processor</key>
    <string>URLTextSearcher</string>
</dict>
```

**Translating curl commands:**
The user will typically provide a working `curl` command. Map flags to processor arguments:
- `-H "Header: value"` → `request_headers` dict entry
- `-A "agent"` → `request_headers` → `user-agent`
- `-e "url"` → `request_headers` → `Referer`
- `-b` / `-c` (cookies) → `curl_opts` with `%RECIPE_CACHE_DIR%/cookies.txt`
- `-d` / `-X POST` → `curl_opts` as literal strings
- `-L` (follow redirects) → already default, no action needed
- `-k` (insecure) → **never use**
- Any other curl flags → `curl_opts` as literal strings

See [download recipe headers reference](./download-recipe.md#translating-curl-commands-to-processor-arguments) for full mapping table and example.

**When headers are needed:**
- 403/406 responses from URLTextSearcher or URLDownloader
- Vendor CDNs checking `Referer` or `user-agent`
- Cookie-based download sessions
- Sites requiring `Sec-Fetch-*` navigation headers

**Rules:**
- Keep `request_headers` keys in alphabetical order
- Place `curl_opts` before `request_headers` in Arguments dict
- Use the same headers in both URLTextSearcher and URLDownloader when scraping then downloading from the same site
- Only include headers from the provided curl command — don't add extras
- Cookie paths must use `%RECIPE_CACHE_DIR%/` — never hardcode local paths

### Sparkle Feeds with Request Headers

SparkleUpdateInfoProvider uses `appcast_request_headers` (not `request_headers`) for custom headers on the appcast URL:

```xml
<dict>
    <key>Arguments</key>
    <dict>
        <key>appcast_request_headers</key>
        <dict>
            <key>user-agent</key>
            <string>Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15</string>
        </dict>
        <key>appcast_url</key>
        <string>https://vendor.com/appcast.xml</string>
    </dict>
    <key>Processor</key>
    <string>SparkleUpdateInfoProvider</string>
</dict>
```

**Note:** This is different from `request_headers` on URLDownloader. If both the appcast and the download need headers, set `appcast_request_headers` on SparkleUpdateInfoProvider AND `request_headers` on URLDownloader separately.

### Pattern 5: Dual Version Extraction
Two URLTextSearcher calls for full version + partial version.

### Pattern 6: Relative Path Resolution
Capture relative path, combine with base URL.

## Common Regex Patterns

| Pattern | Use Case | Example |
|---------|----------|---------|
| `([0-9]+(\.[0-9]+)+)` | Standard dotted versions | 1.2.3, 10.5.1 |
| `([0-9]+(-[0-9]+)+)` | Hyphenated versions (from URLs) | 1-8-1, 2-0-3-1 |
| `([0-9]+(_[0-9]+)+)` | Underscore versions | 1_2_3 |
| `(4\..*?)` | Major version locked | 4.x only |
| `([A-Za-z0-9]+(\.[A-Za-z0-9]+)+)` | Build numbers | 2024a.1.2 |
| `[0-9]{8}` | Date-based | 20240315 |

**Critical:** Always use flexible patterns that match **any number** of version components. Never use fixed-group patterns like `(\d+)\.(\d+)\.(\d+)` — versions may have 2, 3, 4, or more components.

## Named Capture Groups in URLTextSearcher

Use Python named capture group syntax `(?P<variable_name>...)` in `re_pattern` to set custom output variables. This is useful when you need to capture multiple values from a single regex, or when the captured value needs post-processing (e.g., version conversion via FindAndReplace).

**Syntax:** `(?P<name>pattern)` — sets the output variable `%name%` to the matched text.

### Pattern: Version Extraction with Named Capture Group

Capture both a download path and a hyphenated version simultaneously:

```xml
<dict>
    <key>Arguments</key>
    <dict>
        <key>re_pattern</key>
        <string>href="(/downloads/[^"]+/app-(?P&lt;version_hyphenated&gt;[0-9]+(-[0-9]+)+)-macos[^"]+\.zip)"</string>
        <key>result_output_var_name</key>
        <string>download_path</string>
        <key>url</key>
        <string>https://vendor.com/download-page</string>
    </dict>
    <key>Processor</key>
    <string>URLTextSearcher</string>
</dict>
```

This sets two variables:
- `%download_path%` — from `result_output_var_name` (the full match group 1)
- `%version_hyphenated%` — from the named capture group `(?P<version_hyphenated>...)`

**Important:** In recipe XML, angle brackets in named groups must be escaped: `(?P&lt;name&gt;...)`.

The `%version_hyphenated%` variable can then be fed to `FindAndReplace` to produce `%version%`.

## Code Signature Verification

**Format Selection Rule:**
- **DMG or ZIP containing .app** → Use `requirement` key with designated requirement string
- **PKG installer files** → Use `expected_authority_names` array with certificate chain

### For .app Bundles (DMG/ZIP) — Use 'requirement'
```xml
<dict>
    <key>Arguments</key>
    <dict>
        <key>input_path</key>
        <string>%pathname%/ActualAppName.app</string>
        <key>requirement</key>
        <string>identifier "com.developer.app" and anchor apple generic and certificate 1[field.1.2.840.113635.100.6.2.6] /* exists */ and certificate leaf[field.1.2.840.113635.100.6.1.13] /* exists */ and certificate leaf[subject.OU] = TEAMID</string>
    </dict>
    <key>Processor</key>
    <string>CodeSignatureVerifier</string>
</dict>
```

### For .pkg Files — Use 'expected_authority_names'
```xml
<dict>
    <key>Arguments</key>
    <dict>
        <key>expected_authority_names</key>
        <array>
            <string>Developer ID Installer: Company (TEAMID)</string>
            <string>Developer ID Certification Authority</string>
            <string>Apple Root CA</string>
        </array>
        <key>input_path</key>
        <string>%pathname%</string>
    </dict>
    <key>Processor</key>
    <string>CodeSignatureVerifier</string>
</dict>
```

**Critical**: Hardcode app names — never use `%NAME%.app`. Never use variables in input_path.

## Installs Array Generation

### For .app files
```xml
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
```

**Rules:**
- Primary application must be first in installs_item_paths
- Use plist items, not bundle items (for .definitions support)
- Avoid file items (require hash generation)
- MunkiPkginfoMerger must immediately follow
- Never use placeholder names — examine actual package contents

## Minimum OS Version Detection

### Method 1: derive_minimum_os_version (Preferred)
Via MunkiInstallsItemsCreator — requires MinimumVersion 2.7.

### Method 2: PlistReader
```xml
<dict>
    <key>Arguments</key>
    <dict>
        <key>info_path</key>
        <string>%RECIPE_CACHE_DIR%/Applications/%NAME%.app</string>
        <key>plist_keys</key>
        <dict>
            <key>LSMinimumSystemVersion</key>
            <string>min_os_ver</string>
        </dict>
    </dict>
    <key>Processor</key>
    <string>PlistReader</string>
</dict>
<dict>
    <key>Arguments</key>
    <dict>
        <key>additional_pkginfo</key>
        <dict>
            <key>minimum_os_version</key>
            <string>%min_os_ver%</string>
        </dict>
    </dict>
    <key>Processor</key>
    <string>MunkiPkginfoMerger</string>
</dict>
```

### Method 3: Distribution File
Parse `system.version.ProductVersion` from the package Distribution file using URLTextSearcher, then merge via MunkiPkginfoMerger:

```xml
<dict>
    <key>Arguments</key>
    <dict>
        <key>re_pattern</key>
        <string>system.version.ProductVersion, \"([0-9]+(.[0-9]+)+)\"</string>
        <key>result_output_var_name</key>
        <string>min_os_ver</string>
        <key>url</key>
        <string>file://localhost/%RECIPE_CACHE_DIR%/unpacked/Distribution</string>
    </dict>
    <key>Processor</key>
    <string>URLTextSearcher</string>
</dict>
<dict>
    <key>Arguments</key>
    <dict>
        <key>additional_pkginfo</key>
        <dict>
            <key>minimum_os_version</key>
            <string>%min_os_ver%</string>
        </dict>
    </dict>
    <key>Processor</key>
    <string>MunkiPkginfoMerger</string>
</dict>
```

**Notes:**
- The `file://localhost/` prefix is required for URLTextSearcher to read local files
- The Distribution file path must match the `destination_path` used in FlatPkgUnpacker (e.g., `%RECIPE_CACHE_DIR%/unpacked/Distribution`)
- Use this method when the .app Info.plist lacks `LSMinimumSystemVersion` or when the package doesn't contain a .app bundle

### Method 4: Vendor Website
Scrape minimum OS from vendor's download page/release notes.

## Version Handling

### Testing Version Sort
Use MunkiLooseVersion to verify Munki sorts versions correctly:
```python
#!/usr/local/munki/munki-python
import sys
sys.path.insert(0, "/usr/local/munki")
from munkilib.pkgutils import MunkiLooseVersion
versions = ["16.4 (1906)", "16.3.1 (1889)", "16.3 (1866)"]
print(sorted(versions, key=MunkiLooseVersion, reverse=True))
```

When version sorting fails, implement a custom `install_check_script` in zsh:

```xml
<key>install_check_script</key>
<string>#!/bin/zsh --no-rcs

# Path to the application
app_path="/Applications/MyApp.app"

# Exit 0 = not installed (install needed), Exit 1 = installed (no action)
if [[ ! -d "${app_path}" ]]; then
    exit 0
fi

# Get installed version
installed_version=$(/usr/bin/defaults read "${app_path}/Contents/Info" CFBundleShortVersionString 2>/dev/null)

# Compare with available version
# Custom comparison logic here for non-standard version formats

exit 1
</string>
```

**Rules for install_check_script:**
- Always use `#!/bin/zsh --no-rcs` shebang — never bash, sh, or Python
- Exit 0 = application needs to be installed/updated
- Exit 1 = application is already installed and current
- Use `/usr/bin/defaults read` to extract version info from app bundles

## Custom Processor Resources

- dataJAR Shared Processors: https://github.com/autopkg/dataJAR-recipes/tree/master/Shared%20Processors
- Community Processors: https://github.com/autopkg/autopkg/wiki/Noteworthy-Processors
- grahampugh CommonProcessors: ChangeModeOwner (for PathDeleter cleanup issues only)
- Python coding standards for custom processors: see [linter-standards.md](./linter-standards.md#custom-processor-python-standards)

## AppDmgVersioner (Simpler DMG Versioning)

For unsigned apps in DMGs where the version key is `CFBundleShortVersionString`, use `AppDmgVersioner` instead of `Versioner` — it's simpler and just needs `dmg_path`:

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
```

**When to use:**
- Download format is DMG
- App is NOT code-signed (signed apps get versioned via CodeSignatureVerifier in download recipe already)
- Version key is `CFBundleShortVersionString` (the default)
- Bundle type is `.app`

**When NOT to use (use Versioner instead):**
- Version key is `CFBundleVersion` — AppDmgVersioner always reads `CFBundleShortVersionString`
- Download format is zip/archive — AppDmgVersioner requires a mounted DMG
- Bundle type is not `.app` (e.g., `.prefpane`, `.plugin`)

## FileFinder Processor

When the package name inside a flat pkg is unknown or varies, use `FileFinder` to locate it by glob:

```xml
<dict>
    <key>Arguments</key>
    <dict>
        <key>find_method</key>
        <string>glob</string>
        <key>pattern</key>
        <string>%RECIPE_CACHE_DIR%/unpack/*.pkg/Payload</string>
    </dict>
    <key>Processor</key>
    <string>FileFinder</string>
</dict>
```

Use `%found_filename%` in subsequent processors to reference the located file. Place FileFinder before PkgPayloadUnpacker when the sub-package name is unknown.

## FindAndReplace Processor

**Core processor since AutoPkg 2.7.6.** Performs string find-and-replace on input text. Requires `MinimumVersion` of `2.7.6`.

**Important:** This is a core processor — use `<string>FindAndReplace</string>`, never `<string>com.github.homebysix.FindAndReplace/FindAndReplace</string>`.

### Arguments

| Key | Required | Description |
|-----|----------|-------------|
| `input_string` | Yes | The string to search within |
| `find` | Yes | The substring to find |
| `replace` | Yes | The replacement string |
| `result_output_var_name` | No | Output variable name (defaults to `output_string`) |

**Always set `result_output_var_name` explicitly** to a meaningful name (e.g., `version`) to avoid conflicts with other processors that may also write to `output_string`.

### Pattern: Convert Hyphenated Version to Dotted

When `URLTextSearcher` captures a version with hyphens (e.g., `1-8-1` from a URL like `app-1-8-1-macos.zip`), use `FindAndReplace` to convert to dotted notation:

```xml
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
```

This converts `1-8-1` → `1.8.1`. The `%version_hyphenated%` variable comes from a named capture group in `URLTextSearcher` (see [Named Capture Groups](#named-capture-groups-in-urltextsearcher)).

### Pattern: Convert Underscored Version to Dotted

Same approach for underscore-separated versions:

```xml
<dict>
    <key>Arguments</key>
    <dict>
        <key>find</key>
        <string>_</string>
        <key>input_string</key>
        <string>%version_underscored%</string>
        <key>replace</key>
        <string>.</string>
        <key>result_output_var_name</key>
        <string>version</string>
    </dict>
    <key>Processor</key>
    <string>FindAndReplace</string>
</dict>
```

## Version Comparison Key in MunkiImporter

When the app uses `CFBundleVersion` instead of the default `CFBundleShortVersionString` for versioning, add `version_comparison_key` to MunkiImporter so Munki compares the correct key:

```xml
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

Also merge the version into pkginfo when using a non-default version key:

```xml
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
```

## Download Filename Patterns

Use version in filename when it's available (from Sparkle or GitHub), plain NAME otherwise:

| Source | Filename Pattern |
|--------|-----------------|
| Sparkle feed | `%NAME%-%version%.dmg` |
| GitHub Releases | `%NAME%-%version%.dmg` |
| Direct URL / Web scraping | `%NAME%.dmg` |
| SourceForge (no reliable version) | `%NAME%.dmg` |

## Version Key Selection

When inspecting an app to determine which version key to use:

1. **Prefer `CFBundleShortVersionString`** — this is the human-readable version (e.g., "3.2.1")
2. **Fall back to `CFBundleVersion`** — this is the build number (e.g., "512")
3. Choose `CFBundleShortVersionString` unless it's clearly not a valid version (not numeric/dotted) and `CFBundleVersion` is

Check both keys with:
```zsh
/usr/bin/defaults read "/Applications/AppName.app/Contents/Info" CFBundleShortVersionString
/usr/bin/defaults read "/Applications/AppName.app/Contents/Info" CFBundleVersion
```

## Discovering Sparkle Feeds

To find an app's Sparkle update feed URL from the app itself:

```zsh
/usr/bin/defaults read "/Applications/AppName.app/Contents/Info" SUFeedURL
```

If `SUFeedURL` is empty, also check:
```zsh
/usr/bin/defaults read "/Applications/AppName.app/Contents/Info" SUOriginalFeedURL
```

Apps using the DevMate framework have an auto-generated feed at:
`https://updates.devmate.com/{bundle_id}.xml`

Check for DevMate with:
```zsh
[[ -d "/Applications/AppName.app/Contents/Frameworks/DevMateKit.framework" ]]
```

## Extracting Code Signing Information

To get code signature information for CodeSignatureVerifier:

```zsh
/usr/bin/codesign --display --verbose=2 -r- "/Applications/AppName.app" 2>&1
```

**For .app bundles (DMG/ZIP downloads):**
- Extract the `designated =>` line from **standard output** for the `requirement` key
- This is the designated requirement string

**For .pkg files:**
- Extract `Authority=` lines from **standard error** for the `expected_authority_names` array
- Include all three: Developer ID Installer, Developer ID Certification Authority, Apple Root CA

For the developer name and Team ID:
```zsh
# Authority line format: "Authority=Developer ID Application: Company Name (TEAMID)"
```

For packages:
```zsh
/usr/sbin/pkgutil --check-signature "/path/to/package.pkg"
```

The authority names from pkgutil output (lines starting with spaces and numbers) map to `expected_authority_names`.

## Blocking Applications

For pkg-based installs, identify blocking applications by examining apps inside the package payload. Common apps to **exclude** from the blocking list (these are not real user-facing apps):
- Autoupdate.app
- Install.app / Installer.app
- Uninstall.app / Uninstaller.app

Add remaining apps found in payload to the `blocking_applications` pkginfo array:
```xml
<key>blocking_applications</key>
<array>
    <string>ActualApp.app</string>
</array>
```

## Supported Bundle Types

AutoPkg recipes can handle these bundle types with different installation destinations:

| Bundle Type | Extension | Default Destination |
|-------------|-----------|-------------------|
| Application | `.app` | `/Applications` |
| Preference Pane | `.prefpane` | `/Library/PreferencePanes` |
| Internet Plugin | `.plugin` | `/Library/Internet Plug-Ins` |
| Quick Look Generator | `.qlgenerator` | `/Library/QuickLook` |
| Screen Saver | `.saver` | `/Library/Screen Savers` |

For non-app bundles, MunkiImporter needs `additional_makepkginfo_options`:
```xml
<key>additional_makepkginfo_options</key>
<array>
    <string>--destinationpath</string>
    <string>/Library/PreferencePanes</string>
    <string>--itemname</string>
    <string>MyPrefPane.prefpane</string>
</array>
```

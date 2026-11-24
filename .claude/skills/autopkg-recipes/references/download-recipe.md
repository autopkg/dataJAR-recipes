# Download Recipe Reference

## Structure Template

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Description</key>
    <string>Downloads the latest version of [APP NAME].</string>
    <key>Identifier</key>
    <string>com.github.dataJAR-recipes.download.[App Name With Spaces]</string>
    <key>Input</key>
    <dict>
        <key>NAME</key>
        <string>[NameNoSpaces]</string>
    </dict>
    <key>MinimumVersion</key>
    <string>1.1</string>
    <key>Process</key>
    <array>
        <!-- Processors go here -->
    </array>
</dict>
</plist>
```

## Required Elements

1. XML plist header with DOCTYPE
2. Description key
3. Identifier: `com.github.dataJAR-recipes.download.[App Name]`
4. Input dict with NAME (no spaces in value)
5. MinimumVersion (1.1 minimum, higher if processors require it)
6. Process array with appropriate processors

## INPUT Section Rules

- INPUT should ideally only contain NAME variable
- Avoid DOWNLOAD_URL in INPUT unless needed for architecture variants
- Add PRERELEASE (empty string) when using GitHubReleasesInfoProvider
- Add DOWNLOAD_ARCH when architecture-specific downloads are needed

## Process Array Order

1. URL discovery / version scraping (URLTextSearcher, SparkleUpdateInfoProvider, GitHubReleasesInfoProvider)
2. URLDownloader
3. EndOfCheckPhase
4. Unarchiver (if needed for .zip files)
5. CodeSignatureVerifier

**Do NOT include these in download recipes** — they belong in the munki recipe:
- FlatPkgUnpacker / PkgPayloadUnpacker (PKG unpacking)
- Versioner (version extraction)
- MunkiInstallsItemsCreator / MunkiPkginfoMerger (installs array generation)

## Download Method Patterns

### Direct URL
```xml
<dict>
    <key>Arguments</key>
    <dict>
        <key>filename</key>
        <string>%NAME%.dmg</string>
        <key>url</key>
        <string>https://vendor.com/downloads/app.dmg</string>
    </dict>
    <key>Processor</key>
    <string>URLDownloader</string>
</dict>
```

### Sparkle Appcast
```xml
<dict>
    <key>Arguments</key>
    <dict>
        <key>appcast_url</key>
        <string>https://vendor.com/appcast.xml</string>
    </dict>
    <key>Processor</key>
    <string>SparkleUpdateInfoProvider</string>
</dict>
<dict>
    <key>Arguments</key>
    <dict>
        <key>filename</key>
        <string>%NAME%-%version%.dmg</string>
    </dict>
    <key>Processor</key>
    <string>URLDownloader</string>
</dict>
```

When a custom user-agent is needed for the appcast, use `appcast_request_headers` (NOT `request_headers`):
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

### GitHub Releases

**Pre-release check:** Before creating a recipe using GitHubReleasesInfoProvider, check whether the releases are pre-releases:

```zsh
curl -s "https://api.github.com/repos/OWNER/REPO/releases" | python3 -c "import sys,json; [print(f'{r[\"tag_name\"]}: prerelease={r[\"prerelease\"]}') for r in json.load(sys.stdin)]"
```

Pre-releases are beta versions. If there is a mix of normal and pre-releases, just continue — `GitHubReleasesInfoProvider` uses the latest normal release by default. If **all** releases are pre-releases (no normal releases exist), **STOP and ask the user** before continuing — the recipe will need `PRERELEASE` set to `True` to find them. Do not silently enable pre-release support.

**asset_regex must be as specific as possible** — use as much of the actual filename as possible, replacing only the version with a capture group. Never use generic wildcards like `.*\.dmg$` or `.*\.pkg$`.

Good progression from actual filename `sqlitestudio-3.4.21-macos-x64.dmg`:
1. Start with actual filename: `sqlitestudio-3.4.21-macos-x64.dmg$`
2. Replace version with capture group: `sqlitestudio-([0-9]+(.[0-9]+)+)-macos-x64.dmg$`
3. Add architecture variable if needed: `sqlitestudio-([0-9]+(.[0-9]+)+)-macos-%DOWNLOAD_ARCH%.dmg$`

```xml
<dict>
    <key>Arguments</key>
    <dict>
        <key>asset_regex</key>
        <string>AppName-([0-9]+(.[0-9]+)+)\.dmg$</string>
        <key>github_repo</key>
        <string>owner/repository</string>
        <key>include_prereleases</key>
        <string>%PRERELEASE%</string>
    </dict>
    <key>Processor</key>
    <string>GitHubReleasesInfoProvider</string>
</dict>
<dict>
    <key>Arguments</key>
    <dict>
        <key>filename</key>
        <string>%NAME%-%version%.dmg</string>
    </dict>
    <key>Processor</key>
    <string>URLDownloader</string>
</dict>
```

Note: Both Sparkle and GitHub provide version information, so use `%NAME%-%version%.ext` for the filename. For direct URLs and web scraping where version is not extracted, use `%NAME%.ext` instead.

### Web Scraping (URLTextSearcher)
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
<dict>
    <key>Arguments</key>
    <dict>
        <key>filename</key>
        <string>%NAME%.dmg</string>
        <key>url</key>
        <string>%DOWNLOAD_URL%</string>
    </dict>
    <key>Processor</key>
    <string>URLDownloader</string>
</dict>
```

## Request Headers

Some vendor download pages or CDNs block requests that don't include browser-like headers. Add `request_headers` to URLTextSearcher or URLDownloader Arguments when needed.

The user will typically provide a working `curl` command — translate it into the appropriate processor arguments using the mapping below.

### Translating curl Commands to Processor Arguments

| curl flag | AutoPkg processor argument | Notes |
|-----------|---------------------------|-------|
| `-H "Header: value"` | `request_headers` dict entry: `<key>Header</key><string>value</string>` | Each `-H` becomes one key/value pair |
| `-A "user-agent string"` | `request_headers` → `<key>user-agent</key>` | Shorthand for `-H "user-agent: ..."` |
| `-e "referer-url"` | `request_headers` → `<key>Referer</key>` | Shorthand for `-H "Referer: ..."` |
| `-b "cookies.txt"` / `--cookie` | `curl_opts` → `<string>--cookie</string><string>path</string>` | Use `%RECIPE_CACHE_DIR%/cookies.txt` |
| `-c "cookies.txt"` / `--cookie-jar` | `curl_opts` → `<string>--cookie-jar</string><string>path</string>` | Use `%RECIPE_CACHE_DIR%/cookies.txt` |
| `-L` / `--location` | Already default in URLDownloader/URLTextSearcher | No action needed |
| `-o filename` | `filename` key in URLDownloader | Use `%NAME%.ext` format |
| `-d "data"` / `--data` | `curl_opts` → `<string>--data</string><string>data</string>` | For POST requests |
| `-X POST` | `curl_opts` → `<string>-X</string><string>POST</string>` | HTTP method override |
| `-k` / `--insecure` | **Do not use** | Security risk — find proper certificate solution |

**Example translation:**

curl command:
```zsh
curl -H "Accept: text/html" \
     -H "Sec-Fetch-Mode: navigate" \
     -H "Sec-Fetch-Site: same-site" \
     -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)" \
     -e "https://vendor.com/page" \
     -b cookies.txt -c cookies.txt \
     "https://vendor.com/download"
```

AutoPkg Arguments:
```xml
<key>curl_opts</key>
<array>
    <string>--cookie</string>
    <string>%RECIPE_CACHE_DIR%/cookies.txt</string>
    <string>--cookie-jar</string>
    <string>%RECIPE_CACHE_DIR%/cookies.txt</string>
</array>
<key>request_headers</key>
<dict>
    <key>Accept</key>
    <string>text/html</string>
    <key>Referer</key>
    <string>https://vendor.com/page</string>
    <key>Sec-Fetch-Mode</key>
    <string>navigate</string>
    <key>Sec-Fetch-Site</key>
    <string>same-site</string>
    <key>user-agent</key>
    <string>Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)</string>
</dict>
```

**Key rules:**
- Only include headers from the curl command that are actually needed — strip standard curl defaults
- `-L` (follow redirects) is handled automatically by URLDownloader/URLTextSearcher
- Cookie paths must use `%RECIPE_CACHE_DIR%/` — never hardcode local paths
- Any curl flags not in the table above go into `curl_opts` as literal strings
- Keep all keys in alphabetical order within `request_headers` and `curl_opts`

### Basic Headers
Minimal set — often just `user-agent` and `Referer` are enough:
```xml
<key>request_headers</key>
<dict>
    <key>Referer</key>
    <string>https://vendor.com/download-page</string>
    <key>user-agent</key>
    <string>Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15</string>
</dict>
```

### Full Browser-Like Headers
For sites with stricter request validation (anti-scraping, CDN protection):
```xml
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
```

### Cookie Handling with curl_opts
For sites that require cookie persistence across redirects or multi-step downloads, use `curl_opts` alongside `request_headers`:
```xml
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
```

### When to Use Headers
- **403 Forbidden** or **406 Not Acceptable** responses from URLTextSearcher/URLDownloader
- Vendor CDNs that check `Referer` or `user-agent`
- Download pages behind cookie-based sessions
- Sites that require `Sec-Fetch-*` headers for navigation requests
- Multi-step downloads where cookies from the first request are needed for subsequent ones

### Header Ordering
Keep `request_headers` keys in alphabetical order (per linter standards). Place `curl_opts` before `request_headers` in the Arguments dict.

## EndOfCheckPhase

Always include immediately after URLDownloader:
```xml
<dict>
    <key>Processor</key>
    <string>EndOfCheckPhase</string>
</dict>
```

## Unarchiver (for .zip files)

```xml
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
```

## Code Signature Verification

**CRITICAL: Use the correct pattern based on download format:**
- **DMG/ZIP containing .app** → Use `requirement` key with designated requirement string
- **PKG files** → Use `expected_authority_names` array with certificate chain

### Pattern 1: .app Bundle in DMG (Use 'requirement')
```xml
<dict>
    <key>Arguments</key>
    <dict>
        <key>input_path</key>
        <string>%pathname%/ActualAppName.app</string>
        <key>requirement</key>
        <string>identifier "com.developer.appname" and anchor apple generic and certificate 1[field.1.2.840.113635.100.6.2.6] /* exists */ and certificate leaf[field.1.2.840.113635.100.6.1.13] /* exists */ and certificate leaf[subject.OU] = TEAMID</string>
    </dict>
    <key>Processor</key>
    <string>CodeSignatureVerifier</string>
</dict>
```

### Pattern 2: .app from ZIP after Unarchiver (Use 'requirement')
```xml
<dict>
    <key>Arguments</key>
    <dict>
        <key>input_path</key>
        <string>%RECIPE_CACHE_DIR%/%NAME%/ActualAppName.app</string>
        <key>requirement</key>
        <string>identifier "com.developer.appname" and anchor apple generic and certificate 1[field.1.2.840.113635.100.6.2.6] /* exists */ and certificate leaf[field.1.2.840.113635.100.6.1.13] /* exists */ and certificate leaf[subject.OU] = TEAMID</string>
    </dict>
    <key>Processor</key>
    <string>CodeSignatureVerifier</string>
</dict>
```

### Pattern 3: PKG Files (Use 'expected_authority_names')
```xml
<dict>
    <key>Arguments</key>
    <dict>
        <key>expected_authority_names</key>
        <array>
            <string>Developer ID Installer: Company Name (TEAMID)</string>
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

**Critical**: Always hardcode app names in CodeSignatureVerifier — never use `%NAME%.app`.

## Important Rules

- No versioning steps in download recipes — version detection belongs in munki recipes
- Filename extension in URLDownloader should match the actual download format
- Use `%NAME%-%version%.ext` when version is available (Sparkle, GitHub), `%NAME%.ext` otherwise
- For DMG files, reference the app within: `%pathname%/AppName.app`
- For zip/archive files after Unarchiver: `%RECIPE_CACHE_DIR%/%NAME%/AppName.app`
- For PKG files, reference directly: `%pathname%`
- Processor arguments must be in alphabetical order
- Processor key must be last in each processor dict
- `purge_destination` should always be `true` on Unarchiver

# Architecture Support Reference

## Download Recipe Architecture (DOWNLOAD_ARCH)

When vendors provide architecture-specific downloads, use the DOWNLOAD_ARCH variable.

### Description Section
Always document the architecture values:
```xml
<key>Description</key>
<string>Downloads the latest version of [APP].

To download Apple Silicon use: "[ARM64_VALUE]" in the DOWNLOAD_ARCH variable
To download Intel use: "[INTEL_VALUE]" in the DOWNLOAD_ARCH variable</string>
```

### Input Section
```xml
<key>DOWNLOAD_ARCH</key>
<string>[DEFAULT_VALUE]</string>
```

### Common URL Patterns

| Pattern | Apple Silicon | Intel | Example URL |
|---------|--------------|-------|-------------|
| Path segment | `""` (empty) | `/x64` | `https://vendor.com/downloads%DOWNLOAD_ARCH%/app.dmg` |
| URL parameter | `arm64` | `x64` | `https://vendor.com/download?arch=%DOWNLOAD_ARCH%` |
| Filename suffix | `-silicon` | `""` (empty) | `https://vendor.com/app%DOWNLOAD_ARCH%.dmg` |
| Underscore prefix | `_arm64` | `""` (empty) | `https://vendor.com/app%DOWNLOAD_ARCH%.dmg` |
| Custom naming | `arm` | `intel` | Vendor-specific terms |
| Platform terms | `MacOsArm64` | `MacOsx` | Vendor-specific terms |

### URL Scraping with Architecture Variable

Include `%DOWNLOAD_ARCH%` in regex patterns when scraping architecture-specific URLs:

```xml
<dict>
    <key>Arguments</key>
    <dict>
        <key>re_pattern</key>
        <string>href=\"(https://cdn\.vendor\.com/releases/app-([0-9\.]+)-osx-%DOWNLOAD_ARCH%\.pkg)\"</string>
        <key>result_output_var_name</key>
        <string>DOWNLOAD_URL</string>
        <key>url</key>
        <string>https://vendor.com/download-page</string>
    </dict>
    <key>Processor</key>
    <string>URLTextSearcher</string>
</dict>
```

### GitHubReleasesInfoProvider with Architecture

Use as much of the actual filename as possible in `asset_regex` — only replace the version with a capture group and the architecture with `%DOWNLOAD_ARCH%`. Never use generic wildcards.

```xml
<!-- In Input -->
<key>DOWNLOAD_ARCH</key>
<string>aarch64</string>

<!-- In processor -->
<dict>
    <key>Arguments</key>
    <dict>
        <key>asset_regex</key>
        <string>AppName\.([0-9]+(\.[0-9]+)+)\.%DOWNLOAD_ARCH%\.dmg$</string>
        <key>github_repo</key>
        <string>owner/repository</string>
        <key>include_prereleases</key>
        <string>%PRERELEASE%</string>
    </dict>
    <key>Processor</key>
    <string>GitHubReleasesInfoProvider</string>
</dict>
```

## Munki Recipe Architecture (SUPPORTED_ARCH)

For architecture-specific Munki deployments:

```xml
<!-- In Description -->
<string>For Intel use: "x86_64" in the SUPPORTED_ARCH variable
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

**Important**: Munki recipes always use `x86_64` and `arm64` for SUPPORTED_ARCH, regardless of what the download recipe uses for DOWNLOAD_ARCH.

## Multi-Variable URL Construction

For complex downloads with multiple variables:

```xml
<!-- Multiple version extractions -->
<dict>
    <key>Arguments</key>
    <dict>
        <key>re_pattern</key>
        <string>AppName ([0-9]+(\.[0-9]+)+)</string>
        <key>result_output_var_name</key>
        <string>FULL_VERSION</string>
        <key>url</key>
        <string>%SEARCH_URL%</string>
    </dict>
    <key>Processor</key>
    <string>URLTextSearcher</string>
</dict>
<dict>
    <key>Arguments</key>
    <dict>
        <key>re_pattern</key>
        <string>AppName (\d\.\d\d)</string>
        <key>result_output_var_name</key>
        <string>PART_VERSION</string>
        <key>url</key>
        <string>%SEARCH_URL%</string>
    </dict>
    <key>Processor</key>
    <string>URLTextSearcher</string>
</dict>
<!-- URL with multiple variables -->
<dict>
    <key>Arguments</key>
    <dict>
        <key>filename</key>
        <string>%NAME%.pkg</string>
        <key>url</key>
        <string>https://cdn.vendor.com/%CHANNEL%/%PART_VERSION%/mac/App_%FULL_VERSION%_%DOWNLOAD_ARCH%.pkg</string>
    </dict>
    <key>Processor</key>
    <string>URLDownloader</string>
</dict>
```

## Custom Request Headers

Some downloads require specific headers:

```xml
<dict>
    <key>Arguments</key>
    <dict>
        <key>filename</key>
        <string>%NAME%.pkg</string>
        <key>request_headers</key>
        <dict>
            <key>Referer</key>
            <string>https://vendor.com/download-page</string>
            <key>user-agent</key>
            <string>Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15</string>
        </dict>
        <key>url</key>
        <string>%DOWNLOAD_URL%</string>
    </dict>
    <key>Processor</key>
    <string>URLDownloader</string>
</dict>
```

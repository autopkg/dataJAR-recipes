# EmacsMinimumOSVersionParser

## Description
A custom AutoPkg processor that determines the minimum required macOS version for Emacs by analyzing the binary filenames in the app bundle. It parses binary names like `Emacs-x86_64-10_14` to find the most permissive (lowest) supported OS version.

## Input Variables
- `pathname`: (Required) Path to the DMG file
- `app_name`: (Required) Name of the app bundle (e.g., 'Emacs.app')

## Output Variables
- `minimum_os_version`: The most permissive (lowest) minimum OS version found

## Example Usage
```
- Processor: EmacsMinimumOSVersionParser
  Arguments:
    app_name: "Emacs.app"
```

Or in plist format:
```
<dict>
    <key>Processor</key>
    <string>EmacsMinimumOSVersionParser</string>
    <key>Arguments</key>
    <dict>
        <key>app_name</key>
        <string>%app_name%</string>
    </dict>
</dict>
```

## Example Output
```
EmacsMinimumOSVersionParser: Most permissive minimum OS version found: 10.12
EmacsMinimumOSVersionParser: All unique OS versions found: 10.12, 10.14, 11
```

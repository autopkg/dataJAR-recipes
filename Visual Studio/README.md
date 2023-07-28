# Microsoft Visual Studio for Mac

## About

[Visual Studio](https://visualstudio.microsoft.com/vs/mac/) is a development suite for .NET

These recipes use the same `installationmanifest.json` file that the `Install Visual Studio for Mac.app` uses: [https://aka.ms/vsmac/manifest/17-stable](https://aka.ms/vsmac/manifest/17-stable) thanks to `jimmy-swings` on [Jamf Nation](https://community.jamf.com/t5/jamf-pro/visual-studio-for-mac-deployment/m-p/292547/highlight/true#M260110)

Recipes (with support for downloading both Intel and Apple Silcon where necessary) have been written for individual App's and Frameworks to allow Admins to add what is important to their Org, and to allow for updates to the individual components.

Worth noting that Visual Studio requires Xcode, and in some cases a specific Xcode version. Please see [Microsofts documentation](https://learn.microsoft.com/en-us/visualstudio/releases/2022/mac-system-requirements) for full details.

## Usage

Visual Studio needs the following components as a base install

- Visual Studio
- Mono Framework
- .NET 6 (Note - This must be installed _before_ .NET 7, otherwise .NET 7 will reinstall)
- .NET 7

Optional installs are:

- Xamarin.Android
- Xamarin.iOS
- Xamarin.Mac
- Xamarin Profiler
- Eclipse Temurin JDK
- Microsoft Build Of OpenJDK
- Android SDK

Some Optional installs also have dependancies which are listed in the `installationmanifest.json` - please refer to this for an updated list when deciding what to include.

- Xamarin.Android
    - Microsoft Build Of OpenJDK
    - Eclipse Temurin JDK
    - Xamarin Profiler
    - Mono Framework
    - Android SDK

- Xamarin.iOS
    - Xamarin Profiler
    - Mono Framework

- Xamarin.Mac
    - Xamarin Profiler
    - Mono Framework

## Munki

For folks using the Munki recipes, you could use the `update_for` key in your override to add the base installs and optional installs.

```
<key>update_for</key>
    <array>
        <string>VisualStudio</string>
    </array>
```

To ensure .NET 6 installs before .NET 7 you could use the `requires` key in your override.

```
<key>requires</key>
    <array>
        <string>DotNet6</string>
    </array>
```

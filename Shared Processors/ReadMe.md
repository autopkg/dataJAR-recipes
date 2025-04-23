# dataJAR AutoPkg Shared Processors

This repository contains shared processors used in dataJAR's AutoPkg recipes.

## Available Processors

### CaseChanger
Changes the case of a string value.

#### Input Variables
- **input_string**
  - **Required**: Yes
  - **Description**: String to change case of.
- **conversion_method**
  - **Required**: Yes
  - **Description**: Case conversion method. Options: "uppercase", "lowercase", "titlecase".

#### Output Variables
- **output_string**
  - **Description**: The case-modified string.

#### Example Usage
```xml
<dict>
    <key>Processor</key>
    <string>com.github.dataJAR-recipes.Shared Processors/CaseChanger</string>
    <key>Arguments</key>
    <dict>
        <key>input_string</key>
        <string>%NAME%</string>
        <key>conversion_method</key>
        <string>titlecase</string>
    </dict>
</dict>
```
### CFBundleVersionCombiner
Combines CFBundleShortVersionString and CFBundleVersion from an app's Info.plist into a single version string.

#### Input Variables
- **app_path**
  - **Required**: Yes
  - **Description**: Path to the app bundle to version.

#### Output Variables
- **version**
  - **Description**: Combined version number in format CFBundleShortVersionString.CFBundleVersion

#### Description
This processor combines the CFBundleShortVersionString and CFBundleVersion from an application's Info.plist into a single version string. This is particularly useful for applications where both version numbers are needed for proper version comparison, such as when the CFBundleVersion contains build numbers or other version-specific information.

The combined version format is: `CFBundleShortVersionString.CFBundleVersion`

For example:
- If CFBundleShortVersionString is "3.3"
- And CFBundleVersion is "3125"
- The combined version will be "3.3.3125"

#### Example Usage
```xml
<dict>
    <key>Processor</key>
    <string>com.github.dataJAR-recipes.Shared Processors/CFBundleVersionCombiner</string>
    <key>Arguments</key>
    <dict>
        <key>app_path</key>
        <string>%RECIPE_CACHE_DIR%/payload/Applications/Example.app</string>
    </dict>
</dict>
```

### ComponentPkgPayloadUnpacker
A processor that unpacks component package payloads using pkgutil.

#### Input Variables
- **pkg_path**
  - **Required**: Yes
  - **Description**: Path to the package to expand.
- **destination_path**
  - **Required**: Yes
  - **Description**: Path where the payload will be unpacked.
- **purge_destination**
  - **Required**: No
  - **Description**: Whether to purge the destination directory before unpacking.
  - **Default**: True

#### Output Variables
- **unpacked_path**
  - **Description**: Path to the unpacked payload.

#### Example Usage
```xml
<dict>
    <key>Processor</key>
    <string>com.github.dataJAR-recipes.Shared Processors/ComponentPkgPayloadUnpacker</string>
    <key>Arguments</key>
    <dict>
        <key>pkg_path</key>
        <string>%path_to_your_package%</string>
        <key>destination_path</key>
        <string>%RECIPE_CACHE_DIR%/unpacked</string>
    </dict>
</dict>
```

### DistributionPkgInfo
Extracts package information from a Distribution file.

#### Input Variables
- **pkg_path**
  - **Required**: Yes
  - **Description**: Path to the distribution package.

#### Output Variables
- **version**
  - **Description**: Extracted version from the distribution file.
- **pkg_id**
  - **Description**: Extracted package identifier.

#### Example Usage
```xml
<dict>
    <key>Processor</key>
    <string>com.github.dataJAR-recipes.Shared Processors/DistributionPkgInfo</string>
    <key>Arguments</key>
    <dict>
        <key>pkg_path</key>
        <string>%pkg_path%</string>
    </dict>
</dict>
```

### FirefoxGetLocaleAndVersion
Retrieves Firefox locale and version information.

#### Input Variables
- **firefox_build**
  - **Required**: Yes
  - **Description**: Firefox build number to process.

#### Output Variables
- **locale**
  - **Description**: Extracted locale information.
- **version**
  - **Description**: Extracted version information.

#### Example Usage
```xml
<dict>
    <key>Processor</key>
    <string>com.github.dataJAR-recipes.Shared Processors/FirefoxGetLocaleAndVersion</string>
    <key>Arguments</key>
    <dict>
        <key>firefox_build</key>
        <string>%firefox_build%</string>
    </dict>
</dict>
```

### GetBinaryMinimumOSVersion
Analyzes all binaries within an application bundle to determine the highest minimum OS version requirement.

#### Input Variables
- **app_path**
  - **Required**: Yes
  - **Description**: Path to the application bundle or binary to analyze. Can be a path within a DMG.
- **search_path**
  - **Required**: No
  - **Description**: Specific path within the app bundle to search for binaries.
  - **Default**: Contents/MacOS

#### Output Variables
- **min_os_ver**
  - **Description**: The highest (most restrictive) minimum OS version found across all binaries.
- **analyzed_binaries**
  - **Description**: Dictionary of all analyzed binaries and their respective minimum OS versions.

#### Example Usage
```xml
<dict>
    <key>Processor</key>
    <string>com.github.dataJAR-recipes.Shared Processors/GetBinaryMinimumOSVersion</string>
    <key>Arguments</key>
    <dict>
        <key>app_path</key>
        <string>%pathname%/Example.app</string>
    </dict>
</dict>
```

### HTMLUnescaper
Unescapes HTML entities in a string.

#### Input Variables
- **input_string**
  - **Required**: Yes
  - **Description**: String containing HTML entities to unescape.

#### Output Variables
- **output_string**
  - **Description**: The unescaped string.

#### Example Usage
```xml
<dict>
    <key>Processor</key>
    <string>com.github.dataJAR-recipes.Shared Processors/HTMLUnescaper</string>
    <key>Arguments</key>
    <dict>
        <key>input_string</key>
        <string>%encoded_string%</string>
    </dict>
</dict>
```

### InstallsArrayCFBundleIdentifierChanger
Modifies the CFBundleIdentifier in an installs array.

#### Input Variables
- **changes**
  - **Required**: Yes
  - **Description**: Array of dictionaries containing path and CFBundleIdentifier to modify.
  - **Format**: Each dictionary must contain:
    - `path`: Path to the application/file
    - `CFBundleIdentifier`: New bundle identifier to set

#### Example Usage
```xml
<dict>
    <key>Arguments</key>
    <dict>
        <key>changes</key>
        <array>
            <dict>
                <key>path</key>
                <string>/path/to/file</string>
                <key>CFBundleIdentifier</key>
                <string>fr.madrau.switchresx.prefpane</string>
            </dict>
        </array>
    </dict>
    <key>Processor</key>
    <string>com.github.dataJAR-recipes.Shared Processors/InstallsArrayCFBundleIdentifierChanger</string>
</dict>
```

### InstallsArrayVersionComparisonKeyChanger
Modifies the version_comparison_key in an installs array.

#### Input Variables
- **changes**
  - **Required**: Yes
  - **Description**: Array of dictionaries containing path and version_comparison_key to modify.
  - **Format**: Each dictionary must contain:
    - `path`: Path to the application/file
    - `version_comparison_key`: New version comparison key to set

#### Example Usage
```xml
<dict>
    <key>Arguments</key>
    <dict>
        <key>changes</key>
        <array>
            <dict>
                <key>path</key>
                <string>/path/to/file</string>
                <key>version_comparison_key</key>
                <string>CFBundleVersion</string>
            </dict>
        </array>
    </dict>
    <key>Processor</key>
    <string>com.github.dataJAR-recipes.Shared Processors/InstallsArrayVersionComparisonKeyChanger</string>
</dict>
```

### JSONFileReader
Reads and processes JSON files.

#### Input Variables
- **json_path**
  - **Required**: Yes
  - **Description**: Path to the JSON file to read.
- **json_key**
  - **Required**: Yes
  - **Description**: Key to extract from the JSON.

#### Output Variables
- **json_value**
  - **Description**: Value extracted from the JSON.

#### Example Usage
```xml
<dict>
    <key>Processor</key>
    <string>com.github.dataJAR-recipes.Shared Processors/JSONFileReader</string>
    <key>Arguments</key>
    <dict>
        <key>json_path</key>
        <string>%path_to_json%</string>
        <key>json_key</key>
        <string>version</string>
    </dict>
</dict>
```

### PkginfoCopierAndModifier
Copies and modifies pkginfo files.

#### Input Variables
- **source_pkginfo**
  - **Required**: Yes
  - **Description**: Path to source pkginfo file.
- **destination_pkginfo**
  - **Required**: Yes
  - **Description**: Path for destination pkginfo file.
- **modifications**
  - **Required**: Yes
  - **Description**: Dictionary of modifications to apply.

#### Example Usage
```xml
<dict>
    <key>Processor</key>
    <string>com.github.dataJAR-recipes.Shared Processors/PkginfoCopierAndModifier</string>
    <key>Arguments</key>
    <dict>
        <key>source_pkginfo</key>
        <string>%RECIPE_CACHE_DIR%/pkginfo</string>
        <key>destination_pkginfo</key>
        <string>%RECIPE_CACHE_DIR%/modified_pkginfo</string>
        <key>modifications</key>
        <dict>
            <key>version</key>
            <string>1.0</string>
        </dict>
    </dict>
</dict>
```

### QuarantineRemover
Removes quarantine attributes from files.

#### Input Variables
- **pathname**
  - **Required**: Yes
  - **Description**: Path to file or directory to process.

#### Example Usage
```xml
<dict>
    <key>Processor</key>
    <string>com.github.dataJAR-recipes.Shared Processors/QuarantineRemover</string>
    <key>Arguments</key>
    <dict>
        <key>pathname</key>
        <string>%downloaded_file%</string>
    </dict>
</dict>
```

### TempFileFinder
Finds temporary files in specified locations.

#### Input Variables
- **pattern**
  - **Required**: Yes
  - **Description**: Pattern to match for temporary files.
- **directory**
  - **Required**: Yes
  - **Description**: Directory to search in.

#### Output Variables
- **found_files**
  - **Description**: List of found temporary files.

#### Example Usage
```xml
<dict>
    <key>Processor</key>
    <string>com.github.dataJAR-recipes.Shared Processors/TempFileFinder</string>
    <key>Arguments</key>
    <dict>
        <key>pattern</key>
        <string>*.tmp</string>
        <key>directory</key>
        <string>%RECIPE_CACHE_DIR%</string>
    </dict>
</dict>
```

### VarSlicer
Slices variables based on specified criteria.

#### Input Variables
- **input_string**
  - **Required**: Yes
  - **Description**: String to slice.
- **slice_start**
  - **Required**: No
  - **Description**: Start index for slicing.
- **slice_end**
  - **Required**: No
  - **Description**: End index for slicing.

#### Output Variables
- **slice_result**
  - **Description**: The sliced string result.

#### Example Usage
```xml
<dict>
    <key>Processor</key>
    <string>com.github.dataJAR-recipes.Shared Processors/VarSlicer</string>
    <key>Arguments</key>
    <dict>
        <key>input_string</key>
        <string>%version%</string>
        <key>slice_start</key>
        <string>0</string>
        <key>slice_end</key>
        <string>5</string>
    </dict>
</dict>
```

## Usage

To use these processors in your recipes:

1. Add the dataJAR-recipes repository to AutoPkg:
```bash
autopkg repo-add dataJAR-recipes
```

2. Reference the processor in your recipe using the examples provided above.

## Support

These processors are distributed 'as is' by DATA JAR LTD.
For more information or support, please visit: http://www.datajar.co.uk

## License

Copyright (c) 2025, dataJAR Ltd. All rights reserved.
See individual processors for full license details.
```

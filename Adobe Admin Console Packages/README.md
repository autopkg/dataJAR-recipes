<details>
<summary>Licensed under the Apache License, Version 2.0 </summary>
Copyright 2024 Jamf LTD

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
</details>

# Adobe Admin Console Packages

## About  
Since 2021, more and more of the Adobe Admin Console Packages have had signed/encrypted payloads.

This means that we cannot pull apart the PKG's to retrieve the needed metadata for AutoPkg recipes.

The prior iterations of our Adobe Versioner would work around this issue by having the data within the Versioner itself, but this then needed annual updates.

The [AdobeAdminConsolePackagesPkgInfoCreator](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/AdobeAdminConsolePackagesPkgInfoCreator.py) processor, utilises the file: [AdobeAutoPkgApplicationData.json](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/AdobeAutoPkgApplicationData.json) to generate the needed metadata.

The idea is that we can update [AdobeAutoPkgApplicationData.json](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/AdobeAutoPkgApplicationData.json), as needed. And not need to create a new processor.

Data within [AdobeAutoPkgApplicationData.json](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/AdobeAutoPkgApplicationData.json), as well as the PKG's `optionXML.xml` and `Application.json` is used to create the metadata needed for the title.

The processor [AdobeAdminConsolePackagesPkgInfoCreator](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/AdobeAdminConsolePackagesPkgInfoCreator.py), generates a large about output variables. These are detailed in the table at the end of this README, and are to be used for folks to write their own recipes.

## Quick start guide
1. For each Adobe title you want to import:
   * Download one or more DMG from the [Adobe Admin Console](https://adminconsole.adobe.com), making sure that the name is prefixed with one of the names listed within the [application names table](https://github.com/autopkg/dataJAR-recipes/edit/add-adobe-flat-pkg-support/Adobe%20Admin%20Console%20Packages/README.md#names).
   * Load the .app.
   * Download the title.
   * If the download is a .zip, unzip it.
1. Create an override for each title, from the recipes in this directory.
   * Make sure that the override is prefixed the same as per the name choosen in step 1.
   * Make sure that the override type is included included within the name, such as `munki`.
   * If the pkg is an Apple silicon pkg, add arm64 to the override name.
   * Both plist/xml and yml/yaml overrides are supported.
1. Run `AdobeAdminConsolePackagesImporter.py`, found within this directory. Passing at least the type key (see below for examples):
   * `./AdobeAdminConsolePackagesImporter.py munki` - This will look within ~/Downloads/ for Adobe installers and match with .munki overrides.
   * `./AdobeAdminConsolePackagesImporter.py jamf /Users/Shared/adobe/` - This will look within Users/Shared/adobe/ for Adobe installers and match with jamf overrides.
1. Add icons as needed. (The icons that are accessible within the pkgs are of to low a resolution to be imported into Munki etc).

## Process
1. Adobe Admin Console
   * Create a package including just a single title and Creative Cloud Desktop app.
   * Prefix the package with one of the names listed within the [application names table](https://github.com/autopkg/dataJAR-recipes/edit/add-adobe-flat-pkg-support/Adobe%20Admin%20Console%20Packages/README.md#names).
   * Finish creating the package seleting the wanted options and whilst bundle or [flat packages](https://helpx.adobe.com/uk/enterprise/using/create-flat-packages.html) can be created within the Adobe Admin Console. Bundle packages will not install on macOS15+.
   * Download the DMG.
   * Load the .app.
   * Download the title.
   * If the download is a .zip, unzip it.
1. Create an override for each title, from the recipes in this directory.
   * Make sure that the override is prefixed the same as per the name choosen in step 1.
   * Make sure that the override type is included included within the name, such as `munki`.
   * If the pkg is an Apple silicon pkg, add arm64 to the override name.
1. Run [AdobeAdminConsolePackagesImporter.py](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/AdobeAdminConsolePackagesImporter.py):
   * The minimum arguments `AdobeAdminConsolePackagesImporter.py` needs is the recipe type: `AdobeAdminConsolePackagesImporter.py munki` (for munki recipes).
   * Optionally, pass the root directory containing the Adobe installers downloaded from the Adobe Admin Console (if this is omitted then `~/Downloads/` is used: AdobeAdminConsolePackagesImporter.py /Users/Shared/adobe/`.
   * `AdobeAdminConsolePackagesImporter.py` next:
     * Confirms that the passed directory or the default directory exists, before proceeding.
     * Parses [AdobeAutoPkgApplicationData.json](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/AdobeAutoPkgApplicationData.json) to retrieve a list of application names, (these are the same as found within the [application names table](https://github.com/autopkg/dataJAR-recipes/edit/add-adobe-flat-pkg-support/Adobe%20Admin%20Console%20Packages/README.md#names)).
     * Recursively looks within the defined directory, for .pkg files which start with one of the application names retrieved from the prior step. Recording the path to any matches and if they are a bundle or [flat packages](https://helpx.adobe.com/uk/enterprise/using/create-flat-packages.html) package.
     * Prints a summary of found pcakages.
     * Retrieves a list of [RECIPE_OVERRIDE_DIRS](https://github.com/autopkg/autopkg/wiki/Recipe-Overrides#recipe-override-directories) from AutoPkg's preference domain.
     * Looks within each of the defined [RECIPE_OVERRIDE_DIRS](https://github.com/autopkg/autopkg/wiki/Recipe-Overrides#recipe-override-directories) for overrides that start with:
       * The same name from the application names table](https://github.com/autopkg/dataJAR-recipes/edit/add-adobe-flat-pkg-support/Adobe%20Admin%20Console%20Packages/README.md#names) as the located packages.
       * ContainS the same recipe type that was passed to [AdobeAdminConsolePackagesImporter.py](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/AdobeAdminConsolePackagesImporter.py).
       * Optionally, if the pkg contains `MACARM` looks for `arm64` within the overrides file name.
     * Next, generates a list of each overrides identifier. Which is retreieved from the overrides themselves.
     * Adds three variables to each matched override:
       * `aacp_override_path` - the path to the override itself.
       * `aacp_package_path` - the path to the titles .pkg.
       * `aacp_package_type` - If the pkg is a bundle of flat pkg.
     * Creates a [recipe list](https://github.com/autopkg/autopkg/wiki/Running-Multiple-Recipes#recipe-lists) containg the overrides identifiers for the overrides which have matched a downloaded Adobe Admin Console package in alphabetical order, within the passed/derived directory. (Examples: `~/Downloads/adobe_admin_console_recipes_list.txt`, `/Users/Shared/adobe/adobe_admin_console_recipes_list.txt`)
     * Runs the [recipe list](https://github.com/autopkg/autopkg/wiki/Running-Multiple-Recipes#recipe-lists) via AutoPkg , setting the [report path](https://github.com/autopkg/autopkg/wiki/Processor-Summary-Reporting) to `adobe_admin_console_recipes_report.plist`, within the passed/derived directory. (Examples: `~/Downloads/adobe_admin_console_recipes_report.plist`, `/Users/Shared/adobe/adobe_admin_console_recipes_report.plist`)

## Application names
|Adobe CC 2024|Adobe CC 2023|Adobe CC 2022|Adobe CC 2021| 
|:---:|:---:|:---:|:---:|
|AdobeAcrobatDC|AdobeAcrobatDC|AdobeAcrobatDC|AdobeAcrobatDC|AdobeAcrobatDC|
|AdobeAfterEffects2024|AdobeAfterEffects2023|AdobeAfterEffects2022|AdobeAfterEffects2021|
|AdobeAnimate2024|AdobeAnimate2023|AdobeAnimate2022|AdobeAnimate2021|
|AdobeAudition2024|AdobeAudition2023|AdobeAudition2022|AdobeAudition2021|
|AdobeBridge2024|AdobeBridge2023|AdobeBridge2022|AdobeBridge2021|
|AdobeCharacterAnimator2024|AdobeCharacterAnimator2023|AdobeCharacterAnimator2022|AdobeCharacterAnimator2021|
|AdobeDimension|AdobeDimension|AdobeDimension|AdobeDimension|AdobeDimension|
|AdobeDreamweaver2021|AdobeDreamweaver2021|AdobeDreamweaver2021|AdobeDreamweaver2021|
|AdobeIllustrator2024|AdobeIllustrator2023|AdobeIllustrator2022|AdobeIllustrator2021|
|AdobeInCopy2024|AdobeInCopy2023|AdobeInCopy2022|AdobeInCopy2021|
|AdobeInDesign2024|AdobeInDesign2023|AdobeInDesign2022|AdobeInDesign2021|
|AdobeLightroomCC|AdobeLightroomCC|AdobeLightroomCC|AdobeLightroomCC|
|AdobeLightroomClassic|AdobeLightroomClassic|AdobeLightroomClassic|AdobeLightroomClassic|
|AdobeMediaEncoder2024|AdobeMediaEncoder2023|AdobeMediaEncoder2022|AdobeMediaEncoder2021|
|AdobePhotoshop2024|AdobePhotoshop2023|AdobePhotoshop2022|AdobePhotoshop2021|
|AdobePrelude2022|AdobePrelude2022|AdobePrelude2022|AdobePrelude2021|
|AdobePremierePro2024|AdobePremierePro2023|AdobePremierePro2022|AdobePremierePro2021|
|AdobePremiereRush2.0|AdobePremiereRush2.0|AdobePremiereRush2.0|AdobePremiereRush|
|AdobeSubstance3DDesigner|AdobeSubstance3DDesigner|AdobeSubstance3DDesigner|AdobeSubstance3DDesigner|
|AdobeSubstance3DPainter|AdobeSubstance3DPainter|AdobeSubstance3DPainter|AdobeSubstance3DPainter|
|AdobeSubstance3DSampler|AdobeSubstance3DSampler|AdobeSubstance3DSampler|AdobeSubstance3DSampler|
|AdobeSubstance3DStager|AdobeSubstance3DStager|AdobeSubstance3DStager|AdobeSubstance3DStager|
|AdobeXD|AdobeXD|AdobeXD|AdobeXD|

## Recipe Types
Munki recipes are included in this repo only, as we use these recipes and as such can keep them updated as needed.

Other than the installs array, these included recipes auto-populate the below items. With values from either the [AdobeAutoPkgApplicationData.json](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/AdobeAutoPkgApplicationData.json) and the PKG's `optionXML.xml` and `Application.json` files

• **blocking_applications** - see `aacp_blocking_applications`  in the Variables table below  
• **description** - see `aacp_application_description` in the Variables table below  
• **display_name** - from `display_name` for the titles version, within [AdobeAutoPkgApplicationData.json](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/AdobeAutoPkgApplicationData.json)  
• **installer_type** - set to `<string></string>`, due to: [https://dazwallace.wordpress.com/2021/03/27/adobe-installers-munki-and-error-82/](https://dazwallace.wordpress.com/2021/03/27/adobe-installers-munki-and-error-82/)  
• **minimum_os_version** - from `[SystemRequirement][CheckCompatibility][Content]` from within `Application.json`, derived via the `minos_regex` found within titles version, within [AdobeAutoPkgApplicationData.json](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/AdobeAutoPkgApplicationData.json). With the exception of Acrobat, which it's just pulled from the titles version, within [AdobeAutoPkgApplicationData.json](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/AdobeAutoPkgApplicationData.json)  

If you don't want the above to be set as mentioned, then you'll need to create your own .munki recipes.

You can then make changes to the second `MunkiPkginfoMerger` section, the which looks like the below, to override what it being set by the [AdobeAdminConsolePackagesPkgInfoCreator](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/AdobeAdminConsolePackagesPkgInfoCreator.py) processor:

```
            <dict>
                <key>Processor</key>
                <string>MunkiPkginfoMerger</string>
                <key>Arguments</key>
                <dict>
                    <key>additional_pkginfo</key>
                    <dict>
                        <key>installer_type</key>
                        <string/>
                        <key>version</key>
                        <string>%version%</string>
                    </dict>
                </dict>
            </dict>
```

## Variables
The below are the output_variables from the [AdobeAdminConsolePackagesPkgInfoCreator](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/AdobeAdminConsolePackagesPkgInfoCreator.py) processor, and how the values are derived.

Hopefully this makes things easier to create your own recipes.

| Variable | Generated How? | Usage |
|:---:|:---:|---|
|aacp_application_architecture_type|`optionXML.xml`, the value of the `ProcessorArchitecture` element.|Raises if not found or not either arm64, macuniversal nor x64. x64 is later converted to x86_64.|
|aacp_application_base_version|`optionXML.xml`, either: within .//HDMedias/HDMedia/ where MediaType = Product, then the value for `baseVersion` from the parent element. Or, if RIBS media. Then .//Medias/Media and the value for the `ProdVersion` from the within the parent element.|The major version of a title the installer is for.|
|aacp_application_bundle_id|Manually set in [AdobeAutoPkgApplicationData.json](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/AdobeAutoPkgApplicationData.json)|Value of the titles CFBundleIdentifier.|
|aacp_application_description|[AdobeAutoPkgApplicationData.json](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/AdobeAutoPkgApplicationData.json), the short description found within ["ProductDescription"]["Tagline"]["Language"] where ["locale"] == `installLang`, failsover to the `app_description` key in `AdobeAutoPkgApplicationData.json`.|Description of title.|
|aacp_application_display_name|Manually set in [AdobeAutoPkgApplicationData.json](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/AdobeAutoPkgApplicationData.json)|Display name of the title|
|aacp_application_full_path|Manually set in [AdobeAutoPkgApplicationData.json](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/AdobeAutoPkgApplicationData.json)|Full path to titles .app.|
|aacp_application_install_lang|optionXML.xml, either: within .//HDMedias/HDMedia/ where MediaType = Product, then the value for `installLang` from the parent element. Or, if RIBS media. Then .//Medias/Media and the value for the `installLang` from the within the parent element.|Used to pull the description for the title.|
|aacp_application_maximum_os|Set to `14.99` for bundle packages.|Highest OS version with which the title is compatible.|
|aacp_application_minimum_os|Sourced from `[SystemRequirement][CheckCompatibility][Content]` within [AdobeAutoPkgApplicationData.json](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/AdobeAutoPkgApplicationData.json)With the exception of Acrobat, which is pulled from: [AdobeAutoPkgApplicationData.json](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/AdobeAutoPkgApplicationData.json)|Lowest OS version with which the title is compatible. 
|aacp_application_sap_code|optionXML.xml, either: within .//HDMedias/HDMedia/ where MediaType = Product, then the value for `SAPCode` from the parent element. Or, if RIBS media. Then .//Medias/Media and the value for the `SAPCode` from the within the parent element.|Used to identify which title the installer is for.|
|aacp_blocking_applications|A sorted set of the titles conflicting processes, collated from ['ConflictingProcesses']['ConflictingProcess'] within the [AdobeAutoPkgApplicationData.json](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/AdobeAutoPkgApplicationData.json) where `forceKillAllowed` is `False`.|Used to identify which processes cannot be running during the titles installation.|
|aacp_json_path|os.path.join(self.env['aacp_parent_dir'], 'AdobeAutoPkgApplicationData.json').|Contains details of items to read in per `aacp_sap_code`, per `aacp_base_version`. To be updated with new major releases to drive `AdobeAdminConsolePackagesPkgInfoCreator`|
|aacp_matched_json|Dict containing various pieces of metadata, such as `additional_blocking_applications`, `app_bundle_id`, `app_description`, `app_json_version_key`, `app_name`, `app_path`, `display_name, `maxos_version`, `minos_version` and `version_comparison_key`.|Used to built an installs array. |
|aacp_option_xml_path|Path to the tiles `optionXML.xml` file.|Processed for metadata.|
|aacp_override_path|Path to the recipe override itself.|Used to update the overrides contents.|
|aacp_package_path|Path to the titles package.|For import, and for checking files within for metadata.|
|aacp_package_type|Package type of the pkg, either `bundle` or `flat`|Used to decide how to process the package to obtain the titles metadata.
|aacp_parent_dir|Path to directory which the AdobeAdminConsolePackagesPkgInfoCreator exists.|To create the full path to `AdobeAutoPkgApplicationData.json`.|
|aacp_proxy_xml_path|For Acrobat only, path to the tiles `proxy.xml` file.|Processed for metadata.|
|aacp_root_dir|Path to the dir containing [AdobeAdminConsolePackagesPkgInfoCreator](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/AdobeAdminConsolePackagesPkgInfoCreator.py|Used to build paths for other items.|
|aacp_target_folder|optionXML.xml, either: within .//HDMedias/HDMedia/ where MediaType = Product, then the value for `TargetFolderName` from the parent element. Or, if RIBS media. Then .//Medias/Media and the value for the `TargetFolderName` from the within the parent element.|The name of the folder within the PKG to check additional files for metadata. Will be a folder within: ./Contents/Resources/HD  for a HD installer, and the following for a RIBS installer: ./Contents/Resources/Setup|
|aacp_version|This value is taken from the key defined by `app_json_version_key` within the [AdobeAutoPkgApplicationData.json](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/AdobeAutoPkgApplicationData.json) for the matching `aacp_sap_code` and `aacp_base_version`.|Titles version, `%version%` is set to this value.|
|aacp_version_compare_key|Taken from [AdobeAutoPkgApplicationData.json](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/AdobeAutoPkgApplicationData.json), will be either `CFBundleVersion` or `CFBundleShortVersionString`| The key which holds the applcations version within the applications info.plist. 

## AdobeAutoPkgApplicationData.json structure
The below details the structure and keys in the [AdobeAutoPkgApplicationData.json](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/AdobeAutoPkgApplicationData.json) file.

```
{
        "sap_code": "AME",
        "versions": {
            "15.0": {
                "app_bundle_id": "com.adobe.ame.application.15",
                "app_description": "Quickly output video files for virtually any screen.",
                "app_json_version_key": "CodexVersion",
                "app_name": "AdobeMediaEncoder2021",
                "app_path": "/Applications/Adobe Media Encoder 2021/Adobe Media Encoder 2021.app",
                "display_name": "Adobe Media Encoder 2021",
                "minos_regex": "macChecks={minOSVersion:\\\"(.*?)\\\"",
                "version_comparison_key": "CFBundleShortVersionString"
            },
            "22.0": {
                "app_bundle_id": "com.adobe.ame.application.22",
                "app_description": "Quickly output video files for virtually any screen.",
                "app_json_version_key": "CodexVersion",
                "app_name": "AdobeMediaEncoder2022",
                "app_path": "/Applications/Adobe Media Encoder 2022/Adobe Media Encoder 2022.app",
                "display_name": "Adobe Media Encoder 2022",
                "minos_regex": "macChecks={minOSVersion:\\\"(.*?)\\\"",
                "version_comparison_key": "CFBundleShortVersionString"
            },
            "23.0": {
                "app_bundle_id": "com.adobe.ame.application.23",
                "app_description": "Quickly output video files for virtually any screen.",
                "app_json_version_key": "CodexVersion",
                "app_name": "AdobeMediaEncoder2023",
                "app_path": "/Applications/Adobe Media Encoder 2023/Adobe Media Encoder 2023.app",
                "display_name": "Adobe Media Encoder 2023",
                "minos_regex": "macChecks={minOSVersion:\\\"(.*?)\\\"",
                "version_comparison_key": "CFBundleShortVersionString"
            },
            "24.0": {
                "app_bundle_id": "com.adobe.ame.application.24",
                "app_description": "Quickly output video files for virtually any screen.",
                "app_json_version_key": "CodexVersion",
                "app_name": "AdobeMediaEncoder2024",
                "app_path": "/Applications/Adobe Media Encoder 2024/Adobe Media Encoder 2024.app",
                "display_name": "Adobe Media Encoder 2024",
                "minos_regex": "macChecks={minOSVersion:\\\"(.*?)\\\"",
                "version_comparison_key": "CFBundleShortVersionString"
            }
        }
    },
```

* **sap_code** - required - see `aacp_application_sap_code` in the Variables table above, this is used to define which title the object covers.  
* **versions** -  required - see `aacp_application_major_version` in the Variables table above, this is used to define which major version of the title the object covers.
* **additional_blocking_applications** - optional - Array of additional applications to add to the blocking_applications array. In the case of Acrobat, this is actually the blocking_applications array as cannot be retrieved via the same method as the older titles.
* **app_bundle_id** - required - the titles bundle id, if one isn't defived from [AdobeAdminConsolePackagesPkgInfoCreator](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/AdobeAdminConsolePackagesPkgInfoCreator.py).
* **app_description** - required - the titles description, if one isn't defived from [AdobeAdminConsolePackagesPkgInfoCreator](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/AdobeAdminConsolePackagesPkgInfoCreator.py).
* **app_json_version_key** - required - the key within the `Application.json` which holds the titles version.  
* **app_name** - required - the application name to look for, this should match a value within the [application names table](https://github.com/autopkg/dataJAR-recipes/edit/add-adobe-flat-pkg-support/Adobe%20Admin%20Console%20Packages/README.md#names).
* **app_path** - required - see the path to the application bundle, when installed.
* **display_name** - required - the display name for the title.
* **minos_regex** - required - regex pattern to use when looking to derive the minimum OS version from `[SystemRequirement][CheckCompatibility][Content]` from within `Application.json`.  
* **unsupported_versions_dict** - optional - Array containg the versions of incompatible titles, and a reason why.  
* **version_comparison_key** - required - the key in the titles info.plist to use for version comparisions.  

## FAQ

**Q1:** Do these recipes also retrieve the applications icons?

**A1:** Sadly, no. The reason is that the full icon is within the encrypted payload. The icons we can access have low resolutions,such as 176 x 168.

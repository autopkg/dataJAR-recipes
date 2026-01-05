<details>
<summary>Licensed under the Apache License, Version 2.0 </summary>
Copyright 2024 Jamf LTD

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
</details>

# Adobe Admin Console Packages
<p align="center"><img width="256" alt="Alert" src="https://github.com/user-attachments/assets/3166e0a9-3c2d-4dfd-8599-a30d26d663ad">

## About

For information on how these recipes came about (and why), please click [here.](https://macmule.com/2024/09/09/adobe-admin-console-packages-3-0/)

## Quick start guide
> [!IMPORTANT]
> As of v3+, `AdobeAdminConsolePackagesImporter.py` needs sudo to run, this is due to the fact that `AdobeAdminConsolePackagesImporter.py` v3+ installs the titles locally to retrieve the needed metadata.
> 
> The naming of the packages in the Adobe Admin Console has to match a name within the [application names table](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/README.md#application-names).


1. For each Adobe title you want to import:
   1. Download one or more DMG from the [Adobe Admin Console](https://adminconsole.adobe.com), making sure that the name is prefixed with one of the names listed within the [application names table](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/README.md#application-names).
   1. Load the .app.
   1. Download the title.
   1. If the download is a .zip, unzip it.
1. Create an override for each title, from the recipes in this directory.
   1. Make sure that the override is prefixed the same as per the name choosen in step 1.
   1. Make sure that the override type is included included within the name, such as `munki`.
   1. If the pkg is an Apple silicon pkg, add arm64 to the override name.
   1. Both plist/xml and yml/yaml overrides are supported.
1. Run `sudo ./AdobeAdminConsolePackagesImporter.py`, found within the same directory as this README, authenticating as sudo and passing at least the type key (see below for examples):
   1. `./AdobeAdminConsolePackagesImporter.py munki` - This will look within ~/Downloads/ for Adobe installers and match with .munki overrides.
   1. `./AdobeAdminConsolePackagesImporter.py jamf /Users/Shared/adobe/` - This will look within Users/Shared/adobe/ for Adobe installers and match with jamf overrides.
   1. The `--extract-icons` flag will extract any imported titles Icon file to: `%RECIPE_CACHE_DIR%/%aacp_name%.icns`.
   1. the `--uninstall` this will uninstall the tile from the Mac running `AdobeAdminConsolePackagesImporter.py`, once it has gathered the needed metadata.

## Process
1. Adobe Admin Console
   1. Create a package including just a single title and Creative Cloud Desktop app.
   1. Prefix the package with one of the names listed within the [application names table](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/README.md#application-names).
   1. Finish creating the package selecting, [flat packages](https://helpx.adobe.com/uk/enterprise/using/create-flat-packages.html). Bundle package support has been removed from these recipes as they will not install on macOS15+.
   1. Download the DMG.
   1. Load the .app.
   1. Download the title.
   1. If the download is a .zip, unzip it.
1. Create an override for each title, from the recipes in this directory.
   1. Make sure that the override is prefixed the same as per the name choosen in step 1.
   1. Make sure that the override type is included included within the name, such as `munki`.
   1. If the pkg is an Apple silicon pkg, add arm64 to the override name.
1. Run `sudo ./AdobeAdminConsolePackagesImporter.py`, found within the same directory as this README, authenticating as sudo and passing at least the type key.
   1. The minimum arguments `AdobeAdminConsolePackagesImporter.py` needs is the recipe type: `AdobeAdminConsolePackagesImporter.py munki` (for munki recipes).
   1. Optionally, pass the root directory containing the Adobe installers downloaded from the Adobe Admin Console (if this is omitted then `~/Downloads/` is used, for example `AdobeAdminConsolePackagesImporter.py /Users/Shared/adobe/`.
   1. Optionally, add the flag `--extract-icons`, this will extract any imported titles Icon file to: `%RECIPE_CACHE_DIR%/%aacp_name%.icns`.
   1. Optionally, add the flag `--uninstall` this will uninstall the title from the Mac running `AdobeAdminConsolePackagesImporter.py`, once it has gathered the needed metadata.
   1. Confirms that the passed directory or the default directory exists, before proceeding.
   1. Parses [AdobeAutoPkgApplicationData.json](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/AdobeAutoPkgApplicationData.json) to retrieve a list of titles names, (these are the same as found within the [application names table](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/README.md#application-names)). The json also contains:
       1. `aacp_name` - the titles name, this will be a name from: [application names table](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/README.md#application-names).
       1. `aacp_application_full_path` - the titles full path when installed, used to get the titles Info.plist and to generate an installs array for the supplied .munki recipes.
       1. `aacp_application_description` - Acrobat only, as the the description cannot be obtained from it's pkg itself.
       1. `aacp_blocking_applications` - Acrobat only, as not obtained in the same way as the rest of the Adobe CC titles.
       1. `aacp_application_display_name` - The titles display name, for example: `Adobe Animate 2024` vs `AdobeAnimate2024`
       1. `aacp_application_sap_code` - required for the uninstall scripts within the supplied .munki recipes.
       1. `aacp_version_comparison_key` - what version key, `CFBundleVersion` or `CFBundleShortVersionString` to use when comparing versions.
   1. Recursively looks within the defined direcory for flat pkg files which start with one of the title names retrieved from the prior step. Recording the path to the variable `aacp_package_path`.
   1. Prints a summary of found packages.
   1. Retrieves a list of [RECIPE_OVERRIDE_DIRS](https://github.com/autopkg/autopkg/wiki/Recipe-overrides#recipe-override-directories) from AutoPkg's preference domain.
   1. Looks within each of the defined [RECIPE_OVERRIDE_DIRS](https://github.com/autopkg/autopkg/wiki/Recipe-overrides#recipe-override-directories) for overrides that:
       1. Start with the same name from the [application names table](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/README.md#application-names) as the located packages.
       1. Contains the same recipe type that was passed to [AdobeAdminConsolePackagesImporter.py](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/AdobeAdminConsolePackagesImporter.py).
       1. Optionally, if the pkg contains `MACARM` looks for `arm64` within the overrides file name.
   1. For each package matched with an override:
       1. The matched override's identifier is stored in the variable: `aacp_override_identifier`, and it's path is stored in the variable: `aacp_override_path`.
       1. The package is expanded to a temp directory (the path to which is stored in the variable: `aacp_pkg_expand_dir`).
       1. The packages `optionXML.XML`, located within the packages `Scripts` directory is parsed to retrieve the following:
         1. `aacp_application_architecture_type` - the installers supported architecture, will be one of: arm64, macuniversal or x64.
         1. `aacp_application_base_version` - required for the uninstall scripts within the supplied .munki recipes.
         1. `aacp_application_install_lang` - the installers selected language, used to retrieve the languages description for the title from within it's `Application.json` file (except for Acrobat DC).
         1. `aacp_target_folder` - this is the folder within the packages `Scripts` directory, that holds the installer package for the Adobe title itself (as opposed to ancilliary installers like Creative Cloud Desktop etc).
         1. If the passed pkg is not an Adobe Acrobat installer, the following are then retrieved from the `Application.json` file. Found within a subfolder in the packages `Scripts` directory, named the value of: `aacp_target_folder`.
           1. `aacp_application_description` - the value of `TagLine`, in the same langauge as: `aacp_application_install_lang`. This then used by default, as the description in the supplied Munki recipes.
           1. `aacp_blocking_applications` - list of blocking applications. this list is later added to the overrides pkginfo dicts, (if exists).
           1. `aacp_minimum_os` - the installers minimum OS. This might well differ from the actual titles Info.plist's LSMinimumSystemVersion, but if the title cannot be installed then the latter is a moot point.
       1. The directory which the pkg was expanded into, `aacp_pkg_expand_dir`, is deleted.
       1. For each matched package, the following steps occur:
           1. If the pkg is can be installed on the Mac running the script:
               1. The installed Adobe titles Info.plist is read in, the path of which made up of `aacp_application_full_path` + `Contents/Info.plist`. With the below variables being obtained from the Info.plist:
                   1. `aacp_bundle_icon_file` - the value of `CFBundleIconFile`.
                   1. `aacp_bundle_identifier` - the value of `CFBundleIdentifier`
                   1. `aacp_bundle_short_version_string` - the value of `CFBundleShortVersionString`
                   1. `aacp_bundle_version` - the value of `CFBundleVersion`
                   1. `aacp_application_version` - the titles version, this will be either the value of `aacp_bundle_short_version_string` or `aacp_bundle_version`. Which one is dictated by the value of `aacp_version_comparison_key`.
                   1. If `aacp_minimum_os` has not yet be defined. This is set to the value of: `LSMinimumSystemVersion`
               1. If `--extract-icons` has been passed to `AdobeAdminConsolePackagesImporter.py`, the icon at: `aacp_application_full_path` + `Contents/Resources` + `aacp_bundle_icon_file` is copied to: `%RECIPE_CACHE_DIR%/%aacp_name%.icns`, and `aacp_icon_name` is set to the icons name in `%RECIPE_CACHE_DIR%`
               1. If `--uninstall` has been passed to `AdobeAdminConsolePackagesImporter.py`, `AdobeAdminConsolePackagesImporter.py` will uninstall the application from the Mac that's running: `AdobeAdminConsolePackagesImporter.py`.
           1. If the pkg is cannot be installed on the Mac running the script, the script looks in the list of Adobe installers for a pkg for the same title, that can be installed on the Mac running the script. If a matching pkg is found:
               1. Various keys are checked with across both the pkg which can be installed on the Mac running the script, and the pkg which cannot be installed on the Mac the script.
               1. If all of the keys match, the script will take some of the metadata from the pkg which can be installed on the Mac running the script, and add to the metadata of the the pkg which cannot be installed on the Mac the script.
   1. The matched recipes overrides are updated, with each `aacp_` variable being written into the matched overrides Input dict. This allows these values to be used within the override as wanted. Additionally, if the overrides Input dict contains a pkginfo dict, (such as the case with .munki recipes), then:
       1. `aacp_blocking_applications` then `blocking_applications` is created with the value of `aacp_blocking_applications`
       1. If `aacp_application_architecture_type` is either arm64 or x64, then this `supported_architectures` is created with the value of `aacp_application_architecture_type`.
   1. A [recipe list](https://github.com/autopkg/autopkg/wiki/Running-Multiple-Recipes#recipe-lists) is created, containing the overrides identifiers for the overrides which have matched a downloaded Adobe Admin Console package in alphabetical order, within the passed/derived directory. (Examples: `~/Downloads/adobe_admin_console_recipes_list.txt`, `/Users/Shared/adobe/adobe_admin_console_recipes_list.txt`)
   1. Runs the [recipe list](https://github.com/autopkg/autopkg/wiki/Running-Multiple-Recipes#recipe-lists) via AutoPkg , setting the [report path](https://github.com/autopkg/autopkg/wiki/Processor-Summary-Reporting) to `adobe_admin_console_recipes_report.plist`, within the passed/derived directory. (Examples: `~/Downloads/adobe_admin_console_recipes_report.plist`, `/Users/Shared/adobe/adobe_admin_console_recipes_report.plist`)

## Application names
<div align="center">

|Adobe CC 2026|Adobe CC 2025|Adobe CC 2024|Adobe CC 2023|
|:---:|:---:|:---:|:---:|
|AdobeAcrobatDC|AdobeAcrobatDC|AdobeAcrobatDC|AdobeAcrobatDC|
||AdobeAfterEffects2025|AdobeAfterEffects2024|AdobeAfterEffects2023|
||AdobeAnimate2024|AdobeAnimate2023||
||AdobeAudition2025|AdobeAudition2024|AdobeAudition2023|
|AdobeBridge2026|AdobeBridge2025|AdobeBridge2024|AdobeBridge2023|
||AdobeCharacterAnimator2025|AdobeCharacterAnimator2024|AdobeCharacterAnimator2023|
||AdobeDimension|AdobeDimension|AdobeDimension|
||AdobeDreamweaver2021|AdobeDreamweaver2021|AdobeDreamweaver2021|
|AdobeIllustrator2026|AdobeIllustrator2025|AdobeIllustrator2024|AdobeIllustrator2023|
|AdobeInCopy2026|AdobeInCopy2025|AdobeInCopy2024|AdobeInCopy2023|
|AdobeInDesign2026|AdobeInDesign2025|AdobeInDesign2024|AdobeInDesign2023|
|AdobeLightroomCC|AdobeLightroomCC|AdobeLightroomCC|AdobeLightroomCC|
|AdobeLightroomClassic|AdobeLightroomClassic|AdobeLightroomClassic|AdobeLightroomClassic|
||AdobeMediaEncoder2025|AdobeMediaEncoder2024|AdobeMediaEncoder2023|
|AdobePhotoshop2026|AdobePhotoshop2025|AdobePhotoshop2024|AdobePhotoshop2023|
||AdobePremierePro2025|AdobePremierePro2024|AdobePremierePro2023|
|AdobePremiereRush2.0|AdobePremiereRush2.0|AdobePremiereRush2.0|AdobePremiereRush2.0|
|AdobeSubstance3DDesigner|AdobeSubstance3DDesigner|AdobeSubstance3DDesigner|AdobeSubstance3DDesigner|
|AdobeSubstance3DPainter|AdobeSubstance3DPainter|AdobeSubstance3DPainter|AdobeSubstance3DPainter|
|AdobeSubstance3DSampler|AdobeSubstance3DSampler|AdobeSubstance3DSampler|AdobeSubstance3DSampler|
|AdobeSubstance3DStager|AdobeSubstance3DStager|AdobeSubstance3DStager|AdobeSubstance3DStager|
|AdobeXD|AdobeXD|AdobeXD|AdobeXD|

</div>

## Variables
The below are written to the overrides Input dict, making them available to the recipe as wanted.

With the exception of `aacp_application_architecture_type` and `aacp_blocking_applications`, which will be added to the overrides pkginfo dict, if present and as mentioed above.

Hopefully this makes things easier to create your own recipes.

| Variable | Generated How? | Usage |
|:---:|:---:|:---:|
|aacp_application_architecture_type|`optionXML.xml`, the value of the `ProcessorArchitecture` element.|Will be one of: arm64, macuniversal or x64.|
|aacp_application_base_version|`optionXML.xml`, either: within .//HDMedias/HDMedia/ where MediaType = Product, then the value for `baseVersion` from the parent element. Or, if RIBS media. Then .//Medias/Media and the value for the `ProdVersion` from the within the parent element.|The major version of a title the installer is for, required by the uninstall scripts for all except Adobe Acrobat.|
|aacp_application_description|[The short description found within the titles `Application.json` file within ["ProductDescription"]["Tagline"]["Language"] where ["locale"] == `aacp_application_install_lang`, for all titles except Adobe Acrobat. With Adobe Acrobat's description being set to the value of `aacp_application_description` within [AdobeAutoPkgApplicationData.json](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/AdobeAutoPkgApplicationData.json).|Titles description.|
|aacp_application_display_name|Manually set in [AdobeAutoPkgApplicationData.json](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/AdobeAutoPkgApplicationData.json)|Display name of the title.|
|aacp_application_full_path|Manually set in [AdobeAutoPkgApplicationData.json](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/AdobeAutoPkgApplicationData.json)|Full path to titles .app.|
|aacp_application_install_lang|optionXML.xml, either: within .//HDMedias/HDMedia/ where MediaType = Product, then the value for `installLang` from the parent element. Or, if RIBS media. Then .//Medias/Media and the value for the `installLang` from the within the parent element.|Used to pull the description for the title, for all titles except Adobe Acrobat. See: `aacp_application_description`.|
|aacp_application_minimum_os|Sourced from `[SystemRequirement][CheckCompatibility][Content]` within [AdobeAutoPkgApplicationData.json](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/AdobeAutoPkgApplicationData.json). With the exception of Acrobat, which is pulled from: [AdobeAutoPkgApplicationData.json](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/AdobeAutoPkgApplicationData.json)|Lowest OS version with which the title is compatible.
|aacp_application_sap_code|Taken from [AdobeAutoPkgApplicationData.json](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/AdobeAutoPkgApplicationData.json).|Required by the uninstall scripts for all except Adobe Acrobat.|
|aacp_application_version|The applications version, this will be either the value of `aacp_bundle_short_version_string` or `aacp_bundle_version`. Which one is dictated by the value of `aacp_version_comparison_key`.|The titles version.|
|aacp_blocking_applications|A sorted set of the titles conflicting processes, collated from ['ConflictingProcesses']['ConflictingProcess'] within the `Application.json` file where `forceKillAllowed` is `False`, for all titles except Adobe Acrobat. With Adobe Acrobat's `aacp_blocking_applications` being set to it's vaule in: [AdobeAutoPkgApplicationData.json](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/AdobeAutoPkgApplicationData.json).|Used to identify which processes cannot be running during the titles installation.|
|aacp_bundle_icon_file|Retrieved from the titles Info.plist.|Value of CFBundleIconFile.|
|aacp_bundle_identifier|Retrieved from the titles Info.plist.|Value of CFBundleIdentifier|
|acp_bundle_short_version_string|Retrieved from the titles Info.plist.|Value of CFBundleShortVersionString|
|aacp_bundle_version|Retrieved from the titles Info.plist.|Value of CFBundleVersion|
|aacp_icon_name|Name of the icon file, if it was set to be extracted, in: %RECIPE_CACHE_DIR%|
|aacp_minimum_os|The installers minimum OS, for all titles except Adobe Acrobat. With Adobe Acrobat's being set to the value of LSMinimumSystemVersion from witin it's Info.plist.|The installers minimum OS.
|aacp_name|The name of the title, as matched within: [AdobeAutoPkgApplicationData.json](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/AdobeAutoPkgApplicationData.json).| Titles name.|
|aacp_override_identifier|Name of the titles matched overrides identifier, retrieved from the override at: `aacp_override_path`.|Added to the recipe list.|
|aacp_override_path|Path to the recipe override itself.|Used to update the overrides contents.|
|aacp_pkg_expand_dir|Temp directory where the package was expanded.|Used within `AdobeAdminConsolePackagesImporter.py` to delete the temporary directory after checking it's contents as needed.|
|aacp_target_folder| The folder within the packages `Scripts` directory, that holds the installer package for the Adobe title itself (as opposed to ancilliary installers like Creative Cloud Desktop etc).|To generate the path to the titles `Application.json`
|aacp_version_compare_key|Taken from [AdobeAutoPkgApplicationData.json](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/AdobeAutoPkgApplicationData.json), will be either `CFBundleVersion` or `CFBundleShortVersionString`.|The key which holds the applcations version within the titles info.plist.|

## FAQ
**Q1:** Do these recipes also retrieve the applications icons?

**A1:** ~~Sadly, no. The reason is that the full icon is within the encrypted payload. The icons we can access have low resolutions,such as 176 x 168.~~
> [!TIP]
> If you're using munki. Make sure that the icons your drop within Munki's icon folder are named the same as the munki name. Munki will then match the icons without you having to explicitly state the icons name within the overrride. As mentioned on this [wiki page](https://github.com/munki/munki/wiki/Product-Icons#details).

With v3+, the titles icons can be extracted as per the `--extract-icons` flag.
##
**Q2:** Why does version 2+ of these recipes no longer need the *_Uninstall.pkg?

**A1:** The flat packages do not include a *_Uninstall.pkg, as such the .munki recipes contain uninstallation scripts.. which are the same for all but Acrobat.
##
**Q3:** Why no bundle package support in v3+?

**A3:** Support was dropped as Sequoia doesn't support bundle packages, and it simplifies the code somewhat.
##
**Q4:** What happens if one of the packages needs a different processor architecture than the pkg?

**A4:** That should only apply to 3 of the Substance 3D titles, and hopefully their next releases will have universal packages.

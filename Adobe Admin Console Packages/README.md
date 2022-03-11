### Adobe Admin Console Packages

## About  
Since 2021, more and more of the Adobe Admin Console Packages have had signed/encrypted payloads.

This means that we cannot pull apart the PKG's to retrieve the needed metadata for AutoPkg recipes.

The prior iterations of our Adobe Versioner would work around this issue by having the data within the Versioner itself, but this then needed annual updates.

The [AdobeAdminConsolePackagesPkgInfoCreator](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/AdobeAdminConsolePackagesPkgInfoCreator.py) processor, utilises the file: [AdobeAutoPkgApplicationData.json](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/AdobeAutoPkgApplicationData.json) to generate the needed metadata.

The idea is that we can update [AdobeAutoPkgApplicationData.json](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/AdobeAutoPkgApplicationData.json), as needed. And not need to create a new processor.

Data within [AdobeAutoPkgApplicationData.json](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/AdobeAutoPkgApplicationData.json), as well as the PKG's `optionXML.xml` and `Application.json` is used to create the metadata needed for the title.

The processor [AdobeAdminConsolePackagesPkgInfoCreator](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/AdobeAdminConsolePackagesPkgInfoCreator.py), generates a large about output variables. These are detailed in the table at the end of this README, and are to be used for folks to write their own recipes.

## Usage
1. Naming is important to the recipes, to start with you'll need to create [Managed Package](https://helpx.adobe.com/uk/enterprise/using/manage-packages.html) with one of the below names in the [Adobe Admin Console](https://adminconsole.adobe.com):

|||||
|:---:|:---:|:---:|:---:
|AdobeAcrobatDC| AdobeCharacterAnimator2021| AdobeInDesign2022| AdobePremiereRush|
|AdobeAfterEffects2021| AdobeCharacterAnimator2022| AdobeLightroomCC| AdobePremiereRush2.0|
|AdobeAfterEffects2022| AdobeDimension| AdobeLightroomClassic|AdobeSubstance3DDesigner|
|AdobeAnimate2021| AdobeDreamweaver2021| AdobeMediaEncoder2021|AdobeSubstance3DPainter|
|AdobeAnimate2022| AdobeIllustrator2021| AdobeMediaEncoder2022|AdobeSubstance3DSampler|
|AdobeAudition2021| AdobeIllustrator2022| AdobePhotoshop2021|AdobeSubstance3DStager|
|AdobeAudition2022| AdobeInCopy2021| AdobePhotoshop2022|AdobeXD|
|AdobeBridge2021| AdobeInCopy2022| AdobePremierePro2021||
|AdobeBridge2022| AdobeInDesign2021| AdobePremierePro2022||
2. Download the DMG form the [Adobe Admin Console](https://adminconsole.adobe.com)
3. Load the .app
4. Download the title to your ~/Downloads
5. Unzip the zip file
6. An override is needed for each title, Munki recipes are supplied here. The override needs to start with the a name from the list above, and contain the recipe type. For example, `AdobeAcrobatDC.munki.recipe`
9. With the above in place, call with the recipe "type" [AdobeAdminConsolePackagesImporter.py](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/AdobeAdminConsolePackagesImporter.py). For example: `AdobeAdminConsolePackagesImporter.py munki`

## Process
1. [AdobeAdminConsolePackagesImporter.py](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/AdobeAdminConsolePackagesImporter.py) will create a [recipe list](https://github.com/autopkg/autopkg/wiki/Running-Multiple-Recipes#recipe-lists) at: ~/Downloads/adobe_admin_console_recipes_list.txt  
2. [AdobeAdminConsolePackagesImporter.py](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/AdobeAdminConsolePackagesImporter.py) next checks ~/Dowmloads for any folders that begin with Adobe  
3. Next, these are checked to see if they contain the *_Install.pkg and *_Uninstall.pkg PKG's, (these will be present if a [Managed Package](https://helpx.adobe.com/uk/enterprise/using/manage-packages.html)).  
4. If the above steps pass, then the [RECIPE_OVERRIDE_DIRS](https://github.com/autopkg/autopkg/wiki/Recipe-Overrides#recipe-override-directories) searched. If an override is found which starts with the name of the title (as per the table above), and contains the recipe type as passed to [AdobeAdminConsolePackagesImporter.py](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/AdobeAdminConsolePackagesImporter.py), it's identifier is added to the [recipe list](https://github.com/autopkg/autopkg/wiki/Running-Multiple-Recipes#recipe-lists)  
5. If any matching overrides are found, AutoPkg will run the recipes in the [recipe list](https://github.com/autopkg/autopkg/wiki/Running-Multiple-Recipes#recipe-lists), generating a report at: ~/Downloads/adobe_admin_console_recipes_report.txt  

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
|aacp_application_bundle|`aacp_installdir_maxpath` after regex applied to get the path alone.|Used to generate `aacp_application_full_path`|
|aacp_application_architecture_type|`optionXML.xml`, the value of the `ProcessorArchitecture` element.|Raises if not found or not either arm64 or x64. x64 is later converted to x86_64.|
|aacp_application_description|`Application.json`, the short description found within ["ProductDescription"]["Tagline"]["Language"] where ["locale"] == `installLang`, failsover to the `app_description` key in `AdobeAutoPkgApplicationData.json`.|Description of title.|
|aacp_application_full_path|os.path.join('/Applications', self.env['aacp_application_path'], self.env['aacp_application_bundle'])|Full path to titles .app.|
|aacp_application_install_lang|optionXML.xml, either: within .//HDMedias/HDMedia/ where MediaType = Product, then the value for `installLang` from the parent element. Or, if RIBS media. Then .//Medias/Media and the value for the `installLang` from the within the parent element.|Used to pull the description for the title.|
|aacp_application_json_path|Path to the tiles `Application.json` file.|Processed for metadata.|
|aacp_application_major_version|`optionXML.xml`, either: within .//HDMedias/HDMedia/ where MediaType = Product, then the value for `baseVersion` from the parent element. Or, if RIBS media. Then .//Medias/Media and the value for the `ProdVersion` from the within the parent element.|The major version of a title the installer is for.|
|aacp_application_path|`aacp_installdir_value` after regex applied to get the path alone.|Used to generate `aacp_application_full_path`|
|aacp_application_sap_code|optionXML.xml, either: within .//HDMedias/HDMedia/ where MediaType = Product, then the value for `SAPCode` from the parent element. Or, if RIBS media. Then .//Medias/Media and the value for the `SAPCode` from the within the parent element.|Used to identify which title the installer is for.|
|aacp_target_folder|optionXML.xml, either: within .//HDMedias/HDMedia/ where MediaType = Product, then the value for `TargetFolderName` from the parent element. Or, if RIBS media. Then .//Medias/Media and the value for the `TargetFolderName` from the within the parent element.|The name of the folder within the PKG to check additional files for metadata. Will be a folder within: ./Contents/Resources/HD  for a HD installer, and the following for a RIBS installer: ./Contents/Resources/Setup|
|aacp_application_version|`Application.json`, the value is taken from the key defined by `app_json_version_key` within the `AdobeAutoPkgApplicationData.json` for the matching `aacp_sap_code` and `aacp_base_version`.|Titles version.|
|aacp_blocking_applications|A sorted set of the titles conflicting processes, collated from ['ConflictingProcesses']['ConflictingProcess'] within the `Application.json` where `forceKillAllowed` is `False`.|Used to identify which processes cannot be running during the titles installation.|
|aacp_install_pkg_path|Full path to the `*_Install.pkg`|For import, and for checking files within for metadata.|
|aacp_json_path|os.path.join(self.env['aacp_parent_dir'], 'AdobeAutoPkgApplicationData.json').|Contains details of items to read in per `aacp_sap_code`, per `aacp_base_version`. To be updated with new major releases to drive `AdobeAdminConsolePackagesPkgInfoCreator`|
|aacp_option_xml_path|Path to the tiles `optionXML.xml` file.|Processed for metadata.|
|aacp_parent_dir|Path to directory which the AdobeAdminConsolePackagesPkgInfoCreator exists.|To create the full path to `AdobeAutoPkgApplicationData.json`.|
|aacp_proxy_xml_path|Acroabat only, path to the tiles `proxy.xml` file.|Processed for metadata.|
|aacp_uninstall_pkg_path|Full path to the `*_Uninstall.pkg` |For importing.|
|aacp_version_json|dict from `AdobeAutoPkgApplicationData.json`, which matches the `aacp_application_sap_code` and `aacp_application_major_version`.|More items for mmetadata.|

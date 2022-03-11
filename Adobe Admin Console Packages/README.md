### Adobe Admin Console Packages
##### Table of Contents  
[About](#About)
[Usage](#Usage)
[Process](#Process)
[Output Variables](#Output Variables)

<a name="About">
#### About
Since 2021, more and more of the Adobe Admin Console Packages have had signed/encrypted payloads.

This means that we cannot pull apart the PKG's to retrieve the needed metadata for AutoPkg recipes.

The prior iterations of our Adobe Versioner would work around this issue by having the data within the Versioner itself, but this then needed annual updates.

The [AdobeAdminConsolePackagesPkgInfoCreator](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/AdobeAdminConsolePackagesPkgInfoCreator.py) processor, utilises the file: [AdobeAutoPkgApplicationData.json](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/AdobeAutoPkgApplicationData.json) to generate the needed metadata.

The idea is that we can update [AdobeAutoPkgApplicationData.json](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/AdobeAutoPkgApplicationData.json), as needed. And not need to create a new processor.

Data within [AdobeAutoPkgApplicationData.json](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/AdobeAutoPkgApplicationData.json), as well as the PKG's `optionXML.xml` and `Application.json` is used to create the metadata needed for the title.

The processor [AdobeAdminConsolePackagesPkgInfoCreator](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/AdobeAdminConsolePackagesPkgInfoCreator.py), generates a large about output variables. These are detailed in the table at the end of this README, and are to be used for folks to write their own recipes.

Munki recipes are included only, as we use these recipes and as such can keep them udpated as needed.

<a name="Usage">
#### Usage
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
6. An override is needed for each title, Munki recipes are supplied here. The override needs to start with the a name from the list above, and contain the recipe "type". For example, `AdobeAcrobatDC.munki.recipe`
9. With the above in place, call with the recipe "type" [AdobeAdminConsolePackagesImporter.py](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/AdobeAdminConsolePackagesImporter.py). For example: `AdobeAdminConsolePackagesImporter.py munki`
<a name="Process">
#### Process
<a name="Output Variables">
### Output Variables
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
|aacp_blocking_applications|A sorted set of the titles conflicting processes, collated from ['ConflictingProcesses']['ConflictingProcess'] within the `Application.json`.|Used to identify which processes cannot be running during the titles installation.|
|aacp_install_pkg_path|Full path to the `*_Install.pkg`|For import, and for checking files within for metadata.|
|aacp_json_path|os.path.join(self.env['aacp_parent_dir'], 'AdobeAutoPkgApplicationData.json').|Contains details of items to read in per `aacp_sap_code`, per `aacp_base_version`. To be updated with new major releases to drive `AdobeAdminConsolePackagesPkgInfoCreator`|
|aacp_option_xml_path|Path to the tiles `optionXML.xml` file.|Processed for metadata.|
|aacp_parent_dir|Path to directory which the AdobeAdminConsolePackagesPkgInfoCreator exists.|To create the full path to `AdobeAutoPkgApplicationData.json`.|
|aacp_proxy_xml_path|Acroabat only, path to the tiles `proxy.xml` file.|Processed for metadata.|
|aacp_uninstall_pkg_path|Full path to the `*_Uninstall.pkg` |For importing.|
|aacp_version_json|dict from `AdobeAutoPkgApplicationData.json`, which matches the `aacp_application_sap_code` and `aacp_application_major_version`.|More items for mmetadata.|

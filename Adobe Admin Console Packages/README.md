# IN BETA #

### Adobe Admin Console Packages
#### Requirements
1. An Adobe Admin Console Package created, downloaded, the .app ran, and the .zip uncompressed in ~/Downloads
2. An override for the munki recipe, suffixed the Adobe Admin Console Package name, with "munki" within the name
3. cd to the dir
4. ./AdobeAdminConsolePackagesImporter.py munki

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
|aacp_json_path|os.path.join(self.env['aacp_parent_dir'], 'AdobeAutoPkgApplicationData.json').|Contains details of items to read in per `aacp_sap_code`, per `aacp_base_version`. To be updated with new major releases to drive `AdobeAdminConsolePackagesVersioner`|
|aacp_option_xml_path|Path to the tiles `optionXML.xml` file.|Processed for metadata.|
|aacp_parent_dir|Path to directory which the AdobeAdminConsolePackagesVersioner exists.|To create the full path to `AdobeAutoPkgApplicationData.json`.|
|aacp_proxy_xml_path|Acroabat only, path to the tiles `proxy.xml` file.|Processed for metadata.|
|aacp_uninstall_pkg_path|Full path to the `*_Uninstall.pkg` |For importing.|
|aacp_version_json|dict from `AdobeAutoPkgApplicationData.json`, which matches the `aacp_application_sap_code` and `aacp_application_major_version`.|More items for mmetadata.|

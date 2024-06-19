#!/usr/local/autopkg/python
# pylint: disable = invalid-name
'''
Copyright (c) 2024, Jamf Ltd.  All rights reserved.

DESCRIPTION

Generates installation information for Adobe Admin Console Packages.

'''


# Standard Imports
import json
import os
import plistlib
import re
import shutil
import subprocess
import tempfile
import xml
from xml.etree import ElementTree
import yaml


# AutoPkg imports
# pylint: disable = import-error
from autopkglib import (Processor,
                        ProcessorError)


# Define class
__all__ = ['AdobeAdminConsolePackagesPkgInfoCreator']
__version__ = ['2.0.1']


# Class
class AdobeAdminConsolePackagesPkgInfoCreator(Processor):
    '''
       Parses generated Adobe Admin Console Packages to generate installation information.
    '''

    description = __doc__

    input_variables = {
        'aacp_override_path': {
            'required': True,
            'description': "Path to package to the override. Used to write keys back to.",
        },
        'aacp_package_path': {
            'required': True,
            'description': "Path to package to import, this will be created within the override "
                           "by AdobeAdminConsolePackagesImporter.py",
        },
        'aacp_package_type': {
            'required': True,
            'description': "Type of pkg at aacp_package_path, will be: bundle or flat.",
        },
    }

    output_variables = {
        'aacp_application_architecture_type': {
            'description': "The architecture type for the title, either arm64 or x86_64",
        },
        'aacp_application_base_version': {
            'description': "The base/major version of the title.",
        },
        'aacp_application_bundle_id': {
            'description': "Value of the titles CFBundleIdentifier.",
        },
        'aacp_application_description': {
            'description': "Short description of the title.",
        },
        'aacp_application_display_name': {
            'description': "Display name of the title.",
        },
        'aacp_application_full_path': {
            'description': "Full path to the application bundle on disk, as per Terminal etc, "
                           "not Finder.",
        },
        'aacp_application_install_lang': {
            'description': "The titles installation langauage.",
        },
        'aacp_application_json_path': {
            'description': "Path to the tiles Application.json file.",
        },
        'aacp_application_sap_code': {
            'description': "The titles sap code.",
        },
        'aacp_blocking_applications': {
            'description': "Sorted set of the conflicting processes.",
        },
        'aacp_json_path': {
            'description': "Path to AdobeAutoPkgApplicationData.json.",
        },
        'aacp_matched_json': {
            'description': ('dict from AdobeAutoPkgApplicationData.json, which matches the '
                            '"aacp_application_sap_code" and "aacp_application_base_version".'),
        },
        'aacp_option_xml_path': {
            'description': "Path to the tiles optionXML.xml file.",
        },
        'aacp_package_type': {
                    'description': "Type of pkg at aacp_package_path, will be: bundle or flat.",
        },
        'aacp_package_path': {
            'description': "Path to package to import, this will be created within the override "
                           "by AdobeAdminConsolePackagesImporter.py",
        },
        'aacp_parent_dir': {
            'description': "Path to parent directory of this processor.",
        },
        'aacp_proxy_xml_path': {
            'description': "Acrobat only, path to proxy.xml.",
        },
        'aacp_target_folder': {
            'description': "The name of the folder within the pkg to check files for metadata.",
        },
        'additional_pkginfo': {
            'description': "Additonal pkginfo fields extracted from the Adobe metadata.",
        },
        'version': {
            'description': "The titles version.",
        }
    }


    def main(self):
        '''
            Parses aacp_package_path, to generate pkginfo
        '''

        # Var declaration
        app_json = None
        #self.env['aacp_package_path'] = self.env.get('aacp_package_path')

        # Progress notification
        self.output("Starting Adobe Admin Console Packages pkginfo process...")

        # Progress notification
        self.output(f"aacp_package_path: {self.env['aacp_package_path']}")

        # If aacp_package_path somehow doesn't exist, raise
        if not os.path.exists(self.env['aacp_package_path']):
            # Raise if missing
            raise ProcessorError(f"Cannot find {self.env['aacp_package_path']}, exiting...")

        # If aacp_package_type is bundle
        if self.env['aacp_package_type'] == 'bundle':
            # Set maximum_os to 14.99
            self.env['aacp_application_maximum_os'] = "14.99"
            # Progress notification
            self.output(f"aacp_application_maximum_os has been set to : "
                        f"{self.env['aacp_application_maximum_os']}, as "
                        f"{self.env['aacp_package_path']} is a {self.env['aacp_package_type']} "
                        f"pkg.")

        # Get the installers optionXML.xml
        self.get_option_xml_path()

        # Process the titles optionXML.xml
        self.process_optionxml_xml()

        # If the we're looking at Acrobat, then we need to process things differently
        if self.env['aacp_application_sap_code'] == 'APRO':
            # Process acrobat installer
            self.process_acrobat_installer()
        # If we're looking at another installer
        else:
            # Process HD installer
            app_json = self.process_hd_installer()

        # Process app_json retrieve application metadata
        self.process_adobe_autopkg_application_data()

        # Process
        self.process_matched_json(app_json)

        # Create pkginfo
        self.create_pkginfo()

        # Update the override by adding all aacp prefixed keys, to assist with troubleshooting
        self.update_override()

        # If aacp_temp_dir is declared
        if 'aacp_temp_dir' in self.env:
            # Progress notification
            self.output(f"Deleting: {self.env['aacp_temp_dir']}...")
            # Delete aacp_temp_dir
            shutil.rmtree(self.env['aacp_temp_dir'])

        # Set version to aacp_version
        self.env['version'] = self.env['aacp_version']


    def create_pkginfo(self):
        '''
            Create pkginfo with found details
        '''

        # Var declaration
        self.env['additional_pkginfo'] = {}

        # If we have aacp_application_architecture_type in self.env and it's not macuniversal
        if ('aacp_application_architecture_type' in self.env and not
            self.env['aacp_application_architecture_type'] == 'macuniversal'):
            # Set to ['additional_pkginfo']['supported_architectures']
            self.env['additional_pkginfo']['supported_architectures'] = [
                                           self.env['aacp_application_architecture_type']]

        # If we have aacp_blocking_applications in self.env
        if self.env['aacp_blocking_applications']:
            # Set ['additional_pkginfo']['blocking_applications']
            self.env['additional_pkginfo']['blocking_applications'] = (
                                                    self.env['aacp_blocking_applications'])

        # If we have aacp_application_description in self.env
        if 'aacp_application_description' in self.env:
            # Set ['additional_pkginfo']['description']
            self.env['additional_pkginfo']['description'] = (
                                                  self.env['aacp_application_description'])

        # If we have aacp_application_display_name in self.env
        if 'aacp_application_display_name' in self.env:
            # Set ['additional_pkginfo']['display_name']
            self.env['additional_pkginfo']['display_name'] = (
                                                 self.env['aacp_application_display_name'])

        # If we have aacp_application_maximum_os in self.env
        if 'aacp_application_maximum_os' in self.env:
            # Set ['additional_pkginfo']['maximum_os_version']
            self.env['additional_pkginfo']['maximum_os_version'] = (
                                                   self.env['aacp_application_maximum_os'])

        # If we have aacp_application_minimum_os in self.env
        if 'aacp_application_minimum_os' in self.env:
            # Set pkginfo['minimum_os_version'] to aacp_application_minimum_os
            self.env['additional_pkginfo']['minimum_os_version'] = (
                                                   self.env['aacp_application_minimum_os'])

        # Check for any var replacements
        for some_key in self.env:
            # For keys beginning with aacp_ and those not ending _json
            if some_key.startswith('aacp_') and not some_key.endswith('_json'):
                # Regex replace
                self.replace_element(some_key)

        # Create pkginfo
        self.env['additional_pkginfo']['installs'] = [{
            'CFBundleIdentifier': self.env['aacp_application_bundle_id'],
            self.env['aacp_version_compare_key']: self.env['aacp_version'],
            'path': self.env['aacp_application_full_path'],
            'type': 'application',
            'version_comparison_key': self.env['aacp_version_compare_key']
         }]

        # Progress notification
        self.output(f"additional_pkginfo: {self.env['additional_pkginfo']}")


    def expand_flat_pkg(self):
        '''
            Expands self.env['aacp_package_path'] to a temp dir for processing.
        '''

        # Create a temp dir
        self.env['aacp_temp_dir'] = tempfile.mkdtemp()

        # Progress notification
        self.output(f"Created a temporary directory: {self.env['aacp_temp_dir']}")

        # If aacp_temp_dir does not exist
        if not os.path.exists(self.env['aacp_temp_dir']):
            # Raise if missing
            raise ProcessorError(f"Cannot find {self.env['aacp_temp_dir']}, exiting...")

        # The subprocess command
        cmd_args = ['/usr/sbin/pkgutil', '--expand', self.env['aacp_package_path'],
                                 os.path.join(self.env['aacp_temp_dir'], 'expand')]

        # Progress notification
        self.output(f"Expanding: {self.env['aacp_package_path']}...")

        # Run the command, raising if issues occur
        subprocess.run(cmd_args, check = True)

        # Path to the root dir in the pkg
        self.env['aacp_root_dir'] = os.path.join(self.env['aacp_temp_dir'],
                                             'expand/Install.pkg/Scripts/')


    def get_option_xml_path(self):
        '''
            Returns the path to the installers optionXML.xml
        '''

        # If aacp_package_type is bundle
        if self.env['aacp_package_type'] == 'bundle':
            # Progress notification
            self.output(f"{self.env['aacp_package_path']} is a bundle pkg, processing...")
            # Path to the root dir in the pkg
            self.env['aacp_root_dir'] = os.path.join(self.env['aacp_package_path'],
                                                              'Contents/Resources')
        # If aacp_package_type is flat
        if self.env['aacp_package_type'] == 'flat':
            # Progress notification
            self.output(f"{self.env['aacp_package_path']} is a flat pkg, processing...")
            # Expand the pkg to read the contents
            self.expand_flat_pkg()

        # If aacp_root_dir does not exist, raise
        if not os.path.exists(self.env['aacp_root_dir']):
            # Raise if missing
            raise ProcessorError(f"Cannot find {self.env['aacp_root_dir']}, exiting...")

        # Path to titles optionXML.xml
        self.env['aacp_option_xml_path'] = os.path.join(self.env['aacp_root_dir'],
                                                                      'optionXML.xml')

        # If optionXML.xml does not exist, raise
        if not os.path.exists(self.env['aacp_option_xml_path']):
            # Raise if missing
            raise ProcessorError(f"Cannot find {self.env['aacp_option_xml_path']}, "
                                 f"exiting...")

        # Progress notification
        self.output(f"aacp_option_xml_path: {self.env['aacp_option_xml_path']}")


    def process_acrobat_installer(self):
        '''
            Process Acrobat installer
        '''

        # Progress notification
        self.output("Processing Acrobat installer")

        # Var declaration
        self.env['aacp_blocking_applications'] = []

        # If a bundle pkg
        if self.env['aacp_package_type'] == 'bundle':
            # Progress notification
            self.output(f"{self.env['aacp_package_path']} is a bundle pkg, processing...")
            # Path to proxy.xml
            self.env['aacp_proxy_xml_path'] = (os.path.join(self.env['aacp_package_path'],
                                                               'Contents/Resources/Setup',
                                                           self.env['aacp_target_folder'],
                                                           'proxy.xml'))
        # If a flat pkg
        if self.env['aacp_package_type'] == 'flat':
            # Progress notification
            self.output(f"{self.env['aacp_package_path']} is a flat pkg, processing...")
            # Path to proxy.xml
            self.env['aacp_proxy_xml_path'] = (os.path.join(self.env['aacp_root_dir'],
                                              'Setup', self.env['aacp_target_folder'],
                                                                         'proxy.xml'))

        # Progress notification
        self.output(f"aacp_proxy_xml_path: {self.env['aacp_proxy_xml_path']}")

        # Try to parse proxy_xml
        try:
            # Set to contents of the xml file at aacp_proxy_xml_path
            parse_xml = ElementTree.parse(self.env['aacp_proxy_xml_path'])
        # If an issue is encountered with parsing the at aacp_proxy_xml_path
        except xml.etree.ElementTree.ParseError as err_msg:
            # Raise
            raise ProcessorError(f"Parsing {self.env['aacp_proxy_xml_path']} failed "
                                 f"with: {err_msg}") from err_msg

        # Get root of xml
        root = parse_xml.getroot()

        # Get app_version
        self.env['aacp_version'] = (root.findtext
                                   ('./InstallerProperties/Property[@name=\'ProductVersion\']'))

        # Progress notification
        self.output(f"aacp_version: {self.env['aacp_version']}")


    def process_adobe_autopkg_application_data(self):
        '''
           Get more details from AdobeAutoPkgApplicationData.json
        '''

        # Var declaration
        self.env['aacp_parent_dir'] = os.path.dirname(os.path.realpath(__file__))
        self.env['aacp_json_path'] = os.path.join(self.env['aacp_parent_dir'],
                                                  'AdobeAutoPkgApplicationData.json')

        # Progress notification
        self.output(f"Processing {self.env['aacp_json_path']}...")

        # Read in AdobeAutoPkgApplicationData.json file
        with open(self.env['aacp_json_path'], encoding='utf-8') as json_file:
            # Try to parse json_file as json, raise if an issue
            try:
                # Set aacp_autopkg_json to the content of json_file
                self.env['aacp_autopkg_json'] = json.load(json_file)
            # If we cannot parse json_file as json
            except json.JSONDecodeError as err_msg:
                # Raise
                raise ProcessorError(f"Parsing {self.env['aacp_autopkg_json']} failed with: "
                                     f"{err_msg}") from err_msg

        # Get applications dict from the json
        for application_data in self.env['aacp_autopkg_json']:
            # If sap_code matches
            if application_data['sap_code'] == self.env['aacp_application_sap_code']:
                # For each version
                for aacp_version_json in application_data['versions'].keys():
                    # Try to get data from the json object
                    try:
                        # If the version matches
                        if aacp_version_json == self.env['aacp_application_base_version']:
                            # Set aacp_matched_json to the matched json object
                            self.env['aacp_matched_json'] = (application_data['versions']
                                                 [self.env['aacp_application_base_version']])
                            # Progress notification
                            self.output(f"aacp_matched_json: {self.env['aacp_matched_json']}")
                    # If we cannot find a matching json object
                    except KeyError as err_msg:
                        # Raise
                        raise ProcessorError(f"Cannot find details for "
                                             f"{self.env['aacp_application_sap_code']} "
                                             f"with version: "
                                             f"{self.env['aacp_application_base_version']},"
                                             f"in {self.env['aacp_json_path']}... "
                                             f"exiting...") from err_msg

        # If we found not found a match
        if 'aacp_matched_json' not in self.env:
            # Raise
            raise ProcessorError(f"Cannot find details for {self.env['aacp_application_sap_code']} "
                                f"with version: {self.env['aacp_application_base_version']}, in"
                                f"{self.env['aacp_json_path']}...")


    def process_hd_installer(self):
        '''
            Process HD installer
        '''

        # Var declaration
        self.env['aacp_blocking_applications'] = []
        self.env['aacp_application_json_path'] = os.path.join(self.env['aacp_root_dir'], 'HD',
                                                                  self.env['aacp_target_folder'],
                                                                  'Application.json')

        # Progress notification
        self.output(f"Processing {self.env['aacp_application_json_path']}...")

        # Read in app_json file
        with open(self.env['aacp_application_json_path'], encoding='utf-8') as json_file:
            # Try to parse app_json as json, raise if an issue
            try:
                # Set to the content of json_file
                app_json = json.load(json_file)
            # If we fail to parse json_file
            except json.JSONDecodeError as err_msg:
                # Raise
                raise ProcessorError(f"Parsing {self.env['aacp_application_json_path']} failed "
                                     f"with: {err_msg}") from err_msg

            # For each Tagline
            for tag_line in app_json["ProductDescription"]["Tagline"]["Language"]:
                # Get the Tagline that matches the aacp_application_install_lang locale
                if tag_line['locale'] == self.env['aacp_application_install_lang']:
                    # Set aacp_application_description to that of the matched locale
                    self.env['aacp_application_description'] = tag_line['value']
                    # If aacp_application_description is missing: .
                    if not self.env['aacp_application_description'].endswith('.'):
                        # Add a . if missing from the end
                        self.env['aacp_application_description'] = (
                                            self.env['aacp_application_description'] + '.')
            # Progress notification
            self.output(f"aacp_application_description: {self.env['aacp_application_description']}")

            # Get conflicting processes
            conflicting_processes = app_json['ConflictingProcesses']['ConflictingProcess']

            # For each conflicting_process in conflicting_processes
            for conflicting_process in conflicting_processes:
                # If forceKillAllowed is not set to False
                if not conflicting_process['forceKillAllowed']:
                    # Add to blocking_applications
                    self.env['aacp_blocking_applications'].append(
                                                conflicting_process['ProcessDisplayName'])

            # If we have my aacp_blocking_applications
            if 'aacp_blocking_applications' in self.env:
                # Sort
                self.env['aacp_blocking_applications'] = sorted(set(
                                                  self.env['aacp_blocking_applications']))
                # Progress notification
                self.output(f"aacp_blocking_applications': "
                            f"{self.env['aacp_blocking_applications']}")

        # Return app_json
        return app_json


    def process_matched_json(self, app_json):
        '''
            Get metadata with the aid of self.env['aacp_matched_json']
        '''

        # Applications version, if not APRO
        if not self.env['aacp_application_sap_code'] == 'APRO':
            # Get version from aacp_matched_json
            self.env['aacp_version'] = (app_json[self.env['aacp_matched_json']
                                                     ['app_json_version_key']])
            # Progress notification
            self.output(f"aacp_version: {self.env['aacp_version']}")

        # If the version is unsupported
        if 'unsupported_versions_dict' in self.env['aacp_matched_json']:
            # Progress notification
            self.output(f"unsupported_versions_dict: "
                        f"{self.env['aacp_matched_json']['unsupported_versions_dict']}")
            # Parse json for the unsupported_versions_dict
            for unsupported_version in self.env['aacp_matched_json']['unsupported_versions_dict']:
                # If the version matches
                if unsupported_version == self.env['aacp_version']:
                    # Raise
                    raise ProcessorError(
            f"{self.env['aacp_matched_json']['unsupported_versions_dict'][unsupported_version]}")

        # Set aacp_application_bundle_id to app_bundle_id
        self.env['aacp_application_bundle_id'] = self.env['aacp_matched_json']['app_bundle_id']

        # Progress notification
        self.output(f"aacp_application_bundle_id: {self.env['aacp_application_bundle_id']}")

        # If APRO
        if self.env['aacp_application_sap_code'] == 'APRO':
            # Get aacp_application_minimum_os from aacp_matched_json
            self.env['aacp_application_minimum_os'] = self.env['aacp_matched_json']['minos_version']
        # If not APRO
        else:
            # Get aacp_application_minimum_os from SystemRequirement
            self.env['aacp_application_minimum_os'] = (re.search(
                                              self.env['aacp_matched_json']['minos_regex'],
                        app_json['SystemRequirement']['CheckCompatibility']['Content'])[1])

        # Progress notification
        self.output(f"aacp_application_minimum_os: {self.env['aacp_application_minimum_os']}")

        # Applications version comparison key
        self.env['aacp_version_compare_key'] = (self.env['aacp_matched_json']
                                                ['version_comparison_key'])

        # Progress notification
        self.output(f"aacp_version_compare_key: {self.env['aacp_version_compare_key']}")

        # Applications display name
        self.env['aacp_application_display_name'] = self.env['aacp_matched_json']['display_name']

        # Progress notification
        self.output(f"aacp_application_display_name: {self.env['aacp_application_display_name']}")

        # Full path to the application bundle on disk, as per Terminal etc, not Finder
        self.env['aacp_application_full_path'] = self.env['aacp_matched_json']['app_path']

        # If description is missing
        if not 'aacp_application_description' in self.env:
            # Get from aacp_matched_json
            self.env['aacp_application_description'] = (self.env['aacp_matched_json']
                                                        ['app_description'])

        # Description doesn't end with a: .
        if not self.env['aacp_application_description'].endswith('.'):
            # Add a . to the description
            self.env['aacp_application_description'] = (self.env['aacp_application_description']
                                                        + '.')
        # Progress notification
        self.output(f"aacp_application_description: {self.env['aacp_application_description']}")

        # If additional_blocking_applications in aacp_matched_json
        if 'additional_blocking_applications' in self.env['aacp_matched_json']:
            # For each additional_blocking_application
            for additional_blocking_application in (self.env['aacp_matched_json']
                                                    ['additional_blocking_applications']):
                # Append to aacp_blocking_applications
                self.env['aacp_blocking_applications'].append(additional_blocking_application)
            # Sort aacp_blocking_applications
            self.env['aacp_blocking_applications'] = (
                sorted(set(self.env['aacp_blocking_applications'])))
            # Progress notification
            self.output(f"aacp_blocking_applications updated: "
                        f"{self.env['aacp_blocking_applications']}")


    def process_optionxml_xml(self):
        '''
            Process the titles optionXML.xml
        '''

        # Progress notification
        self.output(f"Processing: {self.env['aacp_option_xml_path']}...")

        # Try to parse option_xml, raise if an issue
        try:
            # Set to content of aacp_option_xml_path
            option_xml = ElementTree.parse(self.env['aacp_option_xml_path'])
        # If we cannot parse aacp_option_xml_path
        except xml.etree.ElementTree.ParseError as err_msg:
            # Raise
            raise ProcessorError(f"Parsing {self.env['aacp_proxy_xml_path']} failed "
                                 f"with: {err_msg}") from err_msg

        # Check to see if HDMedia keys set
        for hd_media in option_xml.findall('.//HDMedias/HDMedia'):
            # If we have HDMedia, set vars
            if hd_media.findtext('MediaType') == 'Product':
                # Set aacp_application_base_version to baseVersion
                self.env['aacp_application_base_version'] = hd_media.findtext('baseVersion')
                # Set aacp_application_install_lang to installLang
                self.env['aacp_application_install_lang'] = hd_media.findtext('installLang')
                # Set aacp_application_sap_code to SAPCode
                self.env['aacp_application_sap_code'] = hd_media.findtext('SAPCode')
                # Set aacp_target_folder to TargetFolderName
                self.env['aacp_target_folder'] = hd_media.findtext('TargetFolderName')

        # If no HDMedia is found, then self.env['aacp_application_install_lang'] will not exist
        if not 'aacp_application_install_lang' in self.env:
            # Get vars for RIBS media
            for ribs_media in option_xml.findall('.//Medias/Media'):
                # Set aacp_application_base_version to prodVersion
                self.env['aacp_application_base_version'] = ribs_media.findtext('prodVersion')
                # Set aacp_application_install_lang to installLang
                self.env['aacp_application_install_lang'] = ribs_media.findtext('installLang')
                # Set aacp_application_sap_code to SAPCode
                self.env['aacp_application_sap_code'] = ribs_media.findtext('SAPCode')
                # Set aacp_target_folder to TargetFolderName
                self.env['aacp_target_folder'] = ribs_media.findtext('TargetFolderName')

        # Set aacp_application_architecture_type
        self.env['aacp_application_architecture_type'] = (
            option_xml.findtext('ProcessorArchitecture').lower())

        # If aacp_application_architecture_type is not arm64, macuniversal or x64
        if not self.env['aacp_application_architecture_type'] in ['arm64', 'macuniversal', 'x64']:
            # Raise
            raise ProcessorError(f"architecture_type: "
                                 f"{self.env['aacp_application_architecture_type']},"
                                 f"is neither arm64, macuniversal nor x64... exiting...")
        # If aacp_application_architecture_type is x64
        if self.env['aacp_application_architecture_type'] == 'x64':
            # Change to x86_64
            self.env['aacp_application_architecture_type'] = 'x86_64'

        # Progress notification
        self.output(f"aacp_application_sap_code: {self.env['aacp_application_sap_code']}")

        # Progress notification
        self.output(f"aacp_target_folder: {self.env['aacp_target_folder']}")

        # Progress notification
        self.output(f"aacp_application_architecture_type: "
                    f"{self.env['aacp_application_architecture_type']}")

        # Progress notification
        self.output(f"aacp_application_install_lang: {self.env['aacp_application_install_lang']}")

        # Progress notification
        self.output(f"aacp_application_base_version: {self.env['aacp_application_base_version']}")


    # pylint: disable = too-many-branches
    def replace_element(self, some_key):
        '''
            Checks for instances of %var_name% and replaces with the value for the matching
            %var_name%
        '''

        # Var declaration
        re_pattern = '%(.*?)%'

        # If it's a string
        if isinstance(self.env[some_key], str):
            # Check for a match
            re_match = re.search(re_pattern, self.env[some_key])
            # if we have a match
            if re_match:
                # Progress notification
                self.output(f"found: %{re_match[1]}% in {some_key}, looking to replace...")
                # Set the value for some_key
                self.env[some_key] = (self.env[some_key].replace('%' + re_match[1] + '%',
                                      self.env[re_match[1]]))
                # Progress notification
                self.output(f"{some_key} is now {self.env[some_key]}...")
        # If a dict
        elif isinstance(self.env[some_key], dict):
            # For each key
            for sub_key in self.env[some_key]:
                # Check for a match
                re_match = re.search('%(.*?)%', self.env[some_key][sub_key])
                # if we have a match
                if re_match:
                    # Progress notification
                    self.output(f"found: %{re_match[1]}% in {sub_key} from {some_key}, "
                                 "looking to replace...")
                    # Set the value for [some_key][sub_key]
                    self.env[some_key][sub_key] = (self.env[some_key][sub_key].replace('%' +
                                                   re_match[1] + '%', self.env[re_match[1]]))
                    # Progress notification
                    self.output(f"{sub_key} in {some_key} is now {self.env[some_key][sub_key]}...")
        # If a list
        elif isinstance(self.env[some_key], list):
            # For each item in the list
            for list_item in self.env[some_key]:
                # If it's a string
                if isinstance(list_item, str):
                    # Check for a match
                    re_match = re.search(re_pattern, list_item)
                    # if we have a match
                    if re_match:
                        # Progress notification
                        self.output(f"found: %{re_match[1]}% in {list_item}, looking to replace...")
                        # Set the value for [some_key][list_item]
                        self.env[some_key][list_item] = self.env[some_key][list_item].replace('%' +
                                                        re_match[1] + '%', self.env[re_match[1]])
                        # Progress notification
                        self.output(f"{list_item} is now {self.env[some_key][list_item]}...")
                # If a dict
                elif isinstance(list_item, dict):
                    # For each sub_item
                    for sub_item in self.env[some_key][list_item]:
                        # check for a match
                        re_match = re.search('%(.*?)%', self.env[some_key][list_item])
                        # if we have a match
                        if re_match:
                            # Progress notification
                            self.output(f"found: %{re_match[1]}% in {sub_item} from {list_item}, "
                                         "looking to replace...")
                            # Set the value for [some_key][list_item]
                            self.env[some_key][list_item] = (
                                self.env[some_key][list_item].replace('%' + re_match[1] + '%',
                                self.env[re_match[1]]))
                            # Progress notification
                            self.output(f"{sub_item} in {list_item} is now "
                                        f"{self.env[some_key][list_item]}...")
                # If a type we're not to process
                else:
                    # Progress notification
                    self.output(f"{some_key} is {type(self.env[some_key])}, processing skipped..")
        # If a type we're not to process
        else:
            ## Progress notification
            self.output(f"{some_key} is {type(self.env[some_key])}, processing skipped..")


    def update_override(self):
        '''
            Update the override by adding all aacp prefixed keys to the override, to assist with
            troubleshooting.
        '''

        # Progress notification
        self.output(f"Updating: {self.env['aacp_override_path']}...")

        # Var declaration
        aacp_vars = {}

        # For each key in self.env
        for some_key in self.env:
            # For keys beginning with aacp_ and isn't aacp_autopkg_json
            if some_key.startswith('aacp_') and some_key != 'aacp_autopkg_json':
                # Add to aacp
                aacp_vars[some_key] = self.env[some_key]

        # If a yaml file
        if (self.env['aacp_override_path'].endswith('.yml') or
                self.env['aacp_override_path'].endswith('.yaml')):
            # Try to read it as yaml
            try:
                # Open yaml file, to read
                with (open(self.env['aacp_override_path'], 'r', encoding = 'utf-8') as
                  read_file):
                    # Create var from the overrides contents
                    override_content = yaml.safe_load(read_file)
                # Remove ['Input']['aacp_override_path'], as in ['aacp vars']
                del override_content['Input']['aacp_override_path']
                # Remove ['Input']['aacp_package_path'], as in ['aacp vars']
                del override_content['Input']['aacp_package_path']
                # Remove ['Input']['aacp_package_type'], as in ['aacp vars']
                del override_content['Input']['aacp_package_type']
                # Add aacp_vars dict
                override_content['aacp_vars'] = aacp_vars
                # Open yaml file, to write
                with (open (self.env['aacp_override_path'], 'w', encoding = 'utf-8') as
                  write_file):
                    # Write the updated content to the override
                    yaml.dump(override_content, write_file, default_flow_style=False)
            # Raise an exception if the override cannot be parsed
            except yaml.scanner.ScannerError as err_msg:
                # Raise
                raise ProcessorError(f"ERROR: Reading, \"{self.env['aacp_override_path']}\" "
                                     f"errored with: {err_msg}") from err_msg
        # If not a .yaml override
        else:
            # Try to read in the file as a plist
            try:
                # Open plist file, to read
                with open(self.env['aacp_override_path'], 'rb') as read_file:
                    # Create var from the overrides contents
                    override_content = plistlib.load(read_file)
                # Remove ['Input']['aacp_override_path'], as in ['aacp vars']
                del override_content['Input']['aacp_override_path']
                # Remove ['Input']['aacp_package_path'], as in ['aacp vars']
                del override_content['Input']['aacp_package_path']
                # Remove ['Input']['aacp_package_type'], as in ['aacp vars']
                del override_content['Input']['aacp_package_type']
                # Add aacp_vars dict
                override_content['aacp_vars'] = aacp_vars
                # Open the override for writing
                with open(self.env['aacp_override_path'], 'wb') as write_file:
                    # Write the updated content to the override
                    plistlib.dump(override_content, write_file)
            # Raise an exception if the override cannot be parsed
            except plistlib.InvalidFileException as err_msg:
                # Raise
                raise ProcessorError(f"ERROR: Reading, \"{self.env['aacp_override_path']}\" "
                                     f"errored with: {err_msg}")  from err_msg


if __name__ == '__main__':
    PROCESSOR = AdobeAdminConsolePackagesPkgInfoCreator()
    PROCESSOR.execute_shell()

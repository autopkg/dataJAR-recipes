#!/usr/local/autopkg/python
# pylint: disable = invalid-name
'''
Copyright (c) 2022, dataJAR Ltd.  All rights reserved.
     Redistribution and use in source and binary forms, with or without
     modification, are permitted provided that the following conditions are met:
             * Redistributions of source code must retain the above copyright
               notice, this list of conditions and the following disclaimer.
             * Redistributions in binary form must reproduce the above copyright
               notice, this list of conditions and the following disclaimer in the
               documentation and/or other materials provided with the distribution.
             * Neither data JAR Ltd nor the names of its contributors may be used to
               endorse or promote products derived from this software without specific
               prior written permission.
     THIS SOFTWARE IS PROVIDED BY DATA JAR LTD 'AS IS' AND ANY
     EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
     WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
     DISCLAIMED. IN NO EVENT SHALL DATA JAR LTD BE LIABLE FOR ANY
     DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
     (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
     LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
     ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
     (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
     SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
SUPPORT FOR THIS PROGRAM
    This program is distributed 'as is' by DATA JAR LTD.
    For more information or support, please utilise the following resources:
            http://www.datajar.co.uk

DESCRIPTION

Generates installation information for Adobe Admin Console Packages
'''

# Standard Imports
import json
import os
import re
import xml
from xml.etree import ElementTree


# AutoPkg imports
# pylint: disable = import-error
from autopkglib import (Processor,
                        ProcessorError)


# Define class
__all__ = ['AdobeAdminConsolePackagesPkgInfoCreator']
__version__ = ['1.0']


# Class def
class AdobeAdminConsolePackagesPkgInfoCreator(Processor):
    '''
       Parses generated Adobe Admin Console Packages to generate installation information.
    '''

    description = __doc__

    input_variables = {
    }

    output_variables = {
        'aacp_application_architecture_type': {
            'description': 'The architecture type for the title, either arm64 or x86_64',
        },
        'aacp_application_bundle_id': {
            'description': 'Value of the titles CFBundleIdentifier.',
        },
        'aacp_application_description': {
            'description': 'Short description of the title.',
        },
        'aacp_application_display_name': {
            'description': 'Display name of the title.',
        },
        'aacp_application_full_path': {
            'description': 'Full path to the application bundle on disk, as per Terminal etc, not Finder.',
        },
        'aacp_application_install_lang': {
            'description': 'The titles installation langauage.',
        },
        'aacp_application_json_path': {
            'description': 'Path to the tiles Application.json file.',
        },
        'aacp_application_major_version': {
            'description': 'The major version of the title.',
        },
        'aacp_application_sap_code': {
            'description': 'The titles sap code.',
        },
        'aacp_blocking_applications': {
            'description': 'Sorted set of the conflicting processes.',
        },
        'aacp_install_pkg_path': {
            'description': 'Path to the Adobe*_Install.pkg.',
        },
        'aacp_json_path': {
            'description': 'Path to AdobeAutoPkgApplicationData.json.',
        },
        'aacp_matched_json': {
            'description': ('dict from AdobeAutoPkgApplicationData.json, which matches the '
                            '"aacp_application_sap_code" and "aacp_application_major_version".'),
        },
        'aacp_option_xml_path': {
            'description': 'Path to the tiles optionXML.xml file.',
        },
        'aacp_parent_dir': {
            'description': 'Path to parent directory of this processor.',
        },
        'aacp_proxy_xml_path': {
            'description': 'Acrobat only, path to proxy.xml.',
        },
        'aacp_target_folder': {
            'description': 'The name of the folder within the pkg to check files for metadata.',
        },
        'aacp_uninstall_pkg_path': {
            'description': 'Path to the Adobe*_Uninstall.pkg.',
        },
        'additional_pkginfo': {
            'description':
                'Additonal pkginfo fields extracted from the Adobe metadata.',
        },
        'version': {
            'description': 'The titles version.',
        }
    }


    def main(self):
        '''
            Find the Adobe*_Install.pkg in the Downloads dir based on the name, raise
            if corresponding *_Uninstall.pkg is missing.
        '''

        # Progress notification
        self.output("Starting versioner process...")

        # Get set packages_path
        self.env['aacp_packages_path'] = os.path.expanduser('~/Downloads/')
        self.output(f"aacp_packages_path: {self.env['aacp_packages_path']}")

        # Check that packages_path exists
        if not os.path.exists(self.env['aacp_packages_path']):
            raise ProcessorError(f"ERROR: Cannot locate directory, "
                                 f"{self.env['aacp_packages_path']}... exiting...")

        # Check that packages_path is a directory
        if not os.path.isdir(self.env['aacp_packages_path']):
            raise ProcessorError(f"ERROR: {self.env['aacp_packages_path']} is a not a "
                                  "directory... exiting...")

        # Path to Adobe*_Install.pkg
        self.env['aacp_install_pkg_path'] = (os.path.join(self.env['aacp_packages_path'],
                                                          self.env['NAME'], 'Build',
                                                          self.env['NAME'] + '_Install.pkg'))

        # Check that the path exists, raise if not
        if not os.path.exists(self.env['aacp_install_pkg_path']):
            raise ProcessorError(f"ERROR: Cannot find "
                                 f"{self.env['aacp_install_pkg_path']}... exiting...")
        self.output(f"aacp_install_pkg_path: {self.env['aacp_install_pkg_path']}")

        # Path to Adobe*_Uninstall.pkg
        self.env['aacp_uninstall_pkg_path'] = (os.path.join(self.env['aacp_packages_path'],
                                                            self.env['NAME'], 'Build',
                                                            self.env['NAME'] + '_Uninstall.pkg'))

        # Check that the path exists, raise if not
        if not os.path.exists(self.env['aacp_uninstall_pkg_path']):
            raise ProcessorError(f"ERROR: Cannot find {self.env['aacp_uninstall_pkg_path']}, these "
                                 f"recipes need packages of the Managed Package variety, which "
                                 f"include _Install and _Uninstall packages.... exiting...")
        self.output(f"aacp_uninstall_pkg_path {self.env['aacp_uninstall_pkg_path']}")

        # Process the titles optionXML.xml
        self.process_optionxml_xml()


    def process_optionxml_xml(self):
        '''
            Process the titles optionXML.xml
        '''

        # Var declaration
        self.env['aacp_application_install_lang'] = None

        # Path to titles optionXML.xml
        self.env['aacp_option_xml_path'] = os.path.join(self.env['aacp_install_pkg_path'],
                                                        'Contents', 'Resources', 'optionXML.xml')
        if not os.path.exists(self.env['aacp_option_xml_path']):
            raise ProcessorError(f"ERROR: Cannot find {self.env['aacp_option_xml_path']}... "
                                  "exiting...")
        self.output(f"aacp_option_xml_path: {self.env['aacp_option_xml_path']}")

        # Progress notification
        self.output(f"Processing: {self.env['aacp_option_xml_path']}...")

        # Try to parse option_xml, raise if an issue
        try:
            option_xml = ElementTree.parse(self.env['aacp_option_xml_path'])
        except xml.etree.ElementTree.ParseError as err_msg:
            raise ProcessorError from err_msg

        # Check to see if HDMedia keys set
        for hd_media in option_xml.findall('.//HDMedias/HDMedia'):
            # If we have HDMedia, set vars
            if hd_media.findtext('MediaType') == 'Product':
                self.env['aacp_application_install_lang'] = hd_media.findtext('installLang')
                self.env['aacp_application_sap_code'] = hd_media.findtext('SAPCode')
                self.env['aacp_target_folder'] = hd_media.findtext('TargetFolderName')
                self.env['aacp_application_major_version'] = hd_media.findtext('baseVersion')

        # If no HDMedia is found, then self.env['aacp_application_install_lang'] will be none
        if not self.env['aacp_application_install_lang']:
            # Get vars for RIBS media
            for ribs_media in option_xml.findall('.//Medias/Media'):
                self.env['aacp_application_install_lang'] = ribs_media.findtext('installLang')
                self.env['aacp_application_sap_code'] = ribs_media.findtext('SAPCode')
                self.env['aacp_target_folder'] = ribs_media.findtext('TargetFolderName')
                self.env['aacp_application_major_version'] = ribs_media.findtext('prodVersion')

        # Check for Processor Architecture
        self.env['aacp_application_architecture_type'] = (
            option_xml.findtext('ProcessorArchitecture').lower())
        if not self.env['aacp_application_architecture_type'] in ['arm64', 'macuniversal', 'x64']:
            raise ProcessorError(f"architecture_type: "
                                 f"{self.env['aacp_application_architecture_type']},"
                                 f" is neither arm64, macuniversal nor x64... exiting...")
        if self.env['aacp_application_architecture_type'] == 'x64':
            self.env['aacp_application_architecture_type'] = 'x86_64'

        # Display progress
        self.output(f"aacp_application_sap_code: {self.env['aacp_application_sap_code']}")
        self.output(f"aacp_target_folder: {self.env['aacp_target_folder']}")
        self.output(f"aacp_application_architecture_type: "
                    f"{self.env['aacp_application_architecture_type']}")
        self.output(f"aacp_application_install_lang: {self.env['aacp_application_install_lang']}")
        self.output(f"aacp_application_major_version: {self.env['aacp_application_major_version']}")

        # If the we're looking at Acrobat, then we need to process things differently
        if self.env['aacp_application_sap_code'] == 'APRO':
            self.process_apro_installer()
        else:
            # Set application_json_path
            self.env['aacp_application_json_path'] = os.path.join(self.env['aacp_install_pkg_path'],
                                                                  'Contents/Resources/HD',
                                                                  self.env['aacp_target_folder'],
                                                                  'Application.json')
            # Process HD installer
            self.process_hd_installer()


    def process_apro_installer(self):
        '''
            Process APRO (Acrobat) installer
        '''

        # Progress notification
        self.output("Processing Acrobat installer")
        self.env['aacp_proxy_xml_path'] = (os.path.join(self.env['aacp_install_pkg_path'],
                                                        'Contents/Resources/Setup',
                                                        self.env['aacp_target_folder'],
                                                        'proxy.xml'))
        self.output(f"aacp_proxy_xml_path: {self.env['aacp_proxy_xml_path']}")

        # Try to parse proxy_xml, raise if an issue
        try:
            parse_xml = ElementTree.parse(self.env['aacp_proxy_xml_path'])
        except xml.etree.ElementTree.ParseError as err_msg:
            raise ProcessorError from err_msg

        # Get root of xml
        root = parse_xml.getroot()

        # Get app_version
        self.env['version'] = (root.findtext
                                   ('./InstallerProperties/Property[@name=\'ProductVersion\']'))
        self.output(f"version: {self.env['version']}")

        # Set to []
        self.env['aacp_blocking_applications'] = []

        # 2nd part of process
        self.process_adobe_autopkg_application_data(None)


    def process_hd_installer(self):
        '''
            Process HD installer
        '''

        # Var declaration
        blocking_applications = []

        # Progress notification
        self.output(f"Processing {self.env['aacp_application_json_path']}...")

        # Read in app_json file
        with open(self.env['aacp_application_json_path'], encoding='utf-8') as json_file:
            # Try to parse app_json as json, raise if an issue
            try:
                load_json = json.load(json_file)
            except json.JSONDecodeError as err_msg:
                raise ProcessorError from err_msg

            # Get description
            tag_lines = load_json["ProductDescription"]["Tagline"]["Language"]
            for tag_line in tag_lines:
                if tag_line['locale'] == self.env['aacp_application_install_lang']:
                    self.env['aacp_application_description'] = tag_line['value']
                    # Add a . if missing from the end
                    if not self.env['aacp_application_description'].endswith('.'):
                        self.env['aacp_application_description'] = (
                                            self.env['aacp_application_description'] + '.')
                    self.output(f"aacp_application_description: "
                                f"{self.env['aacp_application_description']}")

            # Get conflicting processes
            conflicting_processes = load_json['ConflictingProcesses']['ConflictingProcess']
            for conflicting_process in conflicting_processes:
                # Only add if forceKillAllowed is False
                if not conflicting_process['forceKillAllowed']:
                    blocking_applications.append(conflicting_process['ProcessDisplayName'])
            if blocking_applications:
                self.env['aacp_blocking_applications'] = sorted(set(blocking_applications))
                self.output(f"aacp_blocking_applications: "
                            f"{self.env['aacp_blocking_applications']}")

            # 2nd part of process
            self.process_adobe_autopkg_application_data(load_json)


    def process_adobe_autopkg_application_data(self, load_json):
        '''
           Get more details from AdobeAutoPkgApplicationData.json
        '''

        # var declaration
        self.env['aacp_matched_json'] = None

        # Get this scripts parent directory
        self.env['aacp_parent_dir'] = os.path.dirname(os.path.realpath(__file__))
        self.output(f"aacp_parent_dir: {self.env['aacp_parent_dir']}")

        # Get the path to AdobeAutoPkgApplicationData.json
        self.env['aacp_json_path'] = os.path.join(self.env['aacp_parent_dir'],
                                                  'AdobeAutoPkgApplicationData.json')
        self.output(f"aacp_json_path: {self.env['aacp_json_path']}")

        # Progress notification
        self.output(f"Processing {self.env['aacp_json_path']}...")

        # Read in AdobeAutoPkgApplicationData.json file
        with open(self.env['aacp_json_path'], encoding='utf-8') as json_file:
            # Try to parse app_json as json, raise if an issue
            try:
                self.env['aacp_autopkg_json'] = json.load(json_file)
            except json.JSONDecodeError as err_msg:
                raise ProcessorError from err_msg

        # Get applications dict from the json
        for application_data in self.env['aacp_autopkg_json']:
            if application_data['sap_code'] == self.env['aacp_application_sap_code']:
                for aacp_version_json in application_data['versions'].keys():
                    try:
                        if aacp_version_json == self.env['aacp_application_major_version']:
                            self.env['aacp_matched_json'] = (application_data['versions']
                                                 [self.env['aacp_application_major_version']])
                            self.output(f"aacp_matched_json: {self.env['aacp_matched_json']}")
                    except KeyError as err_msg:
                        raise ProcessorError(f"Cannot find details for "
                                             f"{self.env['aacp_application_sap_code']} "
                                             f"with version: "
                                             f"{self.env['aacp_application_major_version']},"
                                             f" in {self.env['aacp_json_path']}... "
                                             f"exiting...") from err_msg

        # If we found a match
        if self.env['aacp_matched_json']:
            self.process_matched_json(load_json)
        else:
            raise ProcessorError("Cannot find details for "
                                f"{self.env['aacp_application_sap_code']} "
                                f"with version: {self.env['aacp_application_major_version']},"
                                f" in {self.env['aacp_json_path']}...")


    def process_matched_json(self, load_json):
        '''
            Get metadata with the aid of self.env['aacp_matched_json']
        '''
        # Applications version, if not APRO
        if not self.env['aacp_application_sap_code'] == 'APRO':
            self.env['version'] = load_json[self.env['aacp_matched_json']['app_json_version_key']]
            self.output(f"version: {self.env['version']}")

        # If the version is unsupported
        if 'unsupported_versions_dict' in self.env['aacp_matched_json']:
            self.output(f"unsupported_versions_dict: "
                        f"{self.env['aacp_matched_json']['unsupported_versions_dict']}")
            for unsupported_version in self.env['aacp_matched_json']['unsupported_versions_dict']:
                if unsupported_version == self.env['version']:
                    raise ProcessorError(
            f"{self.env['aacp_matched_json']['unsupported_versions_dict'][unsupported_version]}")

        # Applications bundle id
        self.env['aacp_application_bundle_id'] = self.env['aacp_matched_json']['app_bundle_id']
        self.output(f"aacp_application_bundle_id: {self.env['aacp_application_bundle_id']}")

        # Applications minimum os, if APRO get from self.env['aacp_matched_json']
        if not self.env['aacp_application_sap_code'] == 'APRO':
            self.env['aacp_application_minimum_os'] = (re.search(self.env['aacp_matched_json']
                                                                 ['minos_regex'],
                                                                 load_json['SystemRequirement']
                                                                 ['CheckCompatibility']
                                                                 ['Content'])[1])
            self.output(f"aacp_application_minimum_os: {self.env['aacp_application_minimum_os']}")
        else:
            self.env['aacp_application_minimum_os'] = self.env['aacp_matched_json']['minos_version']

        # Applications version comparison key
        self.env['aacp_version_compare_key'] = (self.env['aacp_matched_json']
                                                ['version_comparison_key'])
        self.output(f"aacp_version_compare_key: {self.env['aacp_version_compare_key']}")

        # Applications display name
        self.env['aacp_application_display_name'] = self.env['aacp_matched_json']['display_name']
        self.output(f"aacp_application_display_name: {self.env['aacp_application_display_name']}")

        # Full path to the application bundle on disk, as per Terminal etc, not Finder
        self.env['aacp_application_full_path'] = self.env['aacp_matched_json']['app_path']

        # Get description if missing:
        if not 'aacp_application_description' in self.env:
            self.env['aacp_application_description'] = (self.env['aacp_matched_json']
                                                        ['app_description'])
            self.output(f"aacp_application_description: description missing, set from "
                        f"aacp_matched_json: "
                        f"{self.env['aacp_application_description']}")
        # Add a . if missing from the end
        if not self.env['aacp_application_description'].endswith('.'):
            self.env['aacp_application_description'] = (self.env['aacp_application_description']
                                                        + '.')

        # Get additional_blocking_applications
        if 'additional_blocking_applications' in self.env['aacp_matched_json']:
            for additional_blocking_application in (self.env['aacp_matched_json']
                                                    ['additional_blocking_applications']):
                self.env['aacp_blocking_applications'].append(additional_blocking_application)
            self.env['aacp_blocking_applications'] = (
                sorted(set(self.env['aacp_blocking_applications'])))
            self.output(f"aacp_blocking_applications updated: "
                        f"{self.env['aacp_blocking_applications']}")

        # Now we have the deets, let's use them
        self.create_pkginfo()


    def create_pkginfo(self):
        '''
            Create pkginfo with found details
        '''

        # var declaration
        pkginfo = {}

        # Set pkginfo variables
        if (self.env['aacp_application_architecture_type'] and
            not self.env['aacp_application_architecture_type'] == 'macuniversal'):
            pkginfo['supported_architectures'] = [self.env['aacp_application_architecture_type']]

        if self.env['aacp_application_description']:
            pkginfo['description'] = self.env['aacp_application_description']

        if self.env['aacp_application_display_name']:
            pkginfo['display_name'] = self.env['aacp_application_display_name']

        if self.env['aacp_blocking_applications']:
            pkginfo['blocking_applications'] = self.env['aacp_blocking_applications']

        if self.env['aacp_application_minimum_os']:
            pkginfo['minimum_os_version'] = self.env['aacp_application_minimum_os']

        # Check for any var replacements
        for some_key in self.env:
            # only process the keys beginning with aacp_ and those not ending _json
            if some_key.startswith('aacp_') and not some_key.endswith('_json'):
                self.replace_element(some_key)

        # Create pkginfo is missing from installs array
        #if 'pkginfo' not in self.env or 'installs' not in self.env['pkginfo']:
        pkginfo['installs'] = [{
            'CFBundleIdentifier': self.env['aacp_application_bundle_id'],
            self.env['aacp_version_compare_key']: self.env['version'],
            'path': self.env['aacp_application_full_path'],
            'type': 'application',
            'version_comparison_key': self.env['aacp_version_compare_key']
        }]

        # Notify of additional_pkginfo
        self.env['additional_pkginfo'] = pkginfo
        self.output(f"additional_pkginfo: {self.env['additional_pkginfo']}")


    # pylint: disable = too-many-branches
    def replace_element(self, some_key):
        '''
            Checks for instances of %var_name% and replaces with the value for the matching
            %var_name%
        '''

        # regex pattern
        re_pattern = '%(.*?)%'

        # If it's a string
        if isinstance(self.env[some_key], str):
            # check for a match
            re_match = re.search(re_pattern, self.env[some_key])
            # if we have a match
            if re_match:
                self.output(f"found: %{re_match[1]}% in {some_key}, looking to replace...")
                self.env[some_key] = (self.env[some_key].replace('%' + re_match[1] + '%',
                                      self.env[re_match[1]]))
                self.output(f"{some_key} is now {self.env[some_key]}...")
        # If a dict
        elif isinstance(self.env[some_key], dict):
            for sub_key in self.env[some_key]:
                # check for a match
                re_match = re.search('%(.*?)%', self.env[some_key][sub_key])
                # if we have a match
                if re_match:
                    self.output(f"found: %{re_match[1]}% in {sub_key} from {some_key}, "
                                 "looking to replace...")
                    self.env[some_key][sub_key] = (self.env[some_key][sub_key].replace('%' +
                                                   re_match[1] + '%', self.env[re_match[1]]))
                    self.output(f"{sub_key} in {some_key} is now {self.env[some_key][sub_key]}...")
        elif isinstance(self.env[some_key], list):
            for list_item in self.env[some_key]:
                # If it's a string
                if isinstance(list_item, str):
                    # check for a match
                    re_match = re.search(re_pattern, list_item)
                    # if we have a match
                    if re_match:
                        self.output(f"found: %{re_match[1]}% in {list_item}, looking to replace...")
                        self.env[some_key][list_item] = self.env[some_key][list_item].replace('%' +
                                                        re_match[1] + '%', self.env[re_match[1]])
                        self.output(f"{list_item} is now {self.env[some_key][list_item]}...")
                elif isinstance(list_item, dict):
                    for sub_item in self.env[some_key][list_item]:
                        # check for a match
                        re_match = re.search('%(.*?)%', self.env[some_key][list_item])
                        # if we have a match
                        if re_match:
                            self.output(f"found: %{re_match[1]}% in {sub_item} from {list_item}, "
                                         "looking to replace...")
                            self.env[some_key][list_item] = (
                                self.env[some_key][list_item].replace('%' + re_match[1] + '%',
                                self.env[re_match[1]]))
                            self.output(f"{sub_item} in {list_item} is now "
                                        f"{self.env[some_key][list_item]}...")
                else:
                    self.output(f"{some_key} is {type(self.env[some_key])}, processing skipped..")
        else:
            self.output(f"{some_key} is {type(self.env[some_key])}, processing skipped..")



if __name__ == '__main__':
    PROCESSOR = AdobeAdminConsolePackagesPkgInfoCreator()

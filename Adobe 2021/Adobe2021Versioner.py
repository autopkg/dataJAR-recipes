#!/usr/local/autopkg/python
# pylint: disable = invalid-name
'''
Copyright (c) 2021, dataJAR Ltd.  All rights reserved.
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

See docstring for AdobeCC2021Versioner class

'''

# Standard Imports
from __future__ import absolute_import
import json
import os
import re
import xml
import zipfile
from xml.etree import ElementTree


# AutoPkg imports
# pylint: disable = import-error
try:
    from plistlib import loads as load_plist
except ImportError:
    from FoundationPlist import readPlistFromString as load_plist
from autopkglib import Processor, ProcessorError


# Define class
__all__ = ['Adobe2021Versioner']
__version__ = ['1.4.7']


# Class def
class Adobe2021Versioner(Processor):
    '''
       Parses generated Adobe Admin Console 2021 pkgs for
       detailed application path and bundle version info.
    '''

    description = __doc__

    input_variables = {

    }

    output_variables = {
        'additional_pkginfo': {
            'description':
                'Some pkginfo fields extracted from the Adobe metadata.',
        },
        'jss_inventory_name': {
            'description': 'Application title for jamf pro smart group criteria.',
        },
        'version': {
            'description': ('The value of CFBundleShortVersionString for the app bundle. '
                            'This may match user_facing_version, but it may also be more '
                            'specific and add another version component.'),
        },
        'architecture_type': {
            'description': ('The value of ProcessorArchitecture for the package. '
                            'This is either -Intel or -ARM to add with renaming the '
                            'package disk image'),
        },
    }


    def main(self):
        '''
            Find the Adobe*_Install.pkg in the Downloads dir based on the name, raise
            if corresponding *_Uninstall.pkg is missing.

            Then determine a pkginfo, version and jss inventory name from the Adobe*_Install.pkg
        '''

        # var declaration
        download_path = os.path.expanduser('~/Downloads')
        install_lang = None

        # Path to Adobe*_Install.pkg in the titles Downloads folder
        self.env['PKG'] = (os.path.join(download_path, self.env['NAME'], 'Build',
                                        self.env['NAME'] + '_Install.pkg'))
        self.output("install_pkg {}".format(self.env['PKG']))

        # Path to Adobe*_Uninstall.pkg n the titles Downloads folder
        self.env['uninstaller_pkg_path'] = (os.path.join(download_path, self.env['NAME'], 'Build',
                                                         self.env['NAME'] + '_Uninstall.pkg'))
        self.output("uninstall_pkg {}".format(self.env['uninstaller_pkg_path']))

        # Path to titles optionXML.xml
        option_xml_path = os.path.join(self.env['PKG'], 'Contents', 'Resources', 'optionXML.xml')
        self.output("Processing {}".format(option_xml_path))

        # Try to parse option_xml, raise if an issue
        try:
            option_xml = ElementTree.parse(option_xml_path)
        except xml.etree.ElementTree.ParseError as err_msg:
            raise ProcessorError("Failed to read {}: {}".format(option_xml_path, err_msg))

        # Check to see if HDMedia keys set
        for hd_media in option_xml.findall('.//HDMedias/HDMedia'):
            # If we have HDMedia, set vars
            if hd_media.findtext('MediaType') == 'Product':
                install_lang = hd_media.findtext('installLang')
                self.env['sap_code'] = hd_media.findtext('SAPCode')
                self.env['target_folder'] = hd_media.findtext('TargetFolderName')

        # Check for Processor Architecture
        self.env['architecture_type'] = option_xml.findtext('ProcessorArchitecture')

        # If no HDMedia is found, then install_lang will be none
        if install_lang is None:
            # Get vars for RIBS media
            for ribs_media in option_xml.findall('.//Medias/Media'):
                install_lang = ribs_media.findtext('installLang')
                self.env['sap_code'] = ribs_media.findtext('SAPCode')
                self.env['target_folder'] = ribs_media.findtext('TargetFolderName')

        # Display progress
        self.output("sap_code: {}".format(self.env['sap_code']))
        self.output("target_folder: {}".format(self.env['target_folder']))
        self.output("architecture_type: {}".format(self.env['architecture_type']))

        # Get app_json var
        self.env['app_json'] = os.path.join(self.env['PKG'], 'Contents/Resources/HD', \
                                       self.env['target_folder'], 'Application.json')

        # If Application.json exists, we're looking at a HD installer
        if os.path.exists(self.env['app_json']):
            if not self.env['sap_code'] == 'APRO':
                # Process HD installer
                self.process_hd_installer_pt1()
        else:
            # If not a HD installer Acrobat is a 'current' title with a
            # RIBS PKG installer we can extract needed metadata from
            self.env['proxy_xml'] = (os.path.join(self.env['PKG'], 'Contents/Resources/Setup',
                                                  self.env['target_folder'], 'proxy.xml'))
            # If proxy_xml does not exist, raise
            if not os.path.exists(self.env['proxy_xml']):
                raise ProcessorError("APRO selected, proxy.xml not found at: {}"
                                     .format(self.env['proxy_xml']))
            # Else, process the APRO (Acrobat) installer
            self.process_apro_installer()


    def process_apro_installer(self):
        '''
            Process APRO (Acrobat) installer
        '''

        # Progress notification
        self.output("Processing Acrobat installer")
        self.output("proxy_xml: {}".format(self.env['proxy_xml']))

        # Try to parse proxy_xml, raise if an issue
        try:
            parse_xml = ElementTree.parse(self.env['proxy_xml'])
        except xml.etree.ElementTree.ParseError as err_msg:
            raise ProcessorError("Failed to read {}: {}".format(self.env['proxy_xml'],
                                                                err_msg))

        # Get root of xml
        root = parse_xml.getroot()

        # Get app_bundle
        app_bundle_text = (root.findtext
                           ('./ThirdPartyComponent/Metadata/Properties/Property[@name=\'path\']'))
        self.env['app_bundle'] = app_bundle_text.split('/')[1]
        self.output("app_bundle: {}".format(self.env['app_bundle']))

        # Get app_path
        app_path_text = root.findtext('./InstallDir/Platform')
        self.env['app_path'] = app_path_text.split('/')[1]
        self.output("app_path: {}".format(self.env['app_path']))

        # Get generic keys
        self.get_generic_keys()

        # Get app_version
        self.env['app_version'] = root.findtext('./InstallerProperties/Property[@name=\'ProductVersion\']')
        self.output("app_version: {}".format(self.env['app_version']))

        # Get vers_compare_key
        self.env['vers_compare_key'] = 'CFBundleShortVersionString'
        self.output("vers_compare_key: {}".format(self.env['vers_compare_key']))

        # Set bundle id
        self.env['app_bundle_id'] = 'com.adobe.Acrobat.Pro'
        self.output("app_bundle_id: {}".format(self.env['app_bundle_id']))

        # Create pkginfo with found details
        self.create_pkginfo()


    def process_hd_installer_pt1(self):
        '''
            Process HD installer - part 1
        '''

        # Progress notification
        self.output("Processing HD installer")

        # Read in app_json file
        with open(self.env['app_json']) as json_file:

            # Try to parse app_json as json, raise if an issue
            try:
                load_json = json.load(json_file)
            except json.JSONDecodeError as err_msg:
                raise ProcessorError("Failed to parse {}: {}".format(self.env['app_json'],
                                                                     err_msg))

            # Get app_launch
            app_launch = load_json['AppLaunch']
            self.output("app_launch: {}".format(app_launch))

            # Get app_details, app_bundle and app_path
            app_details = list(re.split('/', app_launch))
            if app_details[2].endswith('.app'):
                app_bundle = app_details[2]
                app_path = app_details[1]
            else:
                app_bundle = app_details[1]
                app_path = list(re.split('/', (load_json['InstallDir']['value'])))[1]

            # Get app_bundle
            self.env['app_bundle'] = app_bundle
            self.output("app_bundle: {}".format(self.env['app_bundle']))

            # Get app_path
            self.env['app_path'] = app_path
            self.output("app_path: {}".format(self.env['app_path']))

            # Get generic keys
            self.get_generic_keys()

            # 2nd part of process
            self.process_hd_installer_pt2(load_json)


    def process_hd_installer_pt2(self, load_json):
        '''
            Process HD installer - part 2
        '''

        # Get name of the zip_file were to open
        zip_file = load_json['Packages']['Package'][0]['PackageName']
        self.output("zip_file: {}".format(zip_file))

        # Get pimx_dir
        if zip_file.endswith('-LearnPanel'):
            zip_file = load_json['Packages']['Package'][1]['PackageName']
            pimx_dir = '2'
        else:
            pimx_dir = '1'
        self.output("pimx_dir: {}".format(pimx_dir))

        # Get zip_path
        zip_path = (os.path.join(self.env['PKG'], 'Contents/Resources/HD',
                                 self.env['target_folder'], zip_file + '.zip'))
        self.output("zip_path: {}".format(zip_path))

        # Open zip file, raise if fails
        try:
            with zipfile.ZipFile(zip_path, mode='r') as my_zip:
                # Read in pimx file
                with my_zip.open(zip_file + '.pimx') as my_txt:
                    # Read in pimx file
                    pimx_txt = my_txt.read()
                    # Try to parse pimx file as XML, raise exception if fails
                    try:
                        xml_tree = ElementTree.fromstring(pimx_txt)
                        # Try to read info.plist from within zip_bundle
                        self.read_info_plist(my_zip, pimx_dir, xml_tree, zip_path)
                    # If we cannot read in the pimx
                    except xml.etree.ElementTree.ParseError as err_msg:
                        self.output("Parsing {} failed with: {}, checking {}"
                                    .format(zip_file, err_msg, self.env['app_json']))
                        # Read in values from app_json
                        self.parse_app_json(load_json)
        except zipfile.BadZipfile as err_msg:
            raise ProcessorError("Failed to open {}: {}".format(zip_path, err_msg))

        # Now we have the deets, let's use them
        self.create_pkginfo()


    def get_generic_keys(self):
        '''
            Generic keys to get regardless of title
        '''

        # Progress notification
        self.env['installed_path'] = os.path.join('/Applications', self.env['app_path'],
                                                  self.env['app_bundle'])
        self.output("installed_path: {}".format(self.env['installed_path']))

        # Get display_name
        if not self.env['app_path'].endswith('CC') and not self.env['app_path'].endswith('2021'):
            self.env['display_name'] = self.env['app_path'] + ' 2021'
        elif self.env['app_path'].endswith('CC') and not self.env['app_path'].endswith('2021'):
            self.env['display_name'] = self.env['app_path'] + ' 2021'
        else:
            self.env['display_name'] = self.env['app_path']

        # Progress notification
        self.output("display_name: {}".format(self.env['display_name']))


    def read_info_plist(self, my_zip, pimx_dir, xml_tree, zip_path):
        '''
            Try to read info.plist from within zip_bundle
        '''

        # Loop through .pmx's Assets, look for target=[INSTALLDIR],
        # then grab Assets Source.
        # Break when found .app/Contents/Info.plist
        for xml_elem in xml_tree.findall('Assets'):
            for xml_item in  xml_elem.getchildren():
                # Below special tweak for the non-Classic Lightroom bundle
                if (xml_item.attrib['target'].upper().startswith('[INSTALLDIR]') and
                        not xml_item.attrib['target'].endswith('Icons')):
                    # Get bundle_location
                    bundle_location = xml_item.attrib['source']
                    self.output("bundle_location: {}".format(bundle_location))
                else:
                    continue
                # Amend bundle_location as needed
                if not bundle_location.startswith('[StagingFolder]'):
                    continue
                if bundle_location.endswith('Icons') or \
                         bundle_location.endswith('AMT'):
                    continue
                bundle_location = bundle_location[16:]
                # Create zip_bundle
                if bundle_location.endswith('.app'):
                    zip_bundle = (os.path.join(pimx_dir, bundle_location,
                                               'Contents/Info.plist'))
                else:
                    zip_bundle = (os.path.join(pimx_dir, bundle_location,
                                               self.env['app_bundle'],
                                               'Contents/Info.plist'))
                # Try to read info.plist from within zip_bundle
                try:
                    with my_zip.open(zip_bundle) as my_plist:
                        info_plist = my_plist.read()
                        data = load_plist(info_plist)
                        # If the App is Lightroom (Classic or non-Classic)
                        # we need to compare a different value in Info.plist
                        if self.env['sap_code'] == 'LTRM' or \
                             self.env['sap_code'] == 'LRCC':
                            self.env['vers_compare_key'] = 'CFBundleVersion'
                        else:
                            self.env['vers_compare_key'] = (
                                'CFBundleShortVersionString')

                        # Get version from info.plist
                        app_version = data[self.env['vers_compare_key']]

                        # Get bundleid from info.plist
                        self.env['app_bundle_id'] = data['CFBundleIdentifier']

                        # Progress notifications
                        self.output("vers_compare_key: {}"
                                    .format(self.env['vers_compare_key']))
                        self.output("app_bundle_id: {}"
                                    .format(self.env['app_bundle_id']))
                        self.output("staging_folder: {}"
                                    .format(bundle_location))
                        self.output("staging_folder_path: {}"
                                    .format(zip_bundle))
                        self.env['app_version'] = app_version
                        self.output("app_version: {}".format(self.env['app_version']))
                        break

                # If we cannot read the zip file
                except zipfile.BadZipfile as err_msg:
                    raise ProcessorError("Failed to open {}: {}"
                                         .format(zip_path, err_msg))


    # pylint: disable = too-many-branches, too-many-statements
    def parse_app_json(self, load_json):
        '''
            Read in values from app_json
        '''

        # Get app_version, cautiously for now for only certain apps
        if self.env['sap_code'] == 'CHAR':
            self.env['app_version'] = load_json['CodexVersion']
            self.env['app_bundle_id'] = 'com.adobe.Character-Animator.application'
            self.env['vers_compare_key'] = 'CFBundleShortVersionString'
        elif self.env['sap_code'] == 'ESHR':
            self.env['app_version'] = load_json['CodexVersion']
            self.env['app_bundle_id'] = 'com.adobe.dimension'
            self.env['vers_compare_key'] = 'CFBundleShortVersionString'
        elif self.env['sap_code'] == 'ILST':
            self.env['app_version'] = load_json['CodexVersion']
            self.env['app_bundle_id'] = 'com.adobe.illustrator'
            self.env['vers_compare_key'] = 'CFBundleShortVersionString'
        elif self.env['sap_code'] == 'KBRG':
            self.env['app_version'] = load_json['ProductVersion']
            self.env['app_bundle_id'] = 'com.adobe.bridge11'
            self.env['vers_compare_key'] = 'CFBundleShortVersionString'
        elif self.env['sap_code'] == 'LTRM':
            self.env['app_version'] = load_json['CodexVersion']
            self.env['app_bundle_id'] = 'com.adobe.LightroomClassicCC7'
            self.env['vers_compare_key'] = 'CFBundleVersion'
        elif self.env['sap_code'] == 'PHSP':
            self.env['app_version'] = load_json['CodexVersion']
            self.env['app_bundle_id'] = 'com.adobe.Photoshop'
            self.env['vers_compare_key'] = 'CFBundleShortVersionString'
        elif self.env['sap_code'] == 'SBSTA':
            self.env['app_version'] = load_json['CodexVersion']
            self.env['app_bundle_id'] = 'com.adobe.adobe-substance-3d-sampler'
            self.env['vers_compare_key'] = 'CFBundleShortVersionString'
        elif self.env['sap_code'] == 'SBSTD':
            self.env['app_version'] = load_json['CodexVersion']
            self.env['app_bundle_id'] = 'com.adobe.substance-3d-designer'
            self.env['vers_compare_key'] = 'CFBundleShortVersionString'
        elif self.env['sap_code'] == 'SBSTP':
            self.env['app_version'] = load_json['CodexVersion']
            self.env['app_bundle_id'] = 'com.adobe.Adobe-Substance-3D-Painter'
            self.env['vers_compare_key'] = 'CFBundleShortVersionString'
        elif self.env['sap_code'] == 'SPRK':
            self.env['app_version'] = load_json['ProductVersion']
            self.env['app_bundle_id'] = 'com.adobe.xd'
            self.env['vers_compare_key'] = 'CFBundleShortVersionString'
        elif self.env['sap_code'] == 'STGR':
            self.env['app_version'] = load_json['CodexVersion']
            self.env['app_bundle_id'] = 'com.adobe.stager'
            self.env['vers_compare_key'] = 'CFBundleShortVersionString'
        else:
            raise ProcessorError("Checking app_json for version details but sap code {}, "
                                 "is not within the known list of apps which we know to "
                                 "check via their Application.json".format(self.env['sap_code']))
        self.output("app_version: {}".format(self.env['app_version']))

        # Get app_bundle
        for app_launch in load_json['AppLaunch'].split('/'):
            if app_launch.endswith('.app'):
                app_bundle = ('/Applications/' + app_launch.split('.app')[0] + '/' + app_launch)
        self.output("app_bundle: {}".format(app_bundle))


    def create_pkginfo(self):
        '''
            Create pkginfo with found details
        '''

        # More var declaration
        self.env['jss_inventory_name'] = self.env['app_bundle']
        self.env['pkg_path'] = self.env['PKG']
        self.env['version'] = self.env['app_version']

        # Get minimum_os_version from override
        # https://github.com/autopkg/dataJAR-recipes/issues/138
        pkginfo = {
            'minimum_os_version': self.env['MINIMUM_OS_VERSION']
        }

        # Allow the user to provide a display_name string that prevents CreativeCloudVersioner
        # from overriding it.
        if 'pkginfo' not in self.env or 'display_name' not in self.env['pkginfo']:
            pkginfo['display_name'] = self.env['display_name']

        # Create pkginfo is missing from installs array
        if 'pkginfo' not in self.env or 'installs' not in self.env['pkginfo']:
            pkginfo['installs'] = [{
                self.env['vers_compare_key']: self.env['version'],
                'path': self.env['installed_path'],
                'type': 'application',
                'version_comparison_key': self.env['vers_compare_key'],
                'CFBundleIdentifier': self.env['app_bundle_id'],
            }]

        # Set Processor Architecture info
        if self.env['architecture_type'] == "x64":
            pkginfo['supported_architectures'] = [
                'x86_64',
                'i386',
            ]
            self.env['architecture_type'] = '-Intel'
        elif self.env['architecture_type'] == "arm64":
            pkginfo['supported_architectures'] = [
                'arm64',
            ]
            self.env['architecture_type'] = '-ARM'

        # Notify of additional_pkginfo
        self.env['additional_pkginfo'] = pkginfo
        self.output("additional_pkginfo: {}".format(self.env['additional_pkginfo']))


if __name__ == '__main__':
    PROCESSOR = Adobe2021Versioner()

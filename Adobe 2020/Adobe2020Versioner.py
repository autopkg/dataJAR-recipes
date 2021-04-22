#!/usr/bin/python

# Copyright 2021 dataJAR
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# pylint: disable=import-error

"""See docstring for AdobeCC2019Versioner class"""

from __future__ import absolute_import
import glob
import json
import os
import re
import zipfile
from xml.etree import ElementTree

try:
    from plistlib import loads as load_plist
except ImportError:
    from FoundationPlist import readPlistFromString as load_plist
from autopkglib import Processor, ProcessorError


__all__ = ['Adobe2020Versioner']
__version__ = ['1.3.1']


class Adobe2020Versioner(Processor):
    """Parses generated Adobe Admin Console 2020 pkgs for
       detailed application path and bundle version info"""

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
    }


    def main(self):
        """Find the Adobe*_Install.pkg in the Downloads dir based on the name"""

        download_path = os.path.expanduser('~/Downloads')
        self.env['PKG'] = os.path.join(download_path, self.env['NAME'], \
                            'Build', self.env['NAME'] + '_Install.pkg')
        self.output('pkg %s' % self.env['PKG'])
        self.env['uninstaller_pkg_path'] = glob.glob(os.path.join\
        (os.path.dirname(self.env['PKG']), '*_Uninstall.pkg'))[0]

        self.process_installer()


    def process_installer(self):
        """Determine a pkginfo, version and jss inventory name from the created package.

        Inputs:
            PKG: Path to the pkg
        Outputs:
            app_json/proxy_xml: The path of the files that within the pkg's
        """

        install_lang = None

        option_xml_path = os.path.join(self.env['PKG'], 'Contents', 'Resources', 'optionXML.xml')
        self.output('Processing %s' % option_xml_path)
        option_xml = ElementTree.parse(option_xml_path)

        for hd_media in option_xml.findall('.//HDMedias/HDMedia'):
            if hd_media.findtext('MediaType') == 'Product':
                install_lang = hd_media.findtext('installLang')
                self.env['sap_code'] = hd_media.findtext('SAPCode')
                self.output('SAP Code: %s' % self.env['sap_code'])
                self.env['target_folder'] = hd_media.findtext('TargetFolderName')

        if install_lang is None:
            for ribs_media in option_xml.findall('.//Medias/Media'):
                install_lang = ribs_media.findtext('installLang')
                self.env['sap_code'] = ribs_media.findtext('SAPCode')
                self.output('SAP Code: %s' % self.env['sap_code'])
                self.env['target_folder'] = ribs_media.findtext('TargetFolderName')

        self.env['app_json'] = os.path.join(self.env['PKG'], 'Contents/Resources/HD', \
                                       self.env['target_folder'], 'Application.json')

        # If Application.json exists, we're looking at a HD installer
        if os.path.exists(self.env['app_json']):
            if not self.env['sap_code'] is 'APRO':
                self.output('Installer is HyperDrive')
                self.output('app_json: %s' % self.env['app_json'])
                self.process_hd_installer()
        else:
            # If not a HD installer Acrobat is a 'current' title with a
            # RIBS PKG installer we can extract needed metadata from
            self.env['proxy_xml'] = os.path.join(self.env['PKG'], 'Contents/Resources/Setup', \
                                                      self.env['target_folder'], 'proxy.xml')
            if not os.path.exists(self.env['proxy_xml']):
                raise ProcessorError('APRO selected, proxy.xml not found at: %s' \
                                                          % self.env['proxy_xml'])
            else:
                self.process_apro_installer()


    def process_apro_installer(self):
        '''
        Process APRO installer -
            proxy_xml: Path to proxy_xml if pkg is APRO
        '''

        self.output('Processing Acrobat installer')
        self.output('proxy_xml: %s' % self.env['proxy_xml'])

        tree = ElementTree.parse(self.env['proxy_xml'])
        root = tree.getroot()

        app_bundle_text = root.findtext\
                      ('./ThirdPartyComponent/Metadata/Properties/Property[@name=\'path\']')
        app_bundle = app_bundle_text.split('/')[1]
        self.output('app_bundle: %s' % app_bundle)

        app_path_text = root.findtext('./InstallDir/Platform')
        self.output('app_path_text: %s' % app_path_text)

        app_path = app_path_text.split('/')[1]
        self.output('app_path: %s' % app_path)

        installed_path = os.path.join('/Applications', app_path, app_bundle)
        self.output('installed_path: %s' % installed_path)

        app_version = root.findtext('./InstallerProperties/Property[@name=\'ProductVersion\']')
        self.output('app_version: %s' % app_version)

        self.env['display_name'] = app_path + ' 2020'
        self.output('display_name: %s' % self.env['display_name'])

        self.env['vers_compare_key'] = 'CFBundleShortVersionString'
        self.output('vers_compare_key: %s' % self.env['vers_compare_key'])

        app_bundle_id = 'com.adobe.Acrobat.Pro'
        self.output('app_bundle_id: %s' % app_bundle_id)

        self.create_pkginfo(app_bundle, app_bundle_id, app_version, installed_path)


    # pylint: disable=too-many-branches
    def process_hd_installer(self):
        '''
        Process HD installer -
            app_json: Path to the Application JSON from within the PKG
        '''

        #pylint: disable=too-many-locals, too-many-statements
        self.output('Processing HD installer')
        with open(self.env['app_json']) as json_file:
            load_json = json.load(json_file)

            # AppLaunch is not always in the same format, but is splittable
            if 'AppLaunch' in load_json:  # Bridge CC is HD but does not have AppLaunch
                app_launch = load_json['AppLaunch']
                self.output('app_launch: %s' % app_launch)
                app_details = list(re.split('/', app_launch))
                if app_details[2].endswith('.app'):
                    app_bundle = app_details[2]
                    app_path = app_details[1]
                else:
                    app_bundle = app_details[1]
                    app_path = list(re.split('/', (load_json['InstallDir']['value'])))[1]
                self.output('app_bundle: %s' % app_bundle)
                self.output('app_path: %s' % app_path)

                installed_path = os.path.join('/Applications', app_path, app_bundle)
                self.output('installed_path: %s' % installed_path)

                if not app_path.endswith('CC') and not app_path.endswith('2020'):
                    self.env['display_name'] = app_path + ' 2020'
                elif app_path.endswith('CC') and not app_path.endswith('2020'):
                    self.env['display_name'] = app_path + ' 2020'
                else:
                    self.env['display_name'] = app_path
                self.output('display_name: %s' % self.env['display_name'])

                zip_file = load_json['Packages']['Package'][0]['PackageName']
                pimx_dir = '1'
                if zip_file.endswith('-LearnPanel'):
                    zip_file = load_json['Packages']['Package'][1]['PackageName']
                    pimx_dir = '2'
                self.output('zip_file: %s' % zip_file)

                zip_path = os.path.join(self.env['PKG'], 'Contents/Resources/HD', \
                                    self.env['target_folder'], zip_file + '.zip')
                self.output('zip_path: %s' % zip_path)

                with zipfile.ZipFile(zip_path, mode='r') as myzip:
                    with myzip.open(zip_file + '.pimx') as mytxt:
                        txt = mytxt.read()
                        tree = ElementTree.fromstring(txt)
                        # Loop through .pmx's Assets, look for target=[INSTALLDIR],
                        # then grab Assets Source.
                        # Break when found .app/Contents/Info.plist
                        for elem in tree.findall('Assets'):
                            for i in  elem.getchildren():
                                # Below special tweak for the non-Classic Lightroom bundle
                                if i.attrib['target'].upper().startswith('[INSTALLDIR]') and \
                                                   not i.attrib['target'].endswith('Icons'):
                                    bundle_location = i.attrib['source']
                                    self.output('bundle_location: %s' % bundle_location)
                                else:
                                    continue
                                if not bundle_location.startswith('[StagingFolder]'):
                                    continue
                                elif bundle_location.endswith('Icons') or \
                                         bundle_location.endswith('AMT'):
                                    continue
                                else:
                                    bundle_location = bundle_location[16:]
                                    if bundle_location.endswith('.app'):
                                        zip_bundle = os.path.join(pimx_dir, bundle_location, \
                                                                      'Contents/Info.plist')
                                    else:
                                        zip_bundle = os.path.join(pimx_dir, bundle_location, \
                                                          app_bundle, 'Contents/Info.plist')
                                    try:
                                        with myzip.open(zip_bundle) as myplist:
                                            plist = myplist.read()
                                            data = load_plist(plist)
                                            # If the App is Lightroom (Classic or non-Classic)
                                            # we need to compare a different value in Info.plist
                                            if self.env['sap_code'] == 'LTRM' or \
                                                 self.env['sap_code'] == 'LRCC':
                                                self.env['vers_compare_key'] = 'CFBundleVersion'
                                            else:
                                                self.env['vers_compare_key'] = \
                                                  'CFBundleShortVersionString'
                                            self.output('vers_compare_key: %s' % \
                                                   self.env['vers_compare_key'])
                                            app_version = data[self.env['vers_compare_key']]
                                            app_bundle_id = data['CFBundleIdentifier']
                                            self.output('app_bundle_id: %s' % app_bundle_id)
                                            self.output('staging_folder: %s' % bundle_location)
                                            self.output('staging_folder_path: %s' % zip_bundle)
                                            self.output('app_version: %s' % app_version)
                                            self.output('app_bundle: %s' % app_bundle)
                                            break
                                    except zipfile.BadZipfile:
                                        continue

                # Now we have the deets, let's use them
                self.create_pkginfo(app_bundle, app_bundle_id, app_version, installed_path)


    def create_pkginfo(self, app_bundle, app_bundle_id, app_version, installed_path):
        """Create pkginfo with found details

        Args:
              app_bundle (str): Bundle name
              app_version (str): Bundle version
              installed_path (str): The path where the installed item will be installed.
        """

        self.env['jss_inventory_name'] = app_bundle
        self.env['pkg_path'] = self.env['PKG']
        self.env['version'] = app_version

        pkginfo = {
            'minimum_os_version': self.env['MINIMUM_OS_VERSION']
        }

        # Allow the user to provide a display_name string that prevents CreativeCloudVersioner from overriding it.
        if 'pkginfo' not in self.env or 'display_name' not in self.env['pkginfo']:
            pkginfo['display_name'] = self.env['display_name']

        if 'pkginfo' not in self.env or 'installs' not in self.env['pkginfo']:
            pkginfo['installs'] = [{
                self.env['vers_compare_key']: self.env['version'],
                'path': installed_path,
                'type': 'application',
                'version_comparison_key': self.env['vers_compare_key'],
                'CFBundleIdentifier': app_bundle_id,
            }]

        self.env['additional_pkginfo'] = pkginfo
        self.output('additional_pkginfo: %s' % self.env['additional_pkginfo'])


if __name__ == '__main__':
    PROCESSOR = Adobe2020Versioner()

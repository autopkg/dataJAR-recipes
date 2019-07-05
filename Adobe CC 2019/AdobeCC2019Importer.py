#!/usr/bin/python

'''
Copyright (c) 2019, dataJAR Ltd.  All rights reserved.

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

     THIS SOFTWARE IS PROVIDED BY DATA JAR LTD "AS IS" AND ANY
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

    This program is distributed "as is" by DATA JAR LTD.


DESCRIPTION

Variant of:
https://github.com/autopkg/adobe-ccp-recipes/blob/master/Adobe/CreativeCloudVersioner.py
'''

# Standard Imports
import glob
import json
import os
import re
import zipfile
from xml.etree import ElementTree

# AutoPkg Imports
# pylint: disable=import-error
import FoundationPlist
from autopkglib import Processor, ProcessorError

# Details
__all__ = ['AdobeCC2019Importer']
__version__ = ['1.1']


# Class
class AdobeCC2019Importer(Processor):
    '''
    Parses generated Adobe Admin Console CC 2019 pkgs for 
    detailed application path and bundle version info
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
    }


    def main(self):
        '''
        Find the Adobe*_Install.pkg in the Downloads dir based on the name
        '''

        download_path = os.path.expanduser('~/Downloads')
        self.env['PKG'] = os.path.join(download_path, self.env['NAME'], \
                            'Build', self.env['NAME'] + '_Install.pkg')
        self.output('pkg %s' % self.env['PKG'])
        self.env['uninstaller_pkg_path'] = glob.glob(os.path.join\
        (os.path.dirname(self.env['PKG']), '*_Uninstall.pkg'))[0]

        self.process_installer()


    def process_installer(self):
        '''
        Determine a pkginfo, version and jss inventory name from the created package.

        Inputs:
            PKG: Path to the pkg
        Outputs:
            app_json/proxy_xml: The path of the files that within the pkg's
        '''

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

        self.env['display_name'] = app_path + ' CC 2019'
        self.output('display_name: %s' % self.env['display_name'])

        self.create_pkginfo(app_bundle, app_version, installed_path)


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

                if not app_path.endswith('CC') and not app_path.endswith('CC 2019'):
                    self.env['display_name'] = app_path + ' CC 2019'
                elif app_path.endswith('CC') and not app_path.endswith('CC 2019'):
                    self.env['display_name'] = app_path + ' 2019'
                else:
                    self.env['display_name'] = app_path
                self.output('display_name: %s' % self.env['display_name'])

                zip_file = load_json['Packages']['Package'][0]['PackageName']
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
                                if i.attrib['target'].upper().startswith('[INSTALLDIR]'):
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
                                        zip_bundle = os.path.join('1', bundle_location, \
                                                                 'Contents/Info.plist')
                                    else:
                                        zip_bundle = os.path.join('1', bundle_location, \
                                                     app_bundle, 'Contents/Info.plist')
                                    try:
                                        with myzip.open(zip_bundle) as myplist:
                                            plist = myplist.read()
                                            data = FoundationPlist.readPlistFromString(plist)
                                            if self.env['sap_code'] == 'LTRM':
                                                self.env['vers_compare_key'] = 'CFBundleVersion'
                                            else:
                                                self.env['vers_compare_key'] = \
                                            	  'CFBundleShortVersionString'
                                            self.output('vers_compare_key: %s' % \
                                                   self.env['vers_compare_key'])
                                            app_version = data[self.env['vers_compare_key']]
                                            self.output('staging_folder: %s' % bundle_location)
                                            self.output('staging_folder_path: %s' % zip_bundle)
                                            self.output('app_version: %s' % app_version)
                                            self.output('app_bundle: %s' % app_bundle)
                                            break
                                    except zipfile.BadZipfile:
                                        continue

                # Now we have the deets, let's use them
                self.create_pkginfo(app_bundle, app_version, installed_path)


    def create_pkginfo(self, app_bundle, app_version, installed_path):
        '''Create pkginfo with found details

        Args:
              app_bundle (str): Bundle name
              app_version (str): Bundle version
              installed_path (str): The path where the installed item will be installed.
        '''

        self.env['jss_inventory_name'] = app_bundle
        self.env['pkg_path'] = self.env['PKG']
        self.env['version'] = app_version

        pkginfo = {
            'display_name': self.env['display_name'],
            'minimum_os_version': self.env['MINIMUM_OS_VERSION']
        }

        if 'pkginfo' not in self.env or 'installs' not in self.env['pkginfo']:
            pkginfo['installs'] = [{
                self.env['vers_compare_key']: self.env['version'],
                'path': installed_path,
                'type': 'application',
                'version_comparison_key': self.env['vers_compare_key'],
            }]

        self.env['additional_pkginfo'] = pkginfo
        self.output('additional_pkginfo: %s' % self.env['additional_pkginfo'])


if __name__ == '__main__':
    # pylint: disable=invalid-name
    processor = AdobeCC2019Importer()

#!/usr/local/autopkg/python
# pylint: disable = invalid-name

'''
Copyright (c) 2023, dataJAR Ltd.  All rights reserved.
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
See docstring for CaseChanger class
'''

# Standard imports
import configparser
import glob
import os
import plistlib

# AutoPkg imports
# pylint: disable = import-error
from autopkglib.DmgMounter import DmgMounter
from autopkglib import ProcessorError


__all__ = ['FirefoxGetLocaleAndVersion']
__version__ = '1.0'


# pylint: disable = too-few-public-methods
class FirefoxGetLocaleAndVersion(DmgMounter):
    '''
        Returns the locale and version of the Firefox.app passed to dmg_path

        Raising if Firefox.app not located at dmg_path.

        Based off of:
        https://github.com/autopkg/autopkg/blob/master/Code/autopkglib/AppDmgVersioner.py#L69-L86
    '''

    description = __doc__
    input_variables = {
        'choosen_locale': {
            'required': True,
            'description': ('Value of LOCALE in the override.'),
        },
        'dmg_path': {
            'required': True,
            'description': ('Path to the downloaded DMG.'),
        }
    }

    output_variables = {
        'app_locale': {
            'description': ('Locale of the .app.'),
        },
        'app_version': {
            'description': ('Version of the .app.'),
        },
    }



    def find_app(self, path):
        '''
            Find app bundle at path
        '''

        # Look for any .app in the mounted dmg
        apps = glob.glob(os.path.join(path, "*.app"))

        # Raise if no .app found
        if len(apps) == 0:
            raise ProcessorError("No app found in dmg")

        # Return 1st found .app only
        return apps[0]


    def main(self):
        '''
            See docstring for the FirefoxGetLocaleAndVersion class
        '''

        # Mount the image.
        mount_point = self.mount(self.env["dmg_path"])

        # Wrap all other actions in a try/finally so the image is always
        # unmounted.
        try:

            # Get the path the the .app in the DMG, raise if no .app found
            app_path = self.find_app(mount_point)
            self.output(f"app_path = {app_path}")

            # Get the path to locale.ini, if doesn't exist and LOCALE is en-US we're good
            app_locale_ini = os.path.join(app_path, 'Contents/Resources/locale.ini')
            self.output(f"Looking for {app_locale_ini}...")

            # Get the .app's locale, if app_locale_ini exists
            if os.path.exists(app_locale_ini):
                # Progress notification
                self.output(f"Found: {app_locale_ini}...")
                # Try Read in the locale, raise if cannot be parsed
                try:
                    # Create confgparser object
                    app_config = configparser.ConfigParser()
                    app_config.read(app_locale_ini)
                    # Setting app_locale
                    self.env['app_locale']  = app_config['locale']['locale']
                # Raise if app_locale cannot be retrieved from app_locale_ini
                except Exception as locale_parse_error:
                    raise ProcessorError("Cannot determine app_locale") from locale_parse_error
            # en-US doesn't have a app_locale_ini, so if selected then
            elif self.env["choosen_locale"] == 'en-US':
                # Setting app_locale
                self.env['app_locale']  = 'en-US'
                self.output(f"Setting app_locale to \"en-US\", as {app_locale_ini} does "
                            f"not exist for the \"en-US\" locale")
            # Raise if we can't find app_locale_ini and choosen_locale isn't en-US
            else:
                raise ProcessorError(f"Cannot find {app_locale_ini}")

            # Progress notification
            self.output(f"app_locale: {self.env['app_locale']}")
            # Now we need to get the version
            app_info_plist = os.path.join(app_path, 'Contents/Info.plist')

            # If the info.plist exists
            if os.path.exists(app_info_plist):
                # Try to read in app_info_plist, raise if cannot be parsed
                try:
                    # Read in the plist
                    with open(app_info_plist, "rb") as plist_file:
                        parsed_plist = plistlib.load(plist_file)
                    # Get version from info.plist
                    self.env['app_version'] = parsed_plist['CFBundleShortVersionString']
                    self.output(f"app_version: {self.env['app_version']}")
                # Raising if plist cannot be parsed or version determined from plist
                except Exception as info_plist_error:
                    raise ProcessorError(f"Cannot parse {app_info_plist}") from info_plist_error
            # Raise if we can't find app_info_plist
            else:
                raise ProcessorError(f"Cannot find {app_info_plist}")

        # Unmount the dmg
        finally:
            self.output("unmounting...")
            self.unmount(self.env["dmg_path"])

if __name__ == '__main__':
    PROCESSOR = FirefoxGetLocaleAndVersion()

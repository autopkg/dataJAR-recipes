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
See docstring for FirefoxGetLocaleAndVersion class
'''

# Standard imports
import os
import glob
import plistlib
import subprocess

# AutoPkg imports
from autopkglib.DmgMounter import DmgMounter
from autopkglib import ProcessorError

__all__ = ['FirefoxGetLocaleAndVersion']
__version__ = '1.1'

class FirefoxGetLocaleAndVersion(DmgMounter):
    '''
    Returns the locale and version of the Firefox.app passed to dmg_path.
    Uses unzip command to extract locale information from omni.ja file.
        https://bugzilla.mozilla.org/show_bug.cgi?id=1936505
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
        '''Find app bundle at path'''
        apps = glob.glob(os.path.join(path, "*.app"))
        if len(apps) == 0:
            raise ProcessorError("No app found in dmg")
        return apps[0]

    def get_locale_from_omni(self, app_path):
        '''Extract locale from omni.ja file'''
        omni_path = os.path.join(app_path, 'Contents/Resources/omni.ja')
        if not os.path.exists(omni_path):
            raise ProcessorError(f"Cannot find {omni_path}")

        try:
            cmd = ['unzip', '-p', omni_path, 'default.locale']
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, _ = proc.communicate()

            if proc.returncode != 0:
                raise ProcessorError("Error extracting locale from omni.ja")

            locale = stdout.decode('utf-8').strip()
            if not locale:
                raise ProcessorError("Empty locale returned from omni.ja")

            return locale

        except subprocess.SubprocessError as err:
            raise ProcessorError("Error running unzip command") from err

    def main(self):
        '''Main process'''
        # Mount the image
        mount_point = self.mount(self.env["dmg_path"])

        try:
            # Get the path to the .app
            app_path = self.find_app(mount_point)
            self.output(f"app_path = {app_path}")

            # Get locale from omni.ja
            self.env['app_locale'] = self.get_locale_from_omni(app_path)
            self.output(f"app_locale: {self.env['app_locale']}")

            # Get version from Info.plist
            app_info_plist = os.path.join(app_path, 'Contents/Info.plist')
            if os.path.exists(app_info_plist):
                try:
                    with open(app_info_plist, "rb") as plist_file:
                        parsed_plist = plistlib.load(plist_file)
                    self.env['app_version'] = parsed_plist['CFBundleShortVersionString']
                    self.output(f"app_version: {self.env['app_version']}")
                except Exception as info_plist_error:
                    raise ProcessorError(f"Cannot parse {app_info_plist}") from info_plist_error
            else:
                raise ProcessorError(f"Cannot find {app_info_plist}")

        finally:
            self.output("unmounting...")
            self.unmount(self.env["dmg_path"])

if __name__ == '__main__':
    PROCESSOR = FirefoxGetLocaleAndVersion()

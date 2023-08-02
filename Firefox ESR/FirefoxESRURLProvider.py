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
See docstring for FirefoxESRURLProvider class
'''

# Standard imports
import json


# AutoPkg imports
# pylint: disable = import-error
from autopkglib import ProcessorError, URLGetter

__all__ = ['FirefoxESRURLProvider']
__version__ = '1.0'

# pylint: disable = too-few-public-methods
class FirefoxESRURLProvider(URLGetter):
    '''
        Checks https://product-details.mozilla.org/1.0/firefox_versions.json for the key:
        FIREFOX_ESR_NEXT if this exists, then this keys version is used to generate a download
        URL.
        
        If FIREFOX_ESR_NEXT does not exist, fails over to FIREFOX_ESR.
    '''

    description = __doc__
    input_variables = {
        "locale": {
            "required": False,
            "default": "en-US",
            "description": ("Which localisation to download, default is 'en-US'."),
        }
    }
    output_variables = {
        "url": {"description": "URL to the latest Mozilla product release."},
    }


    def main(self):
        '''
            See docstring for FirefoxESRURLProvider class
        '''

        # URL of json file containing version information
        json_url = 'https://product-details.mozilla.org/1.0/firefox_versions.json'

        # Set locale, defaulting to en-US
        locale = self.env.get("locale", "en-US")
        self.output(f"Locale set to: {locale}")

        # Parse json file to variable
        json_data = self.download(json_url)

        # Convert to dict
        version_data = json.loads(json_data)

        # If there is a FIREFOX_ESR_NEXT key present, use that else use FIREFOX_ESR.
        # Raise if both fail.
        try:
            esr_version = version_data['FIREFOX_ESR_NEXT']
            self.output(f"Found FIREFOX_ESR_NEXT version: {esr_version}")
        except KeyError:
            try:
                esr_version = version_data['FIREFOX_ESR']
                self.output(f"Found FIREFOX_ESR version: {esr_version}")
            except KeyError as exc:
                raise ProcessorError(f"Cannot find FIREFOX_ESR_NEXT or FIREFOX_ESR within "
                                     f"{json_url}") from exc

        # Set URL
        self.env['url'] = (f'https://releases.mozilla.org/pub/firefox/releases/{esr_version}'
                           f'/mac/{locale}/Firefox%20{esr_version}.dmg')

        # Output URL
        self.output(f"URL {self.env['url']}")


if __name__ == "__main__":
    PROCESSOR = FirefoxESRURLProvider()
    PROCESSOR.execute_shell()

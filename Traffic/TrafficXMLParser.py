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
See docstring for TrafficXMLParser class
'''

# Standard imports
import os
from xml.etree import ElementTree

# Other imports
# pylint: disable=import-error
from autopkglib import Processor, ProcessorError


# Processor information
__all__ = ["TrafficXMLParser"]
__version__ = '1.1'


# Class
# pylint: disable = too-few-public-methods
class TrafficXMLParser(Processor):
    '''
        Parses /META-INF/AIR/application.xml from the copied .air installer
    '''

    description = __doc__

    input_variables = {
        "app_xml": {
            "required": True,
            "description": "Path to the application.xml."
        },
    }

    output_variables = {
        "bundleid": {
            "description":
                "Bundled ID.",
        },
        "version": {
            "description": "The value of CFBundleShortVersionString for the app bundle."
        },
    }

    def main(self):
        '''
            Parses /META-INF/AIR/application.xml from the copied .air installer
        '''

        # Raise if app_xml doesn't exist
        if not os.path.exists(self.env["app_xml"]):
            raise ProcessorError(f"application.xml not found at {self.env['app_xml']}")

        # Parse xml
        tree = ElementTree.parse(self.env["app_xml"])
        # Get bundleid
        for b_id in tree.iterfind('{http://ns.adobe.com/air/application/24.0}id'):
            self.env["bundleid"] = b_id.text
        # Get Version
        for ver_num in tree.iterfind('{http://ns.adobe.com/air/application/24.0}versionNumber'):
            self.env["version"] = ver_num.text

        # Output retrieved values
        self.output(f"bundleid: {self.env['bundleid']}")
        self.output(f"version: {self.env['version']}")


if __name__ == "__main__":
    PROCESSOR = TrafficXMLParser()

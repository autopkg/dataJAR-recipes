#!/usr/bin/python

# Copyright 2020 dataJAR
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

# pylint: disable=import-error, too-few-public-methods

"""See docstring for TrafficXMLParser class"""

from __future__ import absolute_import
import os
from xml.etree import ElementTree

from autopkglib import Processor, ProcessorError


__all__ = ["TrafficXMLParser"]
__version__ = '1.1'


class TrafficXMLParser(Processor):
    """Parses /META-INF/AIR/application.xml from the copied .air installer"""
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
        """Parses /META-INF/AIR/application.xml from the copied .air installer"""
        if not os.path.exists(self.env["app_xml"]):
            raise ProcessorError("application.xml not found at %s" % self.env["app_xml"])
        else:
            tree = ElementTree.parse(self.env["app_xml"])
            for b_id in tree.iterfind('{http://ns.adobe.com/air/application/24.0}id'):
                self.env["bundleid"] = b_id.text
            for ver_num in tree.iterfind('{http://ns.adobe.com/air/application/24.0}versionNumber'):
                self.env["version"] = ver_num.text

            self.output("bundleid: %s" % self.env["bundleid"])
            self.output("version: %s" % self.env["version"])


if __name__ == "__main__":
    PROCESSOR = TrafficXMLParser()

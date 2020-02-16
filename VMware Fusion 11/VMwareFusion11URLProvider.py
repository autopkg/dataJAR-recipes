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

"""See docstring for VMwareFusion11URLProvider class"""

# pylint: disable=import-error

import gzip
import urllib2

from xml.etree import ElementTree
from StringIO import StringIO
from distutils.version import LooseVersion

from autopkglib import Processor, ProcessorError

__all__ = ["VMwareFusion11URLProvider"]
__version__ = 1.1

# variables
VMWARE_BASE_URL = 'https://softwareupdate.vmware.com/cds/vmw-desktop/'
FUSION = 'fusion.xml'
MAJOR_VERSION = '11' # lock version in

class VMwareFusion11URLProvider(Processor):
    """Provides URL to the latest VMware Fusion update release."""

    description = __doc__
    input_variables = {
        "product_name": {
            "required": False,
            "description":
                "Default is '%s'." % FUSION,
        },
        "base_url": {
            "required": False,
            "description": "Default is '%s." % VMWARE_BASE_URL,
        },
    }
    output_variables = {
        "url": {
            "description": "URL to the latest VMware Fusion update release.",
        },
        "version": {
            "description": "Version to the latest VMware Fusion update release.",
        },
    }


    # pylint: disable=too-many-locals
    def core_metadata(self, base_url, product_name, major_version):
        """Get metadata from the XML"""
        request = urllib2.Request(base_url+product_name)

        found_urls = {}
        urls = []
        xml_vers = []

        try:
            vsus = urllib2.urlopen(request)
        except urllib2.URLError, err_msg:
            print err_msg.reason

        data = vsus.read()

        try:
            meta_list = ElementTree.fromstring(data)
        except ElementTree.ParseError:
            print "Unable to parse XML data from string"

        for metadata in meta_list:
            url = metadata.find("url")
            urls.append(url.text)

        for some_url in urls:
            if some_url.split('/')[1].startswith(major_version):
                found_urls[some_url.split('/')[1]] = some_url

        for found_ver, _ in found_urls.iteritems():
            xml_vers.append(found_ver)

        if len(xml_vers) == 0:
            raise ProcessorError("Could not find any versions for the \
                                  major_version '%s'." % major_version)

        xml_vers.sort(key=LooseVersion)
        self.env["version"] = xml_vers[-1]
        self.output(self.env["version"])
        core = found_urls[xml_vers[-1]]

        vsus.close()

        request = urllib2.Request(base_url+core)

        try:
            v_latest = urllib2.urlopen(request)
        except urllib2.URLError, err_msg:
            print err_msg.reason

        buf = StringIO(v_latest.read())
        downloaded_file = gzip.GzipFile(fileobj=buf)
        data = downloaded_file.read()

        try:
            metadata_response = ElementTree.fromstring(data)
        except ElementTree.ParseError:
            print "Unable to parse XML data from string"

        relative_path = metadata_response.find("bulletin/componentList/component/relative_path")
        return base_url+core.replace("metadata.xml.gz", relative_path.text)


    def main(self):
        """ Gimme some main """
        product_name = self.env.get("product_name", FUSION)
        base_url = self.env.get("base_url", VMWARE_BASE_URL)
        major_version = self.env.get("major_version", MAJOR_VERSION)

        self.env["url"] = self.core_metadata(base_url, product_name,
                                             major_version)
        self.output("Found URL %s" % self.env["url"])
        self.env["version"] = self.latest
        self.output("Found Version %s" % self.env["version"])


if __name__ == "__main__":
    PROCESSOR = VMwareFusion11URLProvider()
    PROCESSOR.execute_shell()

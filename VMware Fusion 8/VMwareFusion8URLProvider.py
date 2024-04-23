#!/usr/bin/python
#
# Copyright 2014 Justin Rummel, 
#
# Updates added 2018 by macmule:
# https://github.com/autopkg/justinrummel-recipes/pull/7
# https://github.com/autopkg/justinrummel-recipes/pull/14
#
# Thanks fuzzylogiq & Sterling
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

import urllib, urllib2, gzip

from xml.etree import ElementTree
from StringIO import StringIO
from autopkglib import Processor, ProcessorError
import sys
sys.path.insert(0, '/usr/local/munki')
from munkilib.pkgutils import MunkiLooseVersion as LooseVersion

__all__ = ["VMwareFusion8URLProvider"]


# variables
VMWARE_BASE_URL = 'https://softwareupdate.vmware.com/cds/vmw-desktop/'
FUSION = 'fusion.xml'
MAJOR_VERSION = '8' # lock version in

class VMwareFusion8URLProvider(Processor):
    description = "Provides URL to the latest VMware Fusion update release."
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

    __doc__ = description

    def core_metadata(self, base_url, product_name, major_version):
        request = urllib2.Request(base_url+product_name)
        # print base_url

        try:
            vsus = urllib2.urlopen(request)
        except URLError, e:
            print e.reason

        data = vsus.read()
        # print data

        try:
            metaList = ElementTree.fromstring(data)
        except ExpatData:
            print "Unable to parse XML data from string"

        versions = []
        for metadata in metaList:
            version = metadata.find("version")
            if (major_version == 'latest' or
                    major_version == version.text.split('.')[0]):
                versions.append(version.text)
        if len(versions) == 0:
            raise ProcessorError("Could not find any versions for the \
                                  major_version '%s'." % major_version)
        versions.sort(key=LooseVersion)
        self.latest = versions[-1]
        # print latest

        urls = []
        for metadata in metaList:
            url = metadata.find("url")
            urls.append(url.text)

        matching = [s for s in urls if self.latest in s]
        core = [s for s in matching if "core" in s]
        # print core[0]

        vsus.close()

        request = urllib2.Request(base_url+core[0])

        try:
            vLatest = urllib2.urlopen(request)
        except URLError, e:
            print e.reason

        buf = StringIO(vLatest.read())
        f = gzip.GzipFile(fileobj=buf)
        data = f.read()
        # print data

        try:
            metadataResponse = ElementTree.fromstring(data)
        except ExpatData:
            print "Unable to parse XML data from string"

        relativePath = metadataResponse.find("bulletin/componentList/component/relativePath")
        # print core[0].replace("metadata.xml.gz", relativePath.text)
        return base_url+core[0].replace("metadata.xml.gz", relativePath.text)

    def main(self):
        # Determine product_name, and base_url.
        product_name = self.env.get("product_name", FUSION)
        base_url = self.env.get("base_url", VMWARE_BASE_URL)
        major_version = self.env.get("major_version", MAJOR_VERSION)

        self.env["url"] = self.core_metadata(base_url, product_name,
                                             major_version)
        self.output("Found URL %s" % self.env["url"])
        self.env["version"] = self.latest
        self.output("Found Version %s" % self.env["version"])

if __name__ == "__main__":
    processor = VMwareFusion8URLProvider()
    processor.execute_shell()

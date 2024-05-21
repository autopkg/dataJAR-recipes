#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 Justin Rummel
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

from __future__ import absolute_import, print_function

import gzip
import os
import re
from distutils.version import LooseVersion
from xml.etree import ElementTree
from xml.parsers.expat import ExpatError

from autopkglib import ProcessorError, URLGetter

try:
    from urlparse import urljoin
except ImportError:
    from urllib.parse import urljoin


__all__ = ["VMwareFusionURLProvider"]


# variables
VMWARE_BASE_URL = "https://softwareupdate.vmware.com/cds/vmw-desktop/"
FUSION = "fusion-universal.xml"
DEFAULT_MAJOR_VERSION = "13"


class VMwareFusionURLProvider(URLGetter):
    """Processor class."""

    description = "Provides URL to the latest VMware Fusion update release."
    input_variables = {
        "product_name": {"required": False, "description": "Default is '%s'." % FUSION},
        "base_url": {
            "required": False,
            "description": "Default is '%s." % VMWARE_BASE_URL,
        },
        "major_version": {
            "required": False,
            "description": "Default is '%s." % DEFAULT_MAJOR_VERSION,
        },
    }
    output_variables = {
        "url": {"description": "URL to the latest VMware Fusion update release."},
        "version": {
            "description": "Version to the latest VMware Fusion update release."
        },
    }

    __doc__ = description

    def core_metadata(self, base_url, product_name, major_version):
        """Given a base URL, product name, and major version, produce the
        product download URL and latest version.
        """
        fusion_xml_url = urljoin(base_url, product_name)
        self.output("Fetching fusion.xml from {}".format(fusion_xml_url))
        vsus = self.download(fusion_xml_url, text=True)

        try:
            metaList = ElementTree.fromstring(vsus)
        except ExpatError:
            raise ProcessorError("Unable to parse XML data from string.")

        build_re = re.compile(r"^fusion\/([\d\.]+)\/(\d+)\/")

        versions = {}
        for metadata in metaList:
            version = metadata.find("version")
            url = metadata.find("url")
            if major_version == "latest" or major_version == version.text.split(".")[0]:
                # We actually want the URL, instead of the version itself
                self.output(
                    "Found version: {} with URL: {}".format(version.text, url.text),
                    verbose_level=4,
                )
                match = build_re.search(url.text)
                if match.groups():
                    versions[match.group(1)] = url.text
        if not versions:
            raise ProcessorError(
                "Could not find any versions for the "
                "major_version '%s'." % major_version
            )
        latest_version_key = sorted(versions.keys(), key=LooseVersion)[-1]
        self.output(
            "Latest version URL suffix: {}".format(versions[latest_version_key]), verbose_level=2
        )
        full_url = urljoin(base_url, versions[latest_version_key])
        self.output("URL: {}".format(full_url), verbose_level=2)
        download_dir = os.path.join(self.env["RECIPE_CACHE_DIR"], "downloads")
        try:
            os.makedirs(download_dir)
        except os.error:
            # Directory already exists
            pass
        temp_file = os.path.join(download_dir, "metadata.xml.gz")
        vLatest = self.download_to_file(full_url, temp_file)
        try:
            with gzip.open(vLatest, "rb") as f:
                data = f.read()
        except Exception as e:
            raise ProcessorError(e)

        try:
            metadataResponse = ElementTree.fromstring(data)
        except ExpatError:
            raise ProcessorError("Unable to parse XML data from string.")

        relativePath = metadataResponse.find(
            "bulletin/componentList/component/relativePath"
        )
        return (
            full_url.replace("metadata.xml.gz", relativePath.text),
            latest_version_key,
        )

    def main(self):
        """Main process."""

        # Gather input variables
        product_name = self.env.get("product_name", FUSION)
        base_url = self.env.get("base_url", VMWARE_BASE_URL)
        major_version = self.env.get("major_version", DEFAULT_MAJOR_VERSION)

        # Look up URL and set output variables
        self.env["url"], self.env["version"] = self.core_metadata(
            base_url, product_name, major_version
        )
        self.output("Found URL: %s" % self.env["url"])
        self.output("Found Version: %s" % self.env["version"])


if __name__ == "__main__":
    processor = VMwareFusionURLProvider()
    processor.execute_shell()

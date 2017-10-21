#!/usr/bin/python
#
# Copyright 2017 Macmule
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

"""See docstring for PkgInfo class"""

import os.path
import subprocess

from xml.etree import ElementTree

from autopkglib import Processor, ProcessorError


__all__ = ["PkgInfo"]


class PkgInfo(Processor):
    """Parses a distribution pkg to pull the info, other formats to be added later"""

    description = __doc__
    input_variables = {
    }

    output_variables = {
        "pkg_id": {
            "description": ("The package ID.."),
        },
        "version": {
            "description": ("The version of the pkg from it's info"),
        },
    }


    def main(self):
        """ Cobbled together from various sources, should extract information from a
            Distribution pkg"""
        # Build dir as needed,pinched with <3 from:
        # https://github.com/autopkg/autopkg/blob/master/Code/autopkglib/FlatPkgUnpacker.py#L72
        # Extract pkg info, pinched with <3 from:
        # https://github.com/munki/munki/blob/master/code/client/munkilib/pkgutils.py#L374
        self.env["abspkgpath"] = os.path.join(self.env["pathname"])
        file_path = os.path.join(self.env["RECIPE_CACHE_DIR"], "downloads")
        cmd_toc = ['/usr/bin/xar', '-tf', self.env["abspkgpath"]]
        proc = subprocess.Popen(cmd_toc, bufsize=-1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (toc, err) = proc.communicate()
        toc = toc.strip().split('\n')

        if proc.returncode == 0:
            # Walk trough the TOC entries
            if not os.path.exists('file_path'):
                try:
                    os.mkdir('file_path')
                except OSError as err:
                    print(
                        "Can't create %s: %s"
                        % ('file_path', err.strerror))

            for toc_entry in [item for item in toc
                              if item.startswith('Distribution')]:
                cmd_extract = ['/usr/bin/xar', '-xf', self.env["abspkgpath"], \
                               toc_entry, '-C', file_path]
                result = subprocess.call(cmd_extract)
        else:
            raise ProcessorError("pkg not found at pkg_path")

        dist_path = os.path.join(file_path, "Distribution")

        if not os.path.exists(dist_path):
            raise ProcessorError("Cannot find Distribution")
        else:
            tree = ElementTree.parse(dist_path)
            root = tree.getroot()
            for elem in tree.iter(tag='product'):
                version = elem.get("version")
            for elem in tree.iter(tag='pkg-ref'):
                pkg_id = elem.get("id")

        self.env["version"] = version
        self.env["pkg_id"] = pkg_id

if __name__ == '__main__':
    processor = PkgInfo()

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
See docstring for DistributionPkgInfo class
'''

# Standard imports
import os
import subprocess
from xml.etree import ElementTree

# Other imports
# pylint: disable=import-error
from autopkglib import Processor, ProcessorError


# Processor information
__all__ = ["DistributionPkgInfo"]
__version__ = '1.1.2'


# Class
# pylint: disable = too-few-public-methods
class DistributionPkgInfo(Processor):
    '''
        Parses a distribution pkg to pull the info, other formats to be added later
    '''

    description = __doc__

    input_variables = {
        "pkg_path": {
            "required": True,
            "description": ("Path to the Pkg.."),
        },
    }

    output_variables = {
        "pkg_id": {
            "description": ("The package ID.."),
        },
        "version": {
            "description": ("The version of the pkg from it's info"),
        },
    }

    # pylint: disable=too-many-branches
    def main(self):
        '''
            Cobbled together from various sources, should extract information from a
            Distribution pkg
        '''

        # Var declaration
        version = None
        pkg_id = None

        # Build dir as needed,pinched with <3 from:
        # https://github.com/autopkg/autopkg/blob/master/Code/autopkglib/FlatPkgUnpacker.py#L72
        # Extract pkg info, pinched with <3 from:
        # https://github.com/munki/munki/blob/master/code/client/munkilib/pkgutils.py#L374
        self.env["abspkgpath"] = os.path.join(self.env["pkg_path"])
        file_path = os.path.join(self.env["RECIPE_CACHE_DIR"], "downloads")
        cmd_toc = ['/usr/bin/xar', '-tf', self.env["abspkgpath"]]
        with (subprocess.Popen(cmd_toc, bufsize=-1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            as proc):
            (toc, err) = proc.communicate()
        toc = toc.decode("utf-8").strip().split('\n')

        if proc.returncode == 0:
            # Walk trough the TOC entries
            if not os.path.exists(file_path):
                os.mkdir(file_path)

            for toc_entry in [item for item in toc
                              if item.startswith('Distribution')]:
                cmd_extract = ['/usr/bin/xar', '-xf', self.env["abspkgpath"], \
                               toc_entry, '-C', file_path]
                _ = subprocess.call(cmd_extract)
        else:
            raise ProcessorError("pkg not found at pkg_path")

        # Path to Distribution
        dist_path = os.path.join(file_path, "Distribution")

        # If we cannot location Distribution, raise
        if not os.path.exists(dist_path):
            raise ProcessorError("Cannot find Distribution")

        # Read in XML
        tree = ElementTree.parse(dist_path)
        # Iterate over XML, raise if fails
        try:
            _ = tree.getroot()
            for elem in tree.iter(tag='product'):
                version = elem.get("version")
            for elem in tree.iter(tag='pkg-ref'):
                pkg_id = elem.get("id")
        except ElementTree.ParseError as err:
            self.output(f"Can't parse distribution file {dist_path}: {err.strerror}")

        # Raise of cannot get pkg_id
        if not pkg_id:
            raise ProcessorError("cannot get pkg_id")

        self.env["pkg_id"] = pkg_id

        # Raise if cannot get version
        if not version:
            raise ProcessorError("cannot get version")

        self.env["version"] = version

        # Tidy up
        os.remove(dist_path)


if __name__ == '__main__':
    PROCESSOR = DistributionPkgInfo()

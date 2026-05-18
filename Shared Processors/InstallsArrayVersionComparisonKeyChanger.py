'''
Copyright (c) 2024, dataJAR Ltd.  All rights reserved.
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
See docstring for PackageInfoVersioner class
'''

# Amended with <3 from https://github.com/autopkg/nmcspadden-recipes/blob/master/Shared_Processors/InstallsArrayFineTuning.py

from __future__ import absolute_import
from autopkglib import Processor, ProcessorError

__all__ = ["InstallsArrayVersionComparisonKeyChanger"]


class InstallsArrayVersionComparisonKeyChanger(Processor):
    """Change an installs array to allow fine-tuning of version_comparison_key."""

    description = __doc__
    input_variables = {
        "additional_pkginfo": {
            "required": True,
            "description": ("Dictionary containing an installs array."),
        },
        "changes": {
            "required": True,
            "description": (
                "List of dictionaries containing replacement values "
                "for installs comparison key. Each dictionary must contain a "
                "path and the new version_comparison_key."
            ),
        },
    }

    output_variables = {
        "changed_pkginfo": {"description": "Fine tuned additional_pkginfo dictionary."}
    }

    __doc__ = description

    def main(self):
        """Magic."""
        # Get the installs array and changes from environment
        current = self.env["additional_pkginfo"]["installs"]
        changes = self.env["changes"]

        # Process each change entry
        for change in changes:
            path = change.get("path", None)
            if not path:
                raise ProcessorError("No path found in change!")
            newversion_comparison_key = change.get("version_comparison_key", None)
            if not newversion_comparison_key:
                raise ProcessorError("No version_comparison_key found in change!")

            # Loop through installs array to apply changes
            for install in current:
                if install["path"] == path:
                    # Modify the version_comparison_key for the matching install
                    install["version_comparison_key"] = newversion_comparison_key

        # Retrieve the existing 'changed_pkginfo' dictionary, if it exists
        changed_pkginfo = self.env.get("changed_pkginfo", {})

        # Update only the 'installs' key in 'changed_pkginfo', keeping other data intact
        changed_pkginfo["installs"] = current

        # Update the environment with the fine-tuned package info
        self.env["changed_pkginfo"] = changed_pkginfo


if __name__ == "__main__":
    PROCESSOR = InstallsArrayVersionComparisonKeyChanger()
    PROCESSOR.execute_shell()

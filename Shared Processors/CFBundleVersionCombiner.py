#!/usr/local/autopkg/python
"""
CFBundleVersionCombiner Processor for AutoPkg
Combines CFBundleShortVersionString and CFBundleVersion from an app into a single version string.
Uses MunkiLooseVersion for version comparison but outputs string version.
"""

import os.path
import plistlib
from distutils.version import LooseVersion as MunkiLooseVersion

from autopkglib import Processor, ProcessorError

__all__ = ["CFBundleVersionCombiner"]

class CFBundleVersionCombiner(Processor):
    """Combines CFBundleShortVersionString and CFBundleVersion from an app's Info.plist into a single version string."""

    input_variables = {
        "app_path": {
            "required": True,
            "description": "Path to the app bundle to version.",
        },
    }
    output_variables = {
        "version": {
            "description": "Combined version number in format CFBundleShortVersionString.CFBundleVersion",
        }
    }

    description = __doc__

    def main(self):
        """Main process"""

        app_path = self.env["app_path"]
        info_plist_path = os.path.join(app_path, "Contents/Info.plist")

        if not os.path.exists(info_plist_path):
            raise ProcessorError(f"Info.plist not found: {info_plist_path}")

        try:
            with open(info_plist_path, 'rb') as f:
                info_plist = plistlib.load(f)

            short_version = info_plist.get("CFBundleShortVersionString", "0")
            bundle_version = info_plist.get("CFBundleVersion", "0")

            # Combine the versions
            combined_version = f"{short_version}.{bundle_version}"

            # Verify the version string is valid using MunkiLooseVersion
            try:
                MunkiLooseVersion(combined_version)
            except ValueError as err:
                raise ProcessorError(
                    f"Invalid version string '{combined_version}': {err}")

            self.env["version"] = combined_version
            self.output(f"Combined version: {combined_version}")

        except Exception as e:
            raise ProcessorError(f"Error reading Info.plist: {e}")

if __name__ == "__main__":
    PROCESSOR = CFBundleVersionCombiner()
    PROCESSOR.execute_main()

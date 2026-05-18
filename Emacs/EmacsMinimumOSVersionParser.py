#!/usr/local/autopkg/python
"""
AutoPkg Processor to determine minimum OS version from Emacs binary filenames in an app bundle.
Selects the most permissive (lowest) OS version requirement.
"""

import os
from autopkglib import Processor, ProcessorError, DmgMounter

__all__ = ["EmacsMinimumOSVersionParser"]

class EmacsMinimumOSVersionParser(DmgMounter):
    """Determines most permissive (lowest) minimum OS version by parsing Emacs binary filenames."""

    description = __doc__
    input_variables = {
        "pathname": {
            "required": True,
            "description": "Path to the DMG file",
        },
        "app_name": {
            "required": True,
            "description": "Name of the app bundle (e.g., 'Emacs.app')",
        }
    }
    output_variables = {
        "minimum_os_version": {
            "description": "Most permissive (lowest) minimum OS version found in binary filenames",
        }
    }

    def get_version_from_filename(self, filename):
        """Extract and format the OS version from a binary filename."""
        try:
            # Ignore .pdmp files
            if filename.endswith('.pdmp'):
                return None

            # Split by '-' and get the last part which should contain the version
            parts = filename.split('-')
            if len(parts) < 2:
                return None

            version_part = parts[-1]

            # If there's no version information, return None
            if not any(c.isdigit() for c in version_part):
                return None

            # Replace '_' with '.' in version number
            version = version_part.replace('_', '.')
            return version
        except:
            return None

    def version_to_tuple(self, version_str):
        """Convert version string to tuple for comparison."""
        try:
            # Split version into components and pad with zeros for consistent comparison
            components = [int(x) for x in version_str.split('.')]
            # Pad with zeros to handle different version number lengths
            while len(components) < 2:
                components.append(0)
            return components
        except:
            return None

    def main(self):
        """Main process"""
        mount_point = None
        try:
            # Mount the DMG
            mount_point = self.mount(self.env["pathname"])

            # Construct path to MacOS directory
            app_path = os.path.join(mount_point, self.env["app_name"])
            macos_path = os.path.join(app_path, "Contents", "MacOS")

            if not os.path.exists(macos_path):
                raise ProcessorError(f"MacOS directory not found at: {macos_path}")

            # Get all binary files and their versions
            versions = set()  # Using set to remove duplicates
            for item in os.listdir(macos_path):
                version = self.get_version_from_filename(item)
                if version:
                    versions.add(version)

            if not versions:
                raise ProcessorError("No valid version numbers found in binary filenames")

            # Convert version strings to comparable tuples
            version_info = []
            for version in versions:
                tuple_version = self.version_to_tuple(version)
                if tuple_version:
                    version_info.append((tuple_version, version))

            # Sort versions and get the lowest (most permissive) version
            min_version_tuple = min(version_info, key=lambda x: x[0])
            min_version = min_version_tuple[1]

            self.env["minimum_os_version"] = min_version
            self.output(f"Most permissive minimum OS version found: {min_version}")
            self.output(f"All unique OS versions found: {', '.join(sorted(versions))}")

        except Exception as err:
            raise ProcessorError(f"Error determining minimum OS version: {err}")
        finally:
            try:
                if mount_point:
                    self.unmount(mount_point)
            except:
                # Ignore unmounting errors since they don't affect our results
                pass

if __name__ == "__main__":
    PROCESSOR = EmacsMinimumOSVersionParser()
    PROCESSOR.execute_main()

#!/usr/local/autopkg/python
"""
GetBinaryMinimumOSVersion.py

Extracts the highest minimum OS version requirement from all binaries in an application
"""

import os
import subprocess
from autopkglib import Processor, ProcessorError
from distutils.version import LooseVersion
import glob

__all__ = ["GetBinaryMinimumOSVersion"]

class GetBinaryMinimumOSVersion(Processor):
    """Determines highest minimum OS version requirement using otool across all binaries."""

    description = __doc__
    input_variables = {
        "app_path": {
            "required": True,
            "description": "Path to the application bundle or binary to analyze. "
                         "Can be a path within a DMG.",
        },
        "search_path": {
            "required": False,
            "description": "Optional: Specific path within the app bundle to search for binaries. "
                         "Defaults to Contents/MacOS",
        }
    }
    output_variables = {
        "min_os_ver": {
            "description": "Highest minimum OS version requirement found across all binaries.",
        },
        "analyzed_binaries": {
            "description": "Dictionary of analyzed binaries and their minimum OS versions.",
        }
    }

    def mount_dmg(self, dmg_path):
        """
        Mount DMG and return mount point.
        """
        try:
            cmd = ['/usr/bin/hdiutil', 'attach', dmg_path, '-nobrowse', '-plist']
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = proc.communicate()

            if proc.returncode:
                raise ProcessorError(f"hdiutil attach failed with error: {stderr.decode()}")

            # Find mount point from plist output
            from plistlib import loads
            plist = loads(stdout)
            for entity in plist.get('system-entities', []):
                if 'mount-point' in entity:
                    return entity['mount-point']

            raise ProcessorError("No mount point found in hdiutil output")
        except Exception as e:
            raise ProcessorError(f"Error mounting DMG: {e}")

    def unmount_dmg(self, mount_point):
        """
        Unmount a DMG given its mount point.
        """
        try:
            subprocess.check_call(['/usr/bin/hdiutil', 'detach', mount_point])
        except subprocess.CalledProcessError as e:
            raise ProcessorError(f"Error unmounting DMG: {e}")

    def is_macho_binary(self, path):
        """Check if a file is a Mach-O binary."""
        try:
            cmd = ['/usr/bin/file', path]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, _ = process.communicate()
            output = stdout.decode('utf-8')
            return 'Mach-O' in output
        except:
            return False

    def get_binary_min_os(self, binary_path):
        """Get minimum OS version for a specific binary."""
        try:
            cmd = ['/usr/bin/otool', '-l', binary_path]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()

            if process.returncode != 0:
                self.output(f"Warning: otool failed for {binary_path}: {stderr.decode()}")
                return None

            output_lines = stdout.decode().split('\n')
            for line in output_lines:
                if 'minos' in line:
                    return line.strip().split()[-1]

            return None

        except Exception as e:
            self.output(f"Warning: Error processing {binary_path}: {e}")
            return None

    def find_binaries(self, search_path):
        """Find all Mach-O binaries in the specified directory."""
        binaries = []
        try:
            for item in os.listdir(search_path):
                full_path = os.path.join(search_path, item)
                if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                    if self.is_macho_binary(full_path):
                        binaries.append(full_path)
        except Exception as e:
            raise ProcessorError(f"Error searching for binaries: {e}")

        return binaries

    def main(self):
        """Main process"""
        app_path = self.env["app_path"]
        mount_point = None

        try:
            # Check if the path is inside a DMG
            if '.dmg/' in app_path:
                dmg_path = app_path.split('.dmg/')[0] + '.dmg'
                relative_path = app_path.split('.dmg/')[-1]

                if os.path.exists(dmg_path):
                    mount_point = self.mount_dmg(dmg_path)
                    app_path = os.path.join(mount_point, relative_path)

            if not os.path.exists(app_path):
                raise ProcessorError(f"App path does not exist: {app_path}")

            # Determine search path
            if "search_path" in self.env:
                search_path = os.path.join(app_path, self.env["search_path"])
            else:
                if app_path.endswith('.app'):
                    search_path = os.path.join(app_path, 'Contents', 'MacOS')
                else:
                    search_path = os.path.dirname(app_path)

            if not os.path.exists(search_path):
                raise ProcessorError(f"Search path does not exist: {search_path}")

            # Find all binaries
            binaries = self.find_binaries(search_path)
            if not binaries:
                raise ProcessorError(f"No executable binaries found in {search_path}")

            # Analyze each binary
            binary_versions = {}
            highest_version = '0.0'

            for binary in binaries:
                min_os = self.get_binary_min_os(binary)
                if min_os:
                    binary_versions[os.path.basename(binary)] = min_os
                    try:
                        if LooseVersion(min_os) > LooseVersion(highest_version):
                            highest_version = min_os
                    except Exception as e:
                        self.output(f"Warning: Version comparison failed for {min_os}: {e}")

            if not binary_versions:
                raise ProcessorError("Could not determine minimum OS version from any binary")

            # Set output variables
            self.env["min_os_ver"] = highest_version
            self.env["analyzed_binaries"] = binary_versions

            # Output results
            self.output(f"Analyzed {len(binary_versions)} binaries:")
            for binary, version in binary_versions.items():
                self.output(f"  {binary}: {version}")
            self.output(f"Highest minimum OS version requirement: {highest_version}")

        finally:
            # Always unmount DMG if we mounted it
            if mount_point and os.path.exists(mount_point):
                self.unmount_dmg(mount_point)

if __name__ == '__main__':
    PROCESSOR = GetBinaryMinimumOSVersion()
    PROCESSOR.execute_main()

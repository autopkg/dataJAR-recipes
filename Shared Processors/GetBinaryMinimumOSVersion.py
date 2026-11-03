#!/usr/local/autopkg/python
"""
GetBinaryMinimumOSVersion.py

Extracts the highest minimum OS version requirement from all binaries in an application
"""

import os
import plistlib
import re
import subprocess

from autopkglib import Processor, ProcessorError
from autopkglib import APLooseVersion as LooseVersion

__all__ = ["GetBinaryMinimumOSVersion"]

# Mach-O magic numbers, as the first four bytes of the file.
MACHO_MAGICS = {
    b"\xfe\xed\xfa\xce",  # 32-bit
    b"\xfe\xed\xfa\xcf",  # 64-bit
    b"\xce\xfa\xed\xfe",  # 32-bit, reverse byte order
    b"\xcf\xfa\xed\xfe",  # 64-bit, reverse byte order
}
# Universal ("fat") binaries share their magic number with Java class files. The next four
# bytes are the slice count for a fat binary, but a Java class version (always 45+) otherwise.
FAT_MAGICS = {b"\xca\xfe\xba\xbe", b"\xca\xfe\xba\xbf"}
MAX_FAT_SLICES = 32

# Values otool prints for the macOS platform in an LC_BUILD_VERSION load command.
MACOS_PLATFORMS = {"1", "MACOS"}

DMG_PATH_RE = re.compile(r"\.dmg(?:/|$)", re.IGNORECASE)
DISK_DEVICE_RE = re.compile(r"^(?:/dev/)?disk\d+$")
COMMAND_TIMEOUT = 120  # seconds, so a prompt or hung tool can't stall the AutoPkg run
ATTACH_TIMEOUT = 900  # attaching a large DMG can verify checksums and take a while


def whole_disks(entities):
    """Names (e.g. 'disk4') of the whole-disk devices in diskutil/hdiutil system-entities.

    diskutil prints 'disk4' where hdiutil prints '/dev/disk4', so normalise to compare them.
    """
    return [e["dev-entry"].replace('/dev/', '', 1) for e in entities
            if DISK_DEVICE_RE.match(e.get("dev-entry", ""))]


def highest_version(versions):
    """Return the highest of an iterable of version strings, or None."""
    highest = None
    for version in versions:
        if highest is None or LooseVersion(version) > LooseVersion(highest):
            highest = version
    return highest


def to_bool(value):
    """Interpret recipe and command-line values such as 'False' or 'no' as booleans."""
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "y", "on")
    return bool(value)


class GetBinaryMinimumOSVersion(Processor):
    """Determines highest minimum OS version requirement using otool across all binaries."""

    description = __doc__
    input_variables = {
        "app_path": {
            "required": True,
            "description": "Path to the application bundle, binary or directory to analyze. "
                           "Can be a path within a DMG, or a DMG itself.",
        },
        "search_path": {
            "required": False,
            "description": "Optional: Specific path within the app bundle to search for binaries. "
                           "Defaults to Contents/MacOS",
        },
        "recursive": {
            "required": False,
            "description": "Optional: Search subdirectories of the search path as well. "
                           "Defaults to False (top level only).",
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

    def run_command(self, cmd, timeout=COMMAND_TIMEOUT):
        """Run a command without stdin and with a timeout. Raises ProcessorError on failure to run."""
        try:
            return subprocess.run(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, timeout=timeout)
        except (OSError, subprocess.TimeoutExpired) as err:
            raise ProcessorError(f"Error running {cmd[0]}: {err}")

    def attached_disks(self, dmg_path):
        """Find whole-disk devices that a DMG is currently attached as."""
        try:
            proc = self.run_command(['/usr/bin/hdiutil', 'info', '-plist'])
            images = plistlib.loads(proc.stdout).get("images", [])
        except Exception as err:
            self.output(f"Warning: could not list attached disk images: {err}")
            return []
        real_dmg = os.path.realpath(dmg_path)
        disks = []
        for image in images:
            if os.path.realpath(image.get("image-path", "")) != real_dmg:
                continue
            disks.extend(whole_disks(image.get("system-entities", [])))
        return disks

    def mount_dmg(self, dmg_path):
        """Mount DMG read-only and return (mount_points, whole_disk_devices).

        If anything goes wrong after the image may have been attached, the devices this run
        attached (but not ones that were already attached before it) are ejected again.
        """
        before = set(self.attached_disks(dmg_path))

        def clean_up():
            self.unmount_dmg([d for d in self.attached_disks(dmg_path) if d not in before])

        try:
            proc = self.run_command(['/usr/sbin/diskutil', 'image', 'attach', '--plist',
                                     '--readOnly', '--nobrowse', dmg_path],
                                    timeout=ATTACH_TIMEOUT)
        except ProcessorError:
            clean_up()  # a timeout can leave the image attaching in the background
            raise
        if proc.returncode:
            raise ProcessorError(
                f"Error mounting DMG: diskutil image attach failed: {proc.stderr.decode(errors='replace')}")

        try:
            entities = plistlib.loads(proc.stdout).get("system-entities", [])
            mount_points = [e["mount-point"] for e in entities if e.get("mount-point")]
            # Whole-disk devices (e.g. disk4, not disk4s1)
            disks = whole_disks(entities)
            if not mount_points:
                raise ValueError("no mount point found in diskutil output")
        except Exception as err:
            clean_up()
            raise ProcessorError(f"Error mounting DMG: {err}")
        # Only eject what this run attached; leave anything that was already mounted alone
        return mount_points, [d for d in disks if d not in before]

    def unmount_dmg(self, disks):
        """Eject mounted DMG devices. Never raises, so it can't mask an earlier error."""
        for disk in disks:
            device = disk if disk.startswith('/dev/') else f'/dev/{disk}'
            # Ejecting one device can detach others (e.g. an APFS container)
            if not os.path.exists(device):
                continue
            error = ""
            for cmd in (['/usr/sbin/diskutil', 'eject', device],
                        ['/usr/sbin/diskutil', 'eject', 'force', device]):
                try:
                    proc = self.run_command(cmd)
                except ProcessorError as err:
                    error = str(err)
                    continue
                if proc.returncode == 0:
                    break
                error = proc.stderr.decode(errors='replace').strip()
            else:
                if os.path.exists(device):
                    self.output(f"Warning: could not eject {device}: {error}")

    def is_macho_binary(self, path):
        """Check if a file is a Mach-O or universal binary by its magic number."""
        try:
            with open(path, 'rb') as handle:
                header = handle.read(8)
        except OSError:
            return False
        if header[:4] in MACHO_MAGICS:
            return True
        if header[:4] in FAT_MAGICS and len(header) == 8:
            return 0 < int.from_bytes(header[4:], 'big') <= MAX_FAT_SLICES
        return False

    def get_binary_min_os(self, binary_path):
        """Get the highest macOS minimum OS version across all slices of a binary."""
        try:
            process = self.run_command(['/usr/bin/otool', '-l', binary_path])
        except ProcessorError as err:
            self.output(f"Warning: Error processing {binary_path}: {err}")
            return None

        if process.returncode != 0:
            self.output(f"Warning: otool failed for {binary_path}: {process.stderr.decode(errors='replace')}")
            return None

        # Modern binaries use LC_BUILD_VERSION ("minos X", with a platform); older ones, such
        # as many x86_64 builds, use LC_VERSION_MIN_MACOSX ("version X"). Universal binaries
        # have one load command per slice, so collect them all.
        versions = []
        current_cmd = None
        platform = None
        for line in process.stdout.decode(errors='replace').split('\n'):
            parts = line.strip().split()
            if len(parts) != 2:
                continue
            key, value = parts
            if key == 'cmd':
                current_cmd = value
                platform = None
            elif key == 'platform':
                platform = value
            elif key == 'minos' and current_cmd == 'LC_BUILD_VERSION':
                # Ignore Mac Catalyst, iOS and other non-macOS version numbers
                if platform is None or platform.upper() in MACOS_PLATFORMS:
                    versions.append(value)
                else:
                    self.output(f"Warning: ignoring minos {value} for non-macOS platform "
                                f"{platform} in {binary_path}")
            elif key == 'version' and current_cmd == 'LC_VERSION_MIN_MACOSX':
                versions.append(value)

        try:
            return highest_version(versions)
        except Exception as err:
            self.output(f"Warning: Version comparison failed for {binary_path}: {err}")
            return None

    def walk_error(self, err):
        """Report directories that could not be read instead of silently skipping them."""
        self.output(f"Warning: could not read {err.filename}: {err.strerror}")

    def find_binaries(self, search_path, recursive=False):
        """Find Mach-O binaries at, or in, the specified path.

        A file given directly is analyzed as is. In a directory, regular files are checked,
        either at the top level or recursively. Symlinks within the tree are followed and
        de-duplicated; symlinks pointing outside it are ignored.
        """
        if os.path.isfile(search_path):
            return [search_path] if self.is_macho_binary(search_path) else []

        candidates = []
        for root, dirs, files in os.walk(search_path, onerror=self.walk_error):
            candidates.extend(os.path.join(root, name) for name in sorted(files))
            if not recursive:
                break
            dirs.sort()

        binaries, seen = [], set()
        root_real = os.path.join(os.path.realpath(search_path), '')
        # Real files first, so a symlink to a binary doesn't hide the binary's own name
        for path in sorted(candidates, key=os.path.islink):
            real = os.path.realpath(path)
            if real in seen or not os.path.isfile(real) or not self.is_macho_binary(real):
                continue
            if os.path.islink(path) and not real.startswith(root_real):
                # Points outside the tree (e.g. a system binary), so it isn't part of the app
                self.output(f"Warning: ignoring symlink outside search path: {path}")
                continue
            seen.add(real)
            binaries.append(path)
        return binaries

    def resolve_search_path(self, app_path):
        """Work out where to look for binaries."""
        search = self.env.get("search_path")
        if search:
            # Relative to app_path even if given with a leading slash
            return os.path.join(app_path, search.lstrip('/'))
        macos_dir = os.path.join(app_path, 'Contents', 'MacOS')
        # Any bundle (.app, .prefPane, .plugin, ...) keeps its executables in Contents/MacOS
        if app_path.lower().endswith('.app') or os.path.isdir(macos_dir):
            return macos_dir
        return app_path

    def main(self):
        """Main process"""
        app_path = self.env["app_path"]
        if len(app_path) > 1:
            app_path = app_path.rstrip('/')
        disks = []
        mounted = False

        try:
            # Check if the path is, or is inside, a DMG
            match = DMG_PATH_RE.search(app_path)
            if match:
                dmg_path = app_path[:match.end()].rstrip('/')
                relative_path = app_path[match.end():].lstrip('/')
                if os.path.isfile(dmg_path):
                    mount_points, disks = self.mount_dmg(dmg_path)
                    mounted = True
                    candidates = [os.path.join(mp, relative_path) for mp in mount_points]
                    app_path = next((c for c in candidates if os.path.exists(c)),
                                    candidates[0])
                elif not os.path.exists(app_path):
                    raise ProcessorError(f"DMG does not exist: {dmg_path}")

            if not os.path.exists(app_path):
                raise ProcessorError(f"App path does not exist: {app_path}")

            # A DMG given on its own: use the app at the top level of the volume
            if mounted and not match.group(0).endswith('/') and not self.env.get("search_path"):
                apps = sorted(n for n in os.listdir(app_path) if n.lower().endswith('.app'))
                if len(apps) != 1:
                    raise ProcessorError(
                        f"Expected exactly one .app at the top of the DMG, found {apps or 'none'}; "
                        "give app_path as <dmg>/<App>.app")
                app_path = os.path.join(app_path, apps[0])

            search_path = self.resolve_search_path(app_path)
            if not os.path.exists(search_path):
                raise ProcessorError(f"Search path does not exist: {search_path}")

            # Find all binaries
            binaries = self.find_binaries(search_path, to_bool(self.env.get("recursive", False)))
            if not binaries:
                raise ProcessorError(f"No Mach-O binaries found in {search_path}")

            # Analyze each binary
            binary_versions = {}
            for binary in binaries:
                min_os = self.get_binary_min_os(binary)
                if not min_os:
                    self.output(f"Warning: no macOS minimum version found in {binary}, skipping")
                    continue
                name = (os.path.basename(binary) if os.path.isfile(search_path)
                        else os.path.relpath(binary, search_path))
                binary_versions[name] = min_os

            try:
                highest = highest_version(binary_versions.values())
            except Exception as err:
                raise ProcessorError(f"Could not compare minimum OS versions: {err}")
            if highest is None:
                raise ProcessorError("Could not determine minimum OS version from any binary")

            # Set output variables
            self.env["min_os_ver"] = highest
            self.env["analyzed_binaries"] = binary_versions

            # Output results
            self.output(f"Analyzed {len(binary_versions)} binaries:")
            for binary, version in binary_versions.items():
                self.output(f"  {binary}: {version}")
            self.output(f"Highest minimum OS version requirement: {highest}")

        finally:
            # Always unmount DMG if we mounted it
            self.unmount_dmg(disks)


if __name__ == '__main__':
    PROCESSOR = GetBinaryMinimumOSVersion()
    PROCESSOR.execute_main()

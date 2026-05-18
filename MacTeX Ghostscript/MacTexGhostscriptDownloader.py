#!/usr/local/autopkg/python
"""
MacTexGhostscriptDownloader processor for AutoPkg
Downloads the latest stable release of MacTeX Ghostscript, ignoring prereleases
"""

import re
from autopkglib import Processor, ProcessorError, URLGetter

__all__ = ["MacTexGhostscriptDownloader"]

class MacTexGhostscriptDownloader(URLGetter):
    """Downloads the latest stable MacTeX Ghostscript package."""

    description = __doc__
    input_variables = {
        "base_url": {
            "required": True,
            "description": "Base URL for MacTeX Ghostscript downloads",
        },
    }
    output_variables = {
        "url": {
            "description": "URL to the latest stable MacTeX Ghostscript package.",
        },
        "version": {
            "description": "Version of the latest stable MacTeX Ghostscript.",
        },
    }

    def get_version_context(self, html_text, version):
        """
        Get the surrounding context for a specific version.
        Returns the paragraph or section of text that introduces this version.
        """
        # Look for text that introduces this version
        patterns = [
            # Pattern for pre-release or release announcements
            rf'(?:[^<>]{{0,500}})?Ghostscript[- ]{re.escape(version)}[^<>]*(?=<)',
            # Backup pattern if the above doesn't match
            rf'[^<>]*Ghostscript[- ]{re.escape(version)}[^<>]*'
        ]

        for pattern in patterns:
            matches = re.findall(pattern, html_text, re.IGNORECASE | re.DOTALL)
            if matches:
                # Return the longest match as it likely has the most context
                return max(matches, key=len)

        return ""

    def is_prerelease(self, html_text, version):
        """
        Determine if a version is marked as pre-release in the HTML text.
        """
        context = self.get_version_context(html_text, version)
        if not context:
            return False

        # Debug output
        self.output(f"Context for version {version}:")
        self.output(context[:200] + "..." if len(context) > 200 else context)

        # Look for pre-release indicators in the context
        prerelease_indicators = [
            'pre-release version',
            'pre-release',
            'preview',
            'beta',
            'alpha'
        ]

        context_lower = context.lower()
        for indicator in prerelease_indicators:
            if indicator.lower() in context_lower:
                self.output(f"Found pre-release indicator '{indicator}' for version {version}")
                return True

        return False

    def get_ghostscript_version(self, html):
        """Parse the HTML to find the latest stable version."""
        # Regular expression to match version numbers in the format X.XX.X
        version_pattern = r'Ghostscript[- ](\d+\.\d+\.\d+)\.pkg'

        # Find all version numbers in the HTML
        versions = re.finditer(version_pattern, html)

        latest_stable_version = None
        latest_stable_url = None

        found_versions = []
        for match in versions:
            version = match.group(1)
            found_versions.append(version)

            # Skip if this is a pre-release version
            if self.is_prerelease(html, version):
                self.output(f"Skipping pre-release version {version}")
                continue

            # If we haven't set a version yet, or if this version is newer
            if (not latest_stable_version or
                self.compare_versions(version, latest_stable_version) > 0):
                latest_stable_version = version
                latest_stable_url = f"Ghostscript-{version}.pkg"

        if not found_versions:
            raise ProcessorError("No versions found in the HTML")

        if not latest_stable_version:
            raise ProcessorError("No stable version found")

        return latest_stable_version, latest_stable_url

    def compare_versions(self, version1, version2):
        """Compare two version strings."""
        v1_parts = [int(x) for x in version1.split('.')]
        v2_parts = [int(x) for x in version2.split('.')]

        for i in range(max(len(v1_parts), len(v2_parts))):
            v1 = v1_parts[i] if i < len(v1_parts) else 0
            v2 = v2_parts[i] if i < len(v2_parts) else 0
            if v1 > v2:
                return 1
            elif v1 < v2:
                return -1
        return 0

    def main(self):
        """Main process."""
        # Download HTML from base_url
        html = self.download(self.env["base_url"], text=True)

        # Get the latest stable version and URL
        version, pkg_name = self.get_ghostscript_version(html)

        # Construct full URL
        download_url = f"{self.env['base_url']}{pkg_name}"

        self.env["url"] = download_url
        self.env["version"] = version

        self.output(f"Found stable MacTeX Ghostscript version: {version}")
        self.output(f"Download URL: {download_url}")

#!/usr/local/autopkg/python
"""
Opera GX Version Provider

This processor fetches the latest version of Opera GX directly from the official CDN directory
"""

import re
from autopkglib import ProcessorError, URLGetter

__all__ = ["OperaGXVersionProvider"]


class OperaGXVersionProvider(URLGetter):
    """Gets the latest Opera GX version from the CDN directory listing."""

    description = __doc__
    input_variables = {
        "version_url": {
            "required": False,
            "default": "https://download3.operacdn.com/ftp/pub/opera_gx/",
            "description": "URL to the Opera GX CDN directory"
        }
    }
    output_variables = {
        "version": {
            "description": "The latest Opera GX version"
        }
    }

    def main(self):
        """Main processor execution."""
        version_url = self.env.get("version_url")

        try:
            # Fetch the directory listing
            content = self.download(version_url, text=True)
        except Exception as e:
            raise ProcessorError(f"Could not retrieve version URL {version_url}: {e}")

        # Find all version directories using regex
        # Look for pattern like: <a href="122.0.5643.52/">
        version_pattern = r'<a href="(\d+\.\d+\.\d+\.\d+)/">'
        versions = re.findall(version_pattern, content)

        if not versions:
            raise ProcessorError("No version directories found in CDN listing")

        # Sort versions using version comparison
        # Convert version strings to tuples of integers for proper sorting
        def version_key(version):
            return tuple(map(int, version.split('.')))

        sorted_versions = sorted(versions, key=version_key)
        latest_version = sorted_versions[-1]

        self.output(f"Found versions: {len(versions)}")
        self.output(f"Latest version: {latest_version}")

        # Set the version output variable
        self.env["version"] = latest_version


if __name__ == "__main__":
    PROCESSOR = OperaGXVersionProvider()
    PROCESSOR.execute_shell()

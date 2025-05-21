#!/usr/local/autopkg/python


"""Processor for extracting SQL Developer version information."""

from __future__ import absolute_import
from typing import Iterator, TextIO
import configparser
import os.path
from autopkglib import Processor, ProcessorError


class SQLDeveloperVersioner(Processor):
    """Processor that extracts version information from SQLDeveloper's version.properties file."""

    PROPERTIES_RELATIVE_PATH = "Contents/Resources/sqldeveloper/sqldeveloper/bin/version.properties"
    VERSION_PROPERTY_KEY = "VER_FULL"
    PROPERTIES_SECTION = "properties"

    description = "Extracts version information from SQLDeveloper.app's version.properties file."
    input_variables = {
        "app_path": {
            "required": True,
            "description": "Path to SQLDeveloper.app bundle.",
        }
    }
    output_variables = {
        "version": {
            "description": "Extracted version of SQL Developer."
        }
    }

    def _add_section_header(self, properties_file: TextIO, section_name: str) -> Iterator[str]:
        """
        Adds a section header to a properties file to make it compatible with configparser.

        Args:
            properties_file: File object containing properties
            section_name: Name of the section to add

        Yields:
            Lines of the modified properties file content
        """
        yield f'[{section_name}]\n'
        yield from properties_file

    def _get_properties_path(self) -> str:
        """
        Constructs the full path to the version.properties file.

        Returns:
            str: Full path to the version.properties file

        Raises:
            ProcessorError: If app_path is not set
        """
        try:
            return os.path.join(self.env["app_path"], self.PROPERTIES_RELATIVE_PATH)
        except KeyError as err:
            raise ProcessorError("Required app_path input variable is missing") from err

    def _read_version(self, properties_path: str) -> str:
        """
        Reads the version from the properties file.

        Args:
            properties_path: Path to the version.properties file

        Returns:
            str: Version string from the properties file

        Raises:
            ProcessorError: If file cannot be read or parsed
        """
        try:
            with open(properties_path, encoding="utf-8") as prop_file:
                config = configparser.ConfigParser()
                config.read_file(
                    self._add_section_header(prop_file, self.PROPERTIES_SECTION),
                    source=properties_path
                )
                return config[self.PROPERTIES_SECTION][self.VERSION_PROPERTY_KEY]
        except (IOError, KeyError, configparser.Error) as err:
            raise ProcessorError(
                f"Error reading version from {properties_path}: {str(err)}"
            ) from err

    def main(self):
        """Main processor logic to extract SQL Developer version."""
        properties_path = self._get_properties_path()
        self.env["version"] = self._read_version(properties_path)
        self.output(f"Version: {self.env['version']}")


if __name__ == "__main__":
    PROCESSOR = SQLDeveloperVersioner()
    PROCESSOR.execute_shell()

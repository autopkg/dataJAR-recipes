#!/usr/local/autopkg/python
# Copyright (c) 2026, Jamf Software, LLC. All rights reserved.

import plistlib
import struct
from xml.parsers.expat import ExpatError

from autopkglib import Processor, ProcessorError

__all__ = ["PlistNestedKeyReader"]


class PlistNestedKeyReader(Processor):
    """Read a value from a nested key in a plist, e.g. JavaVM:JVMMinimumSystemVersion.

    The core PlistReader processor can only read top-level keys.
    """

    description = __doc__
    input_variables = {
        "plist_path": {
            "required": True,
            "description": "Path to the plist file to read.",
        },
        "key_path": {
            "required": True,
            "description": (
                "Colon separated path to the key, e.g. JavaVM:JVMMinimumSystemVersion."
            ),
        },
        "normalize_version": {
            "required": False,
            "description": (
                "If set to a true value (true, yes, y or 1), leading zeros are "
                "removed from each numeric component of the dotted version, "
                "e.g. 11.00.00 becomes 11.0.0. Non-numeric components are left "
                "as they are."
            ),
        },
        "result_output_var_name": {
            "required": False,
            "description": "Name of the output variable. Defaults to 'plist_value'.",
            "default": "plist_value",
        },
    }
    output_variables = {
        "plist_value": {
            "description": (
                "The value found at key_path. The variable name can be changed "
                "with result_output_var_name."
            )
        },
    }

    __doc__ = description

    def main(self):
        """Read the nested key and set the output variable."""
        plist_path = self.env["plist_path"]
        key_path = self.env["key_path"]

        try:
            with open(plist_path, "rb") as plist_file:
                value = plistlib.load(plist_file)
        except (OSError, ValueError, ExpatError, struct.error) as err:
            raise ProcessorError(f"Unable to read {plist_path}: {err}") from err

        for key in key_path.split(":"):
            if not isinstance(value, dict) or key not in value:
                raise ProcessorError(f"Key path '{key_path}' not found in {plist_path}")
            value = value[key]

        if str(self.env.get("normalize_version", "")).strip().lower() in (
            "true",
            "yes",
            "y",
            "1",
        ):
            value = ".".join(
                str(int(part)) if part.isdecimal() else part
                for part in str(value).split(".")
            )

        output_var = self.env.get("result_output_var_name", "plist_value")
        self.env[output_var] = value
        self.output(f"Assigning value of '{value}' to output variable '{output_var}'")


if __name__ == "__main__":
    PROCESSOR = PlistNestedKeyReader()
    PROCESSOR.execute_shell()

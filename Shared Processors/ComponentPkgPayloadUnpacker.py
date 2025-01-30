#!/usr/local/autopkg/python
#
# Copyright (c) 2025, dataJAR Ltd.  All rights reserved.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#         * Redistributions of source code must retain the above copyright
#           notice, this list of conditions and the following disclaimer.
#         * Redistributions in binary form must reproduce the above copyright
#           notice, this list of conditions and the following disclaimer in the
#           documentation and/or other materials provided with the distribution.
#         * Neither data JAR Ltd nor the names of its contributors may be used to
#           endorse or promote products derived from this software without specific
#           prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY DATA JAR LTD 'AS IS' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL DATA JAR LTD BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# SUPPORT FOR THIS PROGRAM
# This program is distributed 'as is' by DATA JAR LTD.
# For more information or support, please utilise the following resources:
#         http://www.datajar.co.uk

from autopkglib import Processor, ProcessorError
from autopkglib.PkgPayloadUnpacker import PkgPayloadUnpacker
import os
import subprocess

class ComponentPkgPayloadUnpacker(PkgPayloadUnpacker):
    """Unpack component package payloads using pkgutil."""

    description = __doc__

    input_variables = {
        "pkg_path": {
            "required": True,
            "description": "Path to the package to expand.",
        },
        "destination_path": {
            "required": True,
            "description": "Path where the payload will be unpacked.",
        },
        "purge_destination": {
            "required": False,
            "description": "Whether to purge the destination directory before unpacking.",
            "default": True,
        },
    }

    output_variables = {
        "unpacked_path": {
            "description": "Path to the unpacked payload.",
        },
    }

    def main(self):
        pkg_path = self.env["pkg_path"]
        destination_path = self.env["destination_path"]
        purge_destination = self.env.get("purge_destination", True)

        # Verify package exists
        if not os.path.exists(pkg_path):
            raise ProcessorError(f"Package at path {pkg_path} does not exist")

        # Create or purge destination path
        if os.path.exists(destination_path):
            if purge_destination:
                try:
                    subprocess.run(["rm", "-rf", destination_path], check=True)
                    os.makedirs(destination_path)
                except subprocess.CalledProcessError as err:
                    raise ProcessorError(f"Error purging destination path: {err}")
        else:
            try:
                os.makedirs(destination_path)
            except OSError as err:
                raise ProcessorError(f"Error creating destination path: {err}")

        try:
            # Use pkgutil to expand the package
            cmd = [
                "/usr/sbin/pkgutil",
                "--expand",
                pkg_path,
                os.path.join(destination_path, "expanded_pkg")
            ]
            subprocess.run(cmd, check=True)

            # Extract the payload
            expanded_path = os.path.join(destination_path, "expanded_pkg")
            payload_path = os.path.join(expanded_path, "Payload")
            if os.path.exists(payload_path):
                cmd = [
                    "/usr/bin/ditto",
                    "-x",
                    "-z",
                    payload_path,
                    os.path.join(destination_path, "payload")
                ]
                subprocess.run(cmd, check=True)

            self.env["unpacked_path"] = os.path.join(destination_path, "payload")
            self.output(f"Unpacked payload to: {self.env['unpacked_path']}")

        except subprocess.CalledProcessError as err:
            raise ProcessorError(f"Error unpacking package: {err}")

if __name__ == "__main__":
    PROCESSOR = ComponentPkgPayloadUnpacker()
    PROCESSOR.execute_shell()

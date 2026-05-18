#!/usr/local/autopkg/python
# pylint: disable = invalid-name

'''
[Previous sections remain the same]
'''

# Standard Imports
from __future__ import absolute_import
import subprocess
import os
import sys

# AutoPkg imports
from autopkglib import Processor, ProcessorError


__all__ = ['OnePasswordCLIVersioner']
__version__ = '1.0'


class OnePasswordCLIVersioner(Processor):
    '''
        Returns the version from the 1Password CLI binary

        Raising if the key is not found.
    '''

    description = __doc__
    input_variables = {
        'binary_path': {
            'required': True,
            'description': ('Path to the 1Password CLI binary.'),
        },
    }

    output_variables = {
        'version': {
            'description': ('Version of the 1Password CLI binary.'),
        },
    }

    def main(self):
        '''
            See docstring for OnePasswordCLIVersioner class
        '''

        # var declaration
        version = None

        # Progress notification
        self.output("Starting 1Password CLI version check...")
        self.output("Binary path to check: {}".format(self.env['binary_path']))

        # If binary exists
        if os.path.isfile(self.env['binary_path']):
            self.output("Binary found at specified path")

            # Get binary version: https://developer.1password.com/docs/cli/reference
            try:
                self.output("Attempting to execute version check command...")
                cmd = [self.env['binary_path'], '--version']
                self.output("Executing command: {}".format(' '.join(cmd)))

                process_output = subprocess.check_output(cmd)
                self.output("Raw command output: {}".format(process_output))

                # Strip whitespace and decode the output
                version = process_output.strip().decode('utf-8')
                self.output("Successfully extracted version: {}".format(version))

            except subprocess.CalledProcessError as error:
                self.output("Error executing command: {}".format(error))
                raise ProcessorError("Encountered an error when trying to get the "
                                   "1Password CLI binary version. Error: {}".format(error))
            except Exception as error:
                self.output("Error processing version output: {}".format(error))
                raise ProcessorError("Error processing version output: {}"
                                   .format(error))
        else:
            self.output("Binary not found at path: {}".format(self.env['binary_path']))
            raise ProcessorError("Cannot access 1Password CLI binary at path: {}"
                               .format(self.env['binary_path']))

        # Final version check and assignment
        if version:
            self.env['version'] = version
            self.output("Successfully retrieved version: {}".format(self.env['version']))
        else:
            self.output("Failed to obtain version")
            raise ProcessorError("version is None")


if __name__ == '__main__':
    PROCESSOR = OnePasswordCLIVersioner()

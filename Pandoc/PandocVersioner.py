#!/usr/local/autopkg/python
# pylint: disable = invalid-name

'''
Copyright (c) 2024, dataJAR Ltd.  All rights reserved.
     Redistribution and use in source and binary forms, with or without
     modification, are permitted provided that the following conditions are met:
             * Redistributions of source code must retain the above copyright
               notice, this list of conditions and the following disclaimer.
             * Redistributions in binary form must reproduce the above copyright
               notice, this list of conditions and the following disclaimer in the
               documentation and/or other materials provided with the distribution.
             * Neither data JAR Ltd nor the names of its contributors may be used to
               endorse or promote products derived from this software without specific
               prior written permission.
     THIS SOFTWARE IS PROVIDED BY DATA JAR LTD 'AS IS' AND ANY
     EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
     WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
     DISCLAIMED. IN NO EVENT SHALL DATA JAR LTD BE LIABLE FOR ANY
     DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
     (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
     LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
     ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
     (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
     SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
SUPPORT FOR THIS PROGRAM
    This program is distributed 'as is' by DATA JAR LTD.
    For more information or support, please utilise the following resources:
            http://www.datajar.co.uk
DESCRIPTION
See docstring for PandocVersioner class
'''

# Standard Imports
from __future__ import absolute_import
import subprocess
import os

# AutoPkg imports
# pylint: disable = import-error
from autopkglib import Processor, ProcessorError


__all__ = ['PandocVersioner']
__version__ = '1.0'


# pylint: disable = too-few-public-methods
class PandocVersioner(Processor):
    '''
        Returns the version from the pandoc binary

        Raising if the key is not found.
    '''

    description = __doc__
    input_variables = {
        'binary_path': {
            'required': True,
            'description': ('Path to the pandoc binary.'),
        },
    }

    output_variables = {
        'version': {
            'description': ('Version of the pandoc binary.'),
        },
    }

    def main(self):
        '''
            See docstring for PandocVersioner class
        '''

        # var declaration
        version = None

        # Progress notification
        self.output("Looking for: {}".format(self.env['binary_path']))

        # If binary exists
        if os.path.isfile(self.env['binary_path']):
            # Get binary version, from https://github.com/jgm/pandoc/blob/58cc5cc57ee4721acde7c7ef99bf964252611805/doc/getting-started.md?plain=1#L303
            # raise if we error
            try:
                version = subprocess.check_output([self.env['binary_path'], '--version']
                                                 ).split()[1].decode('utf-8')
            except subprocess.CalledProcessError:
                raise ProcessorError("Encountered an error when trying to get the "
                                     "pandoc binary version...")
        # Raise if binary is missing
        else:
            raise ProcessorError("Cannot access pandoc binary at path: {}"
                                 .format(self.env['binary_path']))

        # We should only get here if we have passed the above, but this is belt and braces
        if version:
            self.env['version'] = version
            self.output("version: {}".format(
                self.env['version']))
        else:
            raise ProcessorError("version is None")


if __name__ == '__main__':
    PROCESSOR = PandocVersioner()

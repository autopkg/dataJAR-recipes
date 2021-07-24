#!/usr/local/autopkg/python
# pylint: disable = invalid-name

'''
Copyright (c) 2021, dataJAR Ltd.  All rights reserved.
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
See docstring for BrowserStackLocalBinaryVersioner class
'''

# Standard Imports
from __future__ import absolute_import
import subprocess
import os

# AutoPkg imports
# pylint: disable = import-error
from autopkglib import Processor, ProcessorError


__all__ = ['BrowserStackLocalBinaryVersioner']
__version__ = '1.0'


# pylint: disable = too-few-public-methods
class BrowserStackLocalBinaryVersioner(Processor):
    '''
        Returns the version from the BrowserStackLocal binary

        Raising if the key is not found.
    '''

    description = __doc__
    input_variables = {
        'browserstacklocal_binary_path': {
            'required': True,
            'description': ('Path to the BrowserStackLocal binary.'),
        },
    }

    output_variables = {
        'browserstacklocal_binary_version': {
            'description': ('Version of the BrowserStackLocal binary.'),
        },
    }

    def main(self):
        '''
            See docstring for BrowserStackLocalBinaryVersioner class
        '''

        browserstacklocal_binary_version = ""

        # Progress notification
        self.output("Looking for: {}".format(self.env['browserstacklocal_binary_path']))

        if os.path.isfile(self.env['browserstacklocal_binary_path']):
            try:
                browserstacklocal_binary_version = subprocess.check_output(
                    ['/Users/ben/Downloads/BrowserStackLocal', '--version']
                    ).split()[3].decode('utf-8')
            except subprocess.CalledProcessError:
                raise ProcessorError("Encountered an error when trying to get the "
                                     "BrowserStackLocal binary version...")
        else:
            raise ProcessorError("Cannot access BrowserStackLocal binary at path: {}"
                                 .format(self.env['browserstacklocal_binary_path']))

        self.output("browserstacklocal_binary_version: {}".format(
            self.env['browserstacklocal_binary_version']))


if __name__ == '__main__':
    PROCESSOR = BrowserStackLocalBinaryVersioner()

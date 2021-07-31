#!/usr/local/autopkg/python
# pylint: disable = invalid-name

'''
Copyright (c) 2021, dataJAR Ltd.  All rights reserved.
     Redistribution and use in source and app forms, with or without
     modification, are permitted provided that the following conditions are met:
             * Redistributions of source code must retain the above copyright
               notice, this list of conditions and the following disclaimer.
             * Redistributions in app form must reproduce the above copyright
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
See docstring for MakeHumanVersioner class
'''

# Standard Imports
from __future__ import absolute_import
import os

# AutoPkg imports
# pylint: disable = import-error
from autopkglib import Processor, ProcessorError


__all__ = ['MakeHumanVersioner']
__version__ = '1.0'


# pylint: disable = too-few-public-methods
class MakeHumanVersioner(Processor):
    '''
        Returns the version from makehuman.py.

        Located within: MakeHuman.app/Contents/Resources/makehuman.py

        Raising if the key is not found.
    '''

    description = __doc__
    input_variables = {
        'app_path': {
            'required': True,
            'description': ('Path to the MakeHuman app.'),
        },
    }

    output_variables = {
        'version': {
            'description': ('Version of the MakeHuman app.'),
        },
    }

    def main(self):
        '''
            See docstring for MakeHumanVersioner class
        '''

        # var declaration
        version = None

        py_path = 'Contents/Resources/makehuman.py'

        full_path = os.path.join(self.env['app_path'], py_path)

        # Progress notification
        self.output("Looking for: {}".format(full_path))

        # If app exists
        if os.path.isfile(full_path):
            # Get app version, from: makehuman.py
            # raise if we error
            try:
                with open(full_path, encoding='utf-8') as py_file:
                    for py_line in py_file:
                        if py_line.startswith('__version__'):
                            version = py_line.split('"')[1]
            except:
                raise ProcessorError("Encountered an error when trying to get the "
                                     "MakeHuman app version...")
        # Raise if app is missing
        else:
            raise ProcessorError("Cannot access makehuman.py at path: {}"
                                 .format(full_path))

        # We should only get here if we have passed the above, but this is belt and braces
        if version:
            self.env['version'] = version
            self.output("version: {}".format(
                self.env['version']))
        else:
            raise ProcessorError("version is None")


if __name__ == '__main__':
    PROCESSOR = MakeHumanVersioner()

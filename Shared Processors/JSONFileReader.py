#!/usr/local/autopkg/python
# pylint: disable = invalid-name

'''
Copyright (c) 2020, dataJAR Ltd.  All rights reserved.
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
See docstring for JSONFileReader class
'''

# Standard Imports
from __future__ import absolute_import
import json
import os

# AutoPkg imports
# pylint: disable = import-error
from autopkglib import Processor, ProcessorError


__all__ = ['JSONFileReader']
__version__ = '1.0'


# pylint: disable = too-few-public-methods
class JSONFileReader(Processor):
    '''
        Parses a JSON file, returning the value of the supplied key.

        Raising if the key is not found.
    '''

    description = __doc__
    input_variables = {
        'json_key': {
            'required': True,
            'description': ('Key to look for, and return the value of'),
        },
        'json_path': {
            'required': True,
            'description': ('Path to the JSON file'),
        },
    }

    output_variables = {
        'json_value': {
            'description': ('Value of the JSON key'),
        },
    }

    def main(self):
        '''
            See docstring for JSONFileReader class
        '''

        # Progress notification
        self.output("Looking for: {}".format(self.env['json_path']))

        if os.path.isfile(self.env['json_path']):

            # Read in JSON file
            with open(self.env['json_path']) as json_file:

                # Try to parse json_path as json, raise if an issue
                try:
                    load_json = json.load(json_file)
                except json.JSONDecodeError as err_msg:
                    raise ProcessorError("Failed to parse {}: {}".format(self.env['json_path'],
                                                                         err_msg))
                # Look for value of key json_key, raise if an issue
                try:
                    self.env['json_value'] = load_json[self.env['json_key']]
                except KeyError:
                    raise ProcessorError("Cannot find key {} within json file: {}"
                                         .format(self.env['json_key'], self.env['json_path']))
        else:
            raise ProcessorError("Cannot access JSON file at path: {}"
                                 .format(self.env['json_path']))

        self.output("json_value: {}".format(self.env['json_value']))


if __name__ == '__main__':
    PROCESSOR = JSONFileReader()

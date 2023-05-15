#!/usr/local/autopkg/python
# pylint: disable = invalid-name

'''
Copyright (c) 2023, dataJAR Ltd.  All rights reserved.
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
See docstring for VarSplitter class
'''

# AutoPkg imports
# pylint: disable = import-error
from autopkglib import Processor


# Details
__all__ = ['VarSplitter']
__version__ = '1.0'


# pylint: disable = too-few-public-methods
class VarSplitter(Processor):
    '''
        Splits the passed variable at the slice specified, retuning the slice at the 1st index.

        Raising if the key is not found.
    '''

    description = __doc__
    input_variables = {
        'input_string': {
            'required': True,
            'description': ('Variable we\'re looking to split.'),
        },
        'split_slice': {
            'required': True,
            'description': ('The slice we want to split the string by, can be postive or '
                            'negative.'),
        },
        'split_string_name': {
            'description': ('The name of the output variable that is returned after split_slice '
                            'has been applied to input_string.'
                            'If not specified, will default to "split_string".'),
            "required": False,
            "default": "split_string",
        },
    }

    output_variables = {
        'split_string_name': {
            'description': ('The value of inpu_string once split by split_slice'),
        },
    }

    def main(self):
        '''
            See docstring for VarSplitter class
        '''

        # Var declaration
        output_var_name = self.env["split_string_name"]

        # Progress notification
        self.output(f"Looking to split {self.env['input_string']} by {self.env['split_slice']}")

        # Split as needed
        self.env[output_var_name] = self.env['input_string'][':' + int(self.env['split_slice'])][0]
        self.output(f"split_string: {self.env['split_string']}")


if __name__ == '__main__':
    PROCESSOR = VarSplitter()

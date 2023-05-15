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
See docstring for VarSlicer class
'''

# AutoPkg imports
# pylint: disable = import-error
from autopkglib import Processor, ProcessorError


# Details
__all__ = ['VarSlicer']
__version__ = '1.0'


# pylint: disable = too-few-public-methods
class VarSlicer(Processor):
    '''
        Slicers the passed variable at the slice specified.

        Raises if cannot slice
    '''

    description = __doc__
    input_variables = {
        'input_string': {
            'required': True,
            'description': ('Variable we\'re looking to slice.'),
        },
        'slice_tuple_pattern': {
            'required': True,
            'description': ('The slice we want to apply to input_string. '
                            'A tuple with 3 members is required'),
        },
        'sliced_string_name': {
            'description': ('The name of the output variable that is returned after '
                            'slice_tuple_pattern has been applied to input_string.'
                            'If not specified, will default to "slice_string".'),
            "required": False,
            "default": "slice_string",
        },
    }

    output_variables = {
        'sliced_string_name': {
            'description': ('The value of input_string once sliced by slice_tuple_pattern'),
        },
    }

    def main(self):
        '''
            See docstring for VarSlicer class
        '''

        # Var declaration
        output_var_name = self.env["sliced_string_name"]

        # Progress notification
        self.output(f"Looking to slice {self.env['input_string']} by "
                    f"({self.env['slice_tuple_pattern']})")

        # Slice as needed, raising if fails
        try:
            # Convert slice_tuple_pattern to tuple
            var_tuple = tuple(((self.env["slice_tuple_pattern"].replace(' ', '')).split(',')))
            # First item for tuple
            if var_tuple[0] != "None":
                first_item = int(var_tuple[0])
            else:
                first_item = None
            # Second item for tuple
            if var_tuple[1] != "None":
                second_item = int(var_tuple[1])
            else:
                second_item = None
            # Third item for tuple
            if var_tuple[2] != "None":
                third_item = int(var_tuple[2])
            else:
                third_item = None
            # Create the slice
            var_slice = slice(first_item, second_item,third_item)
            # Slice, using the above
            self.env[output_var_name] = self.env['input_string'][var_slice]
            # Perform the slice
            #self.env['slice_string'] = 
        except (IndexError, TypeError) as err_msg:
            raise ProcessorError("Cannot slice self.env['input_string'] with: "
                                 "{self.env['slice_tuple_pattern']}, : ") from err_msg

        # Progress notification
        self.output(f"soutput_var_name: {self.env[output_var_name]}")


if __name__ == '__main__':
    PROCESSOR = VarSlicer()

#!/usr/local/autopkg/python
# pylint: disable = invalid-name

'''
Copyright (c) 2022, dataJAR Ltd.  All rights reserved.
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
See docstring for CaseChanger class
'''

# AutoPkg imports
# pylint: disable = import-error
from autopkglib import Processor, ProcessorError


__all__ = ['CaseChanger']
__version__ = '1.0'


# pylint: disable = too-few-public-methods
class CaseChanger(Processor):
    '''
        Parses a JSON file, returning the value of the supplied key.

        Raising if the key is not found.
    '''

    description = __doc__
    input_variables = {
        'input_string': {
            'required': True,
            'description': ('Variable we\'re looking to change the case for.'),
        },
        'wanted_case': {
            'required': True,
            'description': ('The case that we want to change input_variable to. '
            'Only the following are valid options: capitalize, lower, title and upper.'),
        },
    }

    output_variables = {
        'changed_string': {
            'description': ('input_string after case changed to the value passed to wanted_case.'),
        },
    }

    def main(self):
        '''
            See docstring for CaseChanger class
        '''

        # Progress notification
        self.output(f"Looking to change the case of {self.env['input_string']} to "
                    f"{self.env['wanted_case']}")

        # Check that the case wanted is in our list before proceeding
        if self.env['wanted_case'] in ['capitalize', 'lower', 'title', 'upper']:
            if self.env['wanted_case'] == 'capitalize':
                self.env['changed_string'] = self.env['input_string'].capitalize()
            if self.env['wanted_case'] == 'lower':
                self.env['changed_string'] = self.env['input_string'].lower()
            if self.env['wanted_case'] == 'title':
                self.env['changed_string'] = self.env['input_string'].title()
            if self.env['wanted_case'] == 'upper':
                self.env['changed_string'] = self.env['input_string'].upper()
        else:
            raise ProcessorError(f"wanted_case ({self.env['wanted_case']}) is not set to one of "
                                 f"the following: capitalize, lower, title, upper")

        self.output(f"changed_string: {self.env['changed_string']}")


if __name__ == '__main__':
    PROCESSOR = CaseChanger()

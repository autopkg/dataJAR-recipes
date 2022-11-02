#!/usr/local/autopkg/python

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
See docstring for QuarantineRemover class
'''

# Standard imports
import os
import xattr


# AutoPkg imports
from autopkglib import Processor, ProcessorError


# Details
__all__ = ['QuarantineRemover']
__version__ = '1.0'


class QuarantineRemover(Processor):
    '''
        Removes the com.apple.quarantine attribute from a file
    '''

    description = __doc__
    input_variables = {
        'quarantined_files_path': {
            'required': True,
            'description': ('Path to the file we\'re to remove the com.apple.quarantine '
                            'attribute from.'),
        }
    }

    def main(self):
        '''
            See docstring for QuarantineRemover class
        '''

        # Raise if file doesn't exist
        if not os.path.exists(self.env['quarantined_files_path']):
            raise ProcessorError(f"{self.env['quarantined_files_path']} does not exist...")

        # Pinched with <3 from:
        # https://github.com/autopkg/autopkg/blob/7ba6e9da183683e9991882b99cba0d30d359bda8/Code/autopkgserver/itemcopier.py#L172-L177
        # remove com.apple.quarantine attribute if exists
        try:
            if "com.apple.quarantine" in xattr.xattr(self.env['quarantined_files_path']).list():
                xattr.xattr(self.env['quarantined_files_path']).remove("com.apple.quarantine")
                self.output(f"Removed com.apple.quarantine from "
                            f"{self.env['quarantined_files_path']}...")
        except BaseException as err:
            raise ProcessorError(f"Error removing xattr: {err}") from err


if __name__ == '__main__':
    PROCESSOR = QuarantineRemover()

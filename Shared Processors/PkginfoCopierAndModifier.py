# pylint: disable = invalid-name
'''
    See docstring for PkginfoCopierAndModifier class
'''

# Standard Imports
import os
import plistlib
import shutil

# AutoPkg imports
# pylint: disable = import-error
from autopkglib import Processor, ProcessorError



__all__ = ['PkginfoCopierAndModifier']
__version__ = '1.1'



# Class
# pylint: disable = too-few-public-methods
class PkginfoCopierAndModifier(Processor):
    '''
        Copies a pkginfo file then changes values
    '''

    description = __doc__
    input_variables = {
        'munki_info': {
            'required': True,
            'description': ("dict containing munki_info"),
        },
        'MUNKI_REPO': {
            'required': True,
            'description': ("Munki Repo"),
        },
        'new_munki_category': {
            'required': True,
            'description': (""),
        },
        'new_munki_display_name': {
            'required': True,
            'description': (""),
        },
        'new_munki_name': {
            'required': True,
            'description': (""),
        },
        'new_munki_postinstall_script': {
            'required': True,
            'description': (""),
        },
        'pkginfo_repo_path': {
            'required': True,
            'description': ("Path of the pkginfo we're looking to copy"),
        },
        'pkginfo_dest_path': {
            'required': True,
            'description': ("Path to copy the file to"),
        }
    }

    output_variables = {
        'copied_pkginfo_repo_path': {
            'description': ("Updated path of the pkginfo we copied"),
        },
        "munki_importer_summary_result": {
            "description": "Description of interesting results."
        },
        "munki_info": {
            "description": "The pkginfo property list. Empty if item not imported."
        }
    }


    # Main body
    def main(self):
        '''
            See docstring for PkginfoCopierAndModifier class
        '''

        # If the munki_info dict is empty, then no new item uploaded and as such no change
        # needed. So here we only proceed if there is content.
        if self.env['munki_info']:

            # Make sure pkginfo we're to copy exists
            if not os.path.exists(self.env['pkginfo_repo_path']):
                raise ProcessorError(f"Cannot find path {self.env['pkginfo_repo_path']}")

            # Dir we're to copy to
            dest_dir_path = os.path.join(self.env['MUNKI_REPO'], 'pkgsinfo',
                                         self.env['pkginfo_dest_path'])
            self.output(f"dest_dir_path: {dest_dir_path}")

            # Create dest_dir_path if missing
            if not os.path.exists(dest_dir_path):
                try:
                    os.makedirs(dest_dir_path)
                except OSError as err_msg:
                    raise ProcessorError(f"Could not create {dest_dir_path}: "
                                         f"{err_msg.strerror}") from err_msg

            # Copy pkginfo
            self.env['copied_pkginfo_repo_path'] = (os.path.join(dest_dir_path,
                                                    self.env['new_munki_name'] + '-' +
                                                    self.env['munki_info']['version'] + '.plist'))

            # Try to copy the file
            try:
                shutil.copyfile(self.env['pkginfo_repo_path'], self.env['copied_pkginfo_repo_path'])
            except IOError as err_msg:
                raise ProcessorError(f"Could not copy pkginfo to: "
                                     f"{self.env['copied_pkginfo_repo_path']}: "
                                     f"{err_msg.strerror}") from err_msg

            # Read in copied pkginfo
            with open(self.env['copied_pkginfo_repo_path'], "rb") as pkginfo_file:
                copied_pkginfo = plistlib.load(pkginfo_file)

            # Update with new values
            copied_pkginfo['category'] = self.env['new_munki_category']
            copied_pkginfo['display_name'] = self.env['new_munki_display_name']
            copied_pkginfo['name'] = self.env['new_munki_name']
            copied_pkginfo['postinstall_script'] = self.env['new_munki_postinstall_script']

            # Update munki info with new values
            self.env['munki_info']['category'] = self.env['new_munki_category']
            self.env['munki_info']['display_name'] = self.env['new_munki_display_name']
            self.env['munki_info']['name'] = self.env['new_munki_name']
            self.env['munki_info']['postinstall_script'] = self.env['new_munki_postinstall_script']

            # Update definitions input variables info with new values
            self.env['MUNKI_CATEGORY'] = self.env['new_munki_category']
            self.env['MUNKI_DISPLAY_NAME'] = self.env['new_munki_display_name']
            self.env['MUNKI_NAME'] = self.env['new_munki_name']

            # Write new plist
            with open(self.env['copied_pkginfo_repo_path'], "wb") as pkginfo_file:
                plistlib.dump(copied_pkginfo, pkginfo_file)

            # Export as Munki.. as can then be picked up with other automations
            self.env['munki_importer_summary_result'] = {
                'summary_text': 'The following new items were imported into Munki:',
                'report_fields': [
                    'name',
                    'version',
                    'catalogs',
                    'pkginfo_path',
                    'pkg_repo_path',
                    'icon_repo_path',
                ],
                'data': {
                    'name': self.env['new_munki_name'],
                    'version': self.env['munki_info']['version'],
                    'catalogs': ','.join(self.env['munki_info']['catalogs']),
                    'pkginfo_path': self.env['copied_pkginfo_repo_path'].replace(
                                             os.path.join(self.env['MUNKI_REPO'], 'pkgsinfo/'), ''),
                    'pkg_repo_path': self.env['munki_info']['installer_item_location'],
                    'icon_repo_path': '',
                },
            }
        else:
            self.output("Nothing imported, skipping...")

if __name__ == '__main__':
    PROCESSOR = PkginfoCopierAndModifier()

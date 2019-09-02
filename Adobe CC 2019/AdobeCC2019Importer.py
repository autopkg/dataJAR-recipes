#!/usr/bin/python
'''
Copyright (c) 2019, dataJAR Ltd.  All rights reserved.
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

Imports Adobe CC 2019 titles found in running users ~/Downloads

'''

from __future__ import absolute_import, print_function

# Standard Imports
import argparse
import glob
import os
import subprocess
import sys

# Version
__version__ = '1.0'


# Script
def main():
    '''Gimme some main'''

    adobe_folders = []

    for some_item in os.listdir(DOWNLOADS_PATH):
        some_path = os.path.join(DOWNLOADS_PATH, some_item)
        if os.path.isdir(some_path):
            if some_item.startswith('Adobe') and some_item.endswith('CC2019'):
                adobe_folders.append(some_item)

    if not len(adobe_folders):
        print('No Adobe*CC2019 folders found in %s, exiting...' % DOWNLOADS_PATH)
        sys.exit(1)

    if len(adobe_folders) == 1:
        print('1 Adobe CC 2019 folder found, creating recipe list...')
    else:
        print('%s Adobe CC 2019 folder found, creating recipe list...' % len(adobe_folders))

    open(ADOBE_LIST, 'w').close()
    pkg_checker(adobe_folders)


def file_len(run_day):
    ''' For each weekdays recipe list, return a count '''

    line_count = len(open(ADOBE_LIST).readlines())

    return line_count


def pkg_checker(adobe_folders):
    ''' Check that we have the Install_pkg's & proceed if we do'''

    found_pkgs = 0

    print('Looking for pkgs...')

    for adobe_folder in sorted(adobe_folders):
        try:
            install_pkg = glob.glob(os.path.join(DOWNLOADS_PATH, adobe_folder, \
                                               'Build', '*_Install.pkg'))[0]
            print('Found {0}...'.format(install_pkg))
            if os.path.exists(install_pkg):
                create_list(adobe_folder)
                found_pkgs += 1
            else:
                print('Cannot find pkg ({0}), for {1}... Skipping...'.format\
                                               (install_pkg, adobe_folder))
        except IndexError as err_msg:
            print('Skipping {0}, as cannot find Install.pkg: {1}...'.format(adobe_folder, err_msg))

    if found_pkgs == 0:
        print('No pkgs found, exiting...')
        sys.exit(1)
    else:
        run_list()


def create_list(adobe_folder):
    ''' Create recipe list '''

    library_dir = os.path.expanduser('~/Library/')
    override_path = os.path.join(library_dir, 'AutoPkg', 'RecipeOverrides', \
                                                         adobe_folder + '.' \
                                                 + RECIPE_TYPE + '.recipe')
    override_name = 'local.' + RECIPE_TYPE + '.' + adobe_folder

    if not os.path.isfile(override_path):
        print('Skipping {0}, as cannot find override...'.format(override_path))

    list_file = open(ADOBE_LIST, 'a+')
    list_file.write(override_name + '\n')
    list_file.close()


def run_list():
    '''Run recipe list'''

    if os.path.exists(ADOBE_LIST):
        print('Running recipe_list: `{0}`'.format(ADOBE_LIST))
        print()
        cmd_args = ['/usr/local/bin/autopkg', 'run', '-v', '--recipe-list', ADOBE_LIST, \
                                                         '--report-plist', REPORT_PATH]
        print('Running `{0}`...'.format(cmd_args))
        subprocess.call(cmd_args)
    else:
        print('Recipe list not populated, make sure you have the needed overrides in place....')


if __name__ == '__main__':

    # Try to locate autopkg
    if not os.path.exists('/usr/local/bin/autopkg'):
        print('Cannot find autopkg')
        sys.exit(1)

    # Parse recipe type argument
    parser = argparse.ArgumentParser()
    parser.add_argument('type', type=str, help='Recipe type, either "munki" or "jss"')
    args = parser.parse_args()
    RECIPE_TYPE = args.type.lower()

    # Constants
    DOWNLOADS_PATH = os.path.expanduser('~/Downloads/')
    ADOBE_LIST = os.path.join(DOWNLOADS_PATH + 'adobecc2019_list.txt')
    REPORT_PATH = os.path.join(DOWNLOADS_PATH + 'adobecc2019_report.plist')

    main()

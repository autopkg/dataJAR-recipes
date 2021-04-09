#!/usr/local/autopkg/python
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

Imports Adobe 2021 titles found in running users ~/Downloads

'''

# Standard Imports
from __future__ import absolute_import
from __future__ import print_function
import argparse
import glob
import os
import subprocess
import sys


# Version
__version__ = '1.2'


# Functions
def main():
    '''
        Look within DOWNLOADS_PATH for Adobe*2021* items, add to adobe_folders list if found
    '''

    # Progress notification
    print("Looking for {} folders ...".format(os.path.join(DOWNLOADS_PATH, 'Adobe*2021*')))

    # Create empty list
    adobe_folders = []

    # Look within DOWNLOADS_PATH for Adobe*2021 items, add to adobe_folders list if found
    for some_item in os.listdir(DOWNLOADS_PATH):
        some_path = os.path.join(DOWNLOADS_PATH, some_item)
        if os.path.isdir(some_path):
            if some_item.startswith('Adobe') and '2021' in (some_item):
                adobe_folders.append(some_item)

    # If no folders are found, exit
    if not adobe_folders:
        print("No Adobe*2021 folders found in {}, exiting...".format(DOWNLOADS_PATH))
        sys.exit(1)

    # If 1 or moe folders are found, notify and proceed.
    if len(adobe_folders) == 1:
        print("1 Adobe 2021 folder found, creating recipe list...")
    else:
        print("{} Adobe 2021 folder found, creating recipe list...".format(len(adobe_folders)))

    # Check for pkg's
    pkg_checker(sorted(adobe_folders))


def pkg_checker(adobe_folders):
    '''
        Check that we have the Install_pkg's & Uninstall_pkg's needed, proceed if we do
    '''

    # Progress notification
    print("Looking for pkgs...")

    # count var
    found_pkgs = 0

    # For each folder within adobe_folders, look for *_Install.pkg and *_Uninstall.pkg,
    for adobe_folder in adobe_folders:

        # var declaration
        install_pkg = None
        uninstall_pkg = None
        adobe_build_folder_path = os.path.join(DOWNLOADS_PATH, adobe_folder, 'Build')

        # Look for *_Install.pkg
        try:
            install_pkg = glob.glob(os.path.join(adobe_build_folder_path, '*_Install.pkg'))[0]
            print("Found {}...".format(install_pkg))
        except IndexError:
            print("Cannot find *_Install.pkg within: {}...".format(adobe_build_folder_path))

        # Look for *_Uninstall.pkg
        try:
            uninstall_pkg = glob.glob(os.path.join(adobe_build_folder_path, '*_Install.pkg'))[0]
            print("Found {}...".format(uninstall_pkg))
        except IndexError:
            print("Cannot find *_Uninstall.pkg within: {}...".format(adobe_build_folder_path))

        # If we can find both *_Install.pkg and *_Uninstall.pkg, add to ADOBE_LIST
        if install_pkg and uninstall_pkg:
            # Increment count
            found_pkgs += 1
            # Append to ADOBE_LIST
            create_list(adobe_folder, found_pkgs)
        else:
            print("Cannot find both an *_Install.pkg and *_Uninstall.pkg for {}... "
                  "Skipping...".format(adobe_folder))

    # If we did not find any pkg pairs to import
    if found_pkgs == 0:
        print("ERROR: No Adobe 2021 pkg pairs found, exiting...")
        sys.exit(1)
    # Else, run the recipe list ADOBE_LIST
    else:
        run_list()


def create_list(adobe_folder, found_pkgs):
    '''
        Create recipe list
    '''

    # Create an empty file at ADOBE_List, if this is the 1st found pkg
    if found_pkgs == 1:
        open(ADOBE_LIST, 'w').close()

    # var declaration
    library_dir = os.path.expanduser('~/Library/')
    override_path = os.path.join(library_dir, 'AutoPkg', 'RecipeOverrides', \
                                                         adobe_folder + '.' \
                                                 + RECIPE_TYPE + '.recipe')
    override_name = 'local.' + RECIPE_TYPE + '.' + adobe_folder

    # If we cannot find the override
    if not os.path.isfile(override_path):
        print("Skipping {}, as cannot find override...".format(override_path))
        return

    # Append to ADOBE_LIST
    list_file = open(ADOBE_LIST, 'a+')
    list_file.write(override_name + '\n')
    list_file.close()


def run_list():
    '''
        Run recipe list
    '''

    # Notify we're starting
    print("Running recipe_list: `{}`".format(ADOBE_LIST))
    print()

    # The subprocess command
    cmd_args = ['/usr/local/bin/autopkg', 'run', '-v', '--recipe-list', ADOBE_LIST,
                '--report-plist', REPORT_PATH]

    # Notify what command we're about to run.
    print('Running `{}`...'.format(cmd_args))

    # Run the command
    subprocess.call(cmd_args)


if __name__ == '__main__':

    # Parse recipe type argument
    PARSER = argparse.ArgumentParser()
    PARSER.add_argument('type', type=str, help='Recipe type, either "munki" or "jss"')
    ARG_PARSER = PARSER.parse_args()
    RECIPE_TYPE = ARG_PARSER.type.lower()

    # Constants
    DOWNLOADS_PATH = os.path.expanduser('~/Downloads/')
    ADOBE_LIST = os.path.join(DOWNLOADS_PATH + 'adobe2021_list.txt')
    REPORT_PATH = os.path.join(DOWNLOADS_PATH + 'adobe2021_report.plist')

    # Call main def
    main()

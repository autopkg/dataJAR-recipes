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

Imports Adobe Admin Console Packages

'''

# Standard Imports
import argparse
import glob
import os
import plistlib
import subprocess
import sys
import yaml

# pylint: disable = import-error
from CoreFoundation import CFPreferencesCopyAppValue


# Version
__version__ = '1.0'


# Functions
def main():
    '''
        Check passed arguments before proceeding
    '''

    # Setup arparse
    parser = argparse.ArgumentParser()
    parser.add_argument('type', type=str, help="Recipe type, for example: \"munki\" or \"jss\"")
    arg_parser = parser.parse_args()

    # Retrieve passed arguments, and assign to variables
    recipe_type = arg_parser.type.lower()
    packages_path = os.path.expanduser('~/Downloads/')

    # Check that packages_path exists
    if not os.path.exists(packages_path):
        print(f"ERROR: Cannot locate directory, {packages_path}... exiting...")
        sys.exit(1)

    # Check that packages_path is a directory
    if not os.path.isdir(packages_path):
        print(f"ERROR: {packages_path} is a not a directory... exiting...")
        sys.exit(1)

    # Check for Adobe* dirs
    look_for_dirs(packages_path, recipe_type)


def look_for_dirs(packages_path, recipe_type):
    '''
        Look for dirs starting with Adobe*, in packages_path
    '''

    # Progress notification
    print(f"Looking in {packages_path} for Adobe* folders ...")

    # Create empty list
    adobe_folders = []

    # Look within packages_path for Adobe* items, add to adobe_folders list if found
    for some_item in os.listdir(packages_path):
        some_path = os.path.join(packages_path, some_item)
        if os.path.isdir(some_path):
            if some_item.startswith('Adobe'):
                adobe_folders.append(some_item)

    # If no folders are found, exit
    if not adobe_folders:
        print(f"No Adobe* folders found in {packages_path}, exiting...")
        sys.exit(1)

    # If 1 or more folders are found, notify and proceed.
    if len(adobe_folders) == 1:
        print("1 Adobe folder found...")
    else:
        print(f"{len(adobe_folders)} Adobe folders found...")

    # Get the override_dirs
    try:
        override_dirs = CFPreferencesCopyAppValue('RECIPE_OVERRIDE_DIRS',
                                                  'com.github.autopkg').split()
    except AttributeError:
        override_dirs = os.path.join(os.path.expanduser('~/Library/'), 'AutoPkg',
                                     'RecipeOverrides').split()
    print(f"Override dirs: {override_dirs}")

    # Check for pkg's
    pkg_checker(sorted(adobe_folders), override_dirs, packages_path, recipe_type)


def pkg_checker(adobe_folders, override_dirs, packages_path, recipe_type):
    '''
        Check that we have the Install_pkg's & Uninstall_pkg's needed, proceed if we do
    '''

    # Progress notification
    print("Looking for pkgs...")

    # Count var
    found_pkgs = 0

    # For each folder within adobe_folders, look for *_Install.pkg and *_Uninstall.pkg,
    for adobe_folder in adobe_folders:

        # Var declaration
        install_pkg = None
        uninstall_pkg = None
        adobe_build_folder_path = os.path.join(packages_path, adobe_folder, 'Build')
        recipe_list_path = os.path.join(packages_path + 'adobe_admin_console_recipes_list.txt')
        report_path = os.path.join(packages_path + 'adobe_admin_console_recipes_report.plist')

        # Progress notification
        print(f"Checking {adobe_build_folder_path}...")

        if not os.path.isdir(adobe_build_folder_path):
            print(f"No Build dir at {adobe_build_folder_path}... skipping...")
        else:
            print(f"Found Build dir at {adobe_build_folder_path}...")
            # Look for *_Install.pkg
            try:
                install_pkg = glob.glob(os.path.join(adobe_build_folder_path, '*_Install.pkg'))[0]
                print(f"Found {install_pkg}...")
            except IndexError:
                print(f"Cannot find *_Install.pkg within: {adobe_build_folder_path}...")

            # Look for *_Uninstall.pkg
            try:
                uninstall_pkg = glob.glob(os.path.join(adobe_build_folder_path,
                                                       '*_Uninstall.pkg'))[0]
                print(f"Found {uninstall_pkg}...")
            except IndexError:
                print("Cannot find *_Uninstall.pkg within: {adobe_build_folder_path}...")

            # If we can find both *_Install.pkg and *_Uninstall.pkg, add to recipe_list_path
            if install_pkg and uninstall_pkg:
                # Increment count
                found_pkgs += 1
                # Append to recipe_list_path
                create_list(adobe_folder, found_pkgs, override_dirs, recipe_list_path, recipe_type)
            else:
                print(f"ERROR: Cannot find {adobe_folder}, these recipes need packages of the "
                       "Managed Package variety, which include _Install and _Uninstall packages"
                       ".... skipping...")

    # If we did not find any pkg pairs to import, exit
    if found_pkgs == 0:
        print("ERROR: No Adobe pkg pairs found, exiting...")
        sys.exit(1)

    # Run recipe list
    run_list(recipe_list_path, report_path)


def create_list(adobe_folder, found_pkgs, override_dirs, recipe_list_path, recipe_type):
    '''
        Create recipe list
    '''

    # Var declaration
    override_path = None

    # Look for recipes in override_dirs
    for override_dir in override_dirs:
        recipe_files = os.listdir(override_dir)
        for recipe_file in recipe_files:
            if recipe_file.startswith(adobe_folder) and recipe_type in recipe_file:
                override_path = os.path.join(override_dir, recipe_file)

    if not override_path:
        # Return when we cannot find a matching override
        print(f"Cannot find override starting with: {adobe_folder}, skipping...")
        return
    print(f"Found override at: {override_path}, proceeding...")

    # Create an empty file at recipe_list_path, if this is the 1st found pkg
    if found_pkgs == 1:
        with open(recipe_list_path, 'w', encoding='utf-8') as new_file:
            new_file.write('')

    # Retrieve override name from file
    # Borrowed with <3 from:
    # https://github.com/autopkg/autopkg/blob/405c913deab15042819e2f77f1587a805b7c1ada/Code/autopkglib/__init__.py#L341-L359
    if override_path.endswith(".yaml"):
        try:
            # try to read it as yaml
            with open (override_path, 'rb') as read_file:
                recipe_dict = yaml.load(read_file, Loader=yaml.FullLoader)
            override_name =  recipe_dict["Identifier"]
        # pylint: disable = broad-except
        except Exception as err_msg:
            print(f"ERROR: yaml error for {override_path}: {err_msg}")
            return
    try:
        # try to read it as a plist
        with open (override_path, 'rb') as read_file:
            recipe_dict = plistlib.load(read_file)
        override_name = recipe_dict["Identifier"]
    # pylint: disable = broad-except
    except Exception as err_msg:
        print(f"ERROR: plist error for {override_path}: {err_msg}")
        return

    print(f"Adding {override_path}, to {recipe_list_path} with identifier: {override_name}...")

    # Append to recipe_list_path
    with open(recipe_list_path, 'a+', encoding='utf-8') as list_file:
        list_file.write(override_name + '\n')


def run_list(recipe_list_path, report_path):
    '''
        Run recipe list
    '''

    # Check that the recipe_list file has content before proceeding
    with open (recipe_list_path, encoding='utf-8') as recipe_list_file:
        content_test = recipe_list_file.readlines()
        if not content_test:
            print(f"{recipe_list_path} is empty, no overrides found... exiting ...")
            sys.exit(1)

    # Notify we're starting
    print(f"Running recipe_list: `{recipe_list_path}`")

    # The subprocess command
    cmd_args = ['/usr/local/bin/autopkg', 'run', '-vv', '--recipe-list', recipe_list_path,
                '--report-plist', report_path]

    # Notify what command we're about to run.
    print(f"Running: `{cmd_args}`...")

    # Run the command
    subprocess.call(cmd_args)



if __name__ == '__main__':

    # Gimme some main
    main()

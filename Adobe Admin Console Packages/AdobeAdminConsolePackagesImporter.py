#!/usr/local/autopkg/python
# pylint: disable = invalid-name
'''
Copyright (c) 2024, Jamf Ltd.  All rights reserved.

DESCRIPTION

Imports Adobe Admin Console Packages

'''

# Standard Imports
import argparse
import glob
import json
import os
import plistlib
import subprocess
import sys
import yaml


# Append /Library/AutoPkg dir, to allow module import
# pylint: disable = import-error, wrong-import-position
sys.path.append("/Library/AutoPkg")
from autopkglib import globalPreferences


# Version
__version__ = '2.0.2'


# Functions
def main():
    '''
        Check passed arguments before proceeding
    '''

    # Setup arparse
    parser = argparse.ArgumentParser()
    parser.add_argument('type', help="Recipe type, for example: \"munki\" or \"jamf\"", type=str)
    parser.add_argument('dir', nargs="?", default="~/Downloads",
                        help="Path to dir containing Adobe installers", type=str)
    arg_parser = parser.parse_args()

    # Retrieve passed type
    recipe_type = arg_parser.type.lower()

    # Var declarations
    packages_path = os.path.expanduser(arg_parser.dir)
    recipe_list_path = os.path.join(packages_path, 'adobe_admin_console_recipes_list.txt')
    report_path = os.path.join(packages_path, 'adobe_admin_console_recipes_report.plist')

    # Check that packages_path exists
    if not os.path.exists(packages_path):
        # Exit
        print(f"ERROR: Cannot locate directory, \"{packages_path}\"... exiting...")
        sys.exit(1)

    # Check that packages_path is a directory
    if not os.path.isdir(packages_path):
        # Exit
        print(f"ERROR: \"{packages_path}\" is a not a directory... exiting...")
        sys.exit(1)

    # Parse AdobeAutoPkgApplicationData.json and return a list of names
    app_names_list = get_app_names()

    # Check for Adobe installers
    adobe_installers = get_adobe_installers(app_names_list, packages_path)

    # Get override dirs
    override_dirs = get_override_dirs()

    # Get matching overrides
    adobe_installers = match_overrides(adobe_installers, override_dirs, recipe_type)

    # Update overrides
    update_overrides(adobe_installers)

    # Populate a recipe list
    create_list(adobe_installers, recipe_list_path)

    # Run recipe list
    run_recipe_list(recipe_list_path, report_path)


def create_list(adobe_installers, recipe_list_path):
    '''
        Create recipe list, deleting existing
    '''

    # Var declaration
    line_count = 1
    override_count = len(adobe_installers)

    # If a file exists at recipe_list_path, delete it
    if os.path.exists(recipe_list_path):
        # Progress notification
        print(f"Deleting prior created: {recipe_list_path}...")
        # Delete the file
        os.remove(recipe_list_path)

    # Append to recipe_list_path, creating if file is missing
    with open(recipe_list_path, 'a+', encoding='utf-8') as list_file:
        # For each installer details
        for _, installer_details in adobe_installers.items():
            # If line count is then that override count
            if line_count < override_count:
                # Write the overrides to recipe_list_path. appending a new line
                list_file.write(installer_details['override_identifier'] + '\n')
                # Increment var
                line_count += 1
            # If we're at the last line
            else:
                # Write the overrides to recipe_list_path. without appending a new line
                list_file.write(installer_details['override_identifier'])

    # Progress notification
    print(f"Created recipe list at: {recipe_list_path}...")


def get_adobe_installers(app_names_list, packages_path):
    '''
        Look pkg's starting with names in app_names within the packages_path dir
    '''

    # Progress notification
    print(f"Looking in \"{packages_path}\" for Adobe installers...")

    # Var declaration
    adobe_installers = {}
    bundle_pkgs = []
    flat_pkgs = []

    # Get a sorted list of items beginning with Adobe* in ~/Downloads
    for some_item in sorted(glob.glob(os.path.join(packages_path, '*'))):
        # Iterate over app_names_list
        for app_name in app_names_list:
            # If the items name starts app_name
            if os.path.basename(some_item).startswith(app_name):
                # If some_item is a file, and ends with .pkg
                if os.path.isfile(some_item) and some_item.endswith('.pkg'):
                    # Create nested dict named after the app_name
                    adobe_installers[app_name] = {}
                    # Add pkg_path to adobe_installers[aop_name]
                    adobe_installers[app_name]['pkg_path'] = some_item
                    # Add pkg_type to adobe_installers[aop_name]
                    adobe_installers[app_name]['pkg_type'] = 'flat'
                # If some_item is a dir
                elif os.path.isdir(some_item):
                    # Try to get *_Install.pkg
                    try:
                        # Look for the *_Install.pkg
                        install_pkg = glob.glob(os.path.join(some_item, 'build',
                                                             '*_Install.pkg'))[0]
                        # Create nested dict named after the app_name
                        adobe_installers[app_name] = {}
                        # Add pkg_path to adobe_installers[aop_name]
                        adobe_installers[app_name]['pkg_path'] = install_pkg
                        # Add pkg_type to adobe_installers[aop_name]
                        adobe_installers[app_name]['pkg_type'] = 'bundle'
                    # If *_Install.pkg is missing
                    except IndexError:
                        # Pass to run next loop iteration
                        pass

    # If no Adobe installers found
    if len(adobe_installers.keys()) == 0:
        # Progress notification
        print("WARNNING: 0 Adobe pkg's found, exiting...")
        # Exit
        sys.exit(0)
    # If one Adobe installer is found, notify and proceed
    elif len(adobe_installers.keys()) == 1:
        # Progress notification
        print("1 Adobe pkg found:")
    # If more than one Adobe installer, notify and proceed
    else:
        # Progress notification
        print(f"{len(adobe_installers.keys())} Adobe pkg's found, in total:")

    # For each installer details
    for _, installer_details in adobe_installers.items():
        # If a bundle pkg:
        if installer_details['pkg_type'] == 'bundle':
            # Append to bundle_pkgs
            bundle_pkgs.append(installer_details['pkg_path'])
        # If a bundle pkg:
        if installer_details['pkg_type'] == 'flat':
            # Append to flat_pkgs
            flat_pkgs.append(installer_details['pkg_path'])

    # Print bundle_pkgs details
    print_pkg_summary(sorted(bundle_pkgs), 'bundle')

    # Print flat_pkgs details
    print_pkg_summary(sorted(flat_pkgs), 'flat')

    # Return a dict of installers
    return adobe_installers


def get_app_names():
    '''
        Parses AdobeAutoPkgApplicationData.json, returning an sorted and deduped list of apps
    '''

    # Var declaration
    app_names_list = []

    # Get the path to AdobeAutoPkgApplicationData.json
    json_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             'AdobeAutoPkgApplicationData.json')

    # if AdobeAutoPkgApplicationData.json doesn't exist or isn't a file, error
    if not os.path.isfile(json_path):
        # Print error
        print(f"ERROR: \"{json_path}\" cannot be found, exiting...")
        # Exit
        sys.exit(0)

    # Open json_file
    with open(json_path, encoding='utf-8') as json_file:
        # Create var from the json
        json_data = json.load(json_file)

    # For each json object
    for json_object in json_data:
        # Iterate each key within versions in the the json object
        for version_key in json_object['versions'].keys():
            # Add app_name to app_names_list
            app_names_list.append(json_object['versions'][version_key]['app_name'])

    # If app_names_list is empty
    if not app_names_list:
        # Print error
        print(f"ERROR: Cannot get a list of app names from \"{json_path}\", exiting...")
        # Exit
        sys.exit(0)
    # If we have content in app_names_list
    else:
        # Sort and de-dupe app_names_list
        app_names_list = sorted(set(app_names_list))
        # Progress notification
        print(f"{len(app_names_list)} unique app_name values found within: {json_path}...")
        # Return app_names_list
        return app_names_list


def get_override_dirs():
    '''
        Returns an array of override dirs
    '''

    # Progress notification
    print("Looking for override dirs...")

    # declared, set to the default path
    override_dirs = (globalPreferences.get_pref('RECIPE_OVERRIDE_DIRS') or
                     os.path.join(os.path.expanduser('~/Library/'), 'AutoPkg',
                     'RecipeOverrides/').split())

    # If override_dirs is a string
    if isinstance(override_dirs, str):
        # Convert to list, expanding if needed
        override_dirs = [os.path.expanduser(override_dirs)]

    # If one override dir is found, notify and proceed
    if len(override_dirs) == 1:
        # Progress notification
        print("Using override dir:")
    # If more than one override dir, notify and proceed
    else:
        # Progress notification
        print("Using override dirs:")

    # For each override_dir in override_dirs
    for override_dir in sorted(override_dirs):
        # Get the index
        dir_index = int(override_dirs.index(override_dir))
        # If the dir does not exist
        if not os.path.exists(override_dirs[dir_index]):
            # Remove from override_dirs
            override_dirs.remove(override_dir)
        # If the dir exists
        else:
            # Print the dir
            print(f"\t{override_dirs[dir_index]}")

    # If override_dirs is empty
    if not override_dirs:
        # Print error
        print("ERROR: No override dirs found, exiting...")
        # Exit
        sys.exit(1)
    # If we have one or more override_dir
    else:
        # Return a sorted list of dirs
        return sorted(override_dirs)


def get_override_identifier(override_path):
    '''
        Returns the identifier of the override at override_path
    '''

    # Var declaration
    override_identifier = None

    # If a yaml file
    if override_path.endswith('.yml') or override_path.endswith('.yaml'):
        # Try to read it as yaml
        try:
            # Open yaml file
            with open(override_path, 'r', encoding = 'utf-8') as read_file:
                # Create var from the overrides contents
                override_content = yaml.safe_load(read_file)
                # Get the overrides identifier
                override_identifier = override_content['Identifier']
        # If empty, TypeError is raised
        except TypeError:
            # Progress notification
            print(f"\tWARNING: Reading, \"{override_path}\" errored as the override is empty.")
            return None
        # Raise an exception if the override cannot be parsed
        except yaml.scanner.ScannerError as err_msg:
            # Progress notification
            print(f"\tWARNING: Reading, \"{override_path}\" errored with: {err_msg}")
            # Return None
            return None
    # If not a .yaml override
    else:
        # Try to read in the file as a plist
        try:
            # Open plist file
            with open(override_path, 'rb') as read_file:
                # Create var from the overrides contents
                override_content = plistlib.load(read_file)
                # Get the overrides identifier
                override_identifier = override_content['Identifier']
        # Raise an exception if the override cannot be parsed
        except plistlib.InvalidFileException as err_msg:
            # Progress notification
            print(f"\tWARNING: Reading, \"{override_path}\" errored with: {err_msg}")
            # Return None
            return None

    # If we have extracted the override_identifier
    if override_identifier:
        print(f"\t{override_path}, has identifier: {override_identifier}...")

    # Return override_identifier
    return override_identifier


def match_overrides(adobe_installers, override_dirs, recipe_type):
    '''
       Returns an sorted list of matched overrides, here matched flat pkg's override bundle
    '''

    # Progress notification
    print("Looking in for overrides...")

    # Var declaration
    matched_override = None
    matched_overrides = {}

    # For each override_dir
    for override_dir in override_dirs:
        # Generate a list containing all recipe files
        recipe_files = os.listdir(override_dir)
        # For each recipe file
        for recipe_file in recipe_files:
            # For each adobe_installer
            for adobe_installer in adobe_installers:
                # Var declaration
                override_path = None
                # If 'pkg_path' ends with _MACARM.pkg
                if adobe_installers[adobe_installer]['pkg_path'].endswith('_MACARM.pkg'):
                    # If the override starts with adobe_installer and the type matches
                    if (recipe_file.startswith(adobe_installer) and recipe_type in recipe_file
                      and 'arm64' in recipe_file):
                        # Path to the override
                        override_path = os.path.join(override_dir, recipe_file)
                # If 'pkg_path' does not end with _MACARM.pkg
                else:
                    # If the override starts with adobe_installer and the type matches
                    if (recipe_file.startswith(adobe_installer) and recipe_type in recipe_file
                      and not 'arm64' in recipe_file):
                        # Path to the override
                        override_path = os.path.join(override_dir, recipe_file)
                # If we override_path has a value
                if override_path:
                    # Get the overrides identifier
                    matched_override = get_override_identifier(override_path)
                    # If matched_override is not none
                    if matched_override:
                        # Append to matched_overrides
                        matched_overrides[matched_override] = override_path
                        # Add overrides identifier to adobe_installers dict
                        adobe_installers[adobe_installer]['override_identifier'] = matched_override
                        # Add overrides path to adobe_installers dict
                        adobe_installers[adobe_installer]['override_path'] = override_path

    # For each adobe_installer
    for adobe_installer in list(adobe_installers):
        # If we don't have 'override_identifier' for the adobe_installer
        if 'override_identifier' not in adobe_installers[adobe_installer]:
            # Remove adobe_installer from the dict
            adobe_installers.pop(adobe_installer, None)

    # Print a summary of the matched overrides
    print_matched_override_summary(matched_overrides)

    # Return adobe_installers
    return adobe_installers


def print_matched_override_summary(matched_overrides):
    '''
        Print a summary of the matched overrides
    '''

    # If we have no matched overrides, exit
    if not matched_overrides:
        # Progress notification
        print("WARNNING: 0 overrides matched, exiting...")
        # Exit
        sys.exit(0)
    # If we have matches
    else:
        # If we have only matched 1 override
        if len(matched_overrides) == 1:
            # Progress notification
            print(f"{len(matched_overrides)} override matched...")
        # If more than one override was matched
        else:
            # Progress notification
            print(f"{len(matched_overrides)} overrides matched...")
        # For each matched override
        for matched_override, matched_path in matched_overrides.items():
            # Progress notification
            print(f"\t{matched_override} - {matched_path}")


def print_pkg_summary(pkg_list, pkg_type):
    '''
       Prints out details of the pkg_type pkg's passed to pkg_list
    '''

    # If we have 0 pkg_type {pkg_type} pkgs
    if len(pkg_list) == 0:
        # Progress notification
        print(f"0 {pkg_type} pkg's found...")
    # If more we have one {pkg_type} pkg
    elif len(pkg_list) == 1:
        # Progress notification
        print(f"{len(pkg_list)} {pkg_type} pkg found...")
        # For each adobe_pkg in pkg_list
        for adobe_pkg in sorted(pkg_list):
            # Progress notification
            print(f"\t{adobe_pkg}")
    # If more we have more than one {pkg_type} pkg
    else:
        # Progress notification
        print(f"{len(pkg_list)} {pkg_type} pkg's found...")
        # For each adobe_pkg in pkg_list
        for adobe_pkg in sorted(pkg_list):
            # Progress notification
            print(f"\t{adobe_pkg}")


def run_recipe_list(recipe_list_path, report_path):
    '''
        Run recipe list
    '''

    # Check that the recipe_list file has content before proceeding
    with open (recipe_list_path, encoding='utf-8') as recipe_list_file:
        # Read in content
        if not recipe_list_file.readlines():
            # Progress notification
            print(f"ERROR: {recipe_list_path} is empty, no overrides found... exiting ...")
            # Exit
            sys.exit(1)

    # The subprocess command
    cmd_args = ['/usr/local/bin/autopkg', 'run', '-vv', '--recipe-list', recipe_list_path,
                '--report-plist', report_path]

    # Progress notification
    print(f"Running: {cmd_args}...\n")

    # Run the command, not checking as issues will show in output
    subprocess.run(cmd_args, check = False)


def update_overrides(adobe_installers):
    '''
        Update the overrides by adding/updating aacp_pkg_path
    '''

    # Progress notification
    print("Updating overrides...")

    # For each installer details
    for _, installer_details in adobe_installers.items():
        # Progress notification
        print(f"\tUpdating: {installer_details['override_path']}...")
        # If a yaml file
        if (installer_details['override_path'].endswith('.yml') or
                installer_details['override_path'].endswith('.yaml')):
            # Try to read it as yaml
            try:
                # Open yaml file, to read
                with open(installer_details['override_path'], 'r', encoding = 'utf-8') as read_file:
                    # Create var from the overrides contents
                    override_content = yaml.safe_load(read_file)
                # Set aacp_override_path
                override_content['Input']['aacp_override_path'] = installer_details['override_path']
                # Set aacp_package_path
                override_content['Input']['aacp_package_path'] = installer_details['pkg_path']
                # Set aacp_package_type
                override_content['Input']['aacp_package_type'] = installer_details['pkg_type']
                # Open yaml file, to write
                with (open(installer_details['override_path'], 'w+', encoding = 'utf-8') as
                  write_file):
                    # Write the updated content to the override
                    yaml.dump(override_content, write_file, default_flow_style=False)
            # If empty, TypeError is raised
            except TypeError:
                # Progress notification
                print(f"ERROR: Reading, \"{installer_details['override_path']}\" errored as "
                      f"the override is empty.")
                # Return None
                sys.exit(1)
            # Error if the override cannot be parsed
            except yaml.scanner.ScannerError as err_msg:
                # Progress notification
                print(f"ERROR: Reading, \"{installer_details['override_path']}\" errored with: "
                      f"{err_msg}")
                # Return None
                sys.exit(1)
        # If not a .yaml override
        else:
            # Try to read in the file as a plist
            try:
                # Open plist file, to read
                with open(installer_details['override_path'], 'rb') as read_file:
                    # Create var from the overrides contents
                    override_content = plistlib.load(read_file)
                # Set aacp_override_path
                override_content['Input']['aacp_override_path'] = installer_details['override_path']
                # Set aacp_package_path
                override_content['Input']['aacp_package_path'] = installer_details['pkg_path']
                # Set aacp_package_type
                override_content['Input']['aacp_package_type'] = installer_details['pkg_type']
                # Open the override for writing
                with open(installer_details['override_path'], 'wb') as write_file:
                    # Write the updated content to the override
                    plistlib.dump(override_content, write_file)
            # Raise an exception if the override cannot be parsed
            except plistlib.InvalidFileException as err_msg:
                # Progress notification
                print(f"ERROR: Reading, \"{installer_details['override_path']}\" errored with: "
                      f"{err_msg}")
                # Return None
                sys.exit(1)


if __name__ == '__main__':

    # Gimme some main
    main()

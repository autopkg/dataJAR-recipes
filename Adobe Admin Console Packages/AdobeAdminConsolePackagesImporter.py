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
__version__ = '1.1'


# Functions
def main():
    '''
        Check passed arguments before proceeding
    '''

    # Setup arparse
    parser = argparse.ArgumentParser()
    parser.add_argument('type', type=str, help="Recipe type, for example: \"munki\" or \"jamf\"")
    arg_parser = parser.parse_args()

    # Retrieve passed type
    recipe_type = arg_parser.type.lower()

    # Var declarations
    packages_path = os.path.expanduser('~/Downloads/')
    recipe_list_path = os.path.join(packages_path + 'adobe_admin_console_recipes_list.txt')
    report_path = os.path.join(packages_path + 'adobe_admin_console_recipes_report.plist')

    # Check that packages_path exists
    if not os.path.exists(packages_path):
        # Exit
        print(f"ERROR: Cannot locate directory, {packages_path}... exiting...")
        sys.exit(1)

    # Check that packages_path is a directory
    if not os.path.isdir(packages_path):
        # Exit
        print(f"ERROR: {packages_path} is a not a directory... exiting...")
        sys.exit(1)

    # Parse AdobeAutoPkgApplicationData.json and return a list of names
    app_names_list = get_app_names()

    # Check for Adobe installers
    adobe_installers = look_for_installers(app_names_list, packages_path)

    # Get override dirs
    override_dirs = get_override_dirs()

    # Get matching overrides
    matched_overrides = match_overrides(adobe_installers, override_dirs, recipe_type)

    # Populate a recipe list
    create_list(matched_overrides, recipe_list_path)

    # Run recipe list
    run_recipe_list(recipe_list_path, report_path)


def create_list(matched_overrides, recipe_list_path):
    '''
        Create recipe list, deleting existing
    '''

    # Var declaration
    line_count = 1
    override_count = len(matched_overrides)

    # If a file exists at recipe_list_path, delete it
    if os.path.exists(recipe_list_path):
        # Progress notification
        print(f"Deleting prior created: {recipe_list_path}...")
        # Delete the file
        os.remove(recipe_list_path)

    # Append to recipe_list_path, creating if file is missing
    with open(recipe_list_path, 'a+', encoding='utf-8') as list_file:
        # For each override
        for matched_override in matched_overrides:
            # If line count is then that override count
            if line_count < override_count:
                # Write the overrides to recipe_list_path. appending a new line
                list_file.write(matched_override + '\n')
                # Increment var
                line_count += 1
            # If we're at the last line
            else:
                # Write the overrides to recipe_list_path. without appending a new line
                list_file.write(matched_override)

    # Progress notification
    print(f"Created recipe list at: {recipe_list_path}...")


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

    # Retrieve override name from file
    # Borrowed with <3 from:
    # https://github.com/autopkg/autopkg/blob/405c913deab15042819e2f77f1587a805b7c1ada/Code/autopkglib/__init__.py#L341-L359
    if override_path.endswith(".yaml"):
        # Try to read it as yaml
        try:
           # Open yaml file
            with open (override_path, 'rb') as read_file:
                # Create var from the overrides contents
                recipe_dict = yaml.load(read_file, Loader=yaml.FullLoader)
                # Get the overrides identifier
                override_identifier = recipe_dict["Identifier"]
        # pylint: disable = broad-except
        except yaml.scanner.ScannerError as err_msg:
            # Progress notification
            print(f"\tWARNING: Reading, \"{override_path}\" errored with: {err_msg}")
            # Pass to run next loop iteration
            # pylint: disable = unnecessary-pass
            pass
    # If not a .yaml override
    else:
        # Try to read in the file as a plist
        try:
            # Open plist file
            with open (override_path, 'rb') as read_file:
                # Create var from the overrides contents
                recipe_dict = plistlib.load(read_file)
                # Get the overrides identifier
                override_identifier = recipe_dict["Identifier"]
        # Raise an exception if the plist cannot be parsed
        except plistlib.InvalidFileException as err_msg:
            # Progress notification
            print(f"\tWARNING: Reading, \"{override_path}\" errored with: {err_msg}")
            # Pass to run next loop iteration
            # pylint: disable = unnecessary-pass
            pass

    # If we have extracted the override_identifier
    if override_identifier:
        print(f"\t{override_path}, has identifier: {override_identifier}...")

    # Return override_identifier
    return override_identifier


def look_for_installers(app_names_list, packages_path):
    '''
        Look pkg's starting with names in app_names within the packages_path dir
    '''

    # Progress notification
    print(f"Looking in {packages_path} for Adobe installers...")

    # Var declaration
    adobe_installers = {}
    adobe_installers['bundle_pkgs'] = {}
    adobe_installers['flat_pkgs'] = {}

    # Get a sorted list of items beginning with Adobe* in ~/Downloads
    for some_item in sorted(glob.glob(os.path.join(packages_path, '*'))):
        # Iterate over app_names_list
        for app_name in app_names_list:
            # If the items name starts app_name
            if os.path.basename(some_item).startswith(app_name):
                # If some_item is a file, and ends with .pkg
                if os.path.isfile(some_item) and some_item.endswith('.pkg'):
                    # Add adobe_installers['flat_pkgs'][aop_name]
                    adobe_installers['flat_pkgs'][app_name] = some_item
                # If some_item is a dir
                elif os.path.isdir(some_item):
                    # Try to get *_Install.pkg and *_Uninstall.pkg pkg's
                    try:
                        # Look for the *_Install.pkg
                        install_pkg = glob.glob(os.path.join(some_item, 'build',
                                                             '*_Install.pkg'))[0]
                        # Look for the *_Uninstall.pkg
                        uninstall_pkg = (glob.glob(os.path.join(some_item, 'build',
                                                                '*_Uninstall.pkg'))[0])
                        # Append to adobe_installers['bundle_pkgs'] both pkg's as a list
                        adobe_installers['bundle_pkgs'][app_name] = [install_pkg, uninstall_pkg]
                    # If either *_Install.pkg and *_Uninstall.pkg is missing
                    except IndexError:
                        # Pass to run next loop iteration
                        pass

    # If no folders are found, exit
    if not adobe_installers:
        # Progress notification
        print(f"WARNING: No Adobe isntallers found in {packages_path}, exiting..")
        # Exit
        sys.exit(0)

    # Total count
    total_pkgs_count = ((len(adobe_installers['bundle_pkgs']) * 2) +
                         len(adobe_installers['flat_pkgs']))

    # If no Adobe installers found
    if total_pkgs_count == 0:
        # Progress notification
        print("WARNNING: 0 Adobe pkg's found, exiting...")
        # Exit
        sys.exit(0)
    # If one Adobe installer is found, notify and proceed
    elif total_pkgs_count == 1:
        # Progress notification
        print("1 Adobe pkg found:")
    # If more than one Adobe installer, notify and proceed
    else:
        # Progress notification
        print(f"{total_pkgs_count} Adobe pkg's found, in total:")

    # Print bundle_pkgs details
    print_pkg_info(adobe_installers['bundle_pkgs'], 'bundle')

    # Print flat_pkgs details
    print_pkg_info(adobe_installers['flat_pkgs'], 'flat')

    # Return a dict of installers
    return adobe_installers


def match_overrides(adobe_installers, override_dirs, recipe_type):
    '''
       Returns an sorted list of matched overrides, here matched flat pkg's override bundle
    '''

    # Progress notification
    print("Looking in for overrides...")

    # Var declaration
    matched_overrides = []
    bundle_pkg_matches = sorted(adobe_installers['bundle_pkgs'].keys())
    flat_pkg_matches = sorted(adobe_installers['flat_pkgs'].keys())

    # For each override_dir
    for override_dir in override_dirs:
        # Generate a list containing all recipe files
        recipe_files = os.listdir(override_dir)
        # For each recipe file
        for recipe_file in recipe_files:
            # Check against bundle_pkg_matches
            for bundle_pkg_match in bundle_pkg_matches:
                # If the override starts with bundle_pkg_match and the type matches
                if recipe_file.startswith(bundle_pkg_match) and recipe_type in recipe_file:
                    # Get the overrides identifier
                    matched_overrides.append(get_override_identifier(os.path.join(override_dir,
                                                                                  recipe_file)))
            # Check against flat_pkg_matches
            for flat_pkg_match in flat_pkg_matches:
                # If the override starts with flat_pkg_match and the type matches
                if recipe_file.startswith(flat_pkg_match) and recipe_type in recipe_file:
                    # Get the overrides identifier
                    matched_overrides.append(get_override_identifier(os.path.join(override_dir,
                                                                                  recipe_file)))

    # If we have no matched overrides, exit
    if not matched_overrides:
        # Progress notification
        print("WARNNING: 0 overrides matched, exiting...")
        # Exit
        sys.exit(0)
    # If we have matches
    else:
        # Sort and de-dupe matched_overrides
        matched_overrides = sorted(set(matched_overrides))
        # If we have only matched 1 override
        if len(matched_overrides) == 1:
            # Progress notification
            print(f"{len(matched_overrides)} override matched...")
        # If more than one override was matched
        else:
            # Progress notification
            print(f"{len(matched_overrides)} overrides matched...")
        # For each matched override
        for matched_override in matched_overrides:
            # Progress notification
            print(f"\t{matched_override}")

    # Return matched_overrides
    return matched_overrides


def print_pkg_info(pkg_list, pkg_type):
    '''
       Prints out details of the pkg's passed to pkg_list
    '''

    # If pkg_type is bundle
    if pkg_type == 'bundle':
        # If no bundle pkg pair found
        if len(pkg_list) == 0:
            # Progress notification
            print("0 bundle pkg pairs found...")
        # If more we have one bundle pkg pair
        elif len(pkg_list) == 1:
            # Progress notification
            print(f"{len(pkg_list)} bundle pkg pair found...")
            # For each app_name in pkg_list
            for adobe_pkg in sorted(pkg_list.keys()):
                # Progress notification
                print(f"\t{pkg_list[adobe_pkg][0]} and {pkg_list[adobe_pkg][1]}")
        # If more we have more than one bundle pkg pair
        else:
            # Progress notification
            print(f"{len(pkg_list)} bundle pkg pairs found...")
            # For each app_name in pkg_list
            for adobe_pkg in sorted(pkg_list.keys()):
                # Progress notification
                print(f"\t{pkg_list[adobe_pkg][0]} and {pkg_list[adobe_pkg][1]}")

    # If pkg_type is flat
    if pkg_type == 'flat':
        # If we have 0 pkg_type flat pkgs
        if len(pkg_list) == 0:
            # Progress notification
            print("0 flat pkg's found...")
        # If more we have one flat pkg
        elif len(pkg_list) == 1:
            # Progress notification
            print(f"{len(pkg_list)} flat pkg found...")
            # For each adobe_pkg in pkg_list
            for adobe_pkg in sorted(pkg_list):
                # Progress notification
                print(f"\t{pkg_list[adobe_pkg]}")
        # If more we have more than one flat pkg
        else:
            # Progress notification
            print(f"{len(pkg_list)} flat pkg's found...")
            # For each adobe_pkg in pkg_list
            for adobe_pkg in sorted(pkg_list):
                # Progress notification
                print(f"\t{pkg_list[adobe_pkg]}")


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

    # Notify we're starting
    print(f"Running recipe_list: {recipe_list_path}")

    # The subprocess command
    cmd_args = ['/usr/local/bin/autopkg', 'run', '-vv', '--recipe-list', recipe_list_path,
                '--report-plist', report_path]

    # Notify what command we're about to run.
    print(f"Running: {cmd_args}...\n\n")

    # Run the command, not checking as issues will show in output
    subprocess.run(cmd_args, check = False)


if __name__ == '__main__':

    # Gimme some main
    main()

#!/usr/local/autopkg/python
# pylint: disable = invalid-name, too-many-lines
"""
Copyright (c) 2024, Jamf Ltd.  All rights reserved.

See main() docstring for more information,
"""


# Version
__version__ = '3.0'


# Standard Imports
import argparse
import glob
import json
import os
import platform
import plistlib
import re
import shutil
import subprocess
import sys
import tempfile
import xml
from xml.etree import ElementTree
import yaml
# pylint: disable = no-name-in-module
from SystemConfiguration import SCDynamicStoreCopyConsoleUser


# Functions
def main():
    """
    Imports Adobe Admin Console Packages
    """

    # Make sure we're root
    if os.geteuid() != 0:
        # Error notification
        print('ERROR: This script must be run as root')
        # Exit
        sys.exit(1)

    # Setup arparse
    arg_parser = setup_argparse()

    # Retrieve passed type
    recipe_type = arg_parser.type.lower()

    # Var declarations
    packages_path = os.path.expanduser(arg_parser.dir)
    recipe_list_path = os.path.join(packages_path, 'adobe_admin_console_recipes_list.txt')
    report_path = os.path.join(packages_path, 'adobe_admin_console_recipes_report.plist')
    user_name = (SCDynamicStoreCopyConsoleUser(None, None, None) or [None])[0]

    # If we have no value for the above, or we're at the loginwindow.. set username to None
    if user_name in ("", "loginwindow"):
        # Error notification
        print("ERROR: Cannot determine the logged in user, or noone is logged in, exiting...")
        # Exit
        sys.exit(1)

    # Check that "packages_path" exists
    if not os.path.exists(packages_path):
        # Error notification
        print(f"ERROR: Cannot locate directory, {packages_path}, exiting...")
        # Exit
        sys.exit(1)

    # Check that "packages_path" is a directory
    if not os.path.isdir(packages_path):
        # Error notification
        print(f"ERROR: {packages_path} is a not a directory, exiting...")
        # Exit
        sys.exit(1)

    # Read "aacp_json_path", returning a dict
    application_data = read_json_file(os.path.join(os.path.dirname(os.path.realpath(__file__)),
        'AdobeAutoPkgApplicationData.json'))

    # Progress notification
    print(f"Data retrieved for {len(application_data)} for Adobe applications...")

    # Check for "packages_path" for installers that start with names that are in "application_data"
    adobe_installers = get_adobe_installers(application_data, packages_path)

    # Progress notification
    print(f"{len(adobe_installers.keys())} Adobe pkg(s) found:")

    # For each found installer
    for _, installer_data in adobe_installers.items():
        # Print
        print(f"\t{installer_data['aacp_package_path']}")

    # Get RECIPE_CACHE_DIR and RECIPE_OVERRIDE_DIRS from com.github.autopkg.plist
    override_dirs, recipe_cache_dir = get_autopkg_dirs(user_name)

    # Progress notification
    print(f"Retrieved {len(override_dirs)} override dir(s)...")

    # Get matching overrides
    adobe_installers = match_overrides(adobe_installers, override_dirs, recipe_type)

    # Progress notification
    print(f"{len(adobe_installers)} override(s) matched...")

    # For each matched override
    for _, installer_dict in adobe_installers.items():
        # Progress notification
        print(f"\t{installer_dict['aacp_override_identifier']} - "
            f"{installer_dict['aacp_override_path']}")

    # Expand the installers to retrieve more details, deleting the temp dirs when done
    adobe_installers = expand_installers(adobe_installers)

    # If "adobe_installers" is empty
    if not adobe_installers:
        # Progress notification
        print("WARNING: No installers left to process.. exiting...")
        # Exit
        sys.exit(0)

    # Install the Adobe title(s) locally, to retrieve details once installed, getting icon and/or
    # uninstalling as wanted
    adobe_installers = install_adobe_titles(adobe_installers, arg_parser, recipe_cache_dir,
        user_name)

    # Update overrides
    update_overrides(adobe_installers)

    # Creates/overwrites the recipe list at: "recipe_list_path"
    create_list(adobe_installers, recipe_list_path, user_name)

    # Run recipe list
    run_recipe_list(recipe_list_path, report_path, user_name)


def copy_icons_to_cache_dirs(icon_path: str, destination_path: str, recipe_cache_path: str,
    user_name: str):
    """
    Copies the application icons to "RECIPE_CACHE_DIR" or to the default dir of:
    ~Library/AutoPkg/Cache/<override identifier>/

    Parameters
    ----------
    icon_path: str
        Path to the icon to copy.
    destination_path: str
        Path to copy the icon to.
    recipe_cache_dir: str
        Root dir for recipe cache.
    user_name: str
        The logged in users user name.
    """

    # If we don't have a file at "icon_path"
    if not os.path.exists(icon_path):
        # Error notification
        print(f"ERROR: Cannot find icon: {icon_path}, exiting...")
        # Exit
        sys.exit(1)

    # Create the recipe cache folder, if it's not there
    os.makedirs(recipe_cache_path, exist_ok = True)

    # Set the logged in user to the folder owner
    shutil.chown(recipe_cache_path, user_name)

    # Try to:
    try:
        # Progress notification
        print(f"Attempting to copy: {icon_path}, to: {destination_path}...")
        # Copy "icon_path" to "recipe_cache_path"/"adobe_installer".icns
        shutil.copy(icon_path, destination_path)
    # If failed to copy the folder
    except OSError as err_msg:
        # Error notification
        print(f"ERROR: Copying {icon_path} to: {destination_path}, falied with: {err_msg}")
        # Exit
        sys.exit(1)

    # Progress notification
    print(f"Successfully copied: {icon_path}, to: {destination_path}...")

    # Set the logged in user to the icons owner
    shutil.chown(destination_path, user_name)


def create_list(adobe_installers: dict, recipe_list_path: str, user_name: str):
    """
    Creates/overwrites the recipe list at: "recipe_list_path". Adding only the overrides
    which have been matched to installers.

    Parameters
    ----------
    adobe_installers: dict
        Dict containing information around on the Adobe titles.
    recipe_list_path: str
        Full path to the recipe list to create/update.
    user_name: str
        The logged in users user name.
    """

    # Var declaration
    line_count = 1
    override_count = len(adobe_installers)

    # Write a file at "recipe_list_path", creating if missing, overwriting contents if not.
    with open(recipe_list_path, 'w', encoding='utf-8') as list_file:
        # For each adobe installer
        for _, installer_data in list(adobe_installers.items()):
            # Add to the recipe list
            list_file.write(f"{installer_data['aacp_override_identifier']}")
            # Add a new line, if not the last override
            if line_count != override_count:
                # Add a new line
                list_file.write("\n")
                # Increment
                line_count += 1

    # Set the logged in user to the recipe lists owner
    shutil.chown(recipe_list_path, user_name)

    # Progress notification
    print(f"Created recipe list at: {recipe_list_path}...")


def expand_installers(adobe_installers: dict) -> dict:
    """
    Expand each Adobe titles installer, to retrieve the below, adding them to "adobe_installers"
    and deleting the "temp_dir" when done:
        - blocking applications
        - description
        - minimum OS

    Parameters
    ----------
    adobe_installers: dict
        Dict containing information around on the Adobe titles.

    Returns
    ------
    adobe_installers: dict
        dict containing the data on the matched Adobe installers and their additional data
        retrieved from having installed them locally.
    """

    # For each adobe installer
    for adobe_installer, installer_data in list(adobe_installers.items()):
        # Var declaration
        installer_data['aacp_pkg_expand_dir'] = os.path.join(tempfile.mkdtemp(), 'expand')
        # Progress notification
        print(f"Expanding: {installer_data['aacp_package_path']} to "
            f"{installer_data['aacp_pkg_expand_dir']}...")
        # Run subprocess
        run_subprocess(['/usr/sbin/pkgutil', '--expand', installer_data['aacp_package_path'],
            installer_data['aacp_pkg_expand_dir']])
        # Process optionXML.xml, found within the scripts directory of the expanded pkg
        (installer_data['aacp_application_base_version'],
            installer_data['aacp_application_install_lang'],
                installer_data['aacp_application_architecture_type'],
                    installer_data['aacp_target_folder']) = (
                        parse_optionxml_xml(os.path.join(installer_data['aacp_pkg_expand_dir'],
                            'Install.pkg/Scripts/optionXML.xml')))
        # If "adobe_installer" is not AdobeAcrobatDC
        if not adobe_installer == 'AdobeAcrobatDC':
            # Process Application.json, found within a sub dir of /Scripts/HD/ in the expanded pkg
            (installer_data['aacp_application_description'],
                installer_data['aacp_blocking_applications'],
                    installer_data['aacp_minimum_os']) = parse_application_json(
                        os.path.join(installer_data['aacp_pkg_expand_dir'],
                            'Install.pkg/Scripts/HD/', installer_data['aacp_target_folder'],
                                'Application.json'), installer_data)
        # Sort
        installer_data = dict(sorted(installer_data.items()))
        # Try to
        try:
            # Progress notification
            print(f"Deleting: {installer_data['aacp_pkg_expand_dir']}...")
            # Delete "installer_data['aacp_pkg_expand_dir']"
            shutil.rmtree(os.path.dirname(installer_data['aacp_pkg_expand_dir']))
        # If not defined
        except OSError as err_msg:
            # Error notification
            print(f"ERROR: Deleting installer_data['aacp_pkg_expand_dir'] failed with {err_msg}, "
                  f"exiting...")
            # Exit
            sys.exit(1)

    # For each adobe_installer
    for adobe_installer, installer_data in list(adobe_installers.items()):
        # If the installer is not a universal installer
        if installer_data['aacp_application_architecture_type'] != 'macuniversal':
            # Get the running Mac's processor
            host_arch = platform.machine()
            # If the installers architecture isn't the same as the running Mac's
            if installer_data['aacp_application_architecture_type'] != 'host_arch':
                # Remove adobe_installer from the dict
                adobe_installers.pop(adobe_installer, None)
                # Progress notification
                print(f"\tWARNING: Removed {adobe_installer}, as it can only install on: "
                      f"{installer_data['aacp_application_architecture_type']}, and this Mac's "
                      f"processor is: {host_arch}.")

    # Returns
    return adobe_installers


def get_adobe_installers(application_data: dict, packages_path: str) -> dict:
    """
    Looks within "packages_path" for flat packages that names start with the top level keys
    within "application_data". Returning a dict.

    Parameters
    ----------
    application_data: dict
        Dict containing information around on the Adobe titles.
    packages_path: str
        Path to look for the packages.

    Returns
    ------
    adobe_installers: dict
        dict containing the data on the matched Adobe installers and their additional data.
    """

    # Progress notification
    print(f"Looking in {packages_path} for Adobe installers...")

    # Var declaration
    adobe_installers = {}

    # Get a sorted list of items beginning with Adobe* in ~/Downloads
    for some_item in sorted(glob.glob(os.path.join(packages_path, '*'))):
        # Iterate over application_data
        for app_name in application_data:
            # If the items name starts app_name
            if os.path.basename(some_item).split('_')[0] == app_name:
                # If some_item is a file, and ends with .pkg
                if os.path.isfile(some_item) and some_item.endswith('.pkg'):
                    # Create nested dict named after the app_name
                    adobe_installers[app_name] = application_data[app_name]
                    # Add aacp_package_path to adobe_installers[aop_name]
                    adobe_installers[app_name]['aacp_package_path'] = some_item
                # If some_item is a dir
                elif os.path.isdir(some_item):
                    # Warning notification
                    print(f"WARNNING: Skipping {some_item}, as it is a bundle pkg...")

    # If no Adobe installers found
    if len(adobe_installers.keys()) == 0:
        # Error notification
        print("ERROR: 0 Adobe pkg's found, exiting...")
        # Exit
        sys.exit(1)

    # Returns
    return adobe_installers


def get_autopkg_dirs(user_name: str) -> (list, str):
    """
    Checks AutoPkg's pref domain for "RECIPE_CACHE_DIR" and "RECIPE_OVERRIDE_DIRS"

    Parameters
    ----------
    user_name: str
        The logged in users user name.

    Returns
    ------
    override_dirs  list
        List of override dirs.
    recipe_cache_dir: str
        Path to the recipe_cache_dir.
    """

    # Var declaration
    autopkg_plist = os.path.join('/Users/', user_name,
        'Library/Preferences/com.github.autopkg.plist')

    # Read in the plist file
    autopkg_preferences = read_plist_file(autopkg_plist)

    # Progress notification
    print("Retrieving RECIPE_CACHE_DIR...")

    # If "RECIPE_CACHE_DIR" is defined within "autopkg_preferences"
    if 'RECIPE_CACHE_DIR' in autopkg_preferences:
        # Set "recipe_cache_dir" to the "RECIPE_CACHE_DIR"
        recipe_cache_dir = os.path.expanduser(autopkg_preferences['RECIPE_CACHE_DIR'])
    # If not defined
    else:
        # Set to the default path
        recipe_cache_dir = os.path.expanduser('~/Library/AutoPkg/Cache')

    # Progress notification
    print(f"\tRECIPE_CACHE_DIR = {recipe_cache_dir}")


    # Progress notification
    print("Retrieving RECIPE_OVERRIDE_DIRS...")

    # If "RECIPE_OVERRIDE_DIRS" is defined within "autopkg_preferences"
    if 'RECIPE_OVERRIDE_DIRS' in autopkg_preferences:
        # Set "override_dirs" to "RECIPE_OVERRIDE_DIRS"
        override_dirs = os.path.expanduser(autopkg_preferences['RECIPE_OVERRIDE_DIRS']).split()
    # If not defined
    else:
        # Set to the default path
        override_dirs = [os.path.expanduser('~/Library/AutoPkg/RecipeOverrides')]

    # If override_dirs is a string
    if isinstance(override_dirs, str):
        # Convert to list, expanding if needed
        override_dirs = [os.path.expanduser(override_dirs)]

    # Progress notification
    print("Using override dir(s):")

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

    # Return
    return sorted(override_dirs), recipe_cache_dir


def get_override_identifier(aacp_override_path: str) -> str:
    """
    Returns the identifier of the override specified at "aacp_override_path".

    Parameters
    ----------
    aacp_override_path: str
        Path to override to retrieve the identifier from.

    Returns
    ------
    aacp_override_identifier: str
        The overrides identifier.
    """

    # Var declaration
    aacp_override_identifier = None

    # If a yaml file
    if aacp_override_path.endswith('.yml') or aacp_override_path.endswith('.yaml'):
        # Try to read in the file
        override_content = read_yaml_file(aacp_override_path)
    # If not a .yaml override
    else:
        # Try to read in the file
        override_content = read_plist_file(aacp_override_path)

    # If we override has an identifier
    if 'Identifier' in override_content:
        # Set "aacp_override_identifier" to the overrides identifier
        aacp_override_identifier = override_content['Identifier']
    # If we don't have the "Identifier" key
    else:
        # Return None
        return None

    # If we have extracted the aacp_override_identifier
    if aacp_override_identifier:
        print(f"\t{aacp_override_path}, has identifier: {aacp_override_identifier}...")

    # Return
    return aacp_override_identifier


def install_adobe_titles(adobe_installers: dict, arg_parser: argparse.Namespace, recipe_cache_dir,
    user_name: str) -> dict:
    """
    Install the adobe titles locally, to retrieve the value of the keys in "plist_keys" in
    titles Info.plist

    Parameters
    ----------
    adobe_installers: dict
        Dict containing information around on the Adobe titles.
    arg_parser: argparse.Namespace
        The arguments passed to script, to see if we're to get an applications icon and to
        uninstall.
    recipe_cache_dir: str
        Root dir for recipe cache.
    user_name: str
        The logged in users user name.

    Returns
    ------
    adobe_installers: dict
        dict containing the data on the matched Adobe installers and their additional data
        retrieved from having installed them locally.
    """

    # For each adobe installer
    for adobe_installer, installer_data in adobe_installers.items():
        # Progress notification
        print(f"Installing: {installer_data['aacp_package_path']}...")
        # Run subprocess
        run_subprocess(['/usr/bin/sudo', '/usr/sbin/installer', '-pkg',
            installer_data['aacp_package_path'], '-target', '/'])
        # Var declaration
        info_plist_path = os.path.join(installer_data['aacp_application_full_path'],
            'Contents/Info.plist')
        # Read the info.plist
        info_plist_content = read_plist_file(info_plist_path)
        # Progress notification
        print(f"Retrieving keys from: {info_plist_path}...")
        # Get value for "CFBundleIconFile"
        if not info_plist_content['CFBundleIconFile'].endswith('.icns'):
           # Append .icns
            adobe_installers[adobe_installer]['aacp_bundle_icon_file'] = (
                info_plist_content['CFBundleIconFile'] + '.icns')
        # If CFBundleIconFile doesn't need '.icns' added
        else:
            # Don't append .icns
            adobe_installers[adobe_installer]['aacp_bundle_icon_file'] = (
                info_plist_content['CFBundleIconFile'])
        # Progress notification
        print(f"\tRetrieved aacp_bundle_icon_file: "
            f"{adobe_installers[adobe_installer]['aacp_bundle_icon_file']}")
        # Get value for "CFBundleIdentifier"
        adobe_installers[adobe_installer]['aacp_bundle_identifier'] = (
            info_plist_content['CFBundleIdentifier'])
        # Progress notification
        print(f"\tRetrieved aacp_bundle_identifier: "
            f"{adobe_installers[adobe_installer]['aacp_bundle_identifier']}")
        # Get value for "CFBundleShortVersionString"
        adobe_installers[adobe_installer]['aacp_bundle_short_version_string'] = (
            info_plist_content['CFBundleShortVersionString'])
        # Progress notification
        print(f"\tRetrieved aacp_bundle_short_version_string: "
            f"{adobe_installers[adobe_installer]['aacp_bundle_short_version_string']}")
        # Get value for "CFBundleVersion"
        adobe_installers[adobe_installer]['aacp_bundle_version'] = (
            info_plist_content['CFBundleVersion'])
        # Progress notification
        print(f"\tRetrieved aacp_bundle_version: "
            f"{adobe_installers[adobe_installer]['aacp_bundle_version']}")
        # If "aacp_version_comparison_key" is "CFBundleVersion"
        if adobe_installers[adobe_installer]['aacp_version_comparison_key'] == 'CFBundleVersion':
           # Set "aacp_application_version" to the value of "aacp_bundle_version"
            adobe_installers[adobe_installer]['aacp_application_version'] = (
            adobe_installers[adobe_installer]['aacp_bundle_version'])
        # If short version
        else:
            # Set "aacp_application_version" to the value of "aacp_bundle_short_version_string"
            adobe_installers[adobe_installer]['aacp_application_version'] = (
            adobe_installers[adobe_installer]['aacp_bundle_short_version_string'])
        # If we've not already retrieved the titles minimum os
        if not 'aacp_minimum_os' in adobe_installers[adobe_installer]:
            # Get the key from the plist
            plist_key_value = info_plist_content['LSMinimumSystemVersion']
            # Retrieve the value from the info.plist, and update the "adobe_installers" dict
            adobe_installers[adobe_installer]['aacp_minimum_os'] = plist_key_value
            # Progress notification
            print(f"\tRetrieved aacp_minimum_os: {plist_key_value}")
        # If we're to get the applications icon
        if arg_parser.extract_icons:
            # Path to the title icon
            icon_path = os.path.join(installer_data['aacp_application_full_path'],
                'Contents/Resources', adobe_installers[adobe_installer]['aacp_bundle_icon_file'])
            # Path to the recipes cache directory
            recipe_cache_path = os.path.join(recipe_cache_dir,
                installer_data['aacp_override_identifier'])
            # Name of the icon file when moved
            icon_name = adobe_installer + '.icns'
            # Add name to dict
            adobe_installers[adobe_installer]['aacp_icon_name'] = icon_name
            # Full path to the icons destination
            destination_path = os.path.join(recipe_cache_path, icon_name)
            # Get the application icons
            copy_icons_to_cache_dirs(icon_path, destination_path, recipe_cache_path,  user_name)
        # If we're to get uninstall the applications
        if arg_parser.uninstall:
            # Uninstall the Adobe titles
            uninstall_adobe_titles(installer_data)

    # Returns
    return adobe_installers


def match_overrides(adobe_installers: dict, override_dirs: list, recipe_type: str):
    """
    Matches the found overrides to their installer.

    Parameters
    ----------
    adobe_installers: dict
        Dict containing information around on the Adobe installers.
    override_dirs: list
        List containing directories to search for overrides.
    recipe_type: str
        The type of recipe to look for.

    Returns
    ------
    adobe_installers: dict
        dict containing the data on the matched Adobe installers additional data and matched
        override paths.
    """

    # Var declaration
    recipe_files = []

    # For each override_dir
    for override_dir in override_dirs:
        # Progress notification
        print(f"Looking for overrides, in: {override_dir}")
        # Generate a list containing all recipe files
        recipe_files += glob.glob(os.path.join(override_dir, '*'))

    # For each recipe file
    for recipe_file in recipe_files:
        # For each adobe_installer
        for adobe_installer in adobe_installers:
            # Var declaration
            override_details = {}
            # If "aacp_package_path" ends with _MACARM.pkg
            if adobe_installers[adobe_installer]['aacp_package_path'].endswith('_MACARM.pkg'):
                # If the override starts with adobe_installer and the type matches
                if (os.path.basename(recipe_file).startswith(adobe_installer) and recipe_type
                    in recipe_file and 'arm64' in recipe_file):
                    # Path to the override
                    override_details['path'] = recipe_file
            # If "aacp_package_path" does not end with _MACARM.pkg
            else:
                # If the override starts with adobe_installer and the type matches
                if (os.path.basename(recipe_file).startswith(adobe_installer) and recipe_type
                    in recipe_file and not 'arm64' in recipe_file):
                    # Path to the override
                    override_details['path'] = recipe_file
            # Try to
            try:
                # Get the overrides identifier
                override_details['identifier'] = (
                        get_override_identifier(override_details['path']))
                # If we have a path and identifier
                if override_details['identifier'] and override_details['path']:
                    # Add overrides identifier to adobe_installers dict
                    adobe_installers[adobe_installer]['aacp_override_identifier'] = (
                        override_details['identifier'])
                    # Add overrides path to adobe_installers dict
                    adobe_installers[adobe_installer]['aacp_override_path'] = (
                       override_details['path'])
            # If we don't have one of the above defined
            except KeyError:
                pass

    # For each adobe_installer
    for adobe_installer, installer_data in list(adobe_installers.items()):
        # If we don't have "aacp_override_identifier" for the adobe_installer
        if 'aacp_override_identifier' not in adobe_installers[adobe_installer]:
            # Remove adobe_installer from the dict
            adobe_installers.pop(adobe_installer, None)
            # Progress notification
            print(f"\tWARNING: Removed {adobe_installer}, as could not find a matching override.")
        # If the installer has a matched override
        else:
            # Add the titles name
            installer_data['aacp_name'] = adobe_installer
            # Progress notification
            print(f"\tMatched aacp_name: {installer_data['aacp_name']}

    # If we have no matched overrides, exit
    if not adobe_installers:
        # Error notification
        print("ERROR: 0 overrides matched, exiting...")
        # Exit
        sys.exit(1)

    # Return adobe_installers
    return adobe_installers


def parse_application_json(application_json_path: str, installer_data: dict):
    """
    Parses the installers Application.json file

    Parameters
    ----------
    application_json_path: str
        Path to the application_json_path file.
    installer_data: dict
        Dict containing information around on the Adobe installers.

    Returns
    ------
    aacp_application_description: str
        The applications short description.
    aacp_blocking_applications: list
        List of applications that need to be quit, before installation can proceed.
    aacp_minimum_os: str
        The installers minimum OS.
    """

    # Read in the "application_json_path" to a variable
    application_json = read_json_file(application_json_path)

    # Var declaration
    aacp_application_description = None
    aacp_blocking_applications = []
    aacp_minimum_os = None

    # For each Tagline from within "application_json"
    for tag_line in application_json["ProductDescription"]["Tagline"]["Language"]:
        # Get the Tagline that matches the aacp_application_aacp_application_install_lang locale
        if tag_line['locale'] == installer_data['aacp_application_install_lang']:
            # Set "aacp_application_description" to the matched Tagline
            aacp_application_description = tag_line['value']
            # If "aacp_application_description" doesn't end with a: .
            if not aacp_application_description.endswith('.'):
                # Add . to the end
                aacp_application_description += '.'

    # For each conflicting_process crom within "application_json"
    for conflicting_process in application_json['ConflictingProcesses']['ConflictingProcess']:
        # If forceKillAllowed is not set to False
        if not conflicting_process['forceKillAllowed']:
            # Add to "aacp_blocking_applications"
            aacp_blocking_applications.append(conflicting_process['ProcessDisplayName'])

    # Remove duplicates and sort "aacp_blocking_applications"
    aacp_blocking_applications = sorted(set(aacp_blocking_applications))

    # Get aacp_minimum_os from within "application_json"
    aacp_minimum_os = (re.search('macChecks={minOSVersion:\\\"(.*?)\\\"',
        application_json['SystemRequirement']['CheckCompatibility']['Content'])[1])

    # Progress notification
    print(f"\tRetrieved aacp_application_description: {aacp_application_description}")

    # Progress notification
    print(f"\tRetrieved aacp_blocking_applications: {aacp_blocking_applications}")

    # Progress notification
    print(f"\tRetrieved aacp_minimum_os: {aacp_minimum_os}")

    # Return
    return (aacp_application_description, aacp_blocking_applications, aacp_minimum_os)


def parse_optionxml_xml(optionxml_path: str) -> (str, str, str, str):
    """
    Parses the installers optionXML.xml.

    Parameters
    ----------
    optionxml_path: str
        Path to the optionXML.xml file.

    Returns
    ------
    aacp_application_base_version: str
        The titles base version, required for uninstalls.
    aacp_application_install_lang: str
        The installers language.
    aacp_application_architecture_type: list
        The installers support architecture, either: arm64, macuniversal or x86_64
    aacp_target_folder: str
        The installer titles main application folder.
    """

    # Var declaration
    aacp_application_base_version = None
    aacp_application_install_lang = None
    aacp_target_folder = None

    # Read in the optionXML.xml to a variable
    option_xml = read_xml_file(optionxml_path)

    # Progress notification
    print(f"Parsing: {optionxml_path}...")

    # Check to see if HDMedia keys set
    for hd_media in option_xml.findall('.//HDMedias/HDMedia'):
        # If we have HDMedia, set vars
        if hd_media.findtext('MediaType') == 'Product':
            # Get the aacp_application_base_version
            aacp_application_base_version = hd_media.findtext('baseVersion')
            # Get the value for aacp_application_install_lang
            aacp_application_install_lang = hd_media.findtext('installLang')
            # Get the value for TargetFolderName
            aacp_target_folder = hd_media.findtext('TargetFolderName')

    # If no HDMedia is found, aacp_application_install_lang will not exist
    if not aacp_application_install_lang:
        # Get vars for RIBS media
        for ribs_media in option_xml.findall('.//Medias/Media'):
            # Get the prodVersion, setting as aacp_application_base_version
            aacp_application_base_version = ribs_media.findtext('prodVersion')
            # Get the value for aacp_application_install_lang
            aacp_application_install_lang = ribs_media.findtext('installLang')
            # Get the value for TargetFolderName
            aacp_target_folder = ribs_media.findtext('TargetFolderName')

    # Get the installers supported architecture
    aacp_application_architecture_type = (option_xml.findtext('ProcessorArchitecture').lower())

    # If "adobe_installer['aacp_application_architecture_type']" is not arm64, macuniversal or x64
    if not aacp_application_architecture_type in ['arm64', 'macuniversal', 'x64']:
        # Error notification
        print(f"ERROR: ProcessorArchitecture in {optionxml_path}, is neither arm64, macuniversal "
            f"nor x64. Instead: {aacp_application_architecture_type}, was returned.")
        # Exit
        sys.exit(1)

    # If "aacp_application_architecture_type" is "x64"
    if aacp_application_architecture_type == 'x64':
        # Replace
        aacp_application_architecture_type = 'x86_64'

    # Progress notification
    print(f"\tRetrieved aacp_application_install_lang: {aacp_application_install_lang}")

    # Progress notification
    print(f"\tRetrieved aacp_application_architecture_type: {aacp_application_architecture_type}")

    # Progress notification
    print(f"\tRetrieved aacp_target_folder: {aacp_target_folder}")

    # Return
    return (aacp_application_base_version, aacp_application_install_lang,
        aacp_application_architecture_type, aacp_target_folder)


def read_file(file_path: str) -> str:
    """
    Read in the file at "file_path".

    Parameters
    ----------
    file_path: str
        Path to file to read in.

    Returns
    ------
    file_content: str
        The content of "file_path"
    """

    # Var declaration
    file_content = {}

    # Progress notification
    print(f"Attempting to read in: {file_path}...")

    # If "file_path" doesn't exist or cannot be read
    if not os.path.isfile(file_path):
        # Print error
        print(f"ERROR: \"{file_path}\" cannot be found or read, exiting...")
        # Exit
        sys.exit(0)

    # Try to:
    try:
        # Read in the file at "file_path"
        with open(file_path, 'rb') as some_file:
            # Set "file_content" to the files content
            file_content = some_file.read()
    # If we cannot read the file
    except IOError as err_msg:
        # Print error
        print(f"ERROR: Attempting to read: {file_path}, failed with: {err_msg}")
        # Exit
        sys.exit(0)

    # Return
    return file_content


def read_json_file(json_path: str) -> dict:
    """
    Reads the file at "json_path", returning a dict of the files content.

    Parameters
    ----------
    json_path: str
        Path to json file to parse.

    Returns
    ------
    json_content: dict
        dict containing the contents of "json_path".
    """

    # Var declaration
    file_content = read_file(json_path)
    json_content = {}

    # Try to:
    try:
        # Convert to dict
        json_content = json.loads(file_content)
    # If an exception is raised
    except ValueError as err_msg:
        # Print error
        print(f"ERROR: Attempting to convert the content of {json_path} to dict, "
              f"failed with error error: {err_msg}")
        # Exit
        sys.exit(0)

    # If we have no content
    if not json_content:
        # Print error
        print(f"ERROR: No data retrieved when parsing: {json_path}, exiting...")
        # Exit
        sys.exit(0)

    # Return
    return json_content


def read_plist_file(plist_path: str) -> dict:
    """
    Reads the file at "plist_path", returning a dict of the files content.

    Parameters
    ----------
    plist_path: str
        Path to plist file to parse.

    Returns
    ------
    plist_content: dict
        dict containing the contents of "plist_path".
    """

    # Var declaration
    file_content = read_file(plist_path)
    plist_content = {}

    # Try to:
    try:
        # Convert to dict
        plist_content = plistlib.loads(file_content)
    # If an exception is raised
    except ValueError as err_msg:
        # Print error
        print(f"ERROR: Attempting to convert the content of {plist_path} to dict, "
              f"failed with error error: {err_msg}")
        # Exit
        sys.exit(0)

    # If we have no content
    if not plist_content:
        # Print error
        print(f"ERROR: No data retrieved when parsing: {plist_path}, exiting...")
        # Exit
        sys.exit(0)

    # Return
    return plist_content


def read_xml_file(xml_path: str) -> xml.etree.ElementTree.Element:
    """
    Reads the file at "xml_path", returning a dict of the files content.

    Parameters
    ----------
    xml_path: str
        Path to xml file to parse.

    Returns
    ------
    xml_content: xml.etree.ElementTree.Element
        Object containing the contents of "xml_path"
    """

    # Var declaration
    file_content = read_file(xml_path)
    xml_content = {}

    # Try to:
    try:
        # Parse XML
        xml_content = ElementTree.fromstring(file_content)
    # Raise an exception if the override cannot be parsed
    except xml.etree.ElementTree.ParseError as err_msg:
        # Print error
        print(f"ERROR: Parsing {xml_path}, errored with: {err_msg}")
        # Exit
        sys.exit(0)

    # If we have no content
    if not xml_content:
        # Print error
        print(f"ERROR: No data retrieved when parsing: {xml_path}, exiting...")
        # Exit
        sys.exit(0)

    # Return
    return xml_content


def read_yaml_file(yaml_path: str) -> dict:
    """
    Reads the file at "yaml_path", returning a dict of the files content.

    Parameters
    ----------
    yaml_path: str
        Path to yaml file to parse.

    Returns
    ------
    yaml_content: dict
        dict containing the contents of "yaml_path".
    """

    # Var declaration
    file_content = read_file(yaml_path)
    yaml_content = {}

    # Try to:
    try:
        # Convert to dict
        yaml_content = yaml.safe_load(file_content)
    # If empty, TypeError is raised
    except TypeError as err_msg:
        # Print error
        print(f"ERROR: Reading {yaml_path}, failed with: {err_msg}")
        # Exit
        sys.exit(0)
    # Raise an exception if the override cannot be parsed
    except yaml.scanner.ScannerError as err_msg:
        # Print error
        print(f"ERROR: Parsing {yaml_path}, errored with: {err_msg}")
        # Exit
        sys.exit(0)

    # If we have no content
    if not yaml_content:
        # Print error
        print(f"ERROR: No data retrieved when parsing: {yaml_path}, exiting...")
        # Exit
        sys.exit(0)

    # Return
    return yaml_content


def run_recipe_list(recipe_list_path: str, report_path: str, user_name: str):
    """
    Runs the AutoPkg, via "recipe_list_path", as the logged in user. Writing the report to:
    "report_path".

    Parameters
    ----------
    recipe_list_path: list
        Path to the recipe list.
    report_path: str
    	Path for AutoPkg to write it's report to.
    user_name: str
        The logged in users user name.
    """

    # If report_path exists
    if os.path.isfile(recipe_list_path):
        # Set owner to the logged in user
        shutil.chown(recipe_list_path, user_name)

    # If report_path exists
    if os.path.isfile(report_path):
        # Set owner to the logged in user
        shutil.chown(report_path, user_name)

    # Check that the recipe_list file has content before proceeding
    with open (recipe_list_path, encoding='utf-8') as recipe_list_file:
        # Read in content
        if not recipe_list_file.readlines():
            # Progress notification
            print(f"ERROR: {recipe_list_path} is empty, no overrides found... exiting ...")
            # Exit
            sys.exit(1)

    # Run subprocess
    run_subprocess(['/usr/bin/su', '-l', user_name, '-c', f"/usr/local/bin/autopkg run -vvvv "
                    f"--recipe-list {recipe_list_path} --report-plist {report_path}"])


def run_subprocess(subprocess_args: list):
    """
    Run "subprocess_args", in subprocess.

    Parameters
    ----------
    subprocess_args: list
        Commands to run in subprocess.
    """

    # Progress notification
    print(f"Running: {subprocess_args}")

    # Try to:
    try:
        # Run the command and error if a non-zero exit code returned
        subprocess.run(subprocess_args, check = True)
    # If the command exits with anything but 0
    except subprocess.SubprocessError as err_msg:
        # Error notification
        print(f"ERROR: Command {subprocess_args}, failed with: {err_msg}")
        # Exit
        sys.exit(1)


def setup_argparse() -> argparse.Namespace:
    """
    Creates an argparse object, with the wanted arguments.

    Returns
    --------
    arg_parser.parse_args(): argparse.Namespace
        The argparse object.
    """

    # Add the description
    arg_parser = argparse.ArgumentParser(description = f"AdobeAdminConsolePackagesImporter - "
        f"{__version__}", usage = f"{os.path.realpath(__file__)} type [dir] [--extract-icons] "
        f"[--uninstall]")

    # Add "type" argument
    arg_parser.add_argument('type', help = "Recipe type, for example: munki or jamf",
        type = str)

    # Add "dir" argument
    arg_parser.add_argument('dir', nargs = "?", default = "~/Downloads", help = "Path to dir "
        "containing Adobe installers", type = str)

    # Add the "get-icon" flag
    arg_parser.add_argument('--extract-icons', action = 'store_true', help = "If passed, retrieves "
        "the titles icon.")

    # Add the "uninstall" flag
    arg_parser.add_argument('--uninstall', action = 'store_true', help = "If passed, uninstalls "
        "the Adobe title(s) after installation on this Mac to get the titles metadata.")

    # Return the arg_parser object
    return arg_parser.parse_args()


def uninstall_adobe_titles(installer_data: dict):
    """
    Uninstalls the Adobe title from this Mac.

    Parameters
    ----------
    installer_data: dict
        Dict containing information around on an Adobe title.
    """

    # Var declarations
    acrobat_uninstaller = ('/Applications/Adobe Acrobat DC/Adobe Acrobat.app/Contents/Helpers/'
        'Acrobat Uninstaller.app/Contents/Library/LaunchServices/com.adobe.Acrobat.RemoverTool')
    adobe_uninstaller = '/Library/Application Support/Adobe/Adobe Desktop Common/HDBox/Setup'

    # If "aacp_name" is not AdobeAcrobatDC
    if not installer_data['aacp_name'] == 'AdobeAcrobatDC':
        # Progress notification
        print(f"Uninstalling: {installer_data['aacp_name']}, with: {adobe_uninstaller}...")
        # Run subprocess
        run_subprocess([adobe_uninstaller,
            f"--baseVersion={installer_data['aacp_application_base_version']}",
                '--deleteUserPreferences=false', '--platform=macOS',
                    f"--sapCode={installer_data['aacp_application_sap_code']}", '--uninstall=1'])
    # If "adobe_installer" is AdobeAcrobatDC
    else:
        # Progress notification
        print(f"Uninstalling: {installer_data['aacp_name']}, with: {acrobat_uninstaller}...")
        # Run subprocess
        run_subprocess([acrobat_uninstaller])
        # To tidy output when uninstalling Acrobat
        print()


def update_override_content(installer_data: dict, override_content: dict) -> dict:
    """
    Updates the passed overrides content, adding to the "Input" dict, removing any no longer
    needed "aacp_*" keys and and the "aacp_vars" dict removed (if existed prior).

    Parameters
    ----------
    installer_data: dict
        Dict containing information around on an Adobe title.
    override_content: dict
        Dict containing the overrides content.
    
    Returns
    -------
    override_content: dict
        Dict containing the overrides content.
    """

    # If we have a "aacp_vars" dict
    if 'aacp_vars' in override_content:
        # Delete, as was needed for v2 only.
        del override_content['aacp_vars']

    # For each key in the "Input" dict
    for input_key in list(override_content['Input'].keys()):
        # If the key starts with "aacp_*"
        if input_key.startswith('aacp_'):
            # Delete the key
            del override_content['Input'][input_key]

    # For each key value pair in installer_data
    for installer_data_key, installer_data_value in installer_data.items():
        # Add "installer_data_key" with the value of "installer_data_value" to the "Input" dict
        override_content['Input'][installer_data_key] = installer_data_value

    # If we have a "pkginfo" dict in "Input" dict
    if 'pkginfo' in list(override_content['Input'].keys()):
        # If we have "aacp_blocking_applications" in "installer_data"
        if 'aacp_blocking_applications' in installer_data:
            # Add to the "Input" dict
            override_content['Input']['pkginfo']['blocking_applications'] = (
                installer_data['aacp_blocking_applications'])
        # If we don't have "aacp_blocking_applications" in "installer_data"
        else:
            # If we have "blocking_applications" in the Input dict
            if 'blocking_applications' in override_content['Input']['pkginfo']:
                # Delete
                del override_content['Input']['pkginfo']['blocking_applications']
        if ('aacp_application_architecture_type' in installer_data and
            not installer_data['aacp_application_architecture_type'] == 'macuniversal'):
            # Add to the "Input" dict
            override_content['Input']['pkginfo']['supported_architectures'] = ([
                installer_data['aacp_application_architecture_type']])
        # If we don't have "aacp_application_architecture_type" in "installer_data"
        else:
            # If we have "blocking_applications" in the Input dict
            if 'supported_architectures' in override_content['Input']['pkginfo']:
                # Delete
                del override_content['Input']['pkginfo']['supported_architectures']

    # Return
    return override_content


def update_overrides(adobe_installers: dict):
    """
    Write to the matched overrides, adding all variables a dict called "aacp_vars", and
    replacing occurrences of %aacp_<var name>% with their value.

    Parameters
    ----------
    adobe_installers: dict
        Dict containing information around on the Adobe installers.
    """

    # Progress notification
    print("Updating overrides...")

    # For each adobe installer
    for _, installer_data in list(adobe_installers.items()):
        print(installer_data)
        # Progress notification
        print(f"\tUpdating: {installer_data['aacp_override_path']}...")
        # If a yaml file
        if (installer_data['aacp_override_path'].endswith('.yml') or
                installer_data['aacp_override_path'].endswith('.yaml')):
            # Read in the override as a plist
            override_content = read_plist_file(installer_data['aacp_override_path'])
            # Update the content with data in "installer_data"
            override_content = update_override_content(installer_data, override_content)
            # Try to read it as yaml
            try:
                # Open yaml file, to write
                with (open(installer_data['aacp_override_path'], 'w+', encoding = 'utf-8') as
                  write_file):
                    # Write the updated content to the override
                    yaml.dump(override_content, write_file, default_flow_style=False)
            # If we fail to write to the file
            except OSError as err_msg:
                # Progress notification
                print(f"ERROR: Writing, {installer_data['aacp_override_path']} errored with: "
                      f"{err_msg}")
                # Return None
                sys.exit(1)
        # If not a .yaml override
        else:
            # Read in the override as a plist
            override_content = read_plist_file(installer_data['aacp_override_path'])
            # Update the content with data in "installer_data"
            override_content = update_override_content(installer_data, override_content)
            # Try to read in the file as a plist
            try:
                # Open the override for writing
                with open(installer_data['aacp_override_path'], 'wb') as write_file:
                    # Write the updated content to the override
                    plistlib.dump(override_content, write_file)
            # If we fail to write to the file
            except OSError as err_msg:
                # Progress notification
                print(f"ERROR: Writing, {installer_data['aacp_override_path']} errored with: "
                      f"{err_msg}")
                # Return None
                sys.exit(1)


if __name__ == '__main__':
    main()

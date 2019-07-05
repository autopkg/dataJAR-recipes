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


# Version
__version__ = '1.0'


# Standard Imports
import glob
import os
import subprocess
import sys

# pylint: disable=wrong-import-position
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) \
                                                                     + '/' + 'scripts'))


# Script
def main():
    '''Gimme some main'''

    adobe_folders = []

    download_path = os.path.expanduser('~/Downloads')

    for some_item in os.listdir(download_path):
        some_path = os.path.join(download_path, some_item)
        if os.path.isdir(some_path):
            if some_item.startswith('Adobe') and some_item.endswith('CC2019'):
                adobe_folders.append(some_item)

    if not len(adobe_folders):
        print 'No Adobe*CC2019 folders found in %s, exiting...' % download_path
        sys.exit(1)

    notify_team(len(adobe_folders))
    recipe_list = os.path.expanduser('~/Library/Application Support/AutoPkgr/recipe_list.txt')
    recipe_dir = os.path.join(os.path.dirname(recipe_list) + '/')
    _ = open(os.path.join(recipe_dir + 'adobe_list.txt'), 'w')
    pkg_checker(download_path, adobe_folders)


def file_len(run_day, recipe_dir):
    ''' For each weekdays recipe list, return a count '''
    line_count = len(open(os.path.join(recipe_dir + run_day + '_list.txt')).readlines())
    return line_count


def notify_team(recipe_count):
    ''' Send Notifications as appropirate '''

    os.system('clear')
    msg_text = '%s Adobe CC 2019 recipes found, creating recipe list...' % recipe_count
    print msg_text


def pkg_checker(download_path, adobe_folders):
    ''' Check that we have the Install_pkg's & proceed if we do'''

    for adobe_folder in sorted(adobe_folders):
        try:
            install_pkg = glob.glob(os.path.join(download_path, adobe_folder, \
                                               'Build', '*_Install.pkg'))[0]
            if os.path.exists(install_pkg):
                create_list(adobe_folder)
            else:
                print 'Cannot find pkg ({0}), for {1}... Skipping...'.format\
                                               (install_pkg, adobe_folder)
        except IndexError as err_msg:
            print 'Skipping {0}, as cannot find Install.pkg: {1}...'.format(adobe_folder, err_msg)

    run_list()


def create_list(adobe_folder):
    ''' Create recipe list '''

    library_dir = os.path.expanduser('~/Library/')
    override_path = os.path.join(library_dir, 'AutoPkg', 'RecipeOverrides', \
                             adobe_folder + '-dataJAR-manual.munki.recipe')
    override_name = 'local.munki.' + adobe_folder + '-dataJAR-manual'

    if not os.path.isfile(override_path):
        print 'Skipping {0}, as cannot find override...'.format(override_path)

    recipe_list = os.path.expanduser('~/Library/Application Support/AutoPkgr/recipe_list.txt')
    recipe_dir = os.path.join(os.path.dirname(recipe_list) + '/')
    list_file = open(os.path.join(recipe_dir + 'adobe_list.txt'), 'a+')
    list_file.write(override_name + '\n')
    list_file.close()


def run_list():
    '''Run recipe list'''

    recipe_list = os.path.expanduser('~/Library/Application Support/AutoPkgr/recipe_list.txt')
    recipe_dir = os.path.join(os.path.dirname(recipe_list) + '/')
    adobe_list = os.path.join(recipe_dir + 'adobecc2019_list.txt')
    report_path = os.path.join(recipe_dir + 'adobecc2019_report.plist')

    os.system('clear')
    if os.path.exists(adobe_list):
        msg_text = 'Running recipe_list: `{0}`'.format(adobe_list)
        print msg_text
        print
        cmd_args = ['/usr/local/bin/autopkg', 'run', '-v', '--recipe-list', adobe_list, \
                                                         '--report-plist', report_path]
        msg_text = 'Running `{0}`...'.format(cmd_args)
        subprocess.call(cmd_args)
    else:
        msg_text = 'Cannot find recipe_list: `{0}`'.format(adobe_list)
        print msg_text


if __name__ == '__main__':

    main()

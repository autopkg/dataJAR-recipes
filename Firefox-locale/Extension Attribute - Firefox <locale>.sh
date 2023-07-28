#!/bin/bash

####################################################################################################
#
# In accessing and using this Product, you confirm that you accept the terms of our Product Licence
# in full and agree to comply with the terms of such Licence.
#
# https://datajar.co.uk/product-licence/
#
####################################################################################################
#
# DESCRIPTION
# Returns version of Firefox.app installed, if locale matches the expected locale.
#
####################################################################################################
#
# CHANGE LOG
# 1.0 - Created
#
####################################################################################################

appLocale="en-GB"
infoPlistPath="/Applications/Firefox.app/Contents/Info.plist"
localeIniPath="/Applications/Firefox.app/Contents/Resources/locale.ini"
versionKey="CFBundleShortVersionString"

if [ -f "${localeIniPath}" ]
then
    installedLocale=$(/usr/bin/awk -F"=" '/locale=/{ print $2 }' < "${localeIniPath}")
else
    installedLocale="en-US"
fi

if [ "${appLocale}" != "${installedLocale}" ]
then
    /bin/echo "<result></result>"
else
    if [ -f "${infoPlistPath}" ]
    then
        appVersion=$(/usr/bin/defaults read "${infoPlistPath}" "${versionKey}")
        /bin/echo "<result>${appVersion}</result>"
    else
        /bin/echo "<result></result>"
    fi
fi
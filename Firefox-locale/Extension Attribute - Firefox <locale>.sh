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
# Uses omni.ja file to determine locale for all Firefox versions.
#
####################################################################################################
#
# CHANGE LOG
# 1.0 - Created
# 2.0 - Updated to use omni.ja for locale detection
#
####################################################################################################

# Variables
appLocale="en-GB"
firefoxPath="/Applications/Firefox.app"
infoPlistPath="${firefoxPath}/Contents/Info.plist"
omniPath="${firefoxPath}/Contents/Resources/omni.ja"
versionKey="CFBundleShortVersionString"

# Function to get Firefox locale from omni.ja
get_firefox_locale() {
    if [ -f "${omniPath}" ]; then
        installedLocale=$(/usr/bin/unzip -p "${omniPath}" default.locale 2>/dev/null | /usr/bin/tr -d '\n\r')
        echo "${installedLocale}"
    else
        echo ""
    fi
}

# Check if Firefox is installed
if [ ! -d "${firefoxPath}" ]; then
    /bin/echo "<result></result>"
    exit 0
fi

# Get installed locale
installedLocale=$(get_firefox_locale)

# Check if we got a valid locale
if [ -z "${installedLocale}" ]; then
    /bin/echo "<result></result>"
    exit 0
fi

# Compare locales
if [ "${appLocale}" != "${installedLocale}" ]; then
    /bin/echo "<result></result>"
else
    # Get version if locales match
    if [ -f "${infoPlistPath}" ]; then
        appVersion=$(/usr/bin/defaults read "${infoPlistPath}" "${versionKey}")
        /bin/echo "<result>${appVersion}</result>"
    else
        /bin/echo "<result></result>"
    fi
fi

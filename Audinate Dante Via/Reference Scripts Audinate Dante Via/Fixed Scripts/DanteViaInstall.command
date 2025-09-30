#!/bin/bash

# Must be root to work
if [ "$(id -u)" != "0" ]
then
	echo "This script must be run as root" 1>&2
	echo "running sudo $0"
	sudo "$0"
	exit
fi

syslog -s -l error "Dante Via: executing ${0##*/} ($0)"

# Load common constants
SCRIPT_DIR="${0%/*}"
source "$SCRIPT_DIR"/DanteViaCommon.sh
source "$SCRIPT_DIR"/DanteViaConstants

echo "Creating log dir…"
mkdir -p "$DANTE_VIA_LOG_DIR"

# Log System Integrity Protection status
echo -e "*** System Integrity Protection ***" > $DANTE_VIA_INSTALL_LOGFILE
csrutil status >> $DANTE_VIA_INSTALL_LOGFILE 2>&1

# Log the contents of /Library/Audio/Plug-Ins/HAL/
echo -e "\n*** Contents of $OSX_DRIVER_DIR ***" >> $DANTE_VIA_INSTALL_LOGFILE
ls -al $OSX_DRIVER_DIR >> $DANTE_VIA_INSTALL_LOGFILE 2>&1

if [ ! -d "$DANTE_VIA_DRIVER" ] ||
	[ ! -d "$DANTE_VIA_DIR" ] ||
	[ ! -d "$DANTE_VIA_APP" ]; then

	echo -e "\n*** Failed to install the Via audio driver or the GUI application ***" >> $DANTE_VIA_INSTALL_LOGFILE
	echo -e "\n*** Contents of $DANTE_VIA_DRIVER ***" >> $DANTE_VIA_INSTALL_LOGFILE
	ls -al "$DANTE_VIA_DRIVER"/* >> $DANTE_VIA_INSTALL_LOGFILE 2>&1
	ls -al "$DANTE_VIA_DRIVER"/*/* >> $DANTE_VIA_INSTALL_LOGFILE 2>&1
	echo -e "\n*** Contents of $DANTE_VIA_DIR ***" >> $DANTE_VIA_INSTALL_LOGFILE
	ls -al "$DANTE_VIA_DIR"/* >> $DANTE_VIA_INSTALL_LOGFILE 2>&1
	echo -e "\n*** Contents of $DANTE_VIA_APP ***" >> $DANTE_VIA_INSTALL_LOGFILE
	ls -al "$DANTE_VIA_APP"/* >> $DANTE_VIA_INSTALL_LOGFILE 2>&1

	# Comment out warning dialog - replaced with echo for logging
	# display_alert "'messageText' 'Dante Via installation failed' 'informativeText' 'Failed to install the Dante Via application or audio driver.\nPlease uninstall Dante Via first and then try installing it again.' 'alertStyle' 2 'icon' '$DANTE_VIA_ICON'"
	echo "ERROR: Dante Via installation failed - Failed to install the Dante Via application or audio driver. Please uninstall Dante Via first and then try installing it again."

	delete_silent_install_file
	exit 1
fi

echo "Registering Dante Via…"
# Restart coreaudio - registers new plugin
killall "$OSX_COREAUDIO_DAEMON_NAME"

# Deregister from ConMon (in case the user upgrades from an older Dante Via that was registered with ConMon)
if [ -x "$CONMON_DAEMON_BUNDLE_USE_SCRIPT" ]; then
   "$CONMON_DAEMON_BUNDLE_USE_SCRIPT" -r "$DANTE_VIA_BASE_BUNDLE_ID"
fi

# Clear any leftover Activation app files to avoid stale data being used by the Activation app
rm -rf "$DANTE_VIA_ACTIVATION_APP_USER_DATA_DIR"
rm -rf "$DANTE_VIA_ACTIVATION_APP_CACHE_DIR"

# Make sure the Via Audio Plug-In Driver is running
count=0
while :
do
	sleep 1
	VIA_AUDIO_PLUGIN_PID=$(pgrep ".*DanteViaAudioPlugIn.*")
	if [ "$VIA_AUDIO_PLUGIN_PID" != "" ]; then
		echo -e "\n*** Dante Via Audio Plug-In driver is running with PID: $VIA_AUDIO_PLUGIN_PID ***" >> $DANTE_VIA_INSTALL_LOGFILE
		break
	fi
	count=$((count+1))
	if [[ $count -ge 10 ]]; then
		echo -e "\n*** Dante Via Audio Plug-In Driver is not running ***" >> $DANTE_VIA_INSTALL_LOGFILE
		echo -e "\n*** Contents of $DANTE_VIA_DRIVER ***" >> $DANTE_VIA_INSTALL_LOGFILE
		ls -al "$DANTE_VIA_DRIVER"/* >> $DANTE_VIA_INSTALL_LOGFILE 2>&1
		ls -al "$DANTE_VIA_DRIVER"/*/* >> $DANTE_VIA_INSTALL_LOGFILE 2>&1
		echo -e  "\n*** Disk usage of $VIA_DRIVER_PATH ***" >> $DANTE_VIA_INSTALL_LOGFILE
		du -h "$DANTE_VIA_DRIVER" >> $DANTE_VIA_INSTALL_LOGFILE 2>&1
		break
	fi
done

# start
echo "Starting Dante Via Daemon…"
"$DANTE_VIA_DAEMON_START" > /dev/null 2>&1

# Comment out restart notification dialog - replaced with echo for logging
# display_alert "'messageText' 'Restart your Mac' 'informativeText' 'To complete the Dante Via installation process, please restart your Mac.' 'alertStyle' 1 'firstButtonTitle' 'Continue' 'icon' '$DANTE_VIA_ICON'"
echo "INFO: To complete the Dante Via installation process, please restart your Mac."

delete_silent_install_file

echo "Done"

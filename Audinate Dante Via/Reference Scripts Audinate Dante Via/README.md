# Reference Scripts Audinate Dante Via

This directory contains two versions of the installation scripts:

- **Original Audinate Dante Via Script**: The original scripts from the vendor's package
  - `DanteViaInstall.command` - Installation script from the Payload
  - `preinstall` - Preinstall script from the Scripts archive
- **Fixed Scripts**: The modified scripts that remove user interaction
  - `DanteViaInstall.command` - Modified installation script without dialogs
  - `preinstall` - Modified preinstall script without dialogs

## Changes Made

The fixed scripts remove all dialog calls and replace them with `echo` statements for logging purposes:

### 1. DanteViaInstall.command (in Payload)

Located at: `/Library/Application Support/Audinate/DanteVia/Resources/DanteViaInstall.command`

**Installation failure dialog** - Replaced with:
```bash
echo "ERROR: Dante Via installation failed - Failed to install the Dante Via application or audio driver. Please uninstall Dante Via first and then try installing it again."
```

**Restart notification dialog** - Replaced with:
```bash
echo "INFO: To complete the Dante Via installation process, please restart your Mac."
```

### 2. preinstall (in Scripts archive)

**Core Audio restart confirmation dialog** - Replaced with:
```bash
echo "WARNING: The Core Audio background process (coreaudiod) will be restarted, and audio will be interrupted during installation."
```

This ensures the package can be installed silently without requiring user interaction, while still providing error and informational messages in the logs for troubleshooting.

## Usage

These scripts are used by the pkg recipe to create a silent installer. The pkg recipe will:
1. Extract the original package
2. Replace the `DanteViaInstall.command` script in the Payload with the fixed version
3. Replace the `preinstall` script in the Scripts archive with the fixed version
4. Repackage everything into a new package

You can compare both versions to see the specific modifications made.

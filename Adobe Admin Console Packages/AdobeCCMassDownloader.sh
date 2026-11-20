#!/bin/bash

# Script to mass download Adobe packages
# Requires: Adobe Admin Console Downloader disk images in the downloads folder,
#           Xcode Command Line Tools (swiftc), and Accessibility permission for this terminal.

helperDir=""
trap '[ -n "$helperDir" ] && rm -rf "$helperDir"' EXIT

#Ask for the path of the Download folder
downloadsFolderPath=""
read -r -p "Drag in the default Download folder (the one with all the Admin Console Downloader disk images) and press Return (or just press Return for ~/Downloads): " downloadsFolderPath || exit 1
# Terminal escapes dragged-in paths with backslashes and adds a trailing space
downloadsFolderPath=${downloadsFolderPath//\\/}
downloadsFolderPath=${downloadsFolderPath%"${downloadsFolderPath##*[![:space:]]}"}
downloadsFolderPath=${downloadsFolderPath/#\~/$HOME}
if [ -z "${downloadsFolderPath}" ]
then
    downloadsFolderPath="$HOME/Downloads"
fi
if [ ! -d "$downloadsFolderPath" ]; then
    echo "ERROR: '$downloadsFolderPath' is not a folder."
    exit 1
fi

#Collect the disk images
dmgs=()
for f in "$downloadsFolderPath"/*_Downloader.dmg; do
    [ -f "$f" ] && dmgs+=("$f")
done
if [ ${#dmgs[@]} -eq 0 ]; then
    echo "ERROR: no *_Downloader.dmg files found in '$downloadsFolderPath'."
    exit 1
fi

#Unmount any existing Adobe Package Downloader volumes first
for v in /Volumes/Adobe\ Package\ Downloader*; do
    [ -d "$v" ] && diskutil unmount force "$v" >/dev/null 2>&1
done

#Mount all found disk images
mounted=0
for f in "${dmgs[@]}"; do
    if /usr/bin/hdiutil attach -noverify "$f" >/dev/null 2>&1; then
        mounted=$((mounted + 1))
    else
        echo "WARNING: failed to mount '$f'"
    fi
done

#Wait (up to 20s) for every volume to appear
for _ in $(seq 1 20); do
    count=0
    for v in /Volumes/Adobe\ Package\ Downloader*; do
        [ -d "$v/Adobe Package Downloader.app" ] && count=$((count + 1))
    done
    [ "$count" -ge "$mounted" ] && break
    sleep 1
done
if [ "$count" -ne "${#dmgs[@]}" ]; then
    echo "WARNING: ${#dmgs[@]} disk images found but $count downloader volumes mounted."
    read -r -p "Continue anyway? (y/n): " ans || exit 1
    [[ "$ans" =~ ^[Yy] ]] || exit 1
fi

#Open the downloader app for every volume, remembering exactly which PIDs we started
pids=()
volumes=()
for v in /Volumes/Adobe\ Package\ Downloader*; do
    app="$v/Adobe Package Downloader.app"
    [ -d "$app" ] || continue
    volumes+=("$v")
    # The binary name varies between releases (Install / AdobePackageDownloader)
    exeName=$(/usr/libexec/PlistBuddy -c 'Print :CFBundleExecutable' "$app/Contents/Info.plist" 2>/dev/null)
    exe="$app/Contents/MacOS/$exeName"
    if [ -z "$exeName" ] || [ ! -x "$exe" ]; then
        exe=$(find "$app/Contents/MacOS" -type f -perm -111 | head -1)
    fi
    if [ -z "$exe" ]; then
        echo "WARNING: no executable found in '$app'"
        continue
    fi
    "$exe" >/dev/null 2>&1 &
    pids+=($!)
    disown
done
if [ ${#pids[@]} -eq 0 ]; then
    echo "ERROR: no downloaders were launched."
    exit 1
fi
echo "Launched downloader PIDs: ${pids[*]}"

sleep 3  # Give the UI a moment to appear

# Prompt user to confirm all windows have loaded
while true; do
    read -r -p "Have all Adobe Package Downloader windows loaded? (y/n): " loadedAnswer || exit 1
    case $loadedAnswer in
        [Yy]*) break ;;
        [Nn]*) echo "Waiting for windows to load..."; sleep 2 ;;
        *) echo "Please answer y or n." ;;
    esac
done

# Build a tiny helper that presses "Continue" via the Accessibility API addressed by PID.
# (System Events resolves clicks by process NAME, and all downloaders share one name,
#  so every click landed in the same window.)
helperDir=$(mktemp -d)
cat > "$helperDir/clicker.swift" <<'SWIFT'
import ApplicationServices
import Foundation

func attr(_ e: AXUIElement, _ a: String) -> AnyObject? {
    var v: CFTypeRef?
    guard AXUIElementCopyAttributeValue(e, a as CFString, &v) == .success else { return nil }
    return v
}
func str(_ e: AXUIElement, _ a: String) -> String {
    if let s = attr(e, a) as? String { return s }
    return ""
}
func descendants(_ e: AXUIElement) -> [AXUIElement] {
    var out: [AXUIElement] = []
    for c in (attr(e, "AXChildren") as? [AXUIElement]) ?? [] {
        out.append(c)
        out.append(contentsOf: descendants(c))
    }
    return out
}

// Returns (state, dump). state: clicked | downloading | waiting
func check(_ pid: pid_t) -> (String, String) {
    let app = AXUIElementCreateApplication(pid)
    let windows = (attr(app, "AXWindows") as? [AXUIElement]) ?? []
    if windows.isEmpty { return ("waiting (no window)", "") }
    var dump = ""
    var progress = false
    for w in windows {
        for e in descendants(w) {
            let role = str(e, "AXRole")
            var name = str(e, "AXTitle")
            if name.isEmpty { name = str(e, "AXValue") }
            if name.isEmpty { name = str(e, "AXDescription") }
            dump += "    \(role) | \(name)\n"
            if role == "AXButton" && name == "Continue" {
                if AXUIElementPerformAction(e, kAXPressAction as CFString) == .success {
                    return ("clicked", "")
                }
            }
            if name.contains("remaining") { progress = true }
        }
    }
    if progress { return ("downloading", "") }
    return ("waiting (no Continue yet)", dump)
}

if !AXIsProcessTrusted() {
    print("WARNING: this terminal is not trusted for Accessibility (System Settings > Privacy & Security > Accessibility)")
}
let pids = CommandLine.arguments.dropFirst().compactMap { pid_t($0) }
var handled = Set<pid_t>()
var last: [pid_t: String] = [:]
let end = Date().addingTimeInterval(120)
while Date() < end && handled.count < pids.count {
    for pid in pids where !handled.contains(pid) {
        let (state, dump) = check(pid)
        if last[pid] != state {   // only report when the state itself changes
            print("PID \(pid): \(state)")
            if !dump.isEmpty { print(dump, terminator: "") }
            last[pid] = state
        }
        if state == "clicked" || state == "downloading" { handled.insert(pid) }
    }
    Thread.sleep(forTimeInterval: 1)
}
for pid in pids where !handled.contains(pid) {
    print("NOT HANDLED: PID \(pid)")
}
print("Handled \(handled.count) of \(pids.count) downloaders")
exit(handled.count == pids.count ? 0 : 1)
SWIFT

if ! swiftc -O "$helperDir/clicker.swift" -o "$helperDir/clicker" 2>"$helperDir/swiftc.log"; then
    echo "ERROR: could not build the click helper (are the Xcode Command Line Tools installed?):"
    cat "$helperDir/swiftc.log"
    echo "Click Continue manually in each window."
elif ! "$helperDir/clicker" "${pids[@]}"; then
    echo "WARNING: not every downloader was started automatically (see NOT HANDLED above)."
    echo "Click Continue manually in those windows before continuing."
fi

#Wait for a response that all downloads are done
read -r -p "Press Return when all downloads are complete..." || exit 1

#Kill only the downloader processes this script launched, and wait for them to exit
kill "${pids[@]}" 2>/dev/null
for _ in $(seq 1 10); do
    alive=0
    for p in "${pids[@]}"; do kill -0 "$p" 2>/dev/null && alive=1; done
    [ "$alive" -eq 0 ] && break
    sleep 1
done

#Eject all downloader disk images
ejectFailed=0
for v in "${volumes[@]}"; do
    if ! /usr/bin/hdiutil detach "$v" >/dev/null 2>&1; then
        sleep 2
        if ! /usr/bin/hdiutil detach -force "$v" >/dev/null 2>&1; then
            echo "WARNING: could not eject '$v'"
            ejectFailed=1
        fi
    fi
done

# Ask if user wants to delete the DMGs
if [ "$ejectFailed" -eq 1 ]; then
    echo "Some volumes are still mounted, so the DMGs will not be offered for deletion."
else
    read -r -p "Would you like to delete the DMGs from your download folder? (y/n): " deleteDMGs || exit 1
    if [[ "$deleteDMGs" =~ ^[Yy]$ ]]; then
        rm -v "${dmgs[@]}"
    fi
fi

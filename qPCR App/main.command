#!/bin/bash
cd "$(dirname "$BASH_SOURCE")" || {
    echo "Error getting script directory" >&2
    exit 1
}
osascript -e 'tell application "Terminal" to set visible of front window to false'

python main.py
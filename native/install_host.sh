#!/bin/sh
# Copyright 2013 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

set -e

CHROME_EXE=$(basename $(which chromium chromium-browser chrome))

if [ "$(uname -s)" = "Darwin" ]; then
  if [ "$(whoami)" = "root" ]; then
    TARGET_DIR="/Library/Google/Chrome/NativeMessagingHosts"
  else
    TARGET_DIR="$HOME/Library/Application Support/Google/Chrome/NativeMessagingHosts"
  fi
else
  if [ "$(whoami)" = "root" ]; then
    TARGET_DIR="/etc/opt/chrome/native-messaging-hosts"
  else
    TARGET_DIR="$HOME/.config/${CHROME_EXE}/NativeMessagingHosts"
  fi
fi

HOST_NAME=com.google.chrome.example.echo

# Create directory to store native messaging host.
mkdir -p "$TARGET_DIR"

HOST_NAME="com.erjoalgo.chrome_current_url"
EXE_PATH=$(which chromeurl)
EXTENSION_ID=dnjelpbbbfnipffmhffnlhnlgigokofa
DESCRIPTION="chrome current url native host component"
MANIFEST="$TARGET_DIR/$HOST_NAME.json"

cat <<EOF | sudo tee ${MANIFEST}
{
    "name": "${HOST_NAME}",
    "description": "${DESCRIPTION}",
    "path": "${EXE_PATH}",
    "type": "stdio",
    "allowed_origins": [
        "chrome-extension://${EXTENSION_ID}/"
    ]
}
EOF


# Set permissions for the manifest so that all users can read it.
sudo chmod o+r ${MANIFEST}

echo "Native messaging host $HOST_NAME has been installed at ${MANIFEST}"

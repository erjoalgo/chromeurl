"""install the chrome native host and external extension"""

import os
import json
import logging
import sys


EXE_ABS = sys.argv[0]
HOST_NAME = "com.erjoalgo.chrome_current_url"

logging.basicConfig()
logger = logging.getLogger('chromeurl-installer')
logger.setLevel(logging.DEBUG)

def install_manifest(filename_sans_ext, manifest_dict, directory_candidates,
                     max_installations=float("inf")):
    """install a manifest onto a number of possible directory candidates"""
    installed_manifests = []
    for cand_maybe_tilde in directory_candidates:
        if len(installed_manifests) >= max_installations:
            break
        cand = os.path.expanduser(cand_maybe_tilde)
        parent = os.path.dirname(cand)
        logger.debug("\tconsidering {}".format(cand))
        if not os.path.exists(cand) and os.path.exists(parent):
            # if parent exists, this could be the first native messaging host
            try:
                os.mkdir(cand)
            except Exception as ex:
                logger.debug("unable to mkdir {}: {}".format(cand, ex))

        if os.path.exists(cand):
            manifest_path = os.path.join(cand, "{}.json".format(filename_sans_ext))
            try:
                with open(manifest_path, "w") as fh:
                    json.dump(manifest_dict, fh, indent=4)
                    installed_manifests.append(manifest_path)
                    logger.info("installed manifest at: {}".format(manifest_path))
            except Exception as ex:
                logger.debug("\tfailed to install manifest at {}:\n\t {}"
                             .format(manifest_path, ex))
    return installed_manifests

def install_native_host(extension_id):
    """install chrome native host manifest file"""
    NATIVE_HOST_CANDIDATES = [
        # https://developer.chrome.com/extensions/nativeMessaging

        # OS X (system-wide)
        "/Library/Google/Chrome/NativeMessagingHosts/",
        "/Library/Application Support/Chromium/NativeMessagingHosts/",

        # OS X (user-specific, default path)
        "~/Library/Application Support/Google/Chrome/NativeMessagingHosts/",
        "~/Library/Application Support/Chromium/NativeMessagingHosts/",

        # Linux (system-wide)
        "/etc/opt/chrome/native-messaging-hosts/",
        "/etc/chromium/native-messaging-hosts/",

        # Linux (user-specific, default path)
        "~/.config/google-chrome/NativeMessagingHosts/",
        "~/.config/chromium/NativeMessagingHosts/"
    ]

    manifest = {
        "name": HOST_NAME,
        "description": "chrome current url native host component",
        "path": EXE_ABS,
        "type": "stdio",
        "allowed_origins": [
            "chrome-extension://{}/".format(extension_id)
        ]
    }
    installed_manifests = install_manifest(HOST_NAME, manifest, NATIVE_HOST_CANDIDATES)
    if not installed_manifests:
        logger.error("fatal: could not discover suitable native host installation directory")
        exit(1)

def install_extension(extension_id):
    """install chrome external extension"""
    EXTERNAL_EXTENSION_CANDIDATES = [
        # https://developer.chrome.com/extensions/external_extensions
        "~/Library/Application Support/Google/Chrome/External Extensions/",
        "/Library/Application Support/Google/Chrome/External Extensions/",
        "/opt/google/chrome/extensions/",
        "/usr/share/google-chrome/extensions/",
        "/usr/share/chromium/extensions/"
    ]
    CHROME_WEBSTORE_UPDATE_URL = "https://clients2.google.com/service/update2/crx"
    manifest = {
        "external_update_url": CHROME_WEBSTORE_UPDATE_URL
    }

    installed_manifests = install_manifest(extension_id, manifest, EXTERNAL_EXTENSION_CANDIDATES)
    if not installed_manifests:
        WEBSTORE_URL = "https://chrome.google.com/webstore/detail/{}".format(extension_id)
        logger.warn("could not discover suitable external extension installation directory. "
                    "Install the extension manually from the chrome webstore: {}"
                    .format(WEBSTORE_URL))

def install_all(extension_id):
    """install both native host manifest and external extension"""
    install_native_host(extension_id)
    install_extension(extension_id)

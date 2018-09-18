import os
import re
import json
import atexit
import logging
import distutils.spawn
from setuptools.command.install import install
from setuptools import setup

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

VERSION = re.search("[0-9.]+", read("chromeurl/version.py")).group(0)

EXE = "chromeurl"
PACKAGE = "chromeurl"

logging.basicConfig()
logger = logging.getLogger('chromeurl-installer')

def install_manifest(filename_sans_ext, manifest_dict, directory_candidates,
                     max_installations=float("inf")):
    installed_manifests = []
    for cand_maybe_tilde in directory_candidates:
        if len(installed_manifests) > max_installations:
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


EXTENSION_ID = "eibefbdcoojolecpoehkpmgfaeapngjk"

def install_native_host():
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

    exe_abs = distutils.spawn.find_executable(EXE)

    host_name = "com.erjoalgo.chrome_current_url"

    manifest = {
        "name": host_name,
        "description": "chrome current url native host component",
        "path": exe_abs,
        "type": "stdio",
        "allowed_origins": [
            "chrome-extension://{}/".format(EXTENSION_ID)
        ]
    }
    installed_manifests = install_manifest(host_name, manifest, NATIVE_HOST_CANDIDATES)
    if not installed_manifests:
        logger.error("fatal: could not discover suitable native host installation directory")
        exit(1)

def install_extension():
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

    installed_manifests = install_manifest(EXTENSION_ID, manifest, EXTERNAL_EXTENSION_CANDIDATES)
    if not installed_manifests:
        WEBSTORE_URL = "https://chrome.google.com/webstore/detail/{}".format(EXTENSION_ID)
        logger.warn("could not discover suitable external extension installation directory. "
               "Install the extension from the chrome webstore: {}".format(WEBSTORE_URL))

_post_install = lambda: (install_native_host(), install_extension())

class new_install(install, object):
    def __init__(self, *args, **kwargs):
        super(new_install, self).__init__(*args, **kwargs)
        atexit.register(_post_install)


setup(
    name="chromeurl",
    version=VERSION,
    author="Ernesto Alfonso",
    author_email="erjoalgo@gmail.com",
    description=("native messaging host component of chrome current url extension. "
                 "exposes the current chrome browser url via a REST endpoint"),
    license="GPLv3",
    keywords="chrome chromium url",
    url="https://github.com/erjoalgo/chrome-current-url",
    packages=[PACKAGE],
    # long_description=read('README'),
    install_requires=['flask'],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)'
    ],
    entry_points={
        'console_scripts': [
            '{}={}.main:main'.format(EXE, PACKAGE),
        ]
    },
    cmdclass={
        'install': new_install,
    },
)


# Local Variables:
# compile-command: "python setup.py install --user"
# End:

import os
import re
import subprocess
import json

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

setup(
    name="chrome-current-url-native",
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
    }
)

EXE_ABS = subprocess.check_output(["which", EXE]).strip()

def install_manifest():
    if os.name == "darwin":
        target = "~/Library/Application Support/Google/Chrome/NativeMessagingHosts"
    elif os.name == "posix":
        target = "~/.config/{}/NativeMessagingHosts".format("chromium")

    host_name = "com.erjoalgo.chrome_current_url"
    manifest_path = os.path.expanduser(os.path.join(target, "{}.json".format(host_name)))
    extension_id = "ekofhnkbloagjhkldkgjcbmfealemjnh"

    manifest = {
        "name": host_name,
        "description": "chrome current url native host component",
        "path": EXE_ABS,
        "type": "stdio",
        "allowed_origins": [
            "chrome-extension://{}/".format(extension_id)
        ]
    }

    with open(manifest_path, "w") as fh:
        json.dump(manifest, fh, indent=4)

    print ("Native messaging host {} has been installed at {}".format(host_name, manifest_path))

install_manifest()

# Local Variables:
# compile-command: "python setup.py install"
# End:

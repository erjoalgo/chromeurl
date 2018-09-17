import os
import re
import subprocess
import json
from setuptools.command.install import install
import atexit
from setuptools import setup
import distutils.spawn

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

VERSION = re.search("[0-9.]+", read("chromeurl/version.py")).group(0)

EXE = "chromeurl"
PACKAGE = "chromeurl"

def install_manifest():
    """install chrome native host manifest file"""
    EXE_ABS=distutils.spawn.find_executable(EXE)

    targets=[]
    for target_parent in ["~/Library/Application Support/Google/", "~/.config/"]:
        expanded=os.path.expanduser(target_parent)
        dirnames=os.listdir(expanded) if os.path.exists(expanded) else []
        targets+=[os.path.join(target_parent, dirname, "NativeMessagingHosts")
                 for dirname in dirnames if re.search("chrom", dirname)]

    if not targets:
        print ("cannot discover chrome config directory")
        exit(1)

    host_name = "com.erjoalgo.chrome_current_url"
    extension_id = "eibefbdcoojolecpoehkpmgfaeapngjk"

    manifest = {
        "name": host_name,
        "description": "chrome current url native host component",
        "path": EXE_ABS,
        "type": "stdio",
        "allowed_origins": [
            "chrome-extension://{}/".format(extension_id)
        ]
    }

    for target_dir in targets:
        manifest_path = os.path.expanduser(os.path.join(target_dir, "{}.json".format(host_name)))
        try:
            with open(manifest_path, "w") as fh:
                json.dump(manifest, fh, indent=4)
                print ("installed native messaging host at: {}".format(manifest_path))
        except Exception as ex:
            # import traceback
            # traceback.print_exc()
            print ("warning: failed to install manifest at {}:\n\t {}".format(manifest_path, ex))


_post_install=install_manifest

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

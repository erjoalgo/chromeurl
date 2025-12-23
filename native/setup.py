from setuptools import setup

import os
import re
import tomllib

VERSIONFILE = os.path.join(os.path.dirname(__file__), "pyproject.toml")
with open(VERSIONFILE, "rb") as fh:
    data = tomllib.load(fh)
    __version__ = data["project"]["version"]

NAME = EXE = PACKAGE = "chromeurl"

setup(
    name=NAME,
    version=__version__,
    author="Ernesto Alfonso",
    author_email="erjoalgo@gmail.com",
    description=("native messaging host component of chrome current url extension. "
                 "exposes the current chrome browser url via a REST endpoint"),
    keywords="chrome chromium url native",
    url="https://github.com/erjoalgo/chrome-current-url",
    packages=[PACKAGE],
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


# Local Variables:
# compile-command: "python setup.py install --user"
# End:

#!/usr/bin/env python
from setuptools import find_packages, setup

from eplist import __author__  as author
from eplist import __email__   as email
from eplist import __version__ as version

import sys

info = sys.version_info

if (info.major, info.minor) != (2, 7):
    print "Requires Python 2.7"
    exit(1)

setup(
    name='eplist',
    version=version,
    description='Simple episode renaming program',
    long_description=open('README.rst').read(),
    author=author,
    author_email=email,
    url='https://github.com/djt5019/episode_renamer',
    packages=find_packages(),
    license="unlicense",
    zip_safe=False,
    platforms="all",
    classifiers=[
        "Programming Language :: Python :: 2.7",
        "Topic :: Multimedia :: Video",
        "Topic :: Utilities",
        "Environment :: Console",
        "Environment :: X11 Applications :: Qt",
        "Operating System :: OS Independent",
    ],
    requires=[
        "BeautifulSoup (>=3.2.0)",
        "requests (>=0.9.1)",
    ],
    entry_points={
        'console_scripts': ['eplist = eplist.main:main']
    },
    package_data={'': ['eplist.py', 'LICENSE', 'README.rst']},
    include_package_data=True,
)

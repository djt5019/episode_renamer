#!/usr/bin/env python
from distutils.core import setup
from setuptools import find_packages

setup(
    name='eplist',
    version='0.1.3',
    description='Simple episode renaming program',
    long_description=open('README.rst').read(),
    author='Dan Tracy',
    author_email='djt5019@gmail.com',
    url='https://github.com/djt5019/episode_renamer',
    packages=find_packages(),
    license="MIT",
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

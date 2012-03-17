#!/usr/bin/env python
from distutils.core import setup
from setuptools import find_packages

setup(
    name='eplist',
    version='0.1.0',
    description='Simple episode renaming program',
    long_description=open('README.md').read(),
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
        "Environment :: X11 Applications :: Qt"
    ],
    platforms=['Cross-platform'],
    scripts=['eplist'],
    requires=[
        "BeautifulSoup (>=3.2.0)",
        "requests (>=0.9.1)",
    ]
)

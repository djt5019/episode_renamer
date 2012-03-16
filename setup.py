#!/usr/bin/env python
from distutils.core import setup


setup(
    name='epysode',
    version='0.1',
    description='Simple episode renaming program',
    author='Dan Tracy',
    author_email='djt5019@gmail.com',
    url='https://github.com/djt5019/episode_parser',
    packages=["episode_parser", "tests", "episode_parser.gui", "episode_parser.web_sources"],
    include_package_data=True,
    zip_safe=False,
    license="MIT",
    install_requires=[
        "requests >= 0.9.0",
        "BeautifulSoup >= 3.2.0"
    ]
)

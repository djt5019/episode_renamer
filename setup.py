from distutils.core import setup
from setuptools import find_packages


setup(
    name='epysode',
    version='0.1',
    description='Simple python episode renaming solution',
    author='Dan Tracy',
    author_email='djt5019@gmail.com',
    url='https://github.com/djt5019/episode_parser',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    license="MIT",
)

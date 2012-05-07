# -*- coding: utf-8 -*-
"""
Listing of constants that will be used throughout the program
"""

from __future__ import unicode_literals

import re

import os
import sys
from os.path import join, split, realpath

video_extensions = {'.mkv', '.ogm', '.asf', '.asx', '.avi', '.flv', '.mov',
                    '.mp4', '.mpg', '.rm', '.swf', '.vob',
                    '.wmv', '.mpeg', '.m4v'}

project_source_path = split(realpath(__file__))[0]
project_path = split(project_source_path)[0]
web_sources_path = join(project_source_path, 'web_sources')

resource_path = "eplist"

if sys.platform == "win32":
    resource_path = os.path.join(os.environ['appdata'], resource_path)
else:  # *nix / solaris
    resource_path = os.path.join("~", ".{}".format(resource_path))
    resource_path = os.path.expanduser(resource_path)


show_not_found = []

num_dict = {'0': '', '1': 'one', '2': 'two', '3': 'three', '4': 'four',
        '5': 'five', '6': 'six', '7': 'seven', '8': 'eight', '9': 'nine',
        '10': 'ten', '11': 'eleven', '12': 'twelve', '13': 'thirteen',
        '14': 'fourteen', '15': 'fifteen', '16': 'sixteen', '17': 'seventeen',
        '18': 'eighteen', '19': 'nineteen', '20': 'twenty', '30': 'thirty',
        '40': 'forty', '50': 'fifty', '60': 'sixty', '70': 'seventy',
        '80': 'eighty', '90': 'ninety'}


# If you wish to use braces for matching ranges like {1,10} you need to escape
# the braces by doubling them to prevent pythons formatting from breaking.
# eg: {1,10} becomes {{1, 10}}
types = ['ova', 'ona', 'extra', 'special', 'movie', 'dvd', 'bluray']
types = r'|'.join(types)

regex_vars = {
'sep': r'[\-\~\.\_\s]',
'sum': r'.*[\[\(](?P<checksum>[a-z0-9]{{8}}[\]\)])',
'year': r'(:P<year>(19|20)?\d\d)',
'episode': r'(e|ep|episode)?{sep}(?P<episode_number>\d+)(?:v\d)?',  # ex: e3v2
'season': r'(s|season)?{sep}*?(?P<season>\d+)',
'series': r'(?P<series>.*)',
'subgroup': r'(?P<group>\[.*\])',
'special': r'(?P<special_type>{specical_types}){sep}*?(?P<special_number>\d+)',
'title': r'(?P<title>.*?)',
'specical_types': types,
}

# Substitute any regex variables that may have been used
# within later dictionary entries
regex_vars = {key: regex_vars[key].format(**regex_vars) for key in regex_vars}

regexList = [
   r'^(?P<series>.*?) - Season (?P<season>\d+) - Episode (?P<episode>\d*) - .*',
   r'^(?P<series>.*?) - Episode (?P<episode>\d+) - .*',  # My usual formats
   r'^{series}{sep}+{season}{sep}+?{episode}{sep}+?{title}',
   r'^{series}{sep}+{special}{sep}+?{title}',
   r'^{series}{sep}+{episode}{sep}+?{title}',
   r'^{special}',
   r'^{episode}',
   r'(op|ed|trailer){sep}*(?P<junk>\d*)',  # intro /outro music
   r'{episode}',  # General catch-all, look for the first set of numbers
]

## Substitute the dictionary variables in to the unformatted regex
regexList = [r.format(**regex_vars) for r in regexList]
regexList = [re.compile(regex) for regex in regexList]

checksum_regex = re.compile(r'[\[\(](?P<checksum>[a-f0-9]{8})[\]\)]', re.I)

remove_junk_regex = re.compile(r'[\[\(].*?[\]\]]', re.I)

bracket_season_regex = re.compile(
                   r'[\[\(]{season}X{episode}[\]\)]'.format(**regex_vars), re.I)

encoding_regex = re.compile(r'(?P<encoding>\d{3,4}x\d{3,4}|\d{3,4}p)')

# Used to split ranges of numbers, eg: "1-2-3-4-5"
# becomes [1,2,3,4,5] or range(1, 6) depending of python 2.* or 3
num_range_regex = re.compile(r'[^\d]')


class AttributeDict(dict):
    """docstring for AttributeDict"""
    def __getattribute__(self, val):
        return self[val] if val in self else dict.__getattribute__(self, val)

    def __setattr__(self, name, value):
        self[name] = value

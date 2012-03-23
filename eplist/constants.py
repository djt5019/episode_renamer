# -*- coding: utf-8 -*-

from __future__ import unicode_literals

__author__ = 'Dan Tracy'
__email__ = 'djt5019 at gmail dot com'

import re

import os
import sys
from os.path import join, split, realpath

VIDEO_EXTENSIONS = set(['.mkv', '.ogm', '.asf', '.asx', '.avi', '.flv', '.mov', '.mp4', '.mpg', '.rm', '.swf', '.vob',
                    '.wmv', '.mpeg'])

PROJECT_SOURCE_PATH = split(realpath(__file__))[0]
PROJECT_PATH = split(PROJECT_SOURCE_PATH)[0]
WEB_SOURCES_PATH = join(PROJECT_SOURCE_PATH, 'web_sources')

RESOURCE_PATH = os.path.join("eplist", "resources")

if sys.platform == "win32":
    RESOURCE_PATH = os.path.join(os.environ['APPDATA'], RESOURCE_PATH)
elif sys.platform == 'darwin':
    ## Found at http://stackoverflow.com/questions/1084697/how-do-i-store-desktop-application-data-in-a-cross-platform-way-for-python
    from AppKit import NSSearchPathForDirectoriesInDomains
    RESOURCE_PATH = os.path.join(NSSearchPathForDirectoriesInDomains(14, 1, True)[0], RESOURCE_PATH)
else:  # *nix / solaris
    RESOURCE_PATH = os.path.expanduser(os.path.join("~", "." + RESOURCE_PATH))


SHOW_NOT_FOUND = []

regexList = []

NUM_DICT = {'0': '', '1': 'one', '2': 'two', '3': 'three', '4': 'four', '5': 'five', '6': 'six',
        '7': 'seven', '8': 'eight', '9': 'nine', '10': 'ten', '11': 'eleven', '12': 'twelve',
        '13': 'thirteen', '14': 'fourteen', '15': 'fifteen', '16': 'sixteen', '17': 'seventeen',
        '18': 'eighteen', '19': 'nineteen', '20': 'twenty', '30': 'thirty', '40': 'forty',
        '50': 'fifty', '60': 'sixty', '70': 'seventy', '80': 'eighty', '90': 'ninety'}


regex_vars = {
'sep': r'[\-\~\.\_\s]',
'sum': r'(.*[\[\(](?P<sum>[a-z0-9]{8})[\]\)])',
'year': r'(:P<year>(19|20)?\d\d)',
'episode': r'(e|ep|episode)?{sep}*?(?P<episode>\d+)(?:v\d)?',  # ex: e3v2
'season': r'(s|season)?{sep}*?(?P<season>\d+)',
'series': r'(?P<series>.*)',
'subgroup': r'(?P<group>\[.*\])',
'special': r'(?P<type>ova|ona|extra|special|movie|dvd|bluray){sep}+(?P<special>\d+)',
}

for k, v in regex_vars.iteritems():
    try:
        # Substitute any regex variables that may have been used within later dictionary entries
        regex_vars[k] = v.format(**regex_vars)
    except IndexError as e:
        pass

uncompiled_regex = [
            r'^(?P<series>.*?) - Season (?P<season>\d+) - Episode (?P<episode>\d*) - .*',  # Also mine
            r'^(?P<series>.*?) - Episode (?P<episode>\d*) - .*',  # My usual format
            r'^{series}{sep}+{special}',
            r'^{series}{sep}+{episode}',
            r'^{series}{sep}+{season}{sep}*{episode}',
            r'^{series}{sep}+{season}{sep}*{episode}{sep}*{sum}?',
            r'^{series}{sep}+{episode}',
            r'^(?P<series>.*) - OVA (?P<special>\d+) - \w*',
            r'^{series}{sep}*{special}',
            r'{series}{sep}*(op|ed){sep}*(?P<junk>\d*)',  # Show intro /outro music, just ignore them
            r'.*{episode}',  # More of a general catch-all regex, last resort search for the first numbers in the filename
            ]

## Substitute the dictionary variables in to the unformated regexes (is the plural of regex, regexes?)
uncompiled_regex = [r.format(**regex_vars) for r in uncompiled_regex]

regexList = map(lambda x: re.compile(x, re.I), uncompiled_regex)

checksum_regex = re.compile(r'[\[\(](?P<sum>[a-f0-9]{8})[\]\)]', re.I)
remove_junk_regex = re.compile(r'[\[\(].*?[\]\]]', re.I)
bracket_season_regex = re.compile(r'[\[\(]{season}X{episode}[\]\)]'.format(**regex_vars), re.I)

del k, e, v, regex_vars, uncompiled_regex

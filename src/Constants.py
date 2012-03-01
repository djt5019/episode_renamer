# -*- coding: utf-8 -*-
__author__ = 'Dan Tracy'
__email__ = 'djt5019 at gmail dot com'

from os.path import split, join

VIDEO_EXTENSIONS = ['.mkv', '.ogm', '.asf', '.asx', '.avi', '.flv', '.mov', '.mp4', '.mpg', '.rm', '.swf', '.vob',
                    '.wmv', '.mpeg']

PROJECT_SOURCE_PATH = split(__file__)[0]
PROJECT_PATH = split(PROJECT_SOURCE_PATH)[0]
RESOURCE_PATH = join(PROJECT_PATH, 'resources')
WEB_SOURCES_PATH = join(PROJECT_SOURCE_PATH, 'web_sources')

SHOW_NOT_FOUND = []
regexList = []

## Common video naming formats, will be compiled if they are needed during episode renaming
## in the _compile_regexs function, otherwise they will not be compiled for simple episode
## information retrieval purposes

_REGEX_VARS = {
'sep': r'[\-\~\.\_\s]',
'sum': r'(.*[\[\(](?P<sum>[a-z0-9]{8})[\]\)])',
'year': r'(:P<year>(19|20)?\d\d)',
'episode': r'(e|ep|episode)?{sep}+?(?P<episode>\d+)(?:v\d)?',  # ex: e3v2
'season': r'(s|season)?{sep}*?(?P<season>\d+)',
'series': r'(?P<series>.*)',
'subgroup': r'(\[.*\])',
'special': r'(?P<type>ova|ona|extra|special|movie|dvd|bluray){sep}+(?P<special>\d+)',
}

for k, v in _REGEX_VARS.iteritems():
    try:
        # Substitute any regex variables that may have been used within
        # later dictionary entries kind of like how let* works in scheme.
        _REGEX_VARS[k] = v.format(**_REGEX_VARS)
    except IndexError as e:
        pass

REGEX = [
            r'^(?P<series>.*?) - Season (?P<season>\d+) - Episode (?P<episode>\d*) - .*',  # Also mine
            r'^(?P<series>.*?) - Episode (?P<episode>\d*) - .*',  # My usual format
            r'^{subgroup}*{sep}+{series}{sep}+{special}{sep}+{sum}?',
            r'^{subgroup}*{sep}+{series}{sep}+{episode}{sep}+{sum}?',
            r'^{subgroup}*{sep}+{series}{sep}+{season}{sep}+{episode}{sep}+{sum}?',
            r'^{series}{sep}*\[{season}X{episode}\]{sep}*{sum}?',
            r'^{series}{sep}*{season}{sep}*{episode}{sep}*{sum}?',
            r'^{series}{sep}*{episode}{sep}*{sum}?',
            r'^{series}{sep}+{season}X{episode}{sep}*{sum}?',
            r'^(?P<series>.*) - OVA (?P<special>\d+) - \w*',
            r'^{series}{sep}*{special}',
            r'{series}{sep}*{episode}',  # More of a general catch-all regex, last resort
            r'{series}{sep}*(op|ed){sep}*(?P<junk>\d*){sep}*{sum}?',  # Show intro /outro music, just ignore them
            ]

## Substitute the dictionary variables in to the unformated regexes (is the plural of regex, regexes?)
REGEX = [r.format(**_REGEX_VARS) for r in REGEX]

NUM_DICT = {'0': '', '1': 'one', '2': 'two', '3': 'three', '4': 'four', '5': 'five', '6': 'six',
        '7': 'seven', '8': 'eight', '9': 'nine', '10': 'ten', '11': 'eleven', '12': 'twelve',
        '13': 'thirteen', '14': 'fourteen', '15': 'fifteen', '16': 'sixteen', '17': 'seventeen',
        '18': 'eighteen', '19': 'nineteen', '20': 'twenty', '30': 'thirty', '40': 'forty',
        '50': 'fifty', '60': 'sixty', '70': 'seventy', '80': 'eighty', '90': 'ninety'}
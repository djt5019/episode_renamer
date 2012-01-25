# -*- coding: utf-8 -*-
__author__='Dan Tracy'
__email__='djt5019 at gmail dot com'

import os

from EpParser import __file__ as file_path

VIDEO_EXTENSIONS = {'.mkv', '.ogm', '.asf', '.asx', '.avi', '.flv', '.mov',
                    '.mp4', '.mpg', '.rm',  '.swf', '.vob', '.wmv', '.mpeg'}

PROJECT_PATH = os.path.abspath(os.path.dirname(os.path.join(file_path)))
RESOURCE_PATH = os.path.join( PROJECT_PATH, 'resources')
PROJECT_SOURCE_PATH = os.path.join(PROJECT_PATH, 'src')
WEB_SOURCES_PATH = os.path.join(PROJECT_SOURCE_PATH, 'web_sources')

SHOW_NOT_FOUND = []


## Common video naming formats, will be compiled if they are needed during episode renaming
## in the _compile_regexs function, otherwise they will not be compiled for simple episode 
## information retrieval purposes

_sep = r'[\-\~\.\_\s]'
_REGEX_VARS = {
'sep': _sep,
'sum': r'(.*[\[\(](?P<sum>[a-z0-9]{8})[\]\)])',
'year': r'(:P<year>(19|20)?\d\d)',
'episode': r'(e|episode)?{sep}*(?P<episode>\d+)'.format(sep=_sep),
'season': r'(s|season)?{sep}*(?P<season>\d+)'.format(sep=_sep),
'series': r'(?P<series>.*)',
'subgroup': r'(\[.*\])',
'special': r'(op|ed|ova|ona|extra|special){sep}*(?P<special>\d+)',
}

_UNFORMATED_REGEX = (
            r'^(?P<series>.*?) - Season (?P<season>\d+) - Episode (?P<episode>\d*) - .*',  # Also mine
            r'^(?P<series>.*?) - Episode (?P<episode>\d*) - .*',  # My usual format
            #r'^{subgroup}*{sep}*?{series}{sep}*{season}{sep}*{episode}{sep}+{sum}?',
            #r'^{subgroup}*{sep}*?{series}{sep}*{special}{sep}*{sum}?',
            #r'^{subgroup}*{sep}*?{series}{sep}*{episode}{sep}+{sum}?',
            #r'^{series}{sep}+{year}?{sep}{season}{sep}*{episode}*{sep}*{sum}?',
            #r'^{series}{sep}+{year}?{sep}{episode}{sep}*{sum}?',
            #r'^{series}{sep}+{year}?{sep}{season}X{episode}{sep}*{sum}?',
            #r'^{series}{sep}+{year}?{sep}\[{season}X{episode}\]{sep}*{sum}?',
            #r'^(?P<series>.*) - OVA (?P<special>\d+) - \w*',
            #r'{series}{sep}*{episode}',  # More of a general catch-all regex, last resort
            #r'{series}{sep}*(op|ed){sep}*(?P<special>\d*){sep}*{sum}?',  # Show intro/outro music, just ignore them
            )

## Substitute the dictionary variables in to the unformated regexes (is the plural of regex, regexes?)
REGEX =  [r.format(**_REGEX_VARS) for r in _UNFORMATED_REGEX]

NUM_DICT = { '0' : '','1' : 'one', '2' : 'two', '3' : 'three', '4' : 'four', '5' : 'five', '6' : 'six',
        '7' : 'seven', '8' : 'eight', '9' : 'nine', '10' : 'ten', '11' : 'eleven', '12' : 'twelve',
        '13' : 'thirteen', '14' : 'fourteen', '15' : 'fifteen', '16' : 'sixteen', '17' : 'seventeen',
        '18' : 'eighteen', '19' : 'nineteen', '20' : 'twenty', '30' : 'thirty', '40' : 'forty',
        '50' : 'fifty', '60' : 'sixty', '70' : 'seventy', '80' : 'eighty', '90' : 'ninety'}

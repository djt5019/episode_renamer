# -*- coding: utf-8 -*-
__author__ = 'Dan Tracy'
__email__ = 'djt5019 at gmail dot com'

import re
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
'episode': r'(e|ep|episode)?{sep}*?(?P<episode>\d+)(?:v\d)?',  # ex: e3v2
'season': r'(s|season)?{sep}*?(?P<season>\d+)',
'series': r'(?P<series>.*)',
'subgroup': r'(\[.*\])',
'special': r'(?P<type>ova|ona|extra|special|movie|dvd|bluray){sep}+(?P<special>\d+)',
}

for k, v in _REGEX_VARS.iteritems():
    try:
        # Substitute any regex variables that may have been used within later dictionary entries
        _REGEX_VARS[k] = v.format(**_REGEX_VARS)
    except IndexError as e:
        pass

REGEX = [
            r'^(?P<series>.*?) - Season (?P<season>\d+) - Episode (?P<episode>\d*) - .*',  # Also mine
            r'^(?P<series>.*?) - Episode (?P<episode>\d*) - .*',  # My usual format
            r'^{series}{sep}+{special}',
            r'^{series}{sep}+{episode}',
            r'^{series}{sep}+{season}{sep}+{episode}',
            r'^{series}{sep}*\[{season}X{episode}\]',
            r'^{series}{sep}*{season}{sep}*{episode}{sep}*{sum}?',
            r'^{series}{sep}*{episode}',
            r'^{series}{sep}+{season}X{episode}',
            r'^(?P<series>.*) - OVA (?P<special>\d+) - \w*',
            r'^{series}{sep}*{special}',
            r'{series}{sep}*(op|ed){sep}*(?P<junk>\d*)',  # Show intro /outro music, just ignore them
            r'.*{episode}',  # More of a general catch-all regex, last resort search for the first numbers in the filename
            ]

## Substitute the dictionary variables in to the unformated regexes (is the plural of regex, regexes?)
REGEX = [r.format(**_REGEX_VARS) for r in REGEX]

regexList = map(lambda x: re.compile(x, re.I), REGEX)

NUM_DICT = {'0': '', '1': 'one', '2': 'two', '3': 'three', '4': 'four', '5': 'five', '6': 'six',
        '7': 'seven', '8': 'eight', '9': 'nine', '10': 'ten', '11': 'eleven', '12': 'twelve',
        '13': 'thirteen', '14': 'fourteen', '15': 'fifteen', '16': 'sixteen', '17': 'seventeen',
        '18': 'eighteen', '19': 'nineteen', '20': 'twenty', '30': 'thirty', '40': 'forty',
        '50': 'fifty', '60': 'sixty', '70': 'seventy', '80': 'eighty', '90': 'ninety'}

checksum_regex = re.compile(r'[\[\(](?P<sum>[a-z0-9]{8})[\]\)]', re.I)
encoding_regex = re.compile(r'\[H\.?.*?\]', re.I)
remove_junk_regex = re.compile(r'[\[\(].*[\]\]]', re.I)


############
## Strings to generate default config files
############

DEFAULT_SETTINGS_STRING = """
## Your TvDB api key, required to poll their website
tvdb_key = # your tvdb apikey


## Program logger options
log_config = logger.conf
log_file = output.log

## Database file for our episodes
db_name = episodes.db

## Days to wait to update the show within the database
db_update = 7

## Where to store the old filenames from the last rename operation
rename_backup = last_rename.dat

## File to store the access times data
access_time_file = last_access.dat

## Time in seconds between polling a website, reccomended is 2
poll_delay = 2

## AniDB flat file with the ids of the shows visit link below for updated version from time to time
## http://anidb.net/api/animetitles.dat.gz
anidb_db_file = animetitles.dat
anidb_db_url = http://anidb.net/api/animetitles.dat.gz

## Tag options
tag_config = tags.cfg
tag_start = <
tag_end = >
"""

DEFAULT_LOGGING_CONFIG = '''
[loggers]
keys=root

[logger_root]
handlers=console
qualname=root
level=DEBUG

[formatters]
keys=consoleFormat

[formatter_consoleFormat]
format=%(levelname)s | "%(message)s"

[handlers]
keys=console

[handler_console]
class=logging.StreamHandler
formatter=consoleFormat
level=WARNING
args=(sys.stdout,)
'''

DEFUALT_TAG_CONFIG = """
[episode_name]
tags=name, episode, title

[episode_number]
tags=epnum, number, num

[episode_count]
tags=count, ep

[series_name]
tags=series, show

[season_number]
tags=season, seasons
"""

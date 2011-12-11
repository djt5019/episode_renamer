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

SHOW_NOT_FOUND = ("", [])


## Common video naming formats, will be compiled if they are needed during episode renaming
## in the _compile_regexs function, otherwise they will not be compiled for simple episode 
## information retrieval purposes
_sep = r'[\-\~\.\_\s]'
_sum = r'(.*\[(?P<sum>[a-z0-9]{8})\])'
REGEX = (   r'^\[.*\]?{sep}*(?P<series>.*){sep}+(?P<episode>\d+){sep}*{sum}?'.format(sep=_sep, sum=_sum),
            r'^\[.*\]?{sep}*(?P<series>.*){sep}+OVA[-\._\s]*(?P<special>\d+){sep}*{sum}?'.format(sep=_sep, sum=_sum),
            r'^\[.*\]?{sep}*(?P<series>.*){sep}+(s|season){sep}*(?P<season>\d+){sep}*(?P<episode>\d+)*{sum}?'.format(sep=_sep, sum=_sum),
            r'(?P<series>.*){sep}*S(?P<season>\d+){sep}*(episode|ep|e)(?P<episode>\d+){sep}*{sum}?'.format(sep=_sep, sum=_sum),
            r'(?P<series>.*){sep}*(episode|ep|e)(?P<episode>\d+){sep}*{sum}?'.format(sep=_sep, sum=_sum),
            r'^(?P<series>.*){sep}*\[(?P<season>\d+)x(?P<episode>\d+)\]{sep}*{sum}?'.format(sep=_sep, sum=_sum),
            r'^(?P<series>.*) - Season (?P<season>\d+) - Episode (?P<episode>\d*) - \w*',  # Also mine
            r'^(?P<series>.*) - Episode (?P<episode>\d*) - \w*',  # My usual format
            r'^(?P<series>.*) - OVA (?P<special>\d+) - \w*',
            r'(?P<series>.*)[-\._\s]+(?P<episode>\d+)',
            )

NUM_DICT = { '0' : '','1' : 'one', '2' : 'two', '3' : 'three', '4' : 'four', '5' : 'five', '6' : 'six',
        '7' : 'seven', '8' : 'eight', '9' : 'nine', '10' : 'ten', '11' : 'eleven', '12' : 'twelve',
        '13' : 'thirteen', '14' : 'fourteen', '15' : 'fifteen', '16' : 'sixteen', '17' : 'seventeen',
        '18' : 'eighteen', '19' : 'nineteen', '20' : 'twenty', '30' : 'thirty', '40' : 'forty',
        '50' : 'fifty', '60' : 'sixty', '70' : 'seventy', '80' : 'eighty', '90' : 'ninety'}

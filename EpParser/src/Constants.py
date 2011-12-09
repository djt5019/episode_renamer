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
REGEX = (  r'^\[.*\]?[-\._\s]*(?P<series>.*)[-\._\s]+(?P<episode>\d+)[-\._\s]',
            r'^\[.*\]?[-\._\s]*(?P<series>.*)[-\._\s]+OVA[-\._\s]*(?P<special>\d+)[-\._\s]',
            r'^\[.*\]?[-\._\s]*(?P<series>.*)[-\._\s]+(s|season)[-\._\s]*(?P<season>\d+)[-\._\s]*(?P<episode>\d+)[-\._\s]*',
            r'(?P<series>.*)[\s\._-]*S(?P<season>\d+)[\s\._-]*(episode|ep|e)(?P<episode>\d+)',
			r'(?P<series>.*)[\s\._-]*(episode|ep|e)(?P<episode>\d+)',
			r'^(?P<series>.*)[\s\._-]*\[(?P<season>\d+)x(?P<episode>\d+)\]',
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
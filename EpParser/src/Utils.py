# -*- coding: utf-8 -*-
__author__='Dan Tracy'
__email__='djt5019 at gmail dot com'

import os
import re
import threading
import zlib
import pickle
import requests
import requests.exceptions

import Episode
import Logger

from itertools import ifilter

from EpParser.src.Settings import Settings
from EpParser.src import Constants


def get_URL_descriptor(url):
    """Returns an auto-closing url descriptor or None"""
    try:
        resp = requests.get(url)
    except requests.exceptions.ConnectionError:
        Logger.get_logger().error("Error connecting to {}".format(url))
        return None

    if resp.ok:
        return resp

    return None

def is_valid_file(filename):
    ext = os.path.splitext(filename)[1].lower()

    if os.path.isfile(filename) and ext in Constants.VIDEO_EXTENSIONS:
        return True
    else:
        return False

## Renaming utility functions
def clean_filenames( path ):
    """Attempts to extract order information about the files passed"""
    # Filter out anything that doesnt have the correct extension and
    # filter out any directories
    files = os.listdir(path)
    files = ifilter(lambda x: is_valid_file(x), files)

    if not files:
        Logger.get_logger().error( "No video files were found in {}".format( path ) )
        exit(1)

    _compile_regexs()
    cleanFiles = []
    # We are going to store the episode number and path in a tuple then sort on the
    # episodes number.  Special episodes will be appended to the end of the clean list
    for f in files:
        g = _search(f)
        checksum = 0
        season = -1

        if not g:
            Logger.get_logger().error( "Could not find file information for: {}".format(f) )
            continue

        if 'special' in g.groupdict():
            continue

        index = int(g.group('episode'))

        if 'sum' in g.groupdict():
            checksum = g.group('sum')
            if checksum:
                checksum = int(checksum, base=16)
            else:
                checksum = 0x0

        if 'season' in g.groupdict():
            season = int(g.group('season'))

        cleanFiles.append(Episode.EpisodeFile(os.path.join(path,f), index, season, checksum))

    if not cleanFiles:
        Logger.get_logger().error( "The files could not be matched" )
        return cleanFiles

    Logger.get_logger().info("Successfully cleaned the file names")

    return cleanFiles

regexList = []
def _compile_regexs():
    # This function will only compile the regexs once and store the results
    # in a list within the function.  Monkey-patching is strange.
    if not regexList:
        for r in Constants.REGEX:
            regexList.append(re.compile(r, re.I))
    return regexList

def _search(filename):
    for count, regex in enumerate(_compile_regexs()):
        result = regex.search(filename)
        if result:
            Logger.get_logger().info("Regex #{} matched {}".format(count, filename))
            return result

    return None

def prepare_filenames( path, show):
    """Rename the files located in 'path' to those in the list 'show' """
    path = os.path.abspath(path)
    renamedFiles = []

    files = clean_filenames(path)
    #Match the list of EpisodeFiles to the list of shows in the 'show' variable
    if not files:
        Logger.get_logger().info("No files were able to be renamed")
        return []

    for f in files:
        episode = show.get_episode(f.season, f.index)

        if not episode:
            print "Could not find an episode for {}".format(f.name)

        fileName = encode(episode.title)
        newName = replace_invalid_path_chars(show.formatter.display(episode, f) + f.ext)

        if newName == fileName:
            Logger.get_logger().info("File {} and Episode {} have same name".format(f.name, episode.title))
            continue

        name = os.path.join(path, newName)
        if len(name) > 256:
            Logger.get_logger().error('The filename "{}" may be too long to rename'.format(newName))

        renamedFiles.append( (f.path, name,) )

    return renamedFiles

def rename(files, resp=""):
    """Performs the actual renaming of the files, returns a list of file that weren't able to be renamed"""
    if resp == '':
        resp = raw_input("\nDo you wish to rename these files [y|N]: ").lower()

    if not resp.startswith('y'):
        Logger.get_logger().info( "Changes were not committed to the files" )
        exit(0)

    errors = []
    old_order = []

    for old, new in files:
        try:
            os.rename(old, new)
            old_order.append((new, old))
        except Exception as e:
            errors.append( (old,e) )

    save_renamed_file_info(old_order)

    if errors:
        for e in errors:
            Logger.get_logger().error( "File {} could not be renamed: {}".format( os.path.split(e[0])[1], e[1] ) )
    else:
        Logger.get_logger().info( "Files were successfully renamed")

    return errors


class Thread(threading.Thread):
    def __init__(self, filename):
        super(Thread, self).__init__()
        self.file = filename
        self.sum = 0

    def run(self):
        with open(self.file, 'rb') as f:
            for line in f:
                self.sum += zlib.crc32(line,self.sum)
        print self.sum


def save_renamed_file_info(old_order):
    """ Save the previous names from the last renaming operation to disk """
    Logger.get_logger().info("Backing up old filenames")
    with open(os.path.join(Constants.RESOURCE_PATH, Settings['rename_backup']), 'w') as f:
        pickle.dump(old_order, f)

def load_last_renamed_files():
    """ Restore the previous names from the last renaming operation"""
    Logger.get_logger().info("Loading up old filenames")
    if not os.path.exists(os.path.join(Constants.RESOURCE_PATH, Settings['rename_backup'])):
        Logger.get_logger().warn("There seems to be no files to be un-renamed")
        return []

    with open(os.path.join(Constants.RESOURCE_PATH, Settings['rename_backup'])) as f:
        data = f.readlines()

    # Data will be in the form of a list of tuples
    # [ (new1, old1), ..., (newN, oldN) ]
    return pickle.loads(''.join(data))


## Text based functions
def remove_punctuation(title):
    """Remove any punctuation and whitespace from the title"""
    name, ext = os.path.splitext(title)
    exclude = set('!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~')
    name = ''.join( ch for ch in name if ch not in exclude )
    return name+ext


def replace_invalid_path_chars(path, replacement='-'):
    """Replace invalid path character with a different, acceptable, character"""
    exclude = set('\\/"?<>|*:')
    path = ''.join( ch if ch not in exclude else replacement for ch in path )
    return path


def prepare_title(title):
    """Remove any punctuation and whitespace from the title"""
    title = remove_punctuation(title).split()

    if not title:
        return ""

    if title[0].lower() == 'the':
        title.remove( title[0] )

    out = []
    for n in title:
        try:
            value = num_to_text(int(n))
            out.append(value)
        except Exception:
            out.append(n)

    return ''.join(out)


def num_to_text(num):
    """Converts a number up to 999 to it's English representation"""
    # The purpose of this function is to resolve numbers to text so we don't
    # have additional entries in the database for the same show.  For example
    # The 12 kingdoms and twelve kingdoms will yield the same result in the DB

    if num < 20:
        return Constants.NUM_DICT[str(num)]

    args = []
    num = str(num)

    while num:
        digit = int(num[0])
        length = len(num)

        if length == 3:
            args.append( Constants.NUM_DICT[num[0]] )
            args.append("hundred")
        else:
            value = str( digit * (10**(length-1)) )
            args.append( Constants.NUM_DICT[value] )

        num = num[1:]

    return '_'.join(args)

def encode(text, encoding='utf-8'):
    """Returns a unicode representation of the string """
    if isinstance(text, basestring):
        if not isinstance(text, unicode):
            text = unicode(text, encoding, 'ignore')
    return text

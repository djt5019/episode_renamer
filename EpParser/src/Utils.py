# -*- coding: utf-8 -*-
# author:  Dan Tracy
# program: Utils.py

import os
import re
import gzip

import Episode
import Logger

from itertools import ifilter
from urllib2 import Request, urlopen, URLError
from contextlib import closing
from cStringIO import StringIO

from Constants import VIDEO_EXTENSIONS, REGEX, NUM_DICT

def get_URL_descriptor(url):
    """Returns an autoclosing url descriptor or None"""
    fd = None
    request = Request(url)
    request.add_header('Accept-encoding', 'gzip')

    try:
        fd = urlopen(request)

        if fd.info().get('Content-Encoding') == 'gzip':
            buffer = StringIO( fd.read() )
            fd = gzip.GzipFile(fileobj=buffer)

    except URLError as e:
        if hasattr(e, 'reason'):
            Logger.get_logger().error( 'ERROR: {0} appears to be down at the moment'.format(url) )
            pass
    except Exception as e:
        Logger.get_logger().error("A GZip error has occured {}".format(e))
        exit()
    finally:
        if fd:
            # If we have a valid descriptor return an auto closing one
            return closing(fd)
        else:
            return None


## Renaming utility functions
def clean_filenames( path ):
    """Attempts to extract order information about the files passed"""
    # Filter out anything that doesnt have the correct extension and
    # filter out any directories
    files = os.listdir(path)
    files = ifilter(lambda x: os.path.isfile(os.path.join(path,x)), files)
    files = ifilter(lambda x: os.path.splitext(x)[1].lower() in VIDEO_EXTENSIONS, files)

    if not files:
        Logger.get_logger().error( "No video files were found in {}".format( path ) )
        exit(1)    
    
    _compile_regexs()
    cleanFiles = {}
    curSeason = -1
    epOffset = 0
    # We are going to store the episode number and path in a tuple then sort on the
    # episodes number.  Special episodes will be appended to the end of the clean list
    for f in files:
        g = _search(f)
        season = -1

        if not g:
            Logger.get_logger().error( "Could not find file information for: {}".format(f) )
            continue

        if 'special' in g.groupdict():
            continue

        index = int(g.group('episode'))

        if 'season' in g.groupdict():
            season = int(g.group('season'))

            if curSeason == -1:
                curSeason = season

            elif curSeason != season:
                curSeason = season
                epOffset = index

        index += epOffset

        cleanFiles[index] = Episode.EpisodeFile(os.path.join(path,f), index, season)

    if not cleanFiles:
        Logger.get_logger().error( "The files could not be matched" )
        return cleanFiles

    Logger.get_logger().info("Successfully cleaned the file names")

    return cleanFiles

def _compile_regexs():
    # This function will only compile the regexs once and store the results
    # in a list within the function.  Monkey-patching is strange.
    if not _compile_regexs.regexList:
        for r in REGEX:
            _compile_regexs.regexList.append(re.compile(r, re.I))
    return _compile_regexs.regexList

_compile_regexs.regexList = []
    
def _search(filename):
    for count, regex in enumerate(_compile_regexs()):
        result = regex.search(filename)
        if result:
            Logger.get_logger().info("Regex #{} matched {}".format(count, filename))
            return result

    return None

def rename_files( path, show):
    """Rename the files located in 'path' to those in the list 'show' """
    path = os.path.abspath(path)
    renamedFiles = []

    files = clean_filenames(path)
    #Match the list of EpisodeFiles to the list of shows in the 'show' variable

    if not files:
        Logger.get_logger().info("No files were able to be renamed")
        return []

    for ep in show.episodeList:
        if ep.season > 0:
            file = files.get(ep.episodeNumber, None)

            if file:
                if file.season != ep.season:
                    continue

        elif ep.season == -1:
            file = files.get(ep.episodeCount, None)

        if not file:
            try:
                Logger.get_logger().info("Could not find an episode for {}".format(ep.title))
            except UnicodeEncodeError:
                pass
            continue

        else:
            try:
                Logger.get_logger().info("Found episode {}".format(ep.title))
            except UnicodeEncodeError:
                pass

        fileName = encode( file.name )
        newName = replace_invalid_path_chars(show.formatter.display(ep, file) + file.ext)

        if newName == fileName:
            Logger.get_logger().info("File {} and Episode {} have same name".format(file.name, ep.title))
            continue

        newName = os.path.join(path, newName)

        renamedFiles.append( (file.path, newName,) )

    return renamedFiles

def rename(files, resp=""):
    """Performs the actual renaming of the files, returns a list of file that weren't able to be renamed"""
    if resp == '':
        resp = raw_input("\nDo you wish to rename these files [y|N]: ").lower()

    if not resp.startswith('y'):
        Logger.get_logger().info( "Changes were not committed to the files" )
        exit(0)

    errors = []

    for old, new in files:
        try:
            os.rename(old, new)
        except Exception as e:
            errors.append( (old,e) )

    if errors:
        for e in errors:
            Logger.get_logger().error( "File {} could not be renamed: {}".format( os.path.split(e[0])[1], e[1] ) )
    else:
        Logger.get_logger().info( "Files were successfully renamed")

    return errors


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
            value = intToText(int(n))
            out.append(value)
        except Exception:
            out.append(n)

    return ''.join(out)


def intToText(num):
    """Converts a number up to 999 to it's English representation"""
    # The purpose of this function is to resolve numbers to text so we don't
    # have additional entries in the database for the same show.  For example
    # The 12 kingdoms and twelve kingdoms will yield the same result in the DB

    if num < 20:
        return NUM_DICT[str(num)]

    args = []
    num = str(num)

    while num:
        digit = int(num[0])
        length = len(num)

        if length == 3:
            args.append( NUM_DICT[num[0]] )
            args.append("hundred")
        else:
            value = str( digit * (10**(length-1)) )
            args.append( NUM_DICT[value] )

        num = num[1:]

    return '_'.join(args)

def encode(text, encoding='utf-8'):
    """Returns a unicode representation of the string """
    if isinstance(text, basestring):
        if not isinstance(text, unicode):
            text = unicode(text, encoding, 'ignore')
    return text

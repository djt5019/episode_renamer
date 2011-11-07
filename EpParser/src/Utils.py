# -*- coding: utf-8 -*-
# author:  Dan Tracy
# program: Utils.py

import EpParser
import os
import re
import logging
import logging.config
import atexit

from itertools import izip, ifilter
from urllib2 import Request, urlopen, URLError
from contextlib import closing
from math import log10
from datetime import datetime

VIDEO_EXTS = {'.mkv', '.ogm', '.asf', '.asx', '.avi', '.flv', 
               '.mov', '.mp4', '.mpg', '.rm',  '.swf', '.vob',
               '.wmv', '.mpeg'}
               
PROJECTPATH  = os.path.dirname(EpParser.__file__)
RESOURCEPATH = os.path.join( PROJECTPATH, 'resources')
PROJECTSOURCEPATH = os.path.join(PROJECTPATH, 'src')
WEBSOURCESPATH = os.path.join(PROJECTSOURCEPATH, 'web_sources')

## Common video naming formats
_REGEX = (  re.compile( r'^\[.*\]?[-\._\s]*(?P<series>.*)[-\._\s]+(?P<episode>\d+)[-\._\s]*[\[\(]*', re.I),
            re.compile( r'^\[.*\]?[-\._\s]*(?P<series>.*)[-\._\s]+OVA[-\._\s]*(?P<special>\d+)[-\._\s]*[\[\(]*', re.I),
            re.compile( r'^\[.*\]?[-\._\s]*(?P<series>.*)[-\._\s]+S[-\._\s]*(?P<season>\d+)[-\._\s]*(?P<episode>\d+)[-\._\s]*[\[\(]*', re.I ),
            re.compile( r'\[?.*?\]?[-\._\s]*(?P<series>.*)[-\._\s]+(?P<episode>\d+)[-\._\s]*', re.I),
            re.compile( r'(?P<series>.*)[\s\._-]*S(?P<season>\d+)[\s\._-]*E(?P<episode>\d+)', re.I),
            re.compile( r'^(?P<series>.*)[\s\._-]*\[(?P<season>\d+)x(?P<episode>\d+)\]',re.I),
            re.compile( r'^(?P<series>.*) - Episode (?P<episode>\d+) - \w*', re.I), #My usual format
            re.compile( r'^(?P<series>.*) - Season (?P<season>\d+) - Episode (?P<episode>\d*) - \w*', re.I), #Also mine
            re.compile( r'^(?P<series>.*) - OVA (?P<special>\d+) - \w*', re.I),
            re.compile( r'(?P<series>.*)[-\._\s]+(?P<episode>\d+)', re.I),
            )


class Show(object):
    '''A convenience class to keep track of the list of episodes as well as
       to keep track of the custom formatter for those episodes'''
    def __init__(self, seriesTitle):
        self.title = encode(seriesTitle.title())
        self.properTitle = prepareTitle(self.title)
        self.episodeList = []
        self.specialsList = []
        self.formatter = EpisodeFormatter(self)
        
                
class Episode(object):
    ''' A simple class to organize the episodes, an alternative would be
        to use a namedtuple though this is easier '''
    def __init__(self, title, epNumber, season, episodeCount):
        self.title = encode(title)
        self.season = season
        self.episode = epNumber
        self.count = episodeCount


class EpisodeFormatter(object): 
    def __init__(self, show, fmt = None):
        '''Allows printing of custom formatted episode information'''
        formatString = u"<series> - Episode <count> - <title>"
        self.show = show
        self.formatString = encode(fmt) if fmt else formatString
        self.tokens = self.formatString.split()
        self.episodeNumberTokens = {"episode", "ep"}
        self.seasonTokens = {"season", "s"}
        self.episodeNameTokens = {"title", "name", "epname"}
        self.seriesNameTokens = {"show", "series"}
        self.episodeCounterTokens = {"count", "number"}
        self.re = re.compile('<(?P<tag>.*?)>', re.I)

    def setFormat(self, fmt):
        '''Set the format string for the formatter'''
        if fmt is not None:
            self.formatString = encode( fmt )
            self.tokens = self.formatString.split()
        
    def display(self, ep):
        '''Displays the episode according to the users format'''
        args = []

        for t in self.tokens:
            tag = self.re.search(t)
        
            if not tag: 
                args.append( t )
                continue
            
            pad = False
            token = tag.group('tag')
            prevTag, postTag = t.split( '<'+token+'>' )
            
            if ':pad' in token:             
                token = token.replace(':pad','').strip()
                pad = True

            if token in self.episodeNumberTokens:
                if pad: #Obtain the number of digits in the highest numbered episode
                    pad = int(log10( max(x.episode for x in self.show.episodeList) ) + 1)
                args.append( prevTag + str(ep.episode).zfill(pad) + postTag )
                
            elif token in self.seasonTokens:
                if pad: #Number of digits in the hightest numbered season
                    pad = int(log10(self.show.episodeList[-1].season) + 1)
                args.append( prevTag + str(ep.season).zfill(pad) + postTag )
                
            elif token in self.episodeCounterTokens:
                if pad: #Total number of digits 
                    pad = int(log10( len(self.show.episodeList) ) + 1)
                args.append( prevTag + str(ep.count).zfill(pad) + postTag)
                
            elif token in self.episodeNameTokens:
                args.append( prevTag + ep.title + postTag )
                
            elif token in self.seriesNameTokens:
                args.append( prevTag + self.show.title.title() + postTag )          
            
            else: # If it reaches this case it's most likely an invalid tag
                args.append(t)

        return encode(' '.join(args))


def getURLdescriptor(url):
    '''Returns a valid url descriptor or None, also deals with exceptions'''
    fd = None
    req = Request(url)

    try:
        fd = urlopen(req)
    except URLError as e:
        if hasattr(e, 'reason'):
            logger.error( 'ERROR: {0} appears to be down at the moment'.format(url) )
            pass
        # 404 Not Found
        #if hasattr(e, 'code'):
        #    print 'ERROR: {0} Responded with code {1}'.format(url,e.code)
    finally:
        if fd:
            # If we have a valid descriptor return an auto closing one
            return closing(fd)
        else:
            return None


## Renaming utility functions
def cleanFilenames( path ):
    '''Attempts to extract order information about the files passed'''
    # Filter out anything that doesnt have the correct extenstion and
    # filter out any directories
    files = os.listdir(path)
    files = ifilter(lambda x: os.path.isfile(os.path.join(path,x)), files)
    files = ifilter(lambda x: os.path.splitext(x)[1].lower() in VIDEO_EXTS, files)

    if files == []:
        logger.error( "No video files were found in {}".format( path ) )
        exit(1)
    
    cleanFiles = []
    curSeason = '1'
    epOffset = 0
    # We are going to store the episode number and path in a tuple then sort on the 
    # episodes number.  Special episodes will be appended to the end of the clean list
    for f in files:
        g = _search(f)
        
        if not g:
            logger.error( "Could not find file information for: {}".format(f) )
            continue
        
        if 'special' in g.groupdict():
            continue
        
        ep = int(g.group('episode'))

        if 'season' in g.groupdict():
            season = g.group('season')

            if curSeason != season:
                curSeason = season
                epOffset = ep

        ep = ep + epOffset
        cleanFiles.append( (ep, os.path.join(path,f)) )
        
    if not cleanFiles:
        logger.error( "The files could not be matched" )
        return []
        
    logger.info("Successfully cleaned the file names")
    cleanFiles = sorted(cleanFiles)
    _, cleanFiles = izip( *cleanFiles )
    
    return cleanFiles

def _search(filename):
    for regex in _REGEX:
        result = regex.search(filename)
        if result:          
            return result
        
    return None
    
def renameFiles( path, episodes):
    '''Rename the files located in 'path' to those in the list 'show' '''
    path = os.path.abspath(path)
    renamedFiles = []
    files = cleanFilenames(path)

    if files == []:
        exit("No files were able to be renamed")

    for f, n in izip(files, episodes):
        fileName = encode(f)
        _, ext   = os.path.splitext(f)
        newName  = n + ext
        newName  = replaceInvalidPathChars(newName)
        
        if newName == fileName:
            continue

        fileName = os.path.join(path, fileName)
        newName  = os.path.join(path, newName)

        renamedFiles.append( (fileName, newName,) )
        
    return renamedFiles

def doRename(files, resp=""):
    if resp == '':
        resp = raw_input("\nDo you wish to rename these files [y|N]: ").lower()

    if not resp.startswith('y'):
        logger.info( "Changes were not commited to the files" )
        exit(0)

    errors = []
    
    for old, new in files:
        try:
            os.rename(old, new)
        except Exception as e:
            logger.warning("File {0} could not be renamed".format(os.path.split(old)[1]))
            logger.warning(e)
            errors.append(old)
    
    if not errors:
        logger.info( "Files were successfully renamed")
        
    return errors

    '''Rename the files located in 'path' to those in the list 'show' '''
    renamedFiles = []
    files = cleanFilenames(path)
    
    if files == []:
        exit("No files were able to be renamed")

    for f, n in izip(files, episodes):
        fileName = encode(f)
        _, ext   = os.path.splitext(f)
        newName  = n + ext
        newName  = replaceInvalidPathChars(newName)
        
        if newName == fileName:
            continue

        fileName = os.path.join(path, fileName)
        newName  = os.path.join(path, newName)

        renamedFiles.append( (fileName, newName,) )
        
    return renamedFiles

def doRename(files, resp=""):
    '''Rename the files located in 'path' to those in the list 'show' '''
    renamedFiles = []
    files = cleanFilenames(path)
    
    if files == []:
        exit("No files were able to be renamed")

    for f, n in izip(files, episodes):
        fileName = encode(f)
        _, ext   = os.path.splitext(f)
        newName  = n + ext
        newName  = replaceInvalidPathChars(newName)
        
        if newName == fileName:
            continue

        fileName = os.path.join(path, fileName)
        newName  = os.path.join(path, newName)

        renamedFiles.append( (fileName, newName,) )
        
    return renamedFiles

def doRename(files, resp=""):
    if resp == '':
        resp = raw_input("\nDo you wish to rename these files [y|N]: ").lower()

    if not resp.startswith('y'):
        logger.info( "Changes were not commited to the files" )
        exit(0)

    errors = []
    
    for old, new in files:
        try:
            os.rename(old, new)
        except:
            errors.append(old)
    
    if errors:
        for e in errors:
            logger.error( "File {0} could not be renamed".format( os.path.split(e)[1] ) )
    else:
        logger.info( "Files were successfully renamed")
        
    return errors


## Text based functions
def removePunc(title):
    '''Remove any punctuation and whitespace from the title'''
    name, ext = os.path.splitext(title)
    exclude = set('!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~')
    name = ''.join( ch for ch in name if ch not in exclude )
    return name+ext
    

def replaceInvalidPathChars(path, replacement='-'):
    '''Replace invalid path character with a different, acceptable, character'''
    exclude = set('\\/"?<>|*:')
    path = ''.join( ch if ch not in exclude else replacement for ch in path )
    return path


def prepareTitle(title):
    '''Remove any punctuation and whitespace from the title'''
    title = removePunc(title).split()
    if title == []: 
        return ""
        
    if title[0] == 'the':
        title.remove('the')
    return ''.join(title)


def encode(text, encoding='utf-8'):
    '''Returns a unicode representation of the string '''
    if isinstance(text, basestring):
        if not isinstance(text, unicode):
            text = unicode(text, encoding, 'ignore')
    return text


#Logging Utility
def _closeLogs():
    logger.debug("APPLICATION END: {}".format(datetime.now()))
    logging.shutdown()
    
logging.config.fileConfig( os.path.join(RESOURCEPATH,'logger.conf') )
atexit.register( _closeLogs )
logger = logging.getLogger()
logger.debug("APPLICATION START: {}".format(datetime.now()))

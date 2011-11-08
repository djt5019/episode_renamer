# -*- coding: utf-8 -*-
# author:  Dan Tracy
# program: Utils.py

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
               
PROJECTPATH  = os.path.abspath(os.path.join(os.path.dirname(os.path.join(__file__)), '..'))
RESOURCEPATH = os.path.join( PROJECTPATH, 'resources')
PROJECTSOURCEPATH = os.path.join(PROJECTPATH, 'src')
WEBSOURCESPATH = os.path.join(PROJECTSOURCEPATH, 'web_sources')


## Common video naming formats
_REGEX = (  re.compile( r'^\[.*\]?[-\._\s]*(?P<series>.*)[-\._\s]+(?P<episode>\d+)[-\._\s]*[\[\(]*', re.I),
            re.compile( r'^\[.*\]?[-\._\s]*(?P<series>.*)[-\._\s]+OVA[-\._\s]*(?P<special>\d+)[-\._\s]*[\[\(]*', re.I),
            re.compile( r'^\[.*\]?[-\._\s]*(?P<series>.*)[-\._\s]+S[-\._\s]*(?P<season>\d+)[-\._\s]*(?P<episode>\d+)[-\._\s]*[\[\(]*', re.I ),
            re.compile( r'(?P<series>.*)[\s\._-]*S(?P<season>\d+)[\s\._-]*E(?P<episode>\d+)', re.I),
            re.compile( r'^(?P<series>.*)[\s\._-]*\[(?P<season>\d+)x(?P<episode>\d+)\]',re.I),
            re.compile( r'^(?P<series>.*) - Episode (?P<episode>\d*) - \w*', re.I), #My usual format
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
        self.numSeasons = 0
        self.maxEpisodeNumber = 0
        
    def addEpisodes(self, eps=[]):
        if eps == []:
            return
            
        self.episodeList = eps
        self.numSeasons = eps[-1].season
        self.maxEpisodeNumber = max( x.episode for x in eps )
        self.numEpisodes = len(eps)
        
    def setFormat(self, fmt):
        self.formatter.setFormat(fmt)
        
                
class Episode(object):
    ''' A simple class to organize the episodes, an alternative would be
        to use a namedtuple though this is easier '''
    def __init__(self, title, epNumber, season, episodeCount):
        self.title = encode(title)
        self.season = int(season)
        self.episode = int(epNumber)
        self.count = int(episodeCount)


class EpisodeFormatter(object): 
    def __init__(self, show, fmt = None):
        '''Allows printing of custom formatted episode information'''
        formatString = u"<series> - Episode <count> - <title>"
        self.show = show
        self.formatString = encode(fmt) if fmt else formatString
        self.tokens = self.formatString.split()
        self.episodeNumberTokens = {"episode", "ep"}
        self.seasonTokens = {"season"}
        self.episodeNameTokens = {"title", "name", "epname"}
        self.seriesNameTokens = {"show", "series"}
        self.episodeCounterTokens = {"count", "number"}
        self.re = re.compile('(?P<tag><.*?>)', re.I)

    def setFormat(self, fmt):
        '''Set the format string for the formatter'''
        if fmt is not None:
            self.formatString = encode( fmt )
            self.tokens = self.formatString.split()
            
    def loadFormatTokens(self):
        import ConfigParser 

        path = os.path.join(RESOURCEPATH, 'tags.cfg')

        if not os.path.exists(path):
            getLogger().warning("Tag config file was not found")
            return
        
        cfg = ConfigParser.ConfigParser()
        cfg.read(path)
        
        allTokens = set()
        
        for s in cfg.sections():
            tokens = cfg.get(s, 'tags')
            
            if ',' in tokens: 
                tokens = tokens.split(',')
            
            tokens = { t.strip() for t in tokens }
            
            for f in tokens.intersection(allTokens):
                getLogger().error("In section {} Token {} redefined".format(s,f))
                tokens.remove(f)
                    
            allTokens = allTokens.union(tokens)
            
            if s == 'episode_name':
                self.episodeNameTokens = tokens
            elif s == "episode_number":
                self.episodeNumberTokens = tokens
            elif s == "episode_count":
                self.episodeCounterTokens = tokens
            elif s == "series_name":
                self.seriesNameTokens = tokens
            elif s == "season_number":
                self.seasonTokens = tokens
                
    def display(self, ep):
        '''Displays the episode according to the users format'''
        args = []

        for token in self.tokens:
            tags = self.re.split(token)
    
            if not tags: 
                args.append( t )
                continue
                
            a = []
            for tag in tags:
                if self.re.match(tag): #If it's a tag try to resolve it
                    a.append( self._parse(ep, tag[1:-1]) )
                else:
                    a.append(tag)
            
            args.append( ''.join(a) )
            
        return encode(' '.join(args))
        
    def _parse(self, ep, tag):
        caps = lower = pad = False
        tag = tag.lower()
        
        # Tag modifiers such as number padding and caps
        if ':pad' in tag:             
            tag = tag.replace(':pad','').strip()
            pad = True            
        if ':caps' in tag:
            tag = tag.replace(':caps','').strip()
            caps = True            
        if ':upper' in tag:
            tag = tag.replace(':upper','').strip()
            caps = True            
        if ':lower' in tag:
            tag = tag.replace(':lower','').strip()
            lower = True            
        if ':' in tag:
            tag = tag.split(':',2)[0]
       
        if tag in self.episodeNumberTokens:
            if pad: #Obtain the number of digits in the highest numbered episode
                pad = int( log10(self.show.maxEpisodeNumber) + 1)            
            return str(ep.episode).zfill(pad)
            
        elif tag in self.seasonTokens:
            if pad: #Number of digits in the hightest numbered season
                pad = int(log10(self.show.numSeasons) + 1)
            return str(ep.season).zfill(pad)
            
        elif tag in self.episodeCounterTokens:
            if pad: #Total number of digits 
                pad = int(log10(self.show.numEpisodes) + 1)
            return str(ep.count).zfill(pad)
            
        elif tag in self.episodeNameTokens:
            if lower: return ep.title.lower()
            if caps: return ep.title.upper()
            return ep.title
            
        elif tag in self.seriesNameTokens:
            if lower: return self.show.title.lower()
            if caps: return self.show.title.upper()
            return self.show.title.title()          
        
        else: # If it reaches this case it's most likely an invalid tag
            return "<" + tag + ">"
            

def getURLdescriptor(url):
    '''Returns a valid url descriptor or None, also deals with exceptions'''
    fd = None
    req = Request(url)

    try:
        fd = urlopen(req)
    except URLError as e:
        if hasattr(e, 'reason'):
            getLogger().error( 'ERROR: {0} appears to be down at the moment'.format(url) )
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
        getLogger().error( "No video files were found in {}".format( path ) )
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
        getLogger().error( "The files could not be matched" )
        return []
        
    getLogger().info("Successfully cleaned the file names")
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
        getLogger().info( "Changes were not commited to the files" )
        exit(0)

    errors = []
    
    for old, new in files:
        try:
            os.rename(old, new)
        except Exception as e:
            getLogger().warning("File {0} could not be renamed".format(os.path.split(old)[1]))
            getLogger().warning(e)
            errors.append(old)
    
    if not errors:
        getLogger().info( "Files were successfully renamed")
        
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
        getLogger().info( "Changes were not commited to the files" )
        exit(0)

    errors = []
    
    for old, new in files:
        try:
            os.rename(old, new)
        except:
            errors.append(old)
    
    if errors:
        for e in errors:
            getLogger().error( "File {0} could not be renamed".format( os.path.split(e)[1] ) )
    else:
        getLogger().info( "Files were successfully renamed")
        
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
_logger = None
def getLogger():
    global _logger
    
    if _logger is None:
        logging.config.fileConfig( os.path.abspath(os.path.join(RESOURCEPATH,'logger.conf')))
        _logger = logging.getLogger()
        
        from logging.handlers import RotatingFileHandler
        logPath = os.path.join(RESOURCEPATH, 'output.log')
        fileHandler = RotatingFileHandler(logPath, maxBytes=2**20, backupCount=3)
        fileHandler.setFormatter( logging.Formatter('%(levelname)s | %(module)s.%(funcName)s - "%(message)s"') )
        fileHandler.setLevel( logging.DEBUG)
        
        _logger.addHandler(fileHandler)
                     
        _logger.debug("APPLICATION START: {}".format(datetime.now()))
        atexit.register( _closeLogs )
     
    return _logger
    
def _closeLogs():
    _logger.debug("APPLICATION END: {}".format(datetime.now()))
    logging.shutdown()
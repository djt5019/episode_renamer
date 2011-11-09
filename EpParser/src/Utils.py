# -*- coding: utf-8 -*-
# author:  Dan Tracy
# program: Utils.py

__all__ = ["PROJECTPATH", "RESOURCEPATH", "PROJECTSOURCEPATH", "WEBSOURCESPATH", 
            "renameFiles", "doRename", "getURLdescriptor", "cleanFilenames", "removePunc",
            "replaceInvalidPathChars", "encode", "intToText"]
 
import os
import re
import gzip

from itertools import izip, ifilter
from urllib2 import Request, urlopen, URLError
from contextlib import closing
from math import log10
from cStringIO import StringIO

from Logger import getLogger

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
            re.compile( r'^(?P<series>.*) - Season (?P<season>\d+) - Episode (?P<episode>\d*) - \w*', re.I), #Also mine
            re.compile( r'^(?P<series>.*) - Episode (?P<episode>\d*) - \w*', re.I), #My usual format
            re.compile( r'^(?P<series>.*) - OVA (?P<special>\d+) - \w*', re.I),
            re.compile( r'(?P<series>.*)[-\._\s]+(?P<episode>\d+)', re.I),
            )
            
_numDict = { '0' : '','1' : 'one', '2' : 'two', '3' : 'three', '4' : 'four', '5' : 'five', '6' : 'six',
        '7' : 'seven', '8' : 'eight', '9' : 'nine', '10' : 'ten', '11' : 'eleven', '12' : 'twelve',
        '13' : 'thirteen', '14' : 'fourteen', '15' : 'fifteen', '16' : 'sixteen', '17' : 'seventeen',
        '18' : 'eighteen', '19' : 'nineteen', '20' : 'twenty', '30' : 'thirty', '40' : 'forty',
        '50' : 'fifty', '60' : 'sixty', '70' : 'seventy', '80' : 'eighty', '90' : 'ninety'}
            

def getURLdescriptor(url):
    '''Returns a valid url descriptor or None, also deals with exceptions'''
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
            getLogger().error( 'ERROR: {0} appears to be down at the moment'.format(url) )
            pass
    except Exception as e:
        print e
        exit()
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
    from Episode import EpisodeFile
    files = os.listdir(path)
    files = ifilter(lambda x: os.path.isfile(os.path.join(path,x)), files)
    files = ifilter(lambda x: os.path.splitext(x)[1].lower() in VIDEO_EXTS, files)
    
    if files == []:
        getLogger().error( "No video files were found in {}".format( path ) )
        exit(1)
    
    cleanFiles = {}
    curSeason = -1
    epOffset = 0
    # We are going to store the episode number and path in a tuple then sort on the 
    # episodes number.  Special episodes will be appended to the end of the clean list
    for f in files:
        g = _search(f)
        index = -1
        season = -1
        
        if not g:
            getLogger().error( "Could not find file information for: {}".format(f) )
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

        index = index + epOffset
        
        cleanFiles[index] = EpisodeFile(os.path.join(path,f), index, season)
        
    if not cleanFiles:
        getLogger().error( "The files could not be matched" )
        return []
        
    getLogger().info("Successfully cleaned the file names")
    
    return cleanFiles

def _search(filename):
    for count, regex in enumerate(_REGEX):
        result = regex.search(filename)
        if result:     
            getLogger().info("Regex #{} matched {}".format(count, filename))
            return result       
        
    return None
    
def renameFiles( path, show):
    '''Rename the files located in 'path' to those in the list 'show' '''
    path = os.path.abspath(path)
    renamedFiles = []
    files = cleanFilenames(path)
    #Match the list of EpisodeFiles to the list of shows in the 'show' variable

    if files == []:
        exit("No files were able to be renamed")
               
    for ep in show.episodeList:
        file = files.get(ep.episode, None)
        
        if not file or file.season != ep.season:
            file = files.get(ep.count, None)
            
        if not file:
            getLogger().error("Could not find an episode for {}".format(ep.title))
            continue
                       
        fileName = encode( file.name )
        newName  = replaceInvalidPathChars(show.formatter.display(ep) + file.ext)
        
        if newName == fileName:
            getLogger().info("File {} and Epiosde {} have same name".format(file.name, ep.title))
            continue
            
        newName  = os.path.join(path, newName)

        renamedFiles.append( (file.path, newName,) )
        
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

    if title[0].lower() == 'the':
        title.remove( title[0] )

    out = []
    for n in title:
        try:
            value = intToText(int(n))
            out.append(value)
        except:
            out.append(n)

    return ''.join(out)
    
        
def intToText(num):
    '''Converts a number up to 999 to it's English representation'''
    # The purpose of this function is to resolve numbers to text so we don't
    # have additional entries in the database for the same show.  For example
    # The 12 kingdoms and twelve kingdoms will yeild the same result in the DB

    if num < 20:
        return _numDict[str(num)]
        
    args = []
    num = str(num)
    
    while num:
        digit = int(num[0])
        length = len(num)
        
        if length == 3:
            args.append( _numDict[num[0]] )
            args.append("hundred")
        else:
            value = str( digit * (10**(length-1)) )
            args.append( _numDict[value] )
            
        num = num[1:]
        
    return '_'.join(args)

def encode(text, encoding='utf-8'):
    '''Returns a unicode representation of the string '''
    if isinstance(text, basestring):
        if not isinstance(text, unicode):
            text = unicode(text, encoding, 'ignore')
    return text
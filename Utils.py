# output display format, season is padded with zeros
# Season - Episode Number - Episode Title

import urllib2
import os
from collections import OrderedDict
from itertools import izip

_DISPLAY = "Season {0} - Episode {1} - {2}".decode('utf-8')
_VIDEO_EXTS = set( ['.mkv', '.ogm', '.asf', '.asx', '.avi', '.flv',
                    '.mov', '.mp4', '.mpg', '.rm',  '.swf', '.vob',
                    '.wmv', '.mpeg'])

class Episode(object):
    ''' A simple class to organize the episodes, an alternative would be
        to use a namedtuple though this is easier '''
    def __init__(self, title, epNumber, season):
        self.title = to_unicode(title)
        self.season = season
        self.episode = epNumber
        
    def __repr__(self):
        return _DISPLAY.format(self.season, self.episode, self.title).encode('utf-8')
    
def prepareTitle(title):
    '''Remove any punctuation and whitespace from the title'''
    title = __removePunc(title).split()
    if title[0] == 'the': 
        title.remove('the')
    return ''.join(title)

def to_unicode(text, encoding='utf-8'):
    if isinstance(text, basestring):
        if not isinstance(text, unicode):
            text = unicode(text, encoding)
    return text

def getURLdescriptor(url):
    fd = None
    try:
        fd = urllib2.urlopen(url)
    except:
        pass
    finally:
        return fd
    

def renameFiles( path=None, episodes = None, testRun=True ):
    '''
    We will sort dictionary with respect to key value by
    removing all punctuation then adding each entry into
    a ordered dictionary to preserve sorted order.  We do
    this to insure the file list is in somewhat of a natural
    ordering, otherwise we will have misnamed files
    '''

    global _VIDEO_EXTS
    
    files = os.listdir(path)
    files = filter(lambda x: os.path.isfile(os.path.join(path,x)), files)
    
    clean = map(__removePunc, files)
    
    cleanFiles = dict(izip(clean, files))
    cleanFiles = orderedDictSort(cleanFiles)
        
    for f, n in izip(cleanFiles.iterkeys(), names):
        fileName = cleanFiles[f]
        _, ext   = os.path.splitext(f)
        newName  = str(n) + ext

        if ext not in _VIDEO_EXTS:
            continue

        fileName = os.path.join(path, fileName)
        newName  = os.path.join(path, newName)

        print ("OLD: {0}".format(os.path.split(fileName)[1]))
        print ("NEW: {0}".format(os.path.split(newName)[1]))
        print ""
                
        if not testRun: 
            os.rename(fileName, newName)

def __removePunc(title):
    '''Remove any punctuation and whitespace from the title'''
    name, ext = os.path.splitext(title)
    exclude = set('!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~')
    name = ''.join(ch for ch in name if ch not in exclude)
    return name+ext

def orderedDictSort(dictionary):
    ''' "Sorts" a dictionary by sorting keys then adding them
    into an ordered dict object'''
    keys = dictionary.keys()
    keys.sort()
    return OrderedDict(zip(keys, map(dictionary.get, keys)))


       
                



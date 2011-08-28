# output display format, season is padded with zeros
# Season - Episode Number - Episode Title
# -*- encoding: utf-8 -*-
import re
import urllib2
import os
from collections import OrderedDict
from itertools import izip

_DISPLAY = u"Season {0} - Episode {1} - {2}"


_VIDEO_EXTS = set( ['.mkv', '.ogm', '.asf', '.asx', '.avi', '.flv',
                    '.mov', '.mp4', '.mpg', '.rm',  '.swf', '.vob',
                    '.wmv', '.mpeg'])

regex = re.compile(r"<.*?>", re.I | re.X)

class Episode(object):
    ''' A simple class to organize the episodes, an alternative would be
        to use a namedtuple though this is easier '''
    def __init__(self, series, title, epNumber, season):
        self.series = encode(series)
        self.title = encode(title)
        self.season = season
        self.episode = epNumber
        
    def display(self):
        s = self.season
        e = self.episode
        t = self.title
        d = _DISPLAY.format(s,e,t)
        d.encode('utf-8', 'backslashreplace')
        return d

def printFormat(fmt, eps):
    tokens = regex.findall(fmt)
    argCount = 0

    # Iterate through the tokens and check to see if the episode has the
    # attribute we are trying to substitute
    for token in tokens:
        if hasattr(eps[0], token[1:-1]):
            fmt = fmt.replace( token, "{{{0}}}".format(argCount) )
            argCount += 1

    # Print the episode information according to the format
    for e in eps:
        args = ()
        for token in tokens:
            args += (getattr(e, token[1:-1]),)
        print fmt.format(*args)
            
                
def prepareTitle(title):
    '''Remove any punctuation and whitespace from the title'''
    title = removePunc(title).split()
    if title[0] == 'the': 
        title.remove('the')
    return ''.join(title)

def encode(text, encoding='utf-8'):
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
    

def renameFiles( path=None, episodes = None):
    '''
    We will sort dictionary with respect to key value by
    removing all punctuation then adding each entry into
    a ordered dictionary to preserve sorted order.  We do
    this to insure the file list is in somewhat of a natural
    ordering, otherwise we will have misnamed files
    '''

    global _VIDEO_EXTS
    
    files = os.listdir(path)
    renamedFiles = []

    # Filter out anything that doesnt have the correct extenstion and
    # filter out any directories
    files = filter(lambda x: os.path.isfile(os.path.join(path,x)), files)
    files = filter(lambda x: os.path.splitext(x)[1].lower() in _VIDEO_EXTS, files)
    
    clean = [removePunc(f) for f in files]
    
    cleanFiles = dict(izip(clean, files))
    cleanFiles = orderedDictSort(cleanFiles)
        
    for f, n in izip(cleanFiles.iterkeys(), episodes):
        fileName = cleanFiles[f]
        _, ext   = os.path.splitext(f)
        newName  = n.display() + ext
        newName  = removeInvalidPathChars(newName)

        fileName = os.path.join(path, fileName)
        newName  = os.path.join(path, newName)

        print ("OLD: {0}".format(os.path.split(fileName)[1]))
        print ("NEW: {0}".format(os.path.split(newName)[1]))
        print ""

        renamedFiles.append( (fileName, newName,) )
                

    resp = raw_input("\nDo you wish to rename these files [y|N]: ").lower()

    if resp.startswith('y'):
        for old, new in renamedFiles:
            os.rename(old, new)
    else:
        print "Changes were not commited to the files"

def removePunc(title):
    '''Remove any punctuation and whitespace from the title'''
    name, ext = os.path.splitext(title)
    exclude = set('!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~')
    name = ''.join(ch for ch in name if ch not in exclude)
    return name+ext

def removeInvalidPathChars(path):
    dir, file = os.path.split(path)
    exclude = set('"?<>/\\|*:')
    file = ''.join(ch for ch in file if ch not in exclude)
    return os.path.join(dir,file)

def orderedDictSort(dictionary):
    ''' "Sorts" a dictionary by sorting keys then adding them
    into an ordered dict object'''
    keys = dictionary.keys()
    keys.sort()
    return OrderedDict(izip(keys, [dictionary[k] for k in keys]))


       
            

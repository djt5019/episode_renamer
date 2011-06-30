# output display format, season is padded with zeros
# Season - Episode Number - Episode Title

import urllib2

_DISPLAY = "Season {0} - Episode {1} - {2}".decode('utf-8')

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
    exclude = set('!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~')
    title = ''.join(ch for ch in title if ch not in exclude)
    title = title.split()
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
    

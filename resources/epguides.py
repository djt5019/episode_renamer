import re as _re
import urllib2 as _urllib2
from contextlib import closing as _closing

from Utils import *

_pattern = r"""
            ^		            # Start of the string
            (?:[\s]*?[\d]*\.?)	    # Number on list
            [\s]{2,}		    # Ignore whitespace
            (?P<season>[\d]*)	    # Season number
            -			    # Separator
            [\s]*		    # Optional whitespace
            (?P<episode>[\d]*)	    # Episode number
            [\s]{2,}		    # Whitespace
            (?P<product>.+|)	    # Product number
            [\s]{2,}		    # Whitespace
            (?P<airdate>[\w\s/]*?)  # Air-date
            [\s]{2,}		    # Ignore whitespace
            (?P<name>.*)	    # Episode name
            $			    # End of line
            """


    
def poll(title):
    title = prepareTitle(title)
    episodes = []
    regex = _re.compile(_pattern, _re.X|_re.I )
    url = "http://www.epguides.com/{0}".format(title)
    fd  = getURLdescriptor(url)

    if fd is None: return []

    with _closing( fd ) as request:
        if request.getcode() == 200:
            data = request.readlines()
        else: return []
    
    for line in data:
        info = regex.match(line)
        if info is not None:
            name = info.group('name')
            episode = info.group('episode')
            season = int(info.group('season'))
            name = _re.sub('<.*?>', '', name).strip()               

            episodes.append( _Episode(name, episode, season) )
            
    return episodes

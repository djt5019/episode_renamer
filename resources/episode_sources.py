import epguides
import tvdb

__modules = [ epguides, tvdb ]

def locate_show(title, verbose=False):
    episodes = []
    
    for source in __modules:
        if verbose: print "Polling {0}".format(source)
        episodes = source.poll(title)
        if episodes:
            if verbose: print "Located {0}".format(title)
            break
        if verbose: print "Failed to locate {0} at {1}".format(title, source)
        
    return episodes

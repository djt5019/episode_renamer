import tvdb
import epguides

__modules = [tvdb, epguides]

def locate_show(title, verbose=False):
    episodes = []
    
    for source in __modules:
        if verbose: print "\nPolling {0}".format(source.__name__)
        episodes = source.poll(title)
        if episodes:
            if verbose: print "LOCATED {0}\n".format(title)
            break
        if verbose: print "FAILED to locate {0} at {1}\n".format(title, source.__name__)
        
    return episodes

# -*- coding: utf-8 -*-
# author:  Dan Tracy
# program: poll_sources.py

import sys

from os import listdir

from Utils import WEBSOURCESPATH
from Episode import get_logger

def locate_show(title):
    """Polls the web sources looking for the show"""
    episodes = []
    modules = []

    sys.path.append(WEBSOURCESPATH)
    ## This will import all the modules within the web_sources directory so that we
    ## can easily plug in new sources for finding episode information
    mods = filter( lambda x: x.endswith('py') and not x.startswith('__'),  listdir(WEBSOURCESPATH))
    
    for m in mods:
        get_logger().info("Importing web resource {}".format(m[:-3]))
        x =  __import__(m[:-3]) 
        modules.append(x)
        
    #If the modules have a poll priority we will respect it by sorting the list by priority
    if all( hasattr(x, 'priority') for x in modules ):
        modules = sorted(modules, key=lambda x: x.priority, reverse=True)
    
    get_logger().info("Searching for {}".format(title))
    
    for source in modules:
        get_logger().info( "Polling {0}".format(source.__name__) )
            
        episodes = source.poll(title)
        
        if episodes:
            get_logger().info( "LOCATED {0}".format(title) )
            break
        get_logger().info( "Unable to locate {0} at {1}".format(title, source.__name__) )

    if not episodes:
        get_logger().info("Unable to locate the show: " + title)
        return []
        
    return filter(lambda x: x.episodeNumber > 0, episodes).sort(key = lambda x: x.episodeCount)
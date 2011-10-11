#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author:  Dan Tracy
# program: eplist.py

''' 
This command line program will take a T.V. show as input and
will return information about each episode, such as the title
season and number.  I use this program to help clean up my
TV show collection.  After the show has been found online it 
will be entered into a local databse, provided sqlite3 is available,
for faster lookup in the future.  You are able to filter the shows
by season along with other options on the command line interface.
'''

import argparse
import os

import EpParser.src.Utils as Utils
from EpParser.src.Parser import EpParser as Parser
from EpParser.src.Cache import Cache

def main():    
    ''' Our main function for our command line interface'''
    cmd = argparse.ArgumentParser(description="TV Show Information Parser")

    cmd.add_argument('title', 
        help="The title of the show")
    
    cmd.add_argument('-d', '--display-header', action="store_true", 
        help="Display the header at the top of the output")
    
    cmd.add_argument('-v', '--verbose', action="store_true", 
        help="Be verbose, enable additional output")
    
    cmd.add_argument('-s', '--season', default=-1, type=int, metavar='n', 
        help="The specific season to search for")
    
    cmd.add_argument('-r', '--rename', dest='pathname', metavar='p',
        help="Rename the files in the path provided, a confirmation is required")

    cmd.add_argument('-f', '--format', dest="format", metavar='s',
        help="Rename the files in a directory with a custom format")
        
    cmd.add_argument('-g', '--gui-enabled', action="store_true",
        help="Use the gui rather than the command line, preempts all other switches except the format switch")
    
    namespace = cmd.parse_args()
    verbose   = namespace.verbose
    title     = namespace.title
    season    = namespace.season
    pathname  = namespace.pathname
    display   = namespace.display_header
    formatStr = namespace.format
    useGui    = namespace.gui_enabled
    
    if useGui:
        import EpParser.gui.gui as gui
        exit(gui.main())
    
    rename = pathname is not None

    if rename and not os.path.exists(pathname):
        exit("ERROR - Path provided does not exist")

    cache = Cache( verbose=verbose )
    episodeParser = Parser(title, cache, verbose=verbose)
    episodeParser.show.formatter.setFormat( formatStr )
    show = episodeParser.parseData()
    
    if show.episodeList == []:
        return
    
    # If the user specified a specific season we will filter our results
    # this also checks to make sure its a reasonable season number
    if 0 < season <= show.episodeList[-1].season:
        show.episodeList = [ x for x in show.episodeList if x.season == season ]

    if rename:
        Utils.renameFiles(pathname, show)
        return

    if display or verbose:
        print "\nShow: {0}".format(title)
        print "Number of episodes: {0}".format(len(show.episodeList))
        print "Number of seasons: {0}".format( show.episodeList[-1].season )
        print "-" * 30
    
    currSeason = show.episodeList[0].season
    for eps in show.episodeList:
        if currSeason != eps.season and display:
            print "\nSeason {0}".format(eps.season)
            print "----------"
            
        print show.formatter.display( eps )
        currSeason = eps.season


if __name__ == '__main__':
    main()    

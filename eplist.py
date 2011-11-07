#!/usr/bin/env python
<<<<<<< Updated upstream
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
    
    cmd.add_argument('-s', '--season', default="", type=str,
        help="The specific season to search for")
    
    cmd.add_argument('-r', '--rename', dest='pathname',
        help="Rename the files in the path provided")
    
    cmd.add_argument('-f', '--format', dest="format",
        help="Rename the files in a directory with a custom format")
        
    cmd.add_argument('-g', '--gui-enabled', action="store_true",
        help="Use the gui rather than the command line, preempts all other switches except the format switch")
        
    args = cmd.parse_args()
    if args.verbose:
        from logging import StreamHandler, NOTSET
        for handle in Utils.logger.handlers:
            if isinstance(handle, StreamHandler):
                handle.setLevel(NOTSET)
                break
    
    if args.gui_enabled:
        import EpParser.gui.gui as gui
        exit(gui.main())
    
    rename = args.pathname is not None
    
    if rename and not os.path.exists(args.pathname):
        exit("ERROR - Path provided does not exist")

    cache = Cache()
    episodeParser = Parser(args.title, cache)
    episodeParser.setFormat( args.format )
    show = episodeParser.getShow()
    
    if show.episodeList == []:
        exit(1)
    
    # If the user specified a specific season we will filter our results
=======
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
    
    cmd.add_argument('-s', '--season', default="", type=str,
        help="The specific season to search for")
    
    cmd.add_argument('-r', '--rename', dest='pathname',
        help="Rename the files in the path provided")
    
    cmd.add_argument('-f', '--format', dest="format",
        help="Rename the files in a directory with a custom format")
        
    cmd.add_argument('-g', '--gui-enabled', action="store_true",
        help="Use the gui rather than the command line, preempts all other switches except the format switch")
        
    args = cmd.parse_args()
    if args.verbose:
        from logging import NOTSET
        for handle in Utils.getLogger().handlers:
            handle.setLevel(NOTSET)
    
    if args.gui_enabled:
        import EpParser.gui.gui as gui
        exit(gui.main())
    
    rename = args.pathname is not None
    
    if rename and not os.path.exists(args.pathname):
        exit("ERROR - Path provided does not exist")

    cache = Cache()
    episodeParser = Parser(args.title, cache)
    episodeParser.setFormat( args.format )
    show = episodeParser.getShow()
    
    if show.episodeList == []:
        exit(1)
    
    # If the user specified a specific season we will filter our results
>>>>>>> Stashed changes
    # this also checks to make sure its a reasonable season number
    if args.season:
        if '-' in args.season:
            high, low = args.season.split('-')
            high = int(high)
            low = int(low)
        else:
            high = low = int(args.season)
        
        high = min(high, show.episodeList[-1].season)
        low = max(low, 1)
        
        if low > high: low, high = high, low
        
        seasonRange = xrange( low, high+1 )
<<<<<<< Updated upstream
        print seasonRange
        show.episodeList = [x for x in show.episodeList if x.season in seasonRange]
        
    if rename:
        eps = [ show.formatter.display(x) for x in show.episodeList ]
        eps = Utils.renameFiles(args.pathname, eps)
        for old, new in eps: 
            print (u"OLD: {0}".format( os.path.split(old)[1]))
            print (u"NEW: {0}".format( os.path.split(new)[1]))
            print ""
        Utils.doRename(eps)
        exit(0)

    if args.display_header or args.verbose:
        print "\nShow: {0}".format(args.title)
        print "Number of episodes: {0}".format(len(show.episodeList))
        print "Number of seasons: {0}".format(show.episodeList[-1].season)
        print "-" * 30
        
    
    curr_season = show.episodeList[0].season
    for eps in show.episodeList:
        if curr_season != eps.season and args.display_header:
            print "\nSeason {0}".format(eps.season)
            print "----------"
    
        print show.formatter.display( eps )
        curr_season = eps.season
        

if __name__ == '__main__':
    main()

=======
        show.episodeList = [x for x in show.episodeList if x.season in seasonRange]
        
    if rename:
        eps = [ show.formatter.display(x) for x in show.episodeList ]
        eps = Utils.renameFiles(args.pathname, eps)
        for old, new in eps: 
            print (u"OLD: {0}".format( os.path.split(old)[1]))
            print (u"NEW: {0}".format( os.path.split(new)[1]))
            print ""
        Utils.doRename(eps)
        exit(0)

    if args.display_header or args.verbose:
        print "\nShow: {0}".format(args.title)
        print "Number of episodes: {0}".format(len(show.episodeList))
        print "Number of seasons: {0}".format(show.episodeList[-1].season)
        print "-" * 30
        
    
    curr_season = show.episodeList[0].season
    for eps in show.episodeList:
        if curr_season != eps.season and args.display_header:
            print "\nSeason {0}".format(eps.season)
            print "----------"
    
        print show.formatter.display( eps )
        curr_season = eps.season
        

if __name__ == '__main__':
    main()
>>>>>>> Stashed changes

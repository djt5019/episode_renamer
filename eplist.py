#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__='Dan Tracy'
__email__='djt5019 at gmail dot com'

# This command line program will take a T.V. show as input and
# will return information about each episode, such as the title
# season and number.  I use this program to help clean up my
# TV show collection.  After the show has been found online it
# will be entered into a local database, provided sqlite3 is available,
# for faster lookup in the future.  You are able to filter the shows
# by season along with other options on the command line interface.
# You can also rename files according to a format that you choose as
# well as calculate the CRC32 of a file.  If you mistakenly rename
# files you have the option to revert the last renaming operation

import argparse
import os
import sys

import EpParser.src.Utils as Utils
import EpParser.src.Episode as Episode

from EpParser.src.Parser import EpParser as Parser
from EpParser.src.Cache import Cache
from EpParser.src.Logger import get_logger
from EpParser.src.Settings import Settings

def main():
    if '-u' in sys.argv or '--undo-rename' in sys.argv:
        files = Utils.load_last_renamed_files()
        print_renamed_files(files)
        errors = Utils.rename(files)
        if not errors:
            print "All files were successfully renamed"
        exit(0)

    cmd = argparse.ArgumentParser(description="Renames your TV shows",
                                  prog='eplist', usage='%(prog)s [options] title')

    cmd.add_argument('title',
        help="The title of the show")

    cmd.add_argument('-d', '--display-header', action="store_true",
        help="Display the header at the top of the output")

    cmd.add_argument('-v', '--verbose', action="store_true",
        help="Be verbose, enable additional output")

    cmd.add_argument('-s', '--season', default="", type=str, metavar='N',
        help="The specific season range to search for. Ex: 1-3")
    
    cmd.add_argument('-e', '--episode', default="", type=str, metavar='N',
        help="The specific episode range to search for Ex: 15-30")

    cmd.add_argument('-f', '--format', dest="format", metavar='F',
        help="Rename the files in a directory with a custom format")

    cmd.add_argument('-g', '--gui-enabled', action="store_true",
        help="Use the gui rather than the command line")

    group = cmd.add_mutually_exclusive_group()

    group.add_argument('-r', '--rename', dest='pathname', metavar="PATH",
        help="Rename the files in the path provided")

    group.add_argument('-u', '--undo-rename', action='store_true',
        help="Undo the last rename operation")

    args = cmd.parse_args()
    
    if args.verbose:
        from logging import NOTSET
        for handle in get_logger().handlers:
            handle.setLevel(NOTSET)

    if args.gui_enabled:
        import EpParser.gui.gui as gui
        exit(gui.main())

    rename = args.pathname is not None

    if rename and not os.path.exists(args.pathname):
        exit("ERROR - Path provided does not exist")

    cache = Cache(Settings['db_name'])
    episodeParser = Parser(args.title, cache)

    show = episodeParser.getShow()
    formatter = Episode.EpisodeFormatter(show, args.format)
    formatter.load_format_config()
    show.formatter = formatter

    if not show.episodeList:
        exit(1)

    # If the user specified a specific season we will filter our results
    # this also checks to make sure its a reasonable season number
    if args.season:
        seasonRange = list(parse_range(args.season))
        if seasonRange[-1] <= show.numSeasons:
            show.episodeList = [x for x in show.episodeList if x.season in seasonRange]
        
    if args.episode:
        episodeRange = list(parse_range(args.episode))

        if not args.season:
            show.episodeList = [x for x in show.episodeList if x.episodeCount in episodeRange]
        else:
            show.episodeList = [x for x in show.episodeList if x.episodeNumber in episodeRange]

    if  rename:
        files = Utils.rename_files(args.pathname, show)
        print_renamed_files(files)
        errors = Utils.rename(files)
        if not errors:
            print "All files were successfully renamed"

        exit(0)

    if args.display_header or args.verbose:
        print "\nShow: {0}".format(args.title)
        print "Number of episodes: {0}".format(len(show.episodeList))
        print "Number of seasons: {0}".format(show.episodeList[-1].season)
        print "-" * 30

    print ""
    curr_season = show.episodeList[0].season
    for eps in show.episodeList:
        if curr_season != eps.season and args.display_header:
            print "\nSeason {0}".format(eps.season)
            print "----------"

        print show.formatter.display(eps).encode('ascii','replace')
        curr_season = eps.season


def print_renamed_files(files):
    if not files:
        print "Failed to find any files to rename"
        exit(1)

    p = os.path.dirname(files[0][0])
    print "PATH = {}".format(p)
    print "-------" + '-'*len(p)

    for old, new in files:
        print (u"OLD: {0}".format(os.path.split(old)[1]).encode('ascii','replace'))
        print (u"NEW: {0}".format(os.path.split(new)[1]).encode('ascii','replace'))
        print


def parse_range(range):
    if '-' in range:
        high, low = range.split('-')
        high = int(high)
        low = int(low)
    else:
        high = low = int(range)

    low = max(low, 1)

    if low > high:
        low, high = high, low

    return xrange(low, high + 1)

if __name__ == '__main__':
    main()

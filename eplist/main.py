#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

__author__ = 'Dan Tracy'
__email__ = 'djt5019 at gmail dot com'

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
import logging

from eplist import utils
from eplist import episode

from eplist.cache import Cache
from eplist.show_finder import Parser
from eplist.settings import Settings


def main():
    cmd = argparse.ArgumentParser(description="Renames your TV shows",
                        prog='eplist', usage='%(prog)s --help [options] title')

    cmd.add_argument('title', default="", nargs='?',
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

    cmd.add_argument('--delete-cache', action="store_true",
        help="Delete the cache file and create a new one")

    cmd.add_argument('--update-db', action="store_true",
        help="Update the AniDB titles file, limit to once a day due to size")

    cmd.add_argument('--verify', action="store_true",
        help="Verify the checksums in the filename if they are present")

    cmd.add_argument('--filter', choices=['episodes', 'specials', 'both'],
        help="Filters episodes based on type (default=both)")

    args = cmd.parse_args()

    if 'title' in args:
        Settings['title'] = args.title
    else:
        Settings['title'] = ""

    # Set the correct working path
    if args.pathname:
        Settings['path'] = os.path.realpath(args.pathname)
    else:
        Settings['path'] = os.path.realpath(os.getcwd())

    # If we are acting on files then load the old names into memory
    if args.pathname or args.undo_rename:
        utils.load_renamed_file()

    if args.filter:
        Settings['filter'] = args.filter

    cache = Cache(Settings['db_name'])
    if args.delete_cache:
        cache.recreate_cache()

    if args.title in ('-', '.', 'pwd'):
        # If a dash is entered use the current basename of the path
        args.title = os.path.split(os.getcwd())[1]
        print ("Searching for {}".format(args.title))

    if args.verbose:
        Settings['verbose'] = True
        l = logging.getLogger()
        for handle in l.handlers:
            handle.setLevel(logging.NOTSET)
        l.setLevel(logging.NOTSET)

    if args.gui_enabled:
        import episode_renamer.gui.gui as gui
        exit(gui.main())

    if args.update_db:
        utils.update_db()

    if args.undo_rename:
        file_dict = utils.find_old_filenames(Settings['path'], args.title)
        files = file_dict['file_list']
        print_renamed_files(files)
        old_order, errors = utils.rename(files)

        utils.save_renamed_file_info(old_order, Settings['title'])

        for e in errors:
            print("File {} could not be successfully renamed".format(os.path.split(e)[1]))

        sys.exit(0)

    rename = args.pathname is not None

    if rename and not os.path.exists(args.pathname):
        sys.exit("ERROR - Path provided does not exist")

    if not args.title:
        cmd.print_usage()
        sys.exit(1)

    episodeParser = Parser(args.title, cache)

    show = episodeParser.getShow()
    formatter = episode.EpisodeFormatter(show, args.format)
    show.formatter = formatter

    if not show.episodes:
        sys.exit(1)

    # If the user specified a specific season we will filter our results
    # this also checks to make sure its a reasonable season number
    filtered_episodes = []
    if args.season:
        s_range = list(parse_range(args.season))
        if s_range[-1] > show.num_seasons:
            print ("{} Season {} not found".format(args.title, args.season))
            sys.exit(1)
        filtered_episodes = [x for x in show.episodes if x.season in s_range]

    if args.episode:
        e_range = list(parse_range(args.episode))

        if not args.season:
            filtered_episodes = [x for x in show.episodes if x.episode_count in e_range]
        else:
            filtered_episodes = filtered_episodes[e_range[0] - 1:e_range[-1]]

    ## Renaming functionality
    if  rename:
        path = args.pathname if args.pathname != '.' else os.getcwd()
        utils.prepare_filenames(path, show)
        files = []

        if filtered_episodes:
            episodes = filtered_episodes
        else:
            episodes = show.episodes

        episodes += show.specials if Settings['filter'] in ('both', 'specials') else []

        for e in episodes:
            if e.episode_file and e.episode_file.new_name:
                old = os.path.join(path, e.episode_file.name)
                new = os.path.join(path, e.episode_file.new_name)
                files.append((old, new))

        print_renamed_files(files)
        old_order, errors = utils.rename(files)

        utils.save_renamed_file_info(old_order, Settings['title'])

        if not errors:
            print ("All files were successfully renamed")

        for e in errors:
            print("File {} could not be successfully renamed".format(os.path.split(e)[1]))
        sys.exit(0)

    print ""

    if args.verify:
        verify_files(show)
        exit(1)

    if Settings['filter'] in ('both', 'episodes'):
        if filtered_episodes:
            display_episodes(show, filtered_episodes, args.display_header)
        else:
            display_episodes(show, show.episodes, args.display_header)

    if Settings['filter'] in ('specials', 'both'):
        display_specials(show, args.display_header)


def display_episodes(show, episodes, header=False):
    if header:
        print ("\nShow: {0}".format(show.title))
        print ("Number of episodes: {0}".format(len(show.episodes)))
        print ("Number of specials: {0}".format(len(show.specials)))
        print ("Number of seasons: {0}".format(show.episodes[-1].season))
        print ("-" * 30)

    curr_season = episodes[0].season
    for eps in episodes:
        if curr_season != eps.season and header:
            print ("\nSeason {0}".format(eps.season))
            print ("----------")

        print (show.formatter.display(eps).encode(Settings['encoding'], 'ignore'))
        curr_season = eps.season


def display_specials(show, header=False):
    if header:
        print ("\nSpecials")
        print ("---------")

    for eps in show.specials:
        print (show.formatter.display(eps).encode(Settings['encoding'], 'ignore'))


def verify_files(show):
    if not show:
        return()

    episode_files = show.episodes
    path = Settings.get('path', os.getcwd())
    if not all([e.episode_file for e in episode_files]):
        utils.prepare_filenames(path, show)

    for f in episode_files:
        if not f.episode_file:
            continue

        ep_file = f.episode_file

        if ep_file.given_checksum <= 0:
            print("Episode {} dosen't have a checksum to compare to".format(ep_file.name))
            continue

        if ep_file.verify_integrity():
            print("Episode {} has passed verification".format(ep_file.name))
        else:
            print("Episode {} has failed verification".format(ep_file.name))


def print_renamed_files(files):
    if not files:
        print ("Failed to find any files to rename")
        sys.exit(1)

    p = os.path.dirname(files[0][0])
    print ("PATH = {}".format(p))
    print ("-------" + '-' * len(p))

    for old, new in files:
        print (u"OLD: {0}".format(os.path.split(old)[1]).encode(Settings['encoding'], 'ignore'))
        print (u"NEW: {0}".format(os.path.split(new)[1]).encode(Settings['encoding'], 'ignore'))
        print


def parse_range(range):
    if '-' in range:
        high, low = range.split('-')
        high = int(high)
        low = int(low)
    else:
        high = low = int(range)

    low = max(low, 1)
    high = max(high, 1)

    if low > high:
        low, high = high, low

    return xrange(low, high + 1)


if __name__ == '__main__':
    main()

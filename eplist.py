#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

from episode_parser import Utils
from episode_parser import Episode
from episode_parser import Constants

from episode_parser.Logger import get_logger
from episode_parser.Cache import Cache
from episode_parser.Parser import Parser
from episode_parser.Settings import Settings


def main():
    cmd = argparse.ArgumentParser(description="Renames your TV shows",
                                  prog='eplist', usage='%(prog)s [options] title')

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
        help="Update the AniDB titles file, limit this to once a day since it's large")

    cmd.add_argument('--generate-settings', action="store_true",
        help="Recreate the default config file to resources folder, settings.conf")

    cmd.add_argument('--generate-tags', action="store_true",
        help="Recreate the default tag settings for the formatter")

    cmd.add_argument('--verify', action="store_true",
        help="Verify the checksums in the filename if they are present")

    args = cmd.parse_args()

    if args.generate_settings:
        generate_default_config()

    if args.generate_tags:
        generate_default_tags()

    if args.delete_cache:
        try:
            os.remove(os.path.join(Constants.RESOURCE_PATH, Settings['db_name']))
        except Exception as e:
            get_logger().warning(e)
            exit(1)

    if args.title in ('-', '.', 'pwd'):
        args.title = os.path.split(os.getcwd())[1]  # If a dash is entered use the current basename of the path
        print "Searching for {}".format(args.title)

    Settings['verbose'] = False

    if args.verbose:
        Settings['verbose'] = True
        from logging import NOTSET
        for handle in get_logger().handlers:
            handle.setLevel(NOTSET)

    if args.gui_enabled:
        import episode_parser.gui.gui as gui
        exit(gui.main())

    if args.update_db:
        update_db()

    if args.undo_rename:
        files = Utils.load_last_renamed_files()
        print_renamed_files(files)
        errors = Utils.rename(files)
        if not errors:
            print "All files were successfully renamed"
        exit(0)

    Settings['path'] = args.pathname
    rename = args.pathname is not None

    if rename and not os.path.exists(args.pathname):
        exit("ERROR - Path provided does not exist")

    if not args.title:
        cmd.print_usage()
        exit(1)

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
        else:
            print "{} Season {} not found".format(args.title, args.season)
            exit(1)

    if args.episode:
        episodeRange = list(parse_range(args.episode))

        if not args.season:
            show.episodeList = [x for x in show.episodeList if x.episodeCount in episodeRange]
        else:
            show.episodeList = show.episodeList[episodeRange[0] - 1:episodeRange[-1]]

    if  rename:
        path = args.pathname if args.pathname != '.' else os.getcwd()
        Utils.prepare_filenames(path, show)
        files = []
        for e in show.episodeList + show.specialsList:
            if e.episode_file and e.episode_file.new_name:
                old = os.path.join(path, e.episode_file.name)
                new = os.path.join(path, e.episode_file.new_name)
                files.append((old, new))

        print_renamed_files(files)
        errors = Utils.rename(files)
        if not errors:
            print "All files were successfully renamed"

        exit(0)

    if args.display_header or args.verbose:
        print "\nShow: {0}".format(args.title)
        print "Number of episodes: {0}".format(len(show.episodeList))
        print "Number of specials: {0}".format(len(show.specialsList))
        print "Number of seasons: {0}".format(show.episodeList[-1].season)
        print "-" * 30

    print ""
    curr_season = show.episodeList[0].season
    for eps in show.episodeList:
        if curr_season != eps.season and args.display_header:
            print "\nSeason {0}".format(eps.season)
            print "----------"

        print show.formatter.display(eps).encode(sys.getdefaultencoding(), 'ignore')
        curr_season = eps.season

    if args.display_header:
        print "\nSpecials"
        print "---------"

    for eps in show.specialsList:
        print show.formatter.display(eps).encode(sys.getdefaultencoding(), 'ignore')

    if args.verify:
        verify_files(show)


def update_db():
        one_unix_day = 24 * 60 * 60

        def _download():
            with Utils.open_file_in_resources(Settings['anidb_db_file'], 'w') as f:
                get_logger().info("Retrieving AniDB Database file")
                url = Utils.get_url_descriptor(Settings['anidb_db_url'])

                f.write(url.content)
            get_logger().info("Successfully downloaded the new database")

        if not Utils.file_exists_in_resources(Settings['anidb_db_file']):
            _download()
        elif Utils.able_to_poll('db_download', one_unix_day):
            _download()
        else:
            get_logger().error("Attempting to download the database file multiple times today")


def verify_files(show):
    if not show:
        return

    episode_files = show.episodeList
    path = Settings.get('path', os.getcwd())
    if not all([e.episode_file for e in episode_files]):
        Utils.prepare_filenames(path, show)

    for f in episode_files:
        if not f.episode_file:
            continue

        ep_file = f.episode_file

        if ep_file.given_checksum < 0:
            get_logger().warn("Episode {} dosen't have a checksum to compare to".format(ep_file.name))
            continue

        if ep_file.verify_integrity():
            print("Episode {} has passed verification".format(ep_file.name))
        else:
            print("Episode {} has failed verification".format(ep_file.name))


def print_renamed_files(files):
    if not files:
        print "Failed to find any files to rename"
        exit(1)

    p = os.path.dirname(files[0][0])
    print "PATH = {}".format(p)
    print "-------" + '-' * len(p)

    for old, new in files:
        print (u"OLD: {0}".format(os.path.split(old)[1]).encode(sys.getdefaultencoding(), 'ignore'))
        print (u"NEW: {0}".format(os.path.split(new)[1]).encode(sys.getdefaultencoding(), 'ignore'))
        print


def generate_default_config():
    Utils.write_config(Constants.DEFAULT_SETTINGS_STRING, 'settings.conf')


def generate_default_tags():
    Utils.write_config(Constants.DEFAULT_TAG_STRING, Settings['tag_config'])


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
    if not Utils.file_exists_in_resources('settings.conf'):
        get_logger().warning("Settings not found, creating a new one")
        generate_default_config()

    main()

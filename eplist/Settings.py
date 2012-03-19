# -*- coding: utf-8 -*-
from __future__ import unicode_literals

__author__ = 'Dan Tracy'
__email__ = 'djt5019 at gmail dot com'

import logging

from os.path import realpath
from sys import getdefaultencoding

config = {
    ## Filter to output episodes, specials, or both (both is default)
    'filter': 'both',

    ## Your TvDB api key, required to poll their website
    'tvdb_key': None,

    # Logger output files
    'log_file': 'output.log',

    ## Database file for our episodes
    'db_name': 'episodes.db',

    ## Days to wait to update the show within the database
    'db_update': 7,

    ## Where to store the old filenames from the last rename operation
    'rename_backup': 'last_rename.json',

    ## File to store the access times data
    'access_time_file': 'last_access.json',
    'access_dict': {},

    ## Time in seconds between polling a website, recommended is 2
    'poll_delay': 2,

    ## AniDB flat file with the ids of the shows visit link below for updated version from time to time
    ## http://anidb.net/api/animetitles.dat.gz
    'anidb_db_file': 'animetitles.dat',
    'anidb_db_url': 'http://anidb.net/api/animetitles.dat.gz',
    'anidb_username': None,
    'anidb_password': None,

    ## Verbose output
    'verbose': False,

    ## System encoding, windows command line can't handle utf-8
    'encoding': getdefaultencoding(),

    ## Default Format string
    'format': "<series> - <type> <count:pad> - <title>",

    ## Tag options
    'tag_config': 'tags.cfg',
    'tag_start': '<',
    'tag_end': '>',
    'tags': ['episode_name_tags', 'episode_number_tags', 'episode_count_tags', 'series_name_tags', 'season_number_tags', 'hash_tags', 'type_tags'],

    'episode_name_tags': ['name', 'episode', 'title'],
    'episode_number_tags': ['epnum', 'number', 'num'],
    'episode_count_tags': ['count', 'ep'],
    'series_name_tags': ['series', 'show'],
    'season_number_tags': ['season', 'seasons'],
    'hash_tags': ['hash', 'crc32', 'checksum'],
    'type_tags': ['type', 'format'],

    ## The current working directory
    'path': realpath('.'),

    }


class SettingsDict(dict):
    def __init__(self, *args, **kwargs):
        super(SettingsDict, self).__init__(*args, **kwargs)

    def __getitem__(self, item):
        val = dict.get(self, item)

        if val is None:
            logging.error("Setting {} not present in config file".format(item))
            raise KeyError("Setting: {} not present in config file".format(item))
        else:
            return val

Settings = SettingsDict(config)

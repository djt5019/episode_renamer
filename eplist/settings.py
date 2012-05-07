# -*- coding: utf-8 -*-
"""
The settings module is just a simple dictionary.  While the program
is running more settings will be added or modified.  To edit the defaults
just change the entries below.
"""

from __future__ import unicode_literals

from eplist.constants import resource_path, AttributeDict
from sys import getdefaultencoding, version_info


Settings = AttributeDict({
    ## Filter to output episodes, specials, or both (both is default)
    'filter': 'both',

    ## Your TvDB api key, required to poll their website
    ## grab on at http://thetvdb.com/?tab=apiregister
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

    ## AniDB flat file with the ids of the shows
    ## http://anidb.net/api/animetitles.dat.gz
    'anidb_username': None,
    'anidb_password': None,
    'anidb_db_file': 'animetitles.dat',
    'anidb_db_url': 'http://anidb.net/api/animetitles.dat.gz',

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
    'tags': {
        'episode_name_tags': ['name', 'episode', 'title'],
        'episode_number_tags': ['epnum', 'number', 'num'],
        'episode_count_tags': ['count', 'ep'],
        'series_name_tags': ['series', 'show'],
        'season_number_tags': ['season', 'seasons'],
        'hash_tags': ['hash', 'crc32', 'checksum'],
        'type_tags': ['type', 'format']
    },


    ## The current working directory
    'path': resource_path,

    ## This is true if the current python distribution is py3k, Boolean
    'py3k': (version_info >= (3, 0))

})

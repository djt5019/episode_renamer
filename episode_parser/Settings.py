# -*- coding: utf-8 -*-
__author__ = 'Dan Tracy'
__email__ = 'djt5019 at gmail dot com'

from Exceptions import SettingsException


class SettingsDict(dict):
    def __init__(self, *args, **kwargs):
        super(SettingsDict, self).__init__()
        self.update(kwargs)

    def __getitem__(self, item):
        val = dict.get(self, item)

        if val is None:
            raise SettingsException("Setting: {} not present in config file".format(item))
        else:
            return val


Settings = SettingsDict(
    ## Your TvDB api key, required to poll their website
    {
    'tvdb_key': '',

    # Logger config files
    'log_config': 'logger.conf',
    'log_file': 'output.log',

    ## Database file for our episodes
    'db_name': 'episodes.db',

    ## Days to wait to update the show within the database
    'db_update': '7',

    ## Where to store the old filenames from the last rename operation
    'rename_backup': 'last_rename.dat',

    ## File to store the access times data
    'access_time_file': 'last_access.dat',
    'access_dict': {},

    ## Time in seconds between polling a website, reccomended is 2
    'poll_delay': '2',

    ## AniDB flat file with the ids of the shows visit link below for updated version from time to time
    ## http://anidb.net/api/animetitles.dat.gz
    'anidb_db_file': 'animetitles.dat',
    'anidb_db_url': 'http://anidb.net/api/animetitles.dat.gz',

    ## Tag options
    'tag_config': 'tags.cfg',
    'tag_start': '<',
    'tag_end': '>',
    }
)

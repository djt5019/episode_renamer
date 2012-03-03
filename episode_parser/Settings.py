# -*- coding: utf-8 -*-
__author__ = 'Dan Tracy'
__email__ = 'djt5019 at gmail dot com'

import os
import Constants

from Exceptions import SettingsException


class _SettingsDict(dict):
    def __init__(self):
        super(_SettingsDict, self).__init__()
        self.load_config()

    def __getitem__(self, item):
        val = dict.get(self, item)

        if val is None:
            raise SettingsException("Setting: {} not present in config file".format(item))
        else:
            return val

    def load_config(self):
        with open(os.path.join(Constants.RESOURCE_PATH, 'settings.conf')) as f:
            for number, line in enumerate(f):
                line = line.strip()

                if line.startswith('#') or line.startswith('//'):  # A comment in our config file
                    continue

                if '#' in line:
                    line = line.split('#')[0]

                if not line:  # We have read in a blank line from the config
                    continue

                options = [x.strip() for x in line.split('=')]

                if len(options) != 2:  # possibly an additional equals sign in the config
                    raise SettingsException("Line {} in the settings config contains an error".format(number))

                opt, value = options

                if value:
                    self[opt] = str(value)
                else:
                    self[opt] = None

Settings = _SettingsDict()


def generate_default_config():
    from textwrap import dedent
    config = dedent("""
            ## Your TvDB api key, required to poll their website
            tvdb_key = # your tvdb apikey


            ## Program logger options
            log_config = logger.conf
            log_file = output.log

            ## Database file for our episodes
            db_name = episodes.db

            ## Days to wait to update the show within the database
            db_update = 7

            ## Where to store the old filenames from the last rename operation
            rename_backup = last_rename.dat

            ## File to store the access times data
            access_time_file = last_access.dat

            ## Time in seconds between polling a website, reccomended is 2
            poll_delay = 2

            ## AniDB flat file with the ids of the shows visit link below for updated version from time to time
            ## http://anidb.net/api/animetitles.dat.gz
            anidb_db_file = animetitles.dat
            anidb_db_url = http://anidb.net/api/animetitles.dat.gz

            ## Tag options
            tag_config = tags.cfg
            tag_start = <
            tag_end = >
            """)

    with open(os.path.join(Constants.RESOURCE_PATH, 'settings.conf'), 'w') as f:
        f.write(config)

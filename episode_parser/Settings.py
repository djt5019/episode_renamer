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
        '''
        Load the default settings file
        '''
        config_loc = os.path.join(Constants.RESOURCE_PATH, 'settings.conf')

        ## If the settings aren't found use the default string in the constants
        ## module instead of exploding
        if not os.path.exists(config_loc):
            from cStringIO import StringIO
            from contextlib import closing
            config_loc = closing(StringIO(Constants.DEFAULT_SETTINGS_STRING))
        else:
            config_loc = open(config_loc, 'r')

        with config_loc as f:
            self._read_file(f)

    def _read_file(self, config):
        '''
        Performs the actual reading of the config into the dictionary
        '''
        for number, line in enumerate(config):
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

# -*- coding: utf-8 -*-
__author__='Dan Tracy'
__email__='djt5019 at gmail dot com'

import os
from EpParser.src import Constants

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
        with open( os.path.join(Constants.RESOURCE_PATH, 'settings.conf')) as f:
            for number, line in enumerate(f):
                line = line.strip()

                if line.startswith('#') or line.startswith('//'):  # A comment in our config file
                    continue

                if not line:  # We have read in a blank line from the config
                    continue

                options = [x.strip() for x in line.split('=')]

                if len(options) != 2:  # possibly an additional equals sign in the config
                    raise SettingsException("Line {} in the settings config contains an error".format(number))

                opt, value = options
                self[opt] = str(value)


class SettingsException(Exception):
    pass


Settings = _SettingsDict()


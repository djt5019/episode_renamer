# -*- coding: utf-8 -*-
from __future__ import unicode_literals

__author__ = 'Dan Tracy'
__email__ = 'djt5019 at gmail dot com'

import logging

from Exceptions import SettingsException
from resources.config import config


class SettingsDict(dict):
    def __init__(self, *args, **kwargs):
        super(SettingsDict, self).__init__(*args, **kwargs)

    def __getitem__(self, item):
        val = dict.get(self, item)

        if val is None:
            logging.error("Setting {} not present in config file".format(item))
            raise SettingsException("Setting: {} not present in config file".format(item))
        else:
            return val

Settings = SettingsDict(config)

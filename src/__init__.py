# -*- coding: utf-8 -*-
__author__ = 'Dan Tracy'
__email__ = 'djt5019 at gmail dot com'

import atexit
import Utils

from Settings import Settings

Settings['access_dict'] = {}
atexit.register(Utils.save_last_access_times)

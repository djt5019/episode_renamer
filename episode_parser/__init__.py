# -*- coding: utf-8 -*-
__author__ = 'Dan Tracy'
__email__ = 'djt5019 at gmail dot com'

import atexit

import Utils
import Logger

Logger.init_logging()
atexit.register(Utils.save_last_access_times)
atexit.register(Logger.shutdown_logging)

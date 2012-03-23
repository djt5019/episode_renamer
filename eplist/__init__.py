# -*- coding: utf-8 -*-
__author__ = 'Dan Tracy'
__email__ = 'djt5019 at gmail dot com'

import atexit
import utils
import logger

logger.init_logging()

atexit.register(utils.save_last_access_times)
atexit.register(logger.shutdown_logging)

utils.load_renamed_file()

# -*- coding: utf-8 -*-
__author__ = 'Dan Tracy'
__email__ = 'djt5019 at gmail dot com'
__version__ = '0.1.4'

import atexit
import utils
import logger
import os
import constants

if not os.path.exists(constants.RESOURCE_PATH):
    utils.init_resource_folder()

logger.init_logging()

atexit.register(utils.save_last_access_times)
atexit.register(logger.shutdown_logging)

utils.load_renamed_file()

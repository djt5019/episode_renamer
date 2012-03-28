# -*- coding: utf-8 -*-
__author__ = 'Dan Tracy'
__email__ = 'djt5019 at gmail dot com'
__version__ = '0.1.5'

import atexit
import os

from eplist import utils
from eplist import logger
from eplist import constants

if not os.path.exists(constants.RESOURCE_PATH):
    utils.init_resource_folder()

logger.init_logging()

atexit.register(utils.save_last_access_times)
atexit.register(logger.shutdown_logging)

utils.load_renamed_file()

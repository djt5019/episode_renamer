# -*- coding: utf-8 -*-
from __future__ import unicode_literals

__author__ = 'Dan Tracy'
__email__ = 'djt5019 at gmail dot com'
__version__ = '0.1.7'

import atexit
import os

from eplist import utils
from eplist import logger
from eplist import constants

if not os.path.exists(constants.resource_path):
    utils.init_resource_folder()

logger.init_logging()

atexit.register(utils.save_last_access_times)
atexit.register(logger.shutdown_logging)

utils.load_renamed_file()

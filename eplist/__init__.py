# -*- coding: utf-8 -*-
__author__ = 'Dan Tracy'
__email__ = 'djt5019 at gmail dot com'

import atexit
import os

import utils

import logger
logger.init_logging()
atexit.register(utils.save_last_access_times)
atexit.register(logger.shutdown_logging)

utils.load_renamed_file()

import constants

if not os.path.exists(constants.RESOURCE_PATH):
    os.makedirs(constants.RESOURCE_PATH, 0755)
    utils.update_db()

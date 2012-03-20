# -*- coding: utf-8 -*-
__author__ = 'Dan Tracy'
__email__ = 'djt5019 at gmail dot com'

import atexit
import os

import constants

new = False
if not os.path.exists(constants.RESOURCE_PATH):
    print "Creating resource path"
    os.makedirs(constants.RESOURCE_PATH, 0755)
    new = True

import utils

if new:
    utils.update_db()
    utils.create_new_backup_file()

import logger
logger.init_logging()

atexit.register(utils.save_last_access_times)
atexit.register(logger.shutdown_logging)

utils.load_renamed_file()

# -*- coding: utf-8 -*-
__author__ = 'Dan Tracy'
__email__ = 'djt5019 at gmail dot com'

import atexit
import os

import constants

new = False
if not os.path.exists(constants.RESOURCE_PATH):
    print "[+] Creating resource path"
    print "[+] Path = {}".format(constants.RESOURCE_PATH)
    os.makedirs(constants.RESOURCE_PATH, 0755)
    new = True

import utils

if new:
    print "[+] Updating the AniDb database file"
    utils.update_db()
    print "[+] Creating a renamed file backup listing"
    utils.create_new_backup_file()
    print "[+] Creating new sql schema file"
    utils.create_default_sql_schema()

import logger
logger.init_logging()

atexit.register(utils.save_last_access_times)
atexit.register(logger.shutdown_logging)

utils.load_renamed_file()

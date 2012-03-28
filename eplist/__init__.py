# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

__author__ = 'Dan Tracy'
__email__ = 'djt5019 at gmail dot com'
__version__ = '0.1.5'

import atexit
import os

from . import utils
from . import logger
from . import constants

if not os.path.exists(constants.RESOURCE_PATH):
    utils.init_resource_folder()

logger.init_logging()

atexit.register(utils.save_last_access_times)
atexit.register(logger.shutdown_logging)

utils.load_renamed_file()

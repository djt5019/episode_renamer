# -*- coding: utf-8 -*-
__author__ = 'Dan Tracy'
__email__ = 'djt5019 at gmail dot com'

import logging
import logging.config
import logging.handlers
import atexit

from os.path import join, abspath
from datetime import datetime

from Constants import RESOURCE_PATH
from Settings import Settings

_logger = None


def get_logger():
    """Returns the global logger instance"""
    global _logger

    if _logger is None:
        logging.config.fileConfig(abspath(join(RESOURCE_PATH, Settings['log_config'])))
        _logger = logging.getLogger()

        logPath = join(RESOURCE_PATH, Settings['log_file'])

        fileHandler = logging.handlers.RotatingFileHandler(logPath, maxBytes=2 ** 20, backupCount=3)
        fileHandler.setFormatter(logging.Formatter('%(levelname)s | %(module)s.%(funcName)s - "%(message)s"'))
        fileHandler.setLevel(logging.DEBUG)
        _logger.addHandler(fileHandler)

        _logger.debug("APPLICATION START: {}".format(datetime.now()))
        atexit.register(_closeLogs)

    return _logger


def _closeLogs():
    """
    Properly shutdown the loggers called upon program termination,
    registered to atexit in __init__.py
    """
    _logger.debug("APPLICATION END: {}".format(datetime.now()))
    logging.shutdown()

# -*- coding: utf-8 -*-
__author__ = 'Dan Tracy'
__email__ = 'djt5019 at gmail dot com'

import logging
import logging.config

from os.path import join
from datetime import datetime

from constants import RESOURCE_PATH
from settings import Settings


def init_logging():
    logging.config.dictConfig(log_config)
    logging.debug("APPLICATION START: {}".format(datetime.now()))


def shutdown_logging():
    """
    Properly shutdown the loggers called upon program termination,
    registered to atexit in __init__.py
    """
    logging.debug("APPLICATION END: {}".format(datetime.now()))
    logging.shutdown()


log_config = {
    'version': 1,
    'formatters': {
        'console_format': {
            'format': '%(levelname)s | "%(message)s"'
        },
        'file_format': {
            'format': '%(levelname)s | %(module)s.%(funcName)s - "%(message)s"'
        }
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'file_format',
            'filename': r'{}'.format(join(RESOURCE_PATH, Settings['log_file'])),
            'maxBytes': 2 ** 20,
            'backupCount': 3
        },
        'console': {
            'level': 'WARNING',
            'class': 'logging.StreamHandler',
            'formatter': 'console_format',
        }
    },
    'root': {
        'handlers': ['console', 'file'],
        'qualname': 'root',
        'level': 'DEBUG'
    }
}

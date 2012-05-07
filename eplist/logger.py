# -*- coding: utf-8 -*-
"""
Logging.py
"""
from __future__ import unicode_literals, absolute_import

import logging
import logging.config

from os.path import join
from datetime import datetime

from eplist.constants import resource_path
from eplist.settings import Settings


def init_logging():
    """
    Load the logging config dictionary and begin logging
    """
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
            'filename': r'{}'.format(join(resource_path, Settings.log_file)),
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

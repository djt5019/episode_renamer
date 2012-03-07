# -*- coding: utf-8 -*-
__author__ = 'Dan Tracy'
__email__ = 'djt5019 at gmail dot com'

import logging
import logging.config
import logging.handlers

from os.path import join
from datetime import datetime
from cStringIO import StringIO

from Constants import RESOURCE_PATH
from Settings import Settings


def init_logging():
    logging.config.fileConfig(StringIO(log_config))
    logging.debug("APPLICATION START: {}".format(datetime.now()))


def shutdown_logging():
    """
    Properly shutdown the loggers called upon program termination,
    registered to atexit in __init__.py
    """
    logging.debug("APPLICATION END: {}".format(datetime.now()))
    logging.shutdown()


log_config = '''
[loggers]
keys=root

[logger_root]
handlers=console, file
qualname=root
level=DEBUG

[formatters]
keys=consoleFormat, fileFormat

[formatter_consoleFormat]
format=%(levelname)s | "%(message)s"

[formatter_fileFormat]
format=%(levelname)s | %(module)s.%(funcName)s - "%(message)s"

[handlers]
keys=console, file

[handler_console]
class=logging.StreamHandler
formatter=consoleFormat
level=WARNING
args=(sys.stdout,)

[handler_file]
class=logging.handlers.RotatingFileHandler
formatter=fileFormat
level=DEBUG
backcount=3
maxsize=2**20
args=(r"{}", )
'''.format(join(RESOURCE_PATH, Settings['log_file']))

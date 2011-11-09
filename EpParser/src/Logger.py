import logging
import logging.config
import logging.handlers
import atexit

from os.path import join, abspath
from datetime import datetime

_logger = None
def getLogger():
    global _logger
    
    if _logger is None:
        from Utils import RESOURCEPATH
        logging.config.fileConfig( abspath(join(RESOURCEPATH,'logger.conf')))
        _logger = logging.getLogger()
        
        logPath = join(RESOURCEPATH, 'output.log')
        
        fileHandler = logging.handlers.RotatingFileHandler(logPath, maxBytes=2**20, backupCount=3)
        fileHandler.setFormatter( logging.Formatter('%(levelname)s | %(module)s.%(funcName)s - "%(message)s"') )
        fileHandler.setLevel( logging.DEBUG)
        
        _logger.addHandler(fileHandler)
                     
        _logger.debug("APPLICATION START: {}".format(datetime.now()))
        atexit.register( _closeLogs )
     
    return _logger
    
def _closeLogs():
    _logger.debug("APPLICATION END: {}".format(datetime.now()))
    logging.shutdown()
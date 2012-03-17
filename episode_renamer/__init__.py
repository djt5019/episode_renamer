# -*- coding: utf-8 -*-
__author__ = 'Dan Tracy'
__email__ = 'djt5019 at gmail dot com'

import os
import sys
import atexit

import Utils

RESOURCE_PATH = os.path.join("eplist", "resources")

if sys.platform == "win32":
    RESOURCE_PATH = os.path.join(os.environ['APPDATA'], RESOURCE_PATH)
elif sys.platform == 'darwin':
    ## Found at http://stackoverflow.com/questions/1084697/how-do-i-store-desktop-application-data-in-a-cross-platform-way-for-python
    from AppKit import NSSearchPathForDirectoriesInDomains
    # http://developer.apple.com/DOCUMENTATION/Cocoa/Reference/Foundation/Miscellaneous/Foundation_Functions/Reference/reference.html#//apple_ref/c/func/NSSearchPathForDirectoriesInDomains
    # NSApplicationSupportDirectory = 14
    # NSUserDomainMask = 1
    # True for expanding the tilde into a fully qualified path
    RESOURCE_PATH = os.path.join(NSSearchPathForDirectoriesInDomains(14, 1, True)[0], RESOURCE_PATH)
else:  # *nix / solaris
    RESOURCE_PATH = os.path.expanduser(os.path.join("~", "." + RESOURCE_PATH))

if not os.path.exists(RESOURCE_PATH):
    new_creation = True
    os.makedirs(RESOURCE_PATH, 0755)


import Constants
Constants.RESOURCE_PATH = RESOURCE_PATH

import Logger
Logger.init_logging()
atexit.register(Utils.save_last_access_times)
atexit.register(Logger.shutdown_logging)

try:
    new_creation
except NameError:
    pass
else:
    ## First run so grab the anidb database file
    import Utils
    Utils.update_db()

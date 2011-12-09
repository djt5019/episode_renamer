# -*- coding: utf-8 -*-
__author__='Dan Tracy'
__email__='djt5019 at gmail dot com'

import atexit
import Source_Poll_API

atexit.register(Source_Poll_API.save_last_access_times)
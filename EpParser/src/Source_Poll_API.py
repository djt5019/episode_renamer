# -*- coding: utf-8 -*-
# author:  Dan Tracy
# program: Source_Poll_API.py

import re as re_
import time as time_
import Constants

from os import path as path_
from tempfile import TemporaryFile as TemporaryFile_
from EpParser.src import Utils

show_not_found = "", []
_last_access = {}

def able_to_poll(site):
    """
    Prevents flooding by waiting two seconds from the last poll
    """
    last_access = _last_access.get(site, -1)
    now = int(time_.time())

    if last_access < 0:
        last_access[site] = now
        return True

    if now - last_access >= 2:
        last_access[site] = now
        return True
    
    return False

def open_file_in_resources(name):
    """
    Returns a file object if the filename exists in the resources directory
    """
    if file_exists_in_resources(name):
        name = path_.join(Constants.RESOURCEPATH, name)
        return open(name, 'r')
    return None

def file_exists_in_resources(name):
    """
    Returns true if the filename exists in the resources directory
    """
    name = path_.join(Constants.RESOURCEPATH, name)
    return path_.exists(name)

def regex_compile(regex):
    """
    Returns a compiled regex instance, ignore case and verbose are activated by default
    """
    return re_.compile(regex, re_.I|re_.X)

def regex_sub(pattern, replacement, target):
    """
    Substitutes the replacement in the target if it matches the pattern
    """
    return re_.sub(pattern, replacement, target)

def encode(string):
    """
    Returns a Unicode representation of the string
    """
    return Utils.encode(string)

def get_url_descriptor(url):
    """
    Returns a valid URL descriptor if the URL can be reached, otherwise None
    """
    return Utils.get_URL_descriptor(url)

def prepare_title(title):
    """
    Remove punctuation as well as invalid characters from the title for searching online
    """
    return Utils.prepare_title(title)

def temporary_file(suffix):
    """
    Returns a file object to a temporary file
    """
    return TemporaryFile_(suffix=suffix)

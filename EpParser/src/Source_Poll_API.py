# -*- coding: utf-8 -*-
__author__='Dan Tracy'
__email__='djt5019 at gmail dot com'

#
# The purpose of this file is just to group together several operations and imports that I
# have been using in the web sources.  It's more or less just to cut down on the number of
# imports in those files.
#

import re as re_
import time as time_
import Constants
import pickle as pickle_

from os import path as path_
from tempfile import TemporaryFile as TemporaryFile_

from EpParser.src import Utils
from EpParser.src.Settings import Settings

_site_access_dict = None
show_not_found = Constants.SHOW_NOT_FOUND

def able_to_poll(site):
    """
    Prevents flooding by waiting two seconds from the last poll
    """
    global _site_access_dict
    if not _site_access_dict:
        _site_access_dict = load_last_access_times()

    last_access = _site_access_dict.get(site, -1)
    now = int(time_.time())

    if last_access < 0:
        _site_access_dict[site] = now
        return True

    if now - last_access >= int(Settings['poll_delay']):
        _site_access_dict[site] = now
        return True
    
    return False

def open_file_in_resources(name):
    """
    Returns a file object if the filename exists in the resources directory
    """
    if file_exists_in_resources(name):
        name = path_.join(Constants.RESOURCE_PATH, name)
        return open(name, 'r')
    return None

def file_exists_in_resources(name):
    """
    Returns true if the filename exists in the resources directory
    """
    name = path_.join(Constants.RESOURCE_PATH, name)
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

def save_last_access_times():
    """
    Save the last access times dictionary to a file in resources
    """
    if not _site_access_dict:
        return False
    
    with open(path_.join(Constants.RESOURCE_PATH, Settings['access_time_file']), 'w') as p:
        pickle_.dump(_site_access_dict, p)

    return True

def load_last_access_times():
    """
    Load the access times dictionary from the file in resource path
    """
    name = path_.join(Constants.RESOURCE_PATH, Settings['access_time_file'])
    if path_.exists(name):
        with open_file_in_resources(name) as p:
            data = p.readlines()

        return pickle_.loads(''.join(data))
    else:
        return {}
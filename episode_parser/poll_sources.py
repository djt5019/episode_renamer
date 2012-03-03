# -*- coding: utf-8 -*-
__author__ = 'Dan Tracy'
__email__ = 'djt5019 at gmail dot com'

import sys

from os import listdir
from itertools import ifilter

import Constants

from Logger import get_logger as log
from Episode import Special


def locate_show(title):
    """Polls the web sources looking for the show"""
    modules = []
    eps = []
    specials = []

    sys.path.append(Constants.WEB_SOURCES_PATH)
    # This will import all the modules within the web_sources directory so that
    # we can easily plug in new sources for finding episode information so long
    # as they define a poll function

    for m in listdir(Constants.WEB_SOURCES_PATH):
        if m.endswith('.py') and not m.startswith('__'):
            log().info("Importing web resource {}".format(m[:-3]))

            x = __import__(m[:-3])
            if not hasattr(x, 'poll'):
                log().error("Module {} doesn't have a poll method defined, ignoring module".format(m))
                continue

            if not hasattr(x, 'priority'):
                log().error("Module {} doesn't have a priority defined, defaulting to 0".format(m))
                x.priority = 0

            modules.append(x)

    # If the modules have a poll priority we will respect it
    # by sorting the list by priority, higher number have higher precedence
    modules = sorted(modules, key=lambda x: x.priority, reverse=True)

    log().info("Searching for {}".format(title))

    episodes = Constants.SHOW_NOT_FOUND

    for source in modules:
        log().info("Polling {0}".format(source.__name__))

        episodes = source.poll(title)

        if episodes:
            log().info("LOCATED {0}".format(title))
            break

        log().info("Unable to locate {0} at {1}".format(title, source.__name__))

    if not episodes:
        log().info("Unable to locate the show: " + title)
        return (eps, specials)

    for e in episodes:
        if isinstance(e, Special):
            specials.append(e)
        else:
            eps.append(e)

    eps = sorted(ifilter(lambda x: x.episodeNumber > 0, eps), key=lambda z: z.episodeCount)
    specials = sorted(ifilter(lambda x: x.num > 0, specials), key=lambda z: z.num)

    return (eps, specials)

# -*- coding: utf-8 -*-
"""
Provides the logic for polling web sources.  Any python source in the
web_sources directory that has a poll method defined will be imported.  The
imported modules will then be iterated over and have their poll method called
until one of them returns a list of episodes.  The user can create their
own web source just by defining a poll method and saving the source in the
web_sources directory.
"""
from __future__ import unicode_literals

import sys
import logging

from os import listdir

from eplist import constants


def locate_show(title):
    """Polls the web sources looking for the show"""
    modules = []

    sys.path.append(constants.web_sources_path)
    # This will import all the modules within the web_sources directory so that
    # we can easily plug in new sources for finding episode information so long
    # as they define a poll function

    for mod in listdir(constants.web_sources_path):
        if mod.endswith('.py') and not mod.startswith('__'):
            logging.info("Importing web resource {}".format(mod[:-3]))

            module = __import__(mod[:-3])
            if not hasattr(module, 'poll'):
                logging.error("Module {} doesn't have a poll method defined, ignoring module".format(mod))
                continue

            if not hasattr(module, 'priority'):
                logging.error("Module {} doesn't have a priority defined, defaulting to 0".format(mod))
                module.priority = 0

            modules.append(module)

    # If the modules have a poll priority we will respect it
    # by sorting the list by priority, higher number have higher precedence
    modules = sorted(modules, key=lambda x: x.priority, reverse=True)

    logging.info("Searching for {}".format(title))

    episodes = constants.show_not_found

    for source in modules:
        logging.info("Polling {0}".format(source.__name__))

        episodes = source.poll(title)

        if episodes:
            logging.info("located {0}".format(title))
            break

        msg = "Unable to locate {0} at {1}".format(title, source.__name__)
        logging.info(msg)

    if not episodes:
        logging.info("Unable to locate the show: " + title)

    return sorted(episodes, key=lambda ep: ep.number)

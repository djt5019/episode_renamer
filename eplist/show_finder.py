# -*- coding: utf-8 -*-
"""
Provides funtionality for locating a show.  First tries polling the cache
then calls the locate_show in poll_sources to attempt to locate the show
online
"""
from __future__ import unicode_literals

import logging

from eplist import poll_sources
from eplist import utils

from eplist.episode import Show


class ShowFinder(object):
    """The main parser will poll the internet as well as a database
    looking for the show by using the parseData() function"""

    def __init__(self, showTitle="", cache=None):
        """ Proper title is used for the database/url while the display
        title is used for error messages/display purposes"""
        self.show = Show(showTitle)
        self.cache = cache

    def setShow(self, showTitle):
        """Sets a new show to search for, the old show will be removed """
        if showTitle:
            self.show = Show(showTitle)
            self.show.proper_title = utils.prepare_title(showTitle.lower())
            self.show.title = showTitle
        else:
            raise ValueError("Empty show title passed to set show")

    def getShow(self):
        """ The main driver function of this class, it will poll
        the database first, if the show doesn't exist it will
        then try the internet. """

        if not self.show.title:
            return None

        if self.cache:
            self.show.add_episodes(self._parseCacheData())

        # The show was found in the database
        if self.show.episodes:
            logging.info("Show found in database")
            return self.show

        # The show was not in the database so now we try the website
        logging.info("Show not found in database, polling web")
        self.show.add_episodes(self._parseHTMLData())

        if not self.show.episodes:
            logging.error("Show was not found, check spelling and try again")
            return self.show

        # If we successfully find the show from the internet then
        # we should add it to our database for later use
        if self.cache:
            logging.info("Adding show to the database")
            self.cache.add_show(self.show.proper_title, self.show.episodes,
                                self.show.specials)

        return self.show

    def _parseCacheData(self):
        """The query should return a positive show id otherwise
        it's not in the database"""
        return self.cache.get_episodes(self.show.proper_title)

    def _parseHTMLData(self):
        """ Passes the sites contents through the regex to seperate episode
        information such as name, episode number, and title.  After getting
        the data from the regex we will occupy the episode list """

        return poll_sources.locate_show(self.show.title)

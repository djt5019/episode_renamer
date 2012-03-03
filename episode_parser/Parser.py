# -*- coding: utf-8 -*-
__author__ = 'Dan Tracy'
__email__ = 'djt5019 at gmail dot com'

import poll_sources
import Utils

from Episode import Show
from Logger import get_logger


class Parser(object):
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
            self.show.properTitle = Utils.prepare_title(showTitle.lower())
            self.show.title = showTitle

    def getShow(self):
        """ The main driver function of this class, it will poll
        the database first, if the show doesn't exist it will
        then try the internet. """

        if self.show.title == '':
            return None

        if self.cache:
            (eps, specials) = self._parseCacheData()
            self.show.add_episodes(eps)
            self.show.add_specials(specials)

        # The show was found in the database
        if self.show.episodeList:
            get_logger().info("Show found in database")
            return self.show

        # The show was not in the database so now we try the website
        get_logger().info("Show not found in database, polling web")
        eps, specials = self._parseHTMLData()
        self.show.add_episodes(eps)
        self.show.add_specials(specials)

        if not self.show.episodeList:
            get_logger().error("Show was not found, check spelling and try again")
            return self.show

        # If we successfully find the show from the internet then
        # we should add it to our database for later use
        if self.cache is not None:
            get_logger().info("Adding show to the database")
            self.cache.add_show(self.show.properTitle, self.show.episodeList)
            self.cache.add_specials(self.show.properTitle, self.show.specialsList)

        return self.show

    def _parseCacheData(self):
        """The query should return a positive show id otherwise
        it's not in the database"""
        eps = self.cache.get_episodes(self.show.properTitle)
        spc = self.cache.get_specials(self.show.properTitle)
        return (eps, spc)

    def _parseHTMLData(self):
        """ Passes the sites contents through the regex to seperate episode
        information such as name, episode number, and title.  After getting
        the data from the regex we will occupy the episode list """

        return poll_sources.locate_show(self.show.title)

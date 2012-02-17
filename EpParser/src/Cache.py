# -*- coding: utf-8 -*-
__author__ = 'Dan Tracy'
__email__ = 'djt5019 at gmail dot com'

import os
import datetime
import sqlite3
import atexit

from Episode import Episode, Special
from Constants import RESOURCE_PATH
from Logger import get_logger
from Settings import Settings


class Cache(object):
    """ Our database logic class"""
    def __init__(self, dbName=u"episodes.db"):
        """Establish a connection to the show database"""
        if dbName != ':memory:':
            dbName = os.path.join(RESOURCE_PATH, dbName)
        try:
            if not os.path.exists(dbName) and dbName != ':memory:':
                self.connection = sqlite3.connect(dbName, detect_types=sqlite3.PARSE_DECLTYPES)

                with open(os.path.join(RESOURCE_PATH, 'createDB.sql'), 'r') as f:
                    sql = f.read()
                self.connection.executescript(sql)
            else:
                self.connection = sqlite3.connect(dbName, detect_types=sqlite3.PARSE_DECLTYPES)
        except sqlite3.OperationalError as e:
            get_logger().error("Error connecting to database: {}".format(e))
            self.connection = None

        if self.connection:
            self.cursor = self.connection.cursor()

            #Make sure everything is utf-8
            self.connection.text_factory = lambda x: unicode(x, 'utf-8')
            atexit.register(self.close)

    def close(self):
        """ Commits any changes to the database then closes connections to it"""
        self.cursor.close()
        self.connection.commit()
        self.connection.close()
        get_logger().info("Connections have been closed")

    def add_show(self, showTitle, episodes):
        """ If we find a show on the internet that is not in our database
        we can use this function to add it into our database for the future"""
        title = showTitle
        time = datetime.datetime.now()

        self.cursor.execute("INSERT INTO shows values (NULL, ?, ?)", (title, time))

        showId = self.cursor.lastrowid

        for eps in episodes:
            show = (showId, eps.title, eps.season, eps.episodeNumber,)
            self.cursor.execute(
                "INSERT INTO episodes values (NULL, ?, ?, ?, ?)", show)

    def remove_show(self, sid):
        """Removes show and episodes matching the show id """
        self.cursor.execute("DELETE from SHOWS where sid=?", (sid,))
        self.cursor.execute("DELETE from EPISODES where sid=?", (sid,))

    def get_episodes(self, showTitle):
        """Returns the episodes associated with the show id"""
        title = (showTitle, )
        self.cursor.execute(
            """SELECT eptitle, season, showNumber, shows.sid, shows.time
               FROM episodes INNER JOIN shows
               ON shows.sid=episodes.sid AND shows.title=?""", title)

        result = self.cursor.fetchall()
        eps = []

        if not result:
            return eps

        diffDays = (datetime.datetime.now() - result[0][-1])

        get_logger().info("{} days old".format(diffDays.days))

        update_days = abs(int(Settings['db_update']))

        if diffDays.days >= update_days:
            #If the show is older than a week remove it then return not found
            get_logger().warning("Show is older than a week, removing...")
            sid = result[0][-2]
            self.remove_show(sid)
            return eps

        for count, episode in enumerate(result, start=1):
            eps.append(Episode(episode[0], episode[1], episode[2], count))

        return eps

    def get_specials(self, specialId):
        """ Returns a list of Special episode objects """
        mid = (specialId, )
        self.cursor.execute(
            """SELECT title, showNumber, type
               FROM specials INNER JOIN shows
               ON specials.sid=shows.sid AND shows.title=?""", mid)

        result = self.cursor.fetchall()

        if result is not None:
            eps = [Special(*episode) for episode in result]

        return eps

    def add_specials(self, showTitle, episodes):
        """ Add a list of special episode objects """
        showId = self.get_showId(showTitle)

        for eps in episodes:
            show = (showId, eps.title, eps.episodeNumber, eps.type)
            self.cursor.execute(
                "INSERT INTO specials values (NULL, ?, ?, ?, ?)", show)

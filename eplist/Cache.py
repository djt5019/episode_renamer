# -*- coding: utf-8 -*-
__author__ = 'Dan Tracy'
__email__ = 'djt5019 at gmail dot com'

import os
import datetime
import sqlite3
import atexit
import logging

import utils

from episode import Episode, Special
from constants import RESOURCE_PATH
from settings import Settings

if not utils.file_exists_in_resources(Settings['sql']):
    utils.create_default_sql_schema()

with utils.open_file_in_resources(Settings['sql']) as sql:
    schema = sql.read()


class Cache(object):
    """ Our database logic class"""
    def __init__(self, dbName=u"episodes.db"):
        """Establish a connection to the show database"""
        if not dbName or not isinstance(dbName, basestring):
            raise ValueError("Empty database name passed to cache")

        if dbName != ':memory:':
            dbName = os.path.join(RESOURCE_PATH, dbName)

        try:
            if not os.path.exists(dbName):
                self.connection = sqlite3.connect(dbName, detect_types=sqlite3.PARSE_DECLTYPES)
                logging.debug("Creating database: {}".format(dbName))
                self.connection.executescript(schema)
            else:
                self.connection = sqlite3.connect(dbName, detect_types=sqlite3.PARSE_DECLTYPES)
        except sqlite3.OperationalError as e:
            logging.error("Error connecting to database: {}".format(e))
            self.connection = None

        if self.connection:
            self.cursor = self.connection.cursor()

            #Make sure everything is utf-8
            self.connection.text_factory = lambda x: unicode(x, 'utf-8')
            atexit.register(self.close)
        else:
            logging.critical("Unable to open a connection to the database")
            raise sqlite3.OperationalError

    def close(self):
        """ Commits any changes to the database then closes connections to it"""
        self.cursor.close()
        self.connection.commit()
        self.connection.close()
        logging.info("Connections have been closed")

    def add_show(self, showTitle, episodes):
        """ If we find a show on the internet that is not in our database
        we can use this function to add it into our database for the future"""
        if not (showTitle and episodes):
            raise ValueError("Empty show title or specials list passed to add_specials")

        if not (isinstance(showTitle, basestring) and isinstance(episodes, list)):
            raise ValueError("add_show expects a string and a list")

        title = showTitle
        time = datetime.datetime.now()

        self.cursor.execute("INSERT INTO shows values (NULL, ?, ?)", (title, time))

        showId = self.cursor.lastrowid

        for eps in episodes:
            show = (showId, eps.title, eps.season, eps.episode_number,)
            self.cursor.execute(
                "INSERT INTO episodes values (NULL, ?, ?, ?, ?)", show)

    def remove_show(self, sid):
        """Removes show and episodes matching the show id """
        if not isinstance(sid, int):
            raise ValueError("remove_show expects an integer primary key")

        self.cursor.execute("DELETE FROM episodes where sid=?", (sid,))
        self.cursor.execute("DELETE FROM specials where sid=?", (sid,))
        self.cursor.execute("DELETE FROM shows where sid=?", (sid,))

    def get_episodes(self, showTitle):
        """Returns the episodes associated with the show id"""
        if not showTitle:
            raise ValueError("get_episodes expects a string")

        title = (showTitle, )
        self.cursor.execute(
            """SELECT e.eptitle, e.showNumber,e.season, s.sid, s.time
               FROM episodes AS e INNER JOIN shows AS s
               ON s.sid=e.sid AND s.title=?""", title)

        result = self.cursor.fetchall()
        eps = []

        if not result:
            return eps

        diffDays = (datetime.datetime.now() - result[0][-1])

        logging.info("{} days old".format(diffDays.days))

        update_days = Settings['db_update']

        if diffDays.days >= update_days:
            #If the show is older than a week remove it then return not found
            logging.warning("Show is older than a week, removing...")
            sid = result[0][-2]
            self.remove_show(sid)
            return eps

        for count, episode in enumerate(result, start=1):
            eps.append(Episode(episode[0], episode[1], episode[2], count))

        return eps

    def get_specials(self, showTitle):
        """ Returns a list of Special episode objects """
        if not showTitle:
            raise ValueError("Show title was not an acceptable type: requires string")

        title = (showTitle, )
        self.cursor.execute(
            """SELECT sp.title, sp.showNumber, sp.type
               FROM specials AS sp INNER JOIN shows
               ON sp.sid=shows.sid AND shows.title=?""", title)

        result = self.cursor.fetchall()

        if result is not None:
            eps = [Special(*episode) for episode in result]

        return eps

    def add_specials(self, showTitle, episodes):
        """ Add a list of special episode objects """
        query = """
        INSERT INTO specials (mid,  sid, title, showNumber, type)
        SELECT NULL, sid, ?, ?, ?
        FROM shows
        WHERE shows.title=?
        """

        if not (showTitle and episodes):
            return

        if not (isinstance(showTitle, basestring) and isinstance(episodes, list)):
            raise ValueError("add_specials expects a string and a list")

        for eps in episodes:
            show = (eps.title, eps.num, eps.type, showTitle)
            self.cursor.execute(query, show)

    def recreate_cache(self):
        self.cursor.executescript(schema)

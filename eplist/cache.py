# -*- coding: utf-8 -*-

from __future__ import unicode_literals

__author__ = 'Dan Tracy'
__email__ = 'djt5019 at gmail dot com'

import os
import datetime
import sqlite3
import atexit
import logging

from episode import Episode, Special
from constants import RESOURCE_PATH
from settings import Settings


class Cache(object):
    """ Our database logic class"""
    def __init__(self, dbName):
        """Establish a connection to the show database"""

        if not dbName:
            raise ValueError("Empty database name passed to cache")

        if dbName != ':memory:':
            dbName = os.path.join(RESOURCE_PATH, dbName)

        try:
            self.connection = sqlite3.connect(dbName, detect_types=sqlite3.PARSE_DECLTYPES)
            logging.debug("Creating database: {}".format(dbName))
            self.connection.executescript(create_database)
        except sqlite3.OperationalError as e:
            logging.error("Error connecting to database: {}".format(e))
            self.connection = None

            #Make sure everything is utf-8
            self.connection.text_factory = lambda x: unicode(x, 'utf-8')
            atexit.register(self.close)

    def close(self):
        """ Commits any changes to the database then closes connections to it"""
        self.connection.commit()
        self.connection.close()
        logging.info("Connections have been closed")

    def add_show(self, showTitle, episodes):
        """ If we find a show on the internet that is not in our database
        we can use this function to add it into our database for the future"""
        if not (showTitle and episodes):
            raise ValueError("Empty show title or specials list passed to add_specials")

        title = showTitle
        time = datetime.datetime.now()

        with self.connection as conn:
            curs = conn.execute("INSERT INTO shows values (NULL, ?, ?)", (title, time))
            showId = curs.lastrowid

        with self.connection as conn:
            for eps in episodes:
                show = (showId, eps.title, eps.season, eps.episode_number,)
                conn.execute("INSERT INTO episodes values (NULL, ?, ?, ?, ?)", show)

    def remove_show(self, sid):
        """Removes show and episodes matching the show id """
        sid = (sid,)
        with self.connection as conn:
            conn.execute("DELETE FROM episodes where sid=?", sid)
            conn.execute("DELETE FROM specials where sid=?", sid)
            conn.execute("DELETE FROM shows where sid=?", sid)

    def get_episodes(self, showTitle):
        """Returns the episodes associated with the show id"""
        if not showTitle:
            raise ValueError("get_episodes expects a string")

        title = (showTitle, )
        query = """SELECT e.eptitle, e.showNumber,e.season, s.sid, s.time
                   FROM episodes AS e INNER JOIN shows AS s
                   ON s.sid=e.sid AND s.title=?"""

        with self.connection as conn:
            curs = conn.execute(query, title)
            result = curs.fetchall()

        eps = []

        if not result:
            return eps

        diffDays = (datetime.datetime.now() - result[0][-1])

        logging.info("{} days old".format(diffDays.days))

        if diffDays.days >= Settings['db_update']:
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
            raise ValueError("Show title requires a string")

        title = (showTitle, )

        query = """SELECT sp.title, sp.showNumber, sp.type
                   FROM specials AS sp INNER JOIN shows
                   ON sp.sid=shows.sid AND shows.title=?"""

        with self.connection as conn:
            curs = conn.execute(query, title)
            result = curs.fetchall()

        if result is not None:
            return [Special(*episode) for episode in result]
        else:
            return []

    def add_specials(self, showTitle, episodes):
        """ Add a list of special episode objects """
        query = """INSERT INTO specials (mid,  sid, title, showNumber, type)
                   SELECT NULL, sid, ?, ?, ?
                   FROM shows
                   WHERE shows.title=?"""

        if not (showTitle and episodes):
            return

        with self.connection as conn:
            for eps in episodes:
                show = (eps.title, eps.num, eps.type, showTitle)
                conn.execute(query, show)

    def recreate_cache(self):
        with self.connection as conn:
            conn.executescript(delete_database)
            conn.executescript(create_database)


create_database = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS shows (
    sid INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    time TIMESTAMP
);

CREATE TABLE IF NOT EXISTS episodes (
    eid INTEGER PRIMARY KEY,
    sid INTEGER NOT NULL REFERENCES shows(sid) ON DELETE CASCADE,
    eptitle TEXT NOT NULL,
    season INTEGER NOT NULL,
    showNumber INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS specials(
    mid INTEGER PRIMARY KEY,
    sid INTEGER NOT NULL REFERENCES shows(sid) ON DELETE CASCADE,
    title TEXT NOT NULL,
    showNumber INTEGER NOT NULL,
    type TEXT NOT NULL
);
"""

delete_database = """
DROP TABLE IF EXISTS episodes;
DROP TABLE IF EXISTS specials;
DROP TABLE IF EXISTS shows;
"""

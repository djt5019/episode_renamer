# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

import os
import datetime
import sqlite3
import atexit
import logging

from itertools import chain

from .episode import Episode
from .constants import RESOURCE_PATH
from .settings import Settings
from .utils import encode


class Cache(object):
    """ Our database logic class"""
    def __init__(self, dbName=""):
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
            self.connection.text_factory = lambda x: encode(x)
            atexit.register(self.close)

    def close(self):
        """ Commits any changes to the database then closes connections to it"""
        self.connection.commit()
        self.connection.close()
        logging.info("Connections have been closed")

    def add_show(self, showTitle, episodes, specials):
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
            for eps in chain(episodes, specials):
                show = (showId, eps.title, eps.season, eps.number, eps.count, eps.type,)
                conn.execute("INSERT INTO episodes values (NULL, ?, ?, ?, ?, ?, ?)", show)

    def remove_show(self, sid):
        """Removes show and episodes matching the show id """
        sid = (sid,)
        with self.connection as conn:
            conn.execute("DELETE FROM episodes where sid=?", sid)
            conn.execute("DELETE FROM shows where sid=?", sid)

    def get_episodes(self, showTitle):
        """Returns the episodes associated with the show id"""
        if not showTitle:
            raise ValueError("get_episodes expects a string")

        title = (showTitle, )
        query = """SELECT e.title, e.season, e.number, e.count, e.type, s.sid, s.time
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

        for episode in result:
            title = episode[0]
            season = episode[1]
            number = episode[2]
            count = episode[3]
            type_ = episode[4]
            eps.append(Episode(title, number, season, count, type_))

        return eps

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
    title TEXT NOT NULL,
    season INTEGER NOT NULL,
    number INTEGER NOT NULL,
    count INTEGER NOT NULL,
    type TEXT NOT NULL
);
"""

delete_database = """
DROP TABLE IF EXISTS episodes;
DROP TABLE IF EXISTS shows;
"""

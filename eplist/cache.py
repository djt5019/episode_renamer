# -*- coding: utf-8 -*-
"""
Provides the logic of keeping a cache of show information to avoid slow lookups
on the internet
"""
from __future__ import unicode_literals

import os
import datetime
import logging

from itertools import chain

from sqlite3 import PARSE_DECLTYPES, connect, OperationalError

from eplist import utils
from eplist.episode import Episode
from eplist.constants import resource_path
from eplist.settings import Settings


class Cache(object):
    """ Our database logic class"""
    def __init__(self, dbName=""):
        """Establish a connection to the show database"""

        if not dbName:
            raise ValueError("Empty database name passed to cache")

        if dbName != ':memory:':
            dbName = os.path.join(resource_path, dbName)

        try:
            self.connection = connect(dbName, detect_types=PARSE_DECLTYPES)
            logging.debug("Creating database: {}".format(dbName))
            self.connection.executescript(create_database)
        except OperationalError as reason:
            logging.error("Error connecting to database: {}".format(reason))
            raise reason
        else:
            #Make sure everything is utf-8
            self.connection.text_factory = lambda x: utils.encode(x)

    def close(self):
        """ Commits any changes to the database then closes connections to it"""
        self.connection.commit()
        self.connection.close()
        logging.info("Connections have been closed")

    def add_show(self, showTitle, episodes=None, specials=None):
        """ If we find a show on the internet that is not in our database
        we can use this function to add it into our database for the future"""
        if not showTitle:
            raise ValueError("Empty show title passed to add_specials")

        if not episodes and not specials:
            raise ValueError("Empty specials/episode list passed")

        if not isinstance(episodes, list) or not isinstance(specials, list):
            raise ValueError("Episode/specials must be in a list")

        title = showTitle
        time = datetime.datetime.now()

        with self.connection as conn:
            curs = conn.execute(
                    "INSERT INTO shows values (NULL, ?, ?)",
                    (title, time))

            showId = curs.lastrowid

        with self.connection as conn:
            for eps in chain(episodes, specials):
                show_info = (showId, eps.title, eps.season, eps.number,
                        eps.count, eps.type,)

                conn.execute(
                    "INSERT INTO episodes values (NULL, ?, ?, ?, ?, ?, ?)",
                    show_info)

    def remove_show(self, sid):
        """Removes show and episodes matching the show id """
        sid = (sid,)
        with self.connection as conn:
            conn.execute("DELETE FROM episodes where sid=?", sid)
            conn.execute("DELETE FROM shows where sid=?", sid)

    def get_episodes(self, showTitle, expiration=None):
        """Returns the episodes associated with the show id"""
        if not showTitle:
            raise ValueError("get_episodes expects a string")

        title = (showTitle, )
        query = """
            SELECT e.title, e.season, e.number, e.count, e.type, s.sid, s.time
            FROM episodes AS e INNER JOIN shows AS s
            ON s.sid=e.sid AND s.title=?
            """

        with self.connection as conn:
            curs = conn.execute(query, title)
            result = curs.fetchall()

        eps = []

        if not result:
            return eps

        diffDays = (datetime.datetime.now() - result[0][-1])

        logging.info("{} days old".format(diffDays.days))

        if not expiration:
            expiration = Settings.db_update

        if diffDays.days >= expiration:
            #If the show is older than a week remove it then return not found
            logging.warning("Show is older than a week, updating...")
            sid = result[0][-2]
            self.remove_show(sid)
            return eps

        for episode in result:
            title = utils.encode(episode[0])
            season = episode[1]
            number = episode[2]
            count = episode[3]
            type_ = utils.encode(episode[4])
            eps.append(Episode(title=title, number=number, season=season,
                               count=count, type=type_))

        return eps

    def recreate_cache(self):
        """
        Delete the cache then create a new one
        """
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

-- CREATE TABLE IF NOT EXISTS backup_info (
--     bid INTEGER PRIMARY KEY,
--     path STRING NOT NULL,
--     show STRING NOT NULL,
--     old_name STRING NOT NULL,
--     new_name STRING NOT NULL
--     );

-- CREATE TABLE IF NOT EXISTS access_times (
--     site_id INTEGER PRIMARY KEY,
--     site STRING NOT NULL,
--     last_access TIMESTAMP NOT NULL
--     )
"""

delete_database = """
DROP TABLE IF EXISTS episodes;
DROP TABLE IF EXISTS shows;
"""

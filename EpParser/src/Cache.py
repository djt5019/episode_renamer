# -*- coding: utf-8 -*-
# author:  Dan Tracy
# program: cache.py

import os
import datetime
import sqlite3	
import atexit

from Utils import Episode, RESOURCEPATH, logger

class Cache(object):
	''' Our database logic class'''
	_sqlquery = u'''
		PRAGMA foreign_keys = ON;
		
		CREATE TABLE shows (
			sid INTEGER PRIMARY KEY,
			title TEXT NOT NULL,
			time TIMESTAMP 
		);
		
		CREATE TABLE episodes (
			eid INTEGER PRIMARY KEY,
			sid INTEGER NOT NULL,
			eptitle TEXT NOT NULL,
			season INTEGER NOT NULL,
			showNumber INTEGER NOT NULL,			
			FOREIGN KEY(sid) REFERENCES shows(sid)
		);'''

	def __init__(self, dbName=u"episodes.db"):
		'''Establish a connection to the show database'''
		if dbName != ':memory:':
			dbName = os.path.join(RESOURCEPATH, dbName)

		try:
			if not os.path.exists(dbName) and dbName != ':memory:':
				self.connection = sqlite3.connect(dbName, detect_types=sqlite3.PARSE_DECLTYPES)
				self.connection.executescript( Cache._sqlquery )
			else:
				self.connection = sqlite3.connect(dbName, detect_types=sqlite3.PARSE_DECLTYPES)
		except sqlite3.OperationalError as e:
			logger.error("Error connecting to database: {}".format(e))
			return None
		
		self.cursor = self.connection.cursor()

		#Make sure everything is utf-8
		self.connection.text_factory = lambda x: unicode(x, 'utf-8')
		atexit.register( self.close )


	def close(self):
		''' Commits any changes to the database then closes connections to it'''
		self.cursor.close()
		self.connection.commit()
		self.connection.close()
		logger.info("Connections have been closed")


	def getShowId(self, showTitle):
		'''Returns the shows ID if found, -1 otherwise. If the show is more than
		a week old update the show'''		
		title = (showTitle, )
		now = datetime.datetime.now()

		self.cursor.execute("SELECT sid, time FROM shows WHERE title=? LIMIT 1", title)

		result = self.cursor.fetchone()	

		if result is None:
			return -1

		sid = int(result[0])
		diffDays = (datetime.datetime.now() - result[1])

		logger.info("{} days old".format(diffDays.days))

		if diffDays.days >= 7:
			#If the show is older than a week remove it then return not found
			logger.warning("Show is older than a week, removing...")
			self.removeShow(sid)
			return -1
		else:
			return sid


	def getEpisodes(self, showId):
		'''Returns the episodes associated with the show id'''
		sid = (showId, )
		self.cursor.execute(
			"SELECT eptitle, shownumber, season FROM episodes\
			WHERE sid=?", sid)

		result = self.cursor.fetchall()
		eps = []

		if result is not None:
			for count, episode in enumerate(result, start=1):
				eps.append( Episode(episode[0], episode[1], episode[2], count) )

		return eps


	def addShow(self, showTitle, episodes):
		''' If we find a show on the internet that is not in our database
		we can use this function to add it into our database for the future'''
		title = showTitle
		time = datetime.datetime.now()

		self.cursor.execute("INSERT INTO shows values (NULL, ?, ?)", (title, time))

		showId = self.cursor.lastrowid

		for eps in episodes:
			show = (showId, eps.title, eps.season, eps.episode,)
			self.cursor.execute(
				"INSERT INTO episodes values (NULL, ?, ?, ?, ?)", show)


	def removeShow(self, sid):
		'''Removes show and episodes matching the show id '''
		try:
			self.cursor.execute("DELETE from SHOWS where sid=?", (sid,) )
			self.cursor.execute("DELETE from EPISODES where sid=?", (sid,) )
		except Exception as e:
			logger.error("Something went wrong\n{}".format(e))
			pass

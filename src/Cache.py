# -*- coding: utf-8 -*-
# author:  Dan Tracy
# program: cache.py

import atexit
import os

try:
	import sqlite3
except ImportError:
	exit("sqlite3 not found")
	

from Utils import Episode

class Cache(object):
	''' Our database logic class'''
	_sqlquery = '''
		PRAGMA foreign_keys = ON;
		
		CREATE TABLE shows (
			sid INTEGER PRIMARY KEY,
			title TEXT NOT NULL
		);
		
		CREATE TABLE episodes (
			eid INTEGER PRIMARY KEY,
			sid INTEGER NOT NULL,
			eptitle TEXT NOT NULL,
			season INTEGER NOT NULL,
			showNumber INTEGER NOT NULL,			
			FOREIGN KEY(sid) REFERENCES shows(sid)
		);'''
	
	def __init__(self, dbName=u"episodes.db", verbose=False):
	
		if dbName != ':memory:':
			dbName = 'resources/' + dbName
			
		try:
			if not os.path.exists(dbName) and dbName != ':memory:':
				self.connection = sqlite3.connect(dbName)
				self.connection.executescript( Cache._sqlquery )
			else:
				self.connection = sqlite3.connect(dbName)
		except sqlite3.OperationalError as e:
			print e
			return
			
		self.verbose = verbose

		
		##if recreate:
		##    if self.verbose:  print "Making a new cache"
		##
		##    self.("DROP TABLE shows")
		##    self.__executeQuery("DROP TABLE episodes")
		##   
		##    self.connection.executescript( Cache._sqlquery )
			
			
		self.cursor = self.connection.cursor()
		
		#Make sure everything is utf-8
		self.connection.text_factory = lambda x: unicode(x, 'utf-8')
		atexit.register( self.close )

	def close(self):
		''' Commits any changes to the database then closes connections to it'''
		self.cursor.close()
		self.connection.commit()
		self.connection.close()

	def getShowId(self, showTitle):
		''' Polls the database for the shows title then returns its show id'''
		title = (showTitle, )
		self.cursor.execute("SELECT sid FROM shows WHERE title=? LIMIT 1", title)
		result = self.cursor.fetchone()
		if result is not None:
			return result[0]
		else:
			return -1

	def getEpisodes(self, showId, showTitle):
		''' Using the show id return the shows associated with that id'''
		sid = (showId, )
		self.cursor.execute(
			"SELECT eptitle, shownumber, season FROM episodes\
			WHERE sid=?", sid)
		
		result = self.cursor.fetchall()
		eps = []
		
		count = 1
		if result is not None:
			for episode in result:
				eps.append( Episode(showTitle, episode[0], episode[1], episode[2], count) )
				count += 1

		return eps

		
	def addShow(self, showTitle, episodes):
		''' If we find a show on the internet that is not in our database
		we can use this function to add it into our database for the future'''
		title = (showTitle, )
		self.cursor.execute("INSERT INTO shows values (NULL, ?)", title)
		showId = self.getShowId(showTitle)
		for eps in episodes:
			show = (showId, eps.title, eps.season, eps.episode,)
			self.cursor.execute(
				"INSERT INTO episodes values (NULL, ?, ?, ?, ?)", show)


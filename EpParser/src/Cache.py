# -*- coding: utf-8 -*-
# author:  Dan Tracy
# program: cache.py

import atexit
import os
import datetime


try:
	import sqlite3
except ImportError:
	exit("sqlite3 not found")
	

from Utils import Episode, RESOURCEPATH

class Cache(object):
	''' Our database logic class'''
	_sqlquery = '''
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
	
	def __init__(self, dbName=u"episodes.db", verbose=False):
	
		if dbName != ':memory:':
			dbName = os.path.join(RESOURCEPATH, dbName)
		
		try:
			if not os.path.exists(dbName) and dbName != ':memory:':
				self.connection = sqlite3.connect(dbName, detect_types=sqlite3.PARSE_DECLTYPES)
				self.connection.executescript( Cache._sqlquery )
			else:
				self.connection = sqlite3.connect(dbName, detect_types=sqlite3.PARSE_DECLTYPES)
		except sqlite3.OperationalError as e:
			print e
			return
			
		self.verbose = verbose
		
		##if recreate:
		##    if self.verbose:  print "Making a new cache"
		##
		##    self.__executeQuery("DROP TABLE shows")
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
		''' Polls the database for the shows title then returns its show id as well
		    as the timestamp.  If the timestamp is more than a week old update the
			show.  This is to take into account newer episodes being aired.'''
		title = (showTitle, )
		now = datetime.datetime.now()
		
		self.cursor.execute("SELECT sid, time FROM shows WHERE title=? LIMIT 1", title)
		
		result = self.cursor.fetchone()	

		if result is None:
			return -1
			
		diffDays = (datetime.datetime.now() - result[1])
		
		if diffDays.days >= 7:
			#If the show is older than a week remove it then return not found
			print "WARNING: Show older than a week, updating..."
			removeShow(sid)
			return -1
		else:
			return result[0]
		

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
		title = showTitle
		time = datetime.datetime.now()
		
		self.cursor.execute("INSERT INTO shows values (NULL, ?, ?)", (title, time))
		
		showId = self.getShowId(showTitle)
		
		for eps in episodes:
			show = (showId, eps.title, eps.season, eps.episode,)
			self.cursor.execute(
				"INSERT INTO episodes values (NULL, ?, ?, ?, ?)", show)

				
	def removeShow(self, sid):
		try:
			self.cursor.execute("DELETE from SHOWS where sid = ", (sid,) )
			self.cursor.execute("DELETE from EPISODES where sid = ", (sid,) )
		except Exception:
			pass

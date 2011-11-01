# -*- coding: utf-8 -*-
# author:  Dan Tracy
# program: utils.py

import poll_sources
import Utils

class EpParser(object):
	'''The main parser will poll the internet as well as a database
	looking for the show by using the parseData() function'''
	
	def __init__(self, showTitle="", cache=None):
		''' Proper title is used for the database/url while the display
		title is used for error messages/display purposes'''
		self.show = Utils.Show(showTitle)        
		self.cache = cache

	def setShow(self, showTitle):
		'''Sets a new show to search for, the old show will be removed '''
		if showTitle:
			self.show = Utils.Show(showTitle)
			self.show.properTitle = Utils.prepareTitle( showTitle.lower() )
			self.show.title = showTitle
		

	def getShow(self):
		''' The main driver function of this class, it will poll
		the database first, if the show dosen't exist it will
		then try the internet. '''

		if self.show.title == '':
			return None

		if self.cache is not None:
			self.show.episodeList = self._parseCacheData()

		# The show was found in the database
		if self.show.episodeList != []:
			Utils.logger.info( "Show found in database")
			return self.show

		# The show was not in the database so now we try the website
		Utils.logger.info( "Show not found in database, polling web")
		self.show.episodeList = self._parseHTMLData()

		if not self.show.episodeList:
			Utils.logger.error("Show was not found, check spelling and try again")
			return self.show
			
		# If we successfully find the show from the internet then
		# we should add it to our database for later use
		if self.cache is not None:
			Utils.logger.info( "Adding show to the database" )
			self.cache.addShow( self.show.properTitle, self.show.episodeList )

		return self.show
			
	def _parseCacheData(self):
		'''The query should return a positive show id otherwise 
		it's not in the database'''
		showId = self.cache.getShowId(self.show.properTitle)

		if showId == -1: 
			return []

		return self.cache.getEpisodes(showId)
				
	def _parseHTMLData(self):
		''' Passes the sites contents through the regex to seperate episode
		information such as name, episode number, and title.  After getting
		the data from the regex we will occupy the episode list '''  
		
		return poll_sources.locate_show(self.show.title)

	def setFormat(self, fmt):
		''' Set the custom formatting for the shows formatter '''
		self.show.formatter.setFormat( fmt )
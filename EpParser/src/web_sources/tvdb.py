#!/usr/bin/env python

import zipfile

from tempfile import TemporaryFile
from os.path import join
from urllib import quote_plus

from EpParser.src.Utils import *

try:
	from BeautifulSoup import BeautifulStoneSoup as Soup
except ImportError:
	print u"Error: BeautifulSoup was not found, unable to parse theTVdb"
	Soup = None
	pass

	
def poll(title):
	if Soup is None:
		return []
	
	try:
		with open( join(RESOURCEPATH,'tvdb.apikey') ,'r') as api:
			API_KEY = api.readline()
	except:
		print "The TvDB Api key file could not be found, unable to poll TvDB"
		return
		
	episodes = []

	cleanTitle = quote_plus(title)

	#1) First we need to find the series ID
	seriesIdLoc = "http://www.thetvdb.com/api/GetSeries.php?seriesname={0}".format(cleanTitle)
	seriesFileDesc = getURLdescriptor( seriesIdLoc )

	if seriesFileDesc is None:
		return []

	with seriesFileDesc as fd:
		seriesIdXml = Soup( fd, convertEntities=Soup.HTML_ENTITIES )
		
	seriesIds = seriesIdXml.findAll('series')

	if not seriesIds: return []

	if len(seriesIds) > 1:
		print "CONFLICT WITH IDS\n\n\n"
		print seriesIds
		#TODO: potential name conflict, deal with this later
		pass

	seriesID = seriesIds[0].seriesid.getString()
	seriesIdXml.close()


	#2) Get base info zip file
	infoLoc = "http://www.thetvdb.com/api/{0}/series/{1}/all/en.zip".format(API_KEY, seriesID)
	infoFileDesc = getURLdescriptor(infoLoc)
	if infoFileDesc is None: return []
	
	tempZip = TemporaryFile(suffix='.zip')
	tempZip.seek(0)
	
	with infoFileDesc as z:
		# download the entire zipfile into the tempfile
		while True:
			packet = z.read()
			if not packet:
				break
			tempZip.write(packet)

	with zipfile.ZipFile(tempZip, 'r') as z:
		with z.open('en.xml') as d:
			soup = Soup( d, convertEntities=Soup.HTML_ENTITIES )


	#3) Now we have the xml data in the soup variable, just populate the list
	count = 1
	for data in soup.findAll('episode'):
		name   = data.episodename.getText()
		season = int(data.seasonnumber.getText())
		num    = int(data.episodenumber.getText())
		
		if int(season) < 1: continue
		
		episodes.append( Episode(name, num, season, count ) )
		count += 1
		
	
	soup.close()
	tempZip.close()
		
	return episodes

if __name__ == '__main__':
	# Test it out
	poll("baccano")

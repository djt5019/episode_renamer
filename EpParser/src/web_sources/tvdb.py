#!/usr/bin/env python

import urllib #for escaping urls
import zipfile
from tempfile import TemporaryFile
from contextlib import closing
from os.path import join

from EpParser.src.Utils import *

try:
	from BeautifulSoup import BeautifulStoneSoup as Soup
except ImportError:
	print u"Error: BeautifulSoup was not found, unable to parse theTVdb"
	Soup = None
	pass

# Load my TVDB api key
try:
	with open( join(RESOURCEPATH,'tvdb.apikey') ,'r') as api:
		API_KEY = api.readline()
except IOError:
	raise IOError("A TVDB api key is required to poll their website")

def poll(title):
	if Soup is None:
		return []
	episodes = []

	cleanTitle = urllib.quote_plus(title)

	#1) First we need to find the series ID
	seriesIdLoc = "http://www.thetvdb.com/api/GetSeries.php?seriesname={0}".format(cleanTitle)
	seriesFileDesc = getURLdescriptor( seriesIdLoc )

	if seriesFileDesc is None:
		return []

	seriesIdXml = Soup( seriesFileDesc )
	seriesIds   = seriesIdXml.findAll('series')

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
	
	with closing(infoFileDesc) as z:
		# download the entire zipfile into the tempfile, f
		while True:
			packet = z.read()
			if not packet:
				break
			tempZip.write(packet)

	with zipfile.ZipFile(tempZip, 'r') as z:
		with z.open('en.xml') as d:
			soup = Soup( d )


	#3) Now we have the xml data in the soup variable, just populate the list
	
	for count, data in enumerate( soup.findAll('episode'), start=1 ):
		name   = data.episodename.getText()
		season = int(data.seasonnumber.getText())
		num    = int(data.episodenumber.getText())
		
		if int(season) < 1: continue
		
		episodes.append( Episode(title, name, num, season, count ) )
	
	soup.close()
	tempZip.close()
		
	return episodes

if __name__ == '__main__':
	# Test it out
	poll("baccano")

#!/usr/bin/env python
# author:  Dan Tracy
# program: eplist.py

''' 
This command line program will take a T.V. show as input and
will return information about each episode, such as the title
season and number.  I use this program to help clean up my
TV show collection.  After the show has been found online it 
will be entered into a local databse, provided sqlite3 is available,
for faster lookup in the future.  You are able to filter the shows
by season along with other options on the command line interface.
'''

import urllib2 
import re
import argparse
from contextlib import closing

try:
    import sqlite3 as databse
except ImportError:
    database = None

# output display format, season is padded with zeros
# Season - Episode Number - Episode Title
DISPLAY = "Season {0} - Episode {1} - {2}"
        
class Episode(object):
    ''' A simple class to organize the episodes, an alternative would be
        to use a named tuple though this is easier '''
    def __init__(self, title, epNumber, season):
        self.title = title
        self.season = season
        self.episode = epNumber
        
    def __repr__(self):
        return DISPLAY.format(self.season, self.episode, self.title)
            
class EpParser(object):
    '''The main parser will poll the internet as well as a database
       looking for the show by using the parseData() function'''
    
    def __init__(self, showTitle, cache=None, verbose=False):
        ''' Proper title is used for the database/url while the display
        title is used for error messages/display purposes'''
        self.properTitle = EpParser.prepareTitle( showTitle.lower() )
        self.displayTitle = showTitle
        
        self.url = "http://epguides.com/" + self.properTitle
        self.episodeList = []
        self.cache = cache
        self.verbose = verbose

    @staticmethod 
    def prepareTitle(title):
        '''Remove any punctuation and whitespace from the title'''
        exclude = set('!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~')
        title = ''.join(ch for ch in title if ch not in exclude)
        title = title.split()
        if title[0] == 'the': 
            title.remove('the')
        return ''.join(title)

    def parseData(self):
        ''' The main driver function of this class, it will poll
        the database first, if the show dosen't exist it will
        then try the internet. '''

        if self.cache is not None:
            self.episodeList = self.parseCacheData()

        # The show was found in the database
        if self.episodeList != []:
            if self.verbose: 
                print "Show found in database"
            self.cache.close()
            return self.episodeList

        # The show was not in the database so now we try the website
        if self.verbose: 
            print "Show not found in database, polling web"
        self.episodeList = self.parseHTMLData()

        # If we successfully find the show from the internet then
        # we should add it to our database for later use
        if self.cache is not None:
            if self.verbose: 
                print "Adding show to the database"
            self.cache.addShow( self.properTitle, self.episodeList )
            self.cache.close()

        return self.episodeList
            
    def parseCacheData(self):
        '''The query should return a positive show id otherwise 
        it's not in the database'''
        showId = self.cache.getShowId(self.properTitle)

        if showId == -1: 
            return []

        return self.cache.getEpisodes(showId)
        

    def getHTMLData(self):
        ''' Fetch the site data and return its contents'''
        with closing(urllib2.urlopen( self.url )) as request:
            if request.getcode() == 200:
                return request.readlines()
            else: return []
            
    def parseHTMLData(self):
        ''' Passes the sites contents through the regex to seperate episode
        information such as name, episode number, and title.  After getting
        the data from the regex we will occupy the episode list '''
        try:
            data = self.getHTMLData()
        except urllib2.HTTPError:
            exit("ERROR: Show was not found, check spelling and try again")
            
        episodes = []
        pattern = r"""
            ^		                # Start of the string
            (?:[\s]*?[\d]*\.?)	    # Number on list
            [\s]{2,}		        # Ignore whitespace
            (?P<season>[\d]*)	    # Season number
            -			            # Separator
            [\s]*			        # Optional whitespace
            (?P<episode>[\d]*)	    # Episode number
            [\s]{2,}		        # Whitespace
            (?P<product>.+|)	    # Product number
            [\s]{2,}		        # Whitespace
            (?P<airdate>[\w\s/]*?)  # Air-date
            [\s]{2,}		        # Ignore whitespace
            (?P<name>.*)		    # Episode name
            $			            # End of line
            """
        regex = re.compile(pattern, re.X|re.I )

        for line in data:
            info = regex.match(line)
            if info is not None:
                name = info.group('name')
                episode = info.group('episode')
                season = int(info.group('season'))
                name = re.sub('<.*?>', '', name).strip()
                episodes.append( Episode(name, episode, season) )
        return episodes

class Cache(object):
    ''' Our database logic class'''
    _sqlquery = '''
        CREATE TABLE shows (
            sid INTEGER PRIMARY KEY,
            title TEXT
        );
        CREATE TABLE episodes (
            eid INTEGER PRIMARY KEY,
            sid INTEGER,
            eptitle TEXT,
            season INTEGER,
            showNumber INTEGER,			
            FOREIGN KEY(sid) REFERENCES shows(sid)
        );'''
    
    def __init__(self, recreate=False, dbName="episodes.db", verbose=False):
        self.connection = databse.connect(dbName)
        self.cursor = self.connection.cursor()
        self.verbose = verbose
        if recreate == True:
            if self.verbose: 
                print "Making a new cache"
            self.cursor.executescript( Cache._sqlquery )

    def close(self):
        ''' Commits any changes to the database then closes connections to it'''
        self.cursor.close()
        self.connection.commit()
        self.connection.close()

    def getShowId(self, showTitle):
        ''' Polls the database for the shows title then returns its show id'''
        title = (showTitle, )
        self.cursor.execute("SELECT sid FROM shows WHERE title=?", title)
        result = self.cursor.fetchone()
        if result is not None:
            return result[0]
        else:
            return -1

    def getEpisodes(self, showId):
        ''' Using the show id return the shows associated with that id'''
        sid = (showId, )
        self.cursor.execute(
            "SELECT eptitle, shownumber, season FROM episodes\
             WHERE sid=?", sid)
        
        result = self.cursor.fetchall()
        eps = []
        
        if result is not None:
            for episode in result:
                eps.append( Episode(episode[0], episode[1], episode[2]) )

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
    
def main():
    ''' Our main function for our command line interface'''
    parser = argparse.ArgumentParser(description="TV Show Information Parser")

    parser.add_argument('title', 
            help="The title of the show")
    
    parser.add_argument('-s', '--season', default=-1, type=int, metavar='n', 
            help="The specific season to search for")
    
    parser.add_argument('-d', '--display-header', action="store_true", 
            help="Display the header at the top of the output")
    
    parser.add_argument('-v', '--verbose', action="store_true", 
            help="Be verbose, enable additional output")

    parser.add_argument('-r', '--recreatecache', action="store_true", 
            help="Will recreate the cache from scratch, be sure you want to")
    
    namespace = parser.parse_args()
    verbose   = namespace.verbose
    title     = namespace.title
    season    = namespace.season
    newCache  = namespace.recreatecache
    displayheader = namespace.display_header	

    cache = None
    if databse is not None:
        cache = Cache(recreate=newCache, verbose=verbose)
        
    # Pass the cache instance as well as the title, the result
    # will be the list of episodes and their information
    episodeParser = EpParser(title, cache, verbose=verbose)
    results = episodeParser.parseData()

    if displayheader or verbose:
        print "\nShow: {0}".format(title)
        print "Number of episodes: {0}".format(len(results))
        print "Number of seasons: {0}".format( results[-1].season )
        print "-" * 30

    
    # If the user specified a specific season we will filter our results
    # this also checks to make sure its a reasonable season number
    if 0 < season < results[-1].season:
        results = [ x for x in results if x.season == season ]

    currSeason = results[0].season
    for eps in results:
        if currSeason != eps.season and (displayheader or verbose) :
            print "\nSeason {0}".format(eps.season)
            print "----------"
        print eps
        currSeason = eps.season


if __name__ == '__main__':
    main()	

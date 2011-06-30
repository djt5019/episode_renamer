# -*- coding: utf-8 -*-
# author:  Dan Tracy
# program: utils.py

import resources.episode_sources as sources
import Utils

class EpParser(object):
    '''The main parser will poll the internet as well as a database
       looking for the show by using the parseData() function'''
    
    def __init__(self, showTitle, cache=None, verbose=False):
        ''' Proper title is used for the database/url while the display
        title is used for error messages/display purposes'''
        self.properTitle = Utils.prepareTitle( showTitle.lower() )
        self.title = showTitle
        self.episodeList = []
        self.cache = cache
        self.verbose = verbose

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

        return self.episodeList
            
    def parseCacheData(self):
        '''The query should return a positive show id otherwise 
        it's not in the database'''
        showId = self.cache.getShowId(self.properTitle)

        if showId == -1: 
            return []

        return self.cache.getEpisodes(showId)
                
    def parseHTMLData(self):
        ''' Passes the sites contents through the regex to seperate episode
        information such as name, episode number, and title.  After getting
        the data from the regex we will occupy the episode list '''  
        episodes = sources.locate_show(self.title, self.verbose)
        
        if not episodes:
            exit("ERROR: Show was not found, check spelling and try again")
                        
        return episodes


# -*- coding: utf-8 -*-
__author__='Dan Tracy'
__email__='djt5019 at gmail dot com'

import ConfigParser
import re
import os
import zlib

import Utils
import Constants
import Logger

from math import log10

from EpParser.src.Settings import Settings

class Show(object):
    """A convenience class to keep track of the list of episodes as well as
       to keep track of the custom formatter for those episodes"""
    def __init__(self, seriesTitle):
        self.title = Utils.encode(seriesTitle.title())
        self.properTitle = Utils.prepare_title(self.title)
        self.episodeList = []
        self.episodesBySeason = {}
        self.specialsList = []
        self.formatter = EpisodeFormatter(self)
        self.numSeasons = 0
        self.maxEpisodeNumber = 0

    def add_episodes(self, eps=None):
        """ Add episodes to the shows episode list """
        if not eps:
            return

        self.episodeList = eps
        self.numSeasons = eps[-1].season
        self.maxEpisodeNumber = max( x.episodeNumber for x in eps )
        self.numEpisodes = len(eps)
        for s in xrange(self.numSeasons+1):
            # Split each seasons episodes into it's own separate list and index it
            # by the season number.  Very easy for looking up individual episodes
            self.episodesBySeason[s] = filter(lambda x: x.season == s, self.episodeList)

    @property
    def show_title(self):
        return self.title

    @show_title.setter
    def show_title(self, val):
        self.title = Utils.encode(val.title())
        self.properTitle = Utils.prepare_title(val)

    def get_episode(self, season, episode):
        """ Returns a specific episode from a specific season, None if it's not present
        """
        if episode < 1:
            return None

        if season > 0:
            season = self.episodesBySeason.get(season, None)
            if season:
                return season[episode-1]  # Adjust by one since episodes start count at 1 not 0
            else:
                return None
        else:
            return self.episodeList[episode-1]


class Episode(object):
    """ A simple class to organize the episodes, an alternative would be
        to use a namedtuple though this is easier """
    def __init__(self, title, epNumber, season, episodeCount):
        self.title = Utils.encode(title)
        self.season = int(season)
        self.episodeNumber = int(epNumber)
        self.episodeCount = int(episodeCount)


class EpisodeFile(object):
    """
    Represents a TV show file.  Used for renaming purposes
    """
    def __init__(self, path, index, season=-1, checksum=-1):
        self.path = path
        self.index = index
        self.season = season
        self.ext = os.path.splitext(self.path)[1]
        self.name = Utils.encode(os.path.split(self.path)[1])
        self.given_checksum = checksum

    def crc32(self):
        with open(self.path, 'rb') as f:
            checksum = 0
            for line in f:
                checksum = zlib.crc32(line, checksum)

        return hex( checksum & 0xFFFFFFFF )
        
    def compare_sums(self):
        if self.given_checksum:
            return self.given_checksum == self.crc32()
            
        return False


class EpisodeFormatter(object):
    def __init__(self, show, fmt=None):
        """Allows printing of custom formatted episode information"""
        formatString = u"<series> - Episode <count> - <title>"
        self.show = show
        self.formatString = Utils.encode(fmt) if fmt else formatString
        self.tokens = self.formatString.split()
        self.episodeNumberTokens = {"episode", "ep"}
        self.seasonTokens = {"season"}
        self.episodeNameTokens = {"title", "name", "epname"}
        self.seriesNameTokens = {"show", "series"}
        self.episodeCounterTokens = {"count", "number"}
        self.hashTokens = {"crc32", "hash", "sum", "checksum"}
        re_format = '(?P<tag>\{}.*?\{})'.format(Settings['tag_start'], Settings['tag_end'])
        self.re = re.compile(re_format, re.I)

    def set_format(self, fmt=None):
        """Set the format string for the formatter"""
        if fmt is not None:
            self.formatString = Utils.encode( fmt )
            self.tokens = self.formatString.split()

    def load_format_config(self, configFileName=None):
        """Load tokens from the format config file in RESOURCEPATH"""
        if not configFileName:
            path = os.path.join(Constants.RESOURCE_PATH, Settings['tag_config'])
        else:
            path = os.path.join(Constants.RESOURCE_PATH, configFileName)

        if not os.path.exists(path):
            Logger.get_logger().warning("Tag config file was not found")
            return

        cfg = ConfigParser.ConfigParser()
        cfg.read(path)

        allTokens = set()

        for s in cfg.sections():
            tokens = cfg.get(s, 'tags')

            if tokens == "":
                Logger.get_logger().error("No tags for section [{}], using defaults".format(s))
                continue

            if ',' in tokens:
                tokens = { t.strip() for t in tokens.split(',') }
            else:
                tokens = { tokens }

            for f in tokens.intersection(allTokens):  
                #Look for duplicates
                Logger.get_logger().error("In section [{}]: token '{}' redefined".format(s,f))
                tokens.remove(f)

            allTokens = allTokens.union(tokens)

            if s == 'episode_name':
                self.episodeNameTokens = tokens
            elif s == "episode_number":
                self.episodeNumberTokens = tokens
            elif s == "episode_count":
                self.episodeCounterTokens = tokens
            elif s == "series_name":
                self.seriesNameTokens = tokens
            elif s == "season_number":
                self.seasonTokens = tokens
            elif s == "hash":
                self.hashTokens = tokens

    def display(self, ep, epFile=None):
        """Displays the episode according to the users format"""
        args = []

        for token in self.tokens:
            tags = self.re.split(token)

            if not tags:
                args.append( token )
                continue

            a = []
            for tag in tags:
                if self.re.match(tag):
                    #If it's a tag try to resolve it
                    a.append( self._parse(ep, tag[1:-1], epFile) )
                else:
                    a.append(tag)

            args.append( ''.join(a) )

        return Utils.encode(' '.join(args))

    def _parse(self, ep, tag, epFile=None):
        caps = lower = pad = False
        tag = tag.lower()

        # Tag modifiers such as number padding and caps
        if ':pad' in tag:
            tag = tag.replace(':pad','').strip()
            pad = True
        if ':caps' in tag:
            tag = tag.replace(':caps','').strip()
            caps = True
        if ':upper' in tag:
            tag = tag.replace(':upper','').strip()
            caps = True
        if ':lower' in tag:
            tag = tag.replace(':lower','').strip()
            lower = True
        if ':' in tag:
            tag = tag.split(':',2)[0]

        if tag in self.episodeNumberTokens:
            if pad: 
                #Obtain the number of digits in the highest numbered episode
                pad = int( log10(self.show.maxEpisodeNumber) + 1)
            return str(ep.episodeNumber).zfill(pad)

        elif tag in self.seasonTokens:
            if pad: 
                #Number of digits in the highest numbered season
                pad = int(log10(self.show.numSeasons) + 1)
            return str(ep.season).zfill(pad)

        elif tag in self.episodeCounterTokens:
            if pad: 
                #Total number of digits
                pad = int(log10(self.show.numEpisodes) + 1)
            return str(ep.episodeCount).zfill(pad)

        elif tag in self.episodeNameTokens:
            if lower:
                return ep.title.lower()
            elif caps:
                return ep.title.upper()
            return ep.title

        elif tag in self.seriesNameTokens:
            if lower:
                return self.show.title.lower()
            elif caps:
                return self.show.title.upper()
            return self.show.title.title()

        elif tag in self.hashTokens:
            if not epFile:
                return Settings['tag_start'] + tag + Settings['tag_end']

            if hasattr(epFile, 'crc32'):
                return str(epFile.crc32())[2:]  # To remove the 0x from the hex string

        else: 
            # If it reaches this case it's most likely an invalid tag
            return Settings['tag_start'] + tag + Settings['tag_end']

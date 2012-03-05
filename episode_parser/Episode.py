# -*- coding: utf-8 -*-
__author__ = 'Dan Tracy'
__email__ = 'djt5019 at gmail dot com'

import ConfigParser
import re
import os
import zlib
import string

import Utils
import Constants
import Logger
import Exceptions

from Settings import Settings


class Show(object):
    """
    A convenience class to keep track of the list of episodes as well as
    to keep track of the custom formatter for those episodes
    """
    def __init__(self, seriesTitle):
        self.title = Utils.encode(string.capwords(seriesTitle))
        self.properTitle = Utils.prepare_title(seriesTitle.lower())
        self.episodeList = []
        self.episodesBySeason = {}
        self.specialsList = []
        self.formatter = EpisodeFormatter(self)
        self.numSeasons = 0
        self.maxEpisodeNumber = 0

    def add_episodes(self, eps):
        """
        Add episodes to the shows episode list
        """
        if eps:
            self.episodeList = eps
            self.numSeasons = eps[-1].season
            self.maxEpisodeNumber = max(x.episodeNumber for x in eps)
            self.numEpisodes = len(eps)

            for s in xrange(self.numSeasons + 1):
                # Split each seasons episodes into it's own separate list and index it
                # by the season number.  Very easy for looking up individual episodes
                self.episodesBySeason[s] = filter(lambda x: x.season == s, self.episodeList)

    def add_specials(self, specials):
            self.specialsList = specials

    @property
    def show_title(self):
        return self.title

    @show_title.setter
    def show_title(self, val):
        """
        Sets the show's title to the value passed as well as prepares it for use
        """
        Logger.get_logger().debug("Setting show title to: {}".format(val))
        self.title = Utils.encode(val.capitalize())
        self.properTitle = Utils.prepare_title(val)

    def get_season(self, season):
        """
        Returns a list of episodes within the season or an empty list
        """
        return self.episodesBySeason.get(season, [])

    def get_episode(self, season, episode):
        """
        Returns a specific episode from a specific season or None
        """
        if not 0 < episode < len(self.episodeList) + 1:
            return None

        # Adjust by one since episodes start count at 1 not 0
        episode = episode - 1

        if season > 0:
            season = self.episodesBySeason.get(season, None)
            if season:
                return season[episode]
            else:
                return None
        else:
            return self.episodeList[episode]

    def get_special(self, special_number):
        if 0 < special_number < len(self.specialsList) + 1:
            return self.specialsList[special_number - 1]
        return None


class Episode(object):
    """
    A simple class to organize the episodes
    """
    def __init__(self, episode_title, episode_number, season, episode_count):
        """
        A container for an episode's information collected from the web
        """
        self.title = Utils.encode(episode_title)
        self.season = int(season)
        self.episodeNumber = int(episode_number)
        self.episodeCount = int(episode_count)
        self.episode_file = None


class Special(object):
    """
    Container class for Specials/Movies/OVAs
    """
    def __init__(self, special_title, special_number, special_type):
        self.title = special_title
        self.num = int(special_number)
        self.type = special_type
        self.episode_file = None


class EpisodeFile(object):
    """
    Represents a TV show file.  Used for renaming purposes
    """
    def __init__(self, path, **args):
        """
        A physical episode on disk
        """
        self.path = path
        self.ext = os.path.splitext(self.path)[1]
        self.name = Utils.encode(os.path.split(self.path)[1])
        self.new_name = ""
        self.verified = False
        self.__dict__.update(args)
        self.is_ova = ('special_number' in args)
        self.episode_number = self.__dict__.get('episode_number', -1)

    def crc32(self):
        """
        Calculate the CRC32 checksum for a file, painfully slow
        """
        Logger.get_logger().info("calculating CRC for {}".format(os.path.split(self.path)[1]))
        with open(self.path, 'rb') as f:
            checksum = 0
            for line in f:
                checksum = zlib.crc32(line, checksum)

        return checksum & 0xFFFFFFFF

    def verify_integrity(self):
        """
        Compares the checksum in the filename to the calculated one
        """
        if self.verified:
            return True

        if self.given_checksum > 0:
            if self.given_checksum == self.crc32():
                self.verified = True
                return True
        return False


class EpisodeFormatter(object):
    def __init__(self, show, fmt=None):
        """
        Allows printing of custom formatted episode information
        """
        formatString = u"<series> - <type> <count> - <title>"
        self.show = show
        self.formatString = Utils.encode(fmt) if fmt else formatString
        self.tokens = self.formatString.split()
        self.episodeTypeTokens = set(['type'])
        self.episodeNumberTokens = set(["episode", "ep"])
        self.seasonTokens = set(["season"])
        self.episodeNameTokens = set(["title", "name", "epname"])
        self.seriesNameTokens = set(["show", "series"])
        self.episodeCounterTokens = set(["count", "number"])
        self.hashTokens = set(["crc32", "hash", "sum", "checksum"])
        re_format = '(?P<tag>\{}.*?\{})'.format(Settings['tag_start'], Settings['tag_end'])
        self.re = re.compile(re_format, re.I)

    def set_format(self, fmt=None):
        """
        Set the format string for the formatter
        """
        if fmt is not None:
            self.formatString = Utils.encode(fmt)
            self.tokens = self.formatString.split()

    def load_format_config(self, configFileName=None):
        """
        Load tokens from the format config file in RESOURCEPATH
        """
        if not configFileName:
            path = os.path.join(Constants.RESOURCE_PATH, Settings['tag_config'])
        else:
            path = os.path.join(Constants.RESOURCE_PATH, configFileName)

        if not os.path.exists(path):
            Logger.get_logger().warning("Tag config file was not found")
            raise Exceptions.FormatterException("Tag config file was not found")
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
                tokens = set(t.strip() for t in tokens.split(','))
            else:
                tokens = set(tokens)

            for f in tokens.intersection(allTokens):
                #Look for duplicates
                Logger.get_logger().error("In section [{}]: token '{}' redefined".format(s, f))
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

    def display(self, ep):
        """
        Displays the episode according to the users format
        """
        args = []

        for token in self.tokens:
            tags = self.re.split(token)

            if not tags:
                args.append(token)
                continue

            a = []
            for tag in tags:
                if self.re.match(tag):
                    #If it's a tag try to resolve it
                    a.append(self._parse(ep, tag[1:-1]))
                else:
                    a.append(tag)

            args.append(''.join(a))

        return Utils.encode(' '.join(args))

    def _parse(self, ep, tag):
        if isinstance(ep, Special):
            return self._parse_special(ep, tag)
        else:
            return self._parse_episode(ep, tag)

    def _parse_episode(self, ep, tag):
        """
        Tokenize and substitute tags for their values using an episode
        as well as the episode file for reference
        """
        caps = lower = pad = False
        tag = tag.lower()

        # Tag modifiers such as number padding and caps
        if ':pad' in tag:
            tag = tag.replace(':pad', '').strip()
            pad = True
        if ':caps' in tag:
            tag = tag.replace(':caps', '').strip()
            caps = True
        if ':upper' in tag:
            tag = tag.replace(':upper', '').strip()
            caps = True
        if ':lower' in tag:
            tag = tag.replace(':lower', '').strip()
            lower = True
        if ':' in tag:
            tag = tag.split(':', 2)[0]

        if tag in self.episodeNumberTokens:
            if pad:
                #Obtain the number of digits in the highest numbered episode
                pad = len(str(self.show.maxEpisodeNumber))
            return str(ep.episodeNumber).zfill(pad)

        elif tag in self.episodeTypeTokens:
            return "Episode"

        elif tag in self.seasonTokens:
            if pad:
                #Number of digits in the highest numbered season
                pad = len(str(self.show.numSeasons))
            return str(ep.season).zfill(pad)

        elif tag in self.episodeCounterTokens:
            if pad:
                #Total number of digits
                pad = len(str(self.show.numEpisodes))
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
            return self.show.title

        elif tag in self.hashTokens:
            if not ep.episode_file:
                return Settings['tag_start'] + tag + Settings['tag_end']

            if hasattr(ep.episode_file, 'crc32'):
                # To remove the 0x from the hex string
                checksum = hex(ep.episode_file.crc32())[2:]
                if checksum.endswith('L'):
                    checksum = checksum.replace('L', '')
                return checksum

        else:
            # If it reaches this case it's most likely an invalid tag
            return Settings['tag_start'] + tag + Settings['tag_end']

    def _parse_special(self, ep, tag):
        """
        Tokenize and substitute tags for their values using an episode
        as well as the episode file for reference
        """
        caps = lower = pad = False
        tag = tag.lower()

        # Tag modifiers such as number padding and caps
        if ':pad' in tag:
            tag = tag.replace(':pad', '').strip()
            pad = True
        if ':caps' in tag:
            tag = tag.replace(':caps', '').strip()
            caps = True
        if ':upper' in tag:
            tag = tag.replace(':upper', '').strip()
            caps = True
        if ':lower' in tag:
            tag = tag.replace(':lower', '').strip()
            lower = True
        if ':' in tag:
            tag = tag.split(':', 2)[0]

        if tag in self.episodeNumberTokens:
            if pad:
                #Obtain the number of digits in the highest numbered episode
                pad = len(str(self.show.specialList[-1].num))
            return str(ep.num).zfill(pad)

        elif tag in self.episodeTypeTokens:
            return ep.type

        elif tag in self.episodeCounterTokens:
            if pad:
                #Total number of digits
                pad = len(str(self.show.specialsList[-1].num))
            return str(ep.num).zfill(pad)

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
            return self.show.title

        elif tag in self.hashTokens:
            if not ep.episode_file:
                return Settings['tag_start'] + tag + Settings['tag_end']

            if hasattr(ep.episode_file, 'crc32'):
                # To remove the 0x from the hex string
                checksum = hex(ep.episode_file.crc32())[2:]
                if checksum.endswith('L'):
                    checksum = checksum.replace('L', '')
                return checksum

        else:
            # If it reaches this case it's most likely an invalid tag
            return Settings['tag_start'] + tag + Settings['tag_end']

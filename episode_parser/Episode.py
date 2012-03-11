# -*- coding: utf-8 -*-
__author__ = 'Dan Tracy'
__email__ = 'djt5019 at gmail dot com'

import re
import os
import zlib
import string
import logging

import Utils
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
        logging.debug("Setting show title to: {}".format(val))
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
        self.type = "Episode"


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
    def __init__(self, path, **kwargs):
        """
        A physical episode on disk
        """
        self.path = path
        self.ext = os.path.splitext(self.path)[1]
        self.name = Utils.encode(os.path.split(self.path)[1])
        self.new_name = ""
        self.verified = False
        self.__dict__.update(kwargs)
        self.is_ova = ('special_number' in kwargs)
        self.episode_number = self.__dict__.get('episode_number', -1)

    def crc32(self):
        """
        Calculate the CRC32 checksum for a file, painfully slow
        """
        logging.info("calculating CRC for {}".format(os.path.split(self.path)[1]))
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
        self.show = show
        self.formatString = Utils.encode(fmt) if fmt else Settings['format']
        re_format = '(?P<tag>\{}.*?\{})'.format(Settings['tag_start'], Settings['tag_end'])
        self.re = re.compile(re_format, re.I)
        self.tokens = self.re.split(self.formatString)
        self.load_format_config()

    def set_format(self, fmt=None):
        """
        Set the format string for the formatter
        """
        if fmt is not None:
            self.formatString = Utils.encode(fmt)
            self.tokens = self.formatString.split()

    def load_format_config(self):
        """
        Load tokens from the format config file in RESOURCEPATH
        """
        allTokens = set()

        for s in Settings['tags']:
            tokens = set(Settings[s])

            redefined = tokens.intersection(allTokens)
            if redefined:
                #Look for duplicates
                msg = "In section [{}]: tokens '{}' redefined".format(s, map(str, redefined))
                logging.error(msg)
                raise Exceptions.FormatterException(msg)

            allTokens = allTokens.union(tokens)

            self.__dict__[s] = tokens

    def display(self, ep):
        """
        Displays the episode according to the users format
        """
        args = []
        strip_whitespace = re.compile(r'[\s]+')

        for token in self.tokens:
            if self.re.match(token):
                #If it's a tag try to resolve it
                token = strip_whitespace.sub("", token)
                args.append(self._parse(ep, token[1:-1]))
            else:
                args.append(token)

        return Utils.encode(''.join(args))

    def _parse_modifiers(self, tag):
        caps = lower = pad = False
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

        return tag, caps, lower, pad

    def _parse(self, ep, tag):
        """
        Tokenize and substitute tags for their values using an episode
        as well as the episode file for reference
        """
        tag = tag.lower()
        tag, upper, lower, pad = self._parse_modifiers(tag)

        if tag in self.episode_number_tags:
            return self._handle_episode_number(ep, tag, pad)

        elif tag in self.type_tags:
            if upper:
                return ep.type.upper()
            if lower:
                return ep.type.lower()
            return ep.type

        elif tag in self.season_number_tags:
            return self._handle_season(ep, tag, pad)

        elif tag in self.episode_count_tags:
            return self._handle_episode_counter(ep, tag, pad)

        elif tag in self.episode_name_tags:
            if lower:
                return ep.title.lower()
            elif upper:
                return ep.title.upper()
            return ep.title

        elif tag in self.series_name_tags:
            if lower:
                return self.show.title.lower()
            elif upper:
                return self.show.title.upper()
            return self.show.title

        elif tag in self.hash_tags:
            hash_ = self._handle_hash(ep, tag).lower()
            if lower:
                return hash_.lower()
            elif upper:
                return hash_.upper()
            return hash_

        else:
            # If it reaches this case it's most likely an invalid tag
            return Settings['tag_start'] + tag + Settings['tag_end']

    def _handle_season(self, ep, tag, pad=False):
        if isinstance(ep, Special):
            return tag

        if pad:
            #Number of digits in the highest numbered season
            pad = len(str(self.show.numSeasons))
        return str(ep.season).zfill(pad)

    def _handle_episode_number(self, ep, tag, pad=False):
        if isinstance(ep, Episode):
            if pad:
                pad = len(str(self.show.maxEpisodeNumber))
            return str(ep.episodeNumber).zfill(pad)
        else:
            if pad:
                pad = len(str(self.show.specialsList[-1].num))
            return str(ep.num).zfill(pad)

    def _handle_episode_counter(self, ep, tag, pad=False):
        if isinstance(ep, Episode):
            if pad:
                pad = len(str(self.show.numEpisodes))
            return str(ep.episodeCount).zfill(pad)
        else:
            if pad:
                pad = len(str(self.show.specialsList[-1].num))
            return str(ep.num).zfill(pad)

    def _handle_hash(self, ep, tag):
        if not ep.episode_file:
            return Settings['tag_start'] + tag + Settings['tag_end']

        if ep.episode_file.checksum > 0:
            return hex(ep.episode_file.checksum)[2:10]

        else:
            # To remove the 0x from the hex string
            return hex(ep.episode_file.crc32())[2:10]

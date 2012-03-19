# -*- coding: utf-8 -*-
from __future__ import unicode_literals

__author__ = 'Dan Tracy'
__email__ = 'djt5019 at gmail dot com'

import re
import os
import zlib
import string
import logging

import utils

from settings import Settings


class Show(object):
    """
    A convenience class to keep track of the list of episodes as well as
    to keep track of the custom formatter for those episodes
    """
    def __init__(self, seriesTitle):
        self.title = utils.encode(string.capwords(seriesTitle))
        self.proper_title = utils.prepare_title(seriesTitle.lower())
        self._episodeList = []
        self._episodes_by_season = {}
        self.specials = []
        self._formatter = None
        self.num_seasons = 0
        self.max_episode_number = 0

    @property
    def episodes(self):
        return self._episodeList

    @episodes.setter
    def episodes(self, eps):
        """
        Add episodes to the shows episode list
        """
        if eps:
            self._episodeList = eps
            self.num_seasons = eps[-1].season
            self.max_episode_number = max(x.episode_number for x in eps)
            self.num_episodes = len(eps)

            for ep in self._episodeList:
                self._episodes_by_season.setdefault(ep.season, []).append(ep)

    @property
    def formatter(self):
        if self._formatter:
            return self._formatter
        else:
            raise AttributeError("Formatter not attached to this show '{}'".format(self.show_title))

    @formatter.setter
    def formatter(self, fmt=None):
        if not fmt or not isinstance(fmt, EpisodeFormatter):
            raise ValueError("Expected a formatter but got {}".format(type(fmt)))

        self._formatter = fmt
        self._formatter.show = self

    @property
    def show_title(self):
        return self.title

    @show_title.setter
    def show_title(self, val):
        """
        Sets the shows title to the value passed as well as prepares it for use
        """
        logging.debug("Setting show title to: {}".format(val))
        self.title = utils.encode(val.capitalize())
        self.proper_title = utils.prepare_title(val)

    def get_season(self, season):
        """
        Returns a list of episodes within the season or an empty list
        """
        return self._episodes_by_season.get(season, [])

    def get_episode(self, episode, season=0):
        """
        Returns a specific episode from a specific season or None
        """
        if not 0 < episode < len(self.episodes) + 1:
            return None

        # Adjust by one since episodes start count at 1 not 0
        episode -= 1

        if season > 0:
            season = self._episodes_by_seasonSeason.get(season, None)
            if season:
                return season[episode]
            else:
                return None
        else:
            return self.episodes[episode]

    def get_special(self, special_number):
        if 0 < special_number < len(self.specials) + 1:
            return self.specials[special_number - 1]
        return None


class Episode(object):
    """
    A simple class to organize the episodes
    """
    def __init__(self, episode_title, episode_number, season, episode_count):
        """
        A container for an episode's information collected from the web
        """
        self.title = utils.encode(episode_title)
        self.season = int(season)
        self.episode_number = int(episode_number)
        self.episode_count = int(episode_count)
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
        self.name = utils.encode(os.path.split(self.path)[1])
        self.new_name = ""
        self.verified = False
        self.__dict__.update(kwargs)
        self.is_ova = ('special_number' in kwargs)
        self.given_checksum = kwargs.get('checksum', 0)
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
        self.show_ = show
        self._format_string = utils.encode(fmt) if fmt else Settings['format']

        ## Use negative lookahead assertion to ensure that the tag had not been escaped
        re_format = r'(?<!\\)(?P<tag>\{start}.*?\{end})'
        re_format = re_format.format(start=Settings['tag_start'], end=Settings['tag_end'])

        self.re = re.compile(re_format, re.I)
        self.tokens = self.re.split(self._format_string)
        self.strip_whitespace_regex = re.compile(r'[\s]+')

        self.episode_number_tags = None
        self.type_tags = None
        self.season_number_tags = None
        self.episode_count_tags = None
        self.episode_name_tags = None
        self.hash_tags = None
        self.series_name_tags = None
        self.tags = filter(lambda x: x.endswith('tags'), dir(self))
        self.settings = dict(upper=False, lower=False, pad=False, proper=False)
        self.load_format_config()

    @property
    def show(self):
        return self.show_

    @show.setter
    def show(self, show=None):
        if not show:
            raise AttributeError("Expected a Show object but got {}".format(type(show)))
        logging.debug("Setting show to {}".format(show.title))
        self.show_ = show

    @property
    def format_string(self):
        return self._format_string

    @format_string.setter
    def format_string(self, fmt=None):
        """
        Set the format string for the formatter
        """
        if fmt is not None:
            self._format_string = utils.encode(fmt)
            self.tokens = self.re.split(fmt)
        else:
            raise AttributeError("Empty format string set")

    def load_format_config(self):
        """
        Load tokens from the format setting in settings.py
        """
        allTokens = set()
        for s in self.tags:
            tokens = set(Settings[s])

            redefined = tokens.intersection(allTokens)
            if redefined:
                #Look for duplicates
                msg = "In section [{}]: tokens '{}' redefined".format(s, map(str, redefined))
                logging.error(msg)
                raise AttributeError(msg)

            allTokens = allTokens.union(tokens)

            self.__dict__[s] = tokens

    def display(self, ep):
        """
        Displays the episode according to the users format
        """
        args = []
        escaped_token = "\{}".format(Settings['tag_start'])
        for token in self.tokens:
            if escaped_token in token:
                args.append(token.replace(escaped_token, Settings['tag_start']))
            elif self.re.match(token):
                #If it's a tag try to resolve it
                token = self.strip_whitespace_regex.sub("", token)
                args.append(self._parse(ep, token[1:-1]))
            else:
                args.append(token)

        return utils.encode(''.join(args))

    def _parse_modifiers(self, tag):
        # Tag modifiers such as number padding and caps
        if ':' in tag:
            res = re.split(':', tag)
            tag = res[0]
            modifiers = res[1:]
        else:
            return tag

        if 'pad' in modifiers:
            self.settings['pad'] = True

        if 'caps' in modifiers or 'upper' in modifiers:
            self.settings['upper'] = True
        elif 'lower' in modifiers:
            self.settings['lower'] = True
        elif 'proper' in modifiers:
            self.settings['proper'] = True

        return tag

    def _parse(self, ep, tag):
        """
        Tokenize and substitute tags for their values using an episode
        as well as the episode file for reference
        """
        self.settings['proper'] = False
        self.settings['upper'] = False
        self.settings['lower'] = False
        self.settings['pad'] = False

        tag = self._parse_modifiers(tag.lower())

        if tag in self.episode_number_tags:
            return self._handle_episode_number(ep)

        elif tag in self.type_tags:
            return self._handle_string(ep.type)

        elif tag in self.season_number_tags:
            return self._handle_season(ep)

        elif tag in self.episode_count_tags:
            return self._handle_episode_counter(ep)

        elif tag in self.episode_name_tags:
            return self._handle_string(ep.title)

        elif tag in self.series_name_tags:
            return self._handle_string(self.show.title)

        elif tag in self.hash_tags:
            return self._handle_hash(ep)

        else:
            # If it reaches this case it's most likely an invalid tag
            return Settings['tag_start'] + tag + Settings['tag_end']

    def _handle_string(self, string_):
        if self.settings['lower']:
            return string_.lower()
        elif self.settings['upper']:
            return string_.upper()
        elif self.settings['proper']:
            return string.capwords(string_)
        else:
            return string_

    def _handle_number(self, number, pad_length):
        if self.settings['pad']:
            return str(number).zfill(pad_length)
        else:
            return str(number)

    def _handle_season(self, ep):
        if isinstance(ep, Special):
            # Going on the basis that specials don't have seasons
            return ""

        pad = len(str(self.show.num_seasons))
        return self._handle_number(ep.season, pad)

    def _handle_episode_number(self, ep):
        if isinstance(ep, Episode):
            number = ep.episode_number
            pad = len(str(self.show.max_episode_number))
        else:
            number = ep.num
            pad = len(str(self.show.specials[-1].num))

        return self._handle_number(number, pad)

    def _handle_episode_counter(self, ep):
        if isinstance(ep, Episode):
            number = ep.episode_count
            pad = len(str(self.show.num_episodes))
        else:
            number = ep.num
            pad = len(str(self.show.specials[-1].num))

        return self._handle_number(number, pad)

    def _handle_hash(self, ep):
        if not ep.episode_file:
            return "00000000"

        if ep.episode_file.checksum > 0:
            return self._handle_string(hex(ep.episode_file.checksum))

        else:
            # To remove the 0x from the hex string
            return self._handle_string(hex(ep.episode_file.crc32())[2:10])

# -*- coding: utf-8 -*-
"""
Module contains logic and containers for dealing with shows/episodes/specials
"""
from __future__ import unicode_literals, absolute_import

import re
import zlib
import string
import logging

from eplist import utils

from eplist.settings import Settings
from eplist.constants import AttributeDict


class Episode(AttributeDict):
    """
    A simple class to organize the episodes/specials
    """
    def __init__(self, **kwargs):
        """
        A container for an episode's information collected from the web
        """
        #title, number, season=1, count=-1,
        super(Episode, self).__init__(kwargs)
        self.title = utils.encode(kwargs['title'])
        self.season = int(kwargs.get('season', 1))
        self.number = int(kwargs['number'])
        self.count = int(kwargs.get('count', '-1'))
        self.type = kwargs.get('type', 'Episode')
        self.file = kwargs.get('file', None)
        self.is_special = (self.type.lower() != "episode")


class EpisodeFile(AttributeDict):
    """
    Represents a TV episode file on disk.  Used for renaming purposes
    """
    @property
    def is_special(self):
        return 'special_number' in self

    def crc32(self):
        """
        Calculate the CRC32 checksum for a file... slowly
        """
        logging.info("calculating CRC for {}".format(self.name))
        with open(self.path, 'rb') as ep_file:
            checksum = 0
            for line in ep_file:
                checksum = zlib.crc32(line, checksum)

        return checksum & 0xFFFFFFFF

    def verify_integrity(self):
        """
        Compares the checksum in the filename to the calculated one
        """
        if self.checksum:
            if self.crc32() == int(self.checksum, base=16):
                return True
        return False


class Show(object):
    """
    A convenience class to keep track of the list of episodes as well as
    to keep track of the custom formatter for those episodes
    """
    def __init__(self, seriesTitle, episodes=None):
        self.title = utils.encode(string.capwords(seriesTitle))
        self.proper_title = utils.prepare_title(seriesTitle.lower())
        self.episodes = []
        self.specials = []
        self._episodes_by_season = {}
        self.formatter = None

        if episodes:
            self.add_episodes(episodes)

    def add_episodes(self, eplist):
        """
        Add a list of specials and episodes to the show object.  They will be
        seperated into different lists depending if the are plain episodes
        or not.
        """
        if not eplist:
            return

        self.episodes = []
        self.specials = []

        eps, spc = [], []

        for e in eplist:
            if e.count < 0 or e.number < 0:
                continue

            if e.is_special:
                spc.append(e)
            else:
                eps.append(e)
                self._episodes_by_season.setdefault(e.season, []).append(e)

        self.episodes = sorted(eps, key=lambda x: x.count)
        self.specials = sorted(spc, key=lambda x: x.number)

    @property
    def num_episodes(self):
        """ Returns the number of episodes in the show """
        return len(self.episodes)

    @property
    def max_episode(self):
        """ Returns the highest episode number in the show """
        return max(x.number for x in self.episodes) if self.episodes else 0

    @property
    def num_seasons(self):
        """ The total number of seasons the show has """
        return self.episodes[-1].season

    @property
    def num_specials(self):
        """ Total count of special episodes """
        return self.specials[-1].number

    @property
    def show_title(self):
        """ The unicode form of the show's title """
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

    def get_episode(self, episode, season):
        """
        Returns a specific episode from a specific season or None
        """
        if episode < 0 or episode > self.num_episodes:
            return None

        # Adjust by one since episodes start count at 1 not 0
        episode -= 1

        season_list = self._episodes_by_season.get(season, None)

        if season_list and season > 1 and len(season_list) > episode:
            return season_list[episode]
        else:
            return self.episodes[episode]

    def get_special(self, special_number):
        """ Returns the specified special or None """
        if 0 < special_number < len(self.specials) + 1:
            return self.specials[special_number - 1]
        return None


class EpisodeFormatter(object):
    """
    Provides custom tag handling, formatting, printing of episode
    and special information based on settings in the config file
    """
    def __init__(self, show, fmt=None):
        """
        Allows printing of custom formatted episode information
        """
        self.show = show
        self._format_string = utils.encode(fmt) if fmt else Settings.format

        ## Use a negative lookahead assertion to ensure that the
        ## tag had not been escaped
        regex = r'(?<!\\)(?P<tag>\{start}.*?\{end})'

        regex = regex.format(start=Settings.tag_start,
                             end=Settings.tag_end)

        self.tag_regex = re.compile(regex, re.I)
        self.tokens = self.tag_regex.split(self._format_string)
        self.strip_whitespace_regex = re.compile(r'[\s]+')

        self.modifier_settings = {'upper': False, 'lower': False,
                                  'pad': False, 'proper': False}

        self.episode_number_tags = Settings.tags['episode_number_tags']
        self.type_tags = Settings.tags['type_tags']
        self.season_number_tags = Settings.tags['season_number_tags']
        self.episode_count_tags = Settings.tags['episode_count_tags']
        self.episode_name_tags = Settings.tags['episode_name_tags']
        self.hash_tags = Settings.tags['hash_tags']
        self.series_name_tags = Settings.tags['series_name_tags']

        self.check_for_duplicate_tokens()

    @property
    def format_string(self):
        """
        Return the current format string
        """
        return self._format_string

    @format_string.setter
    def format_string(self, fmt=None):
        """
        Set the format string for the formatter
        """
        if fmt:
            self._format_string = utils.encode(fmt)
            self.tokens = self.tag_regex.split(fmt)
        else:
            raise AttributeError("Empty format string set")

    def check_for_duplicate_tokens(self):
        """
        Load tokens from the format setting in settings.py
        """
        allTokens = set()
        for tag in Settings.tags:
            tokens = set(Settings.tags[tag])

            redefined = tokens.intersection(allTokens)
            if redefined:
                #Look for duplicates
                msg = "In section [{}]: tokens '{}' redefined"
                msg = msg.format(tag, (str(redef) for redef in redefined))
                logging.error(msg)
                raise AttributeError(msg)

            allTokens = allTokens.union(tokens)

    def display(self, episode):
        """
        Displays the episode according to the users format
        """
        args = []
        escaped_token = "\{}".format(Settings.tag_start)
        for token in self.tokens:
            if escaped_token in token:
                args.append(token.replace(escaped_token, Settings.tag_start))
            elif self.tag_regex.match(token):
                #If it's a tag try to resolve it
                token = self.strip_whitespace_regex.sub("", token)
                args.append(self._parse(episode, token[1:-1]))
            else:
                args.append(token)

        return utils.encode(''.join(args)).strip()

    def _parse_modifiers(self, tag):
        """ Handle tag modifiers such as number padding and caps """
        if ':' in tag:
            res = re.split(':', tag)
            tag = res[0]
            modifiers = res[1:]
        else:
            return tag

        if 'pad' in modifiers:
            self.modifier_settings['pad'] = True

        if 'caps' in modifiers or 'upper' in modifiers:
            self.modifier_settings['upper'] = True
        elif 'lower' in modifiers:
            self.modifier_settings['lower'] = True
        elif 'proper' in modifiers:
            self.modifier_settings['proper'] = True

        return tag

    def _parse(self, episode, tag):
        """
        Tokenize and substitute tags for their values using an episode
        as well as the episode file for reference
        """
        self.modifier_settings['proper'] = False
        self.modifier_settings['upper'] = False
        self.modifier_settings['lower'] = False
        self.modifier_settings['pad'] = False

        tag = self._parse_modifiers(tag.lower())

        if tag in self.episode_number_tags:
            return self._handle_episode_number(episode)

        elif tag in self.type_tags:
            return self._handle_string(episode.type)

        elif tag in self.season_number_tags:
            return self._handle_season(episode)

        elif tag in self.episode_count_tags:
            return self._handle_episode_counter(episode)

        elif tag in self.episode_name_tags:
            return self._handle_string(episode.title)

        elif tag in self.series_name_tags:
            return self._handle_string(self.show.title)

        elif tag in self.hash_tags:
            return self._handle_hash(episode)

        else:
            # If it reaches this case it's most likely an invalid tag
            return Settings.tag_start + tag + Settings.tag_end

    def _handle_string(self, string_):
        """ Applies modifiers to strings in the format """
        if self.modifier_settings['lower']:
            return string_.lower()
        elif self.modifier_settings['upper']:
            return string_.upper()
        elif self.modifier_settings['proper']:
            return string.capwords(string_)
        else:
            return string_

    def _handle_number(self, number, pad_length):
        """ Applies padding to numbers then converts them to strings """
        if self.modifier_settings['pad']:
            return str(number).zfill(pad_length)
        else:
            return str(number)

    def _handle_season(self, episode):
        """ Applies padding to season number """
        if episode.is_special:
            # Going on the basis that specials don't have seasons
            return ""

        pad = len(str(self.show.num_seasons))
        return self._handle_number(episode.season, pad)

    def _handle_episode_number(self, episode):
        """ Applies modifiers to the episode number """
        number = episode.number
        if not episode.is_special:
            pad = len(str(self.show.max_episode))
        else:
            pad = len(str(self.show.num_specials))

        return self._handle_number(number, pad)

    def _handle_episode_counter(self, episode):
        """ Applies modifiers to the episodes overall count """
        number = episode.count
        if not episode.is_special:
            pad = len(str(self.show.num_episodes))
        else:
            pad = len(str(self.show.num_specials))

        return self._handle_number(number, pad)

    def _handle_hash(self, episode):
        """
        Applies string modifiers to the episodes checksum.  Calculates it
        if it is necessary.
        """
        if not episode.file:
            return "00000000"

        if episode.file.checksum:
            checksum = episode.file.checksum
        else:
            # To remove the 0x from the hex string
            checksum = hex(episode.file.crc32())

        if checksum.startswith('0x'):
            checksum = checksum[2:]

        if checksum.endswith('L'):
            checksum = checksum[:-1]

        ## If the checksum is less than 8 digits, pad to to 8
        return self._handle_string(checksum.zfill(8))

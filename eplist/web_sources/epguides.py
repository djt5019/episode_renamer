# -*- coding: utf-8 -*-
__author__ = 'Dan Tracy'
__email__ = 'djt5019 at gmail dot com'

from eplist import utils
from eplist.episode import Episode

import re

priority = 2

pattern = r"""
            ^                       # Start of the string
            (?:[\s]*?[\d]*\.?)      # Number on list
            [\s]{2,}                # Ignore whitespace
            (?P<season>[\d]*)       # Season number
            -                       # Separator
            [\s]*                   # Optional whitespace
            (?P<episode>[\d]*)      # Episode number
            [\s]{2,}                # Whitespace
            (?P<product>.+|)        # Product number
            [\s]{2,}                # Whitespace
            (?P<airdate>[\w\s/]*?)  # Air-date
            [\s]{2,}                # Ignore whitespace
            (?P<name>.*)            # Episode name
            $                       # End of line
            """

epguides_regex = re.compile(pattern)


def poll(title):
    cleanTitle = utils.prepare_title(title)
    episodes = []
    url = "http://www.epguides.com/{0}".format(cleanTitle)
    fd = utils.get_url_descriptor(url)

    if fd is None:
        return utils.show_not_found

    count = 1
    for line in fd.iter_lines():
        info = epguides_regex.match(line)
        if info is not None:
            name = info.group('name')
            episode = info.group('episode')
            season = int(info.group('season'))
            name = re.sub('<.*?>', '', name).strip()

            if '[Trailer]' in name:
                name = name.replace('[Trailer]', '')

            if name == "TBA":
                continue

            episodes.append(Episode(name, episode, season, count))
            count += 1

    return episodes

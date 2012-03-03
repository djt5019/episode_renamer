# -*- coding: utf-8 -*-
__author__ = 'Dan Tracy'
__email__ = 'djt5019 at gmail dot com'

import difflib

from string import punctuation as punct

import episode_parser.Episode as Episode
import episode_parser.Logger as Logger
import episode_parser.Utils as API

try:
    from BeautifulSoup import BeautifulStoneSoup as Soup
except ImportError:
    Logger.get_logger().critical(u"Error: BeautifulSoup was not found, unable to parse AniDB")

priority = 3


def _parse_local(title):
    """
    Try to find the anime ID (aid) in the dump file provided by AniDB
    """
    if not API.file_exists_in_resources('animetitles.dat'):
        Logger.get_logger().warning("AniDB database file not found, unable to poll AniDB at this time")
        return -1

    regex = API.regex_compile(r'(?P<aid>\d+)\|(?P<type>\d)\|(?P<lang>.+)\|(?P<title>.*)')

    sequence = difflib.SequenceMatcher(lambda x: x in punct, title.lower())

    guesses = []

    with API.open_file_in_resources('animetitles.dat') as f:
        for line in f:
            res = regex.search(line)

            if not res:
                continue

            foundTitle = API.remove_punctuation(API.encode(res.group('title')))
            if title == foundTitle.lower():
                return res.group('aid')

            sequence.set_seq2(foundTitle.lower())
            ratio = sequence.ratio()

            if ratio > .80:
                guesses.append((ratio, res.group('aid'), foundTitle))

    if guesses:
        Logger.get_logger().info("{} possibilities".format(len(guesses)))
        _, aid, name = max(guesses)
        Logger.get_logger().error("Closest show to '{}' is {} with id {}".format(title, name, aid))

    return -1


def _connect_HTTP(aid):
    """
    Connect to AniDB using the public HTTP Api, this is used as an alternative to the UDP connection function
    """
    url = r'http://api.anidb.net:9001/httpapi?request=anime&client=eprenamer&clientver=1&protover=1&aid={}'.format(aid)

    resp = API.get_url_descriptor(url)

    if resp is None:
        return []

    soup = Soup(resp.content)

    if soup.find('error'):
        Logger.get_logger().error("Temporally banned from AniDB, most likely due to flooding")
        return []

    episodes = soup.findAll('episode')

    if not episodes:
        return []

    epList = []

    for e in episodes:
        # 1 is a normal episode, 2 is a special
        ep_type = e.epno.attrs[0][1]
        if ep_type not in ('1', '2'):
            continue

        title = e.find('title', {'xml:lang': 'en'})
        title = title.getText()

        if ep_type == '1':
            epNum = int(e.epno.getText())
            epList.append(Episode.Episode(API.encode(title), epNum, -1, epNum))
        else:
            epNum = int(e.epno.getText()[1:])
            epList.append(Episode.Special(API.encode(title), epNum, 'OVA'))

    return epList


def poll(title=""):
    try:
        Soup
    except NameError:
        return API.show_not_found

    aid = _parse_local(title.lower())

    if aid < 0:
        return API.show_not_found

    Logger.get_logger().info("Found AID: {}".format(aid))

    if API.able_to_poll('AniDB'):
        episodes = _connect_HTTP(aid)
        if episodes:
            return episodes

    return API.show_not_found

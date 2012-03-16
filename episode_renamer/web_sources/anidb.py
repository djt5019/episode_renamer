# -*- coding: utf-8 -*-
__author__ = 'Dan Tracy'
__email__ = 'djt5019 at gmail dot com'

import difflib
import logging

from string import punctuation as punct

from episode_renamer import Utils

from episode_renamer.Episode import Episode, Special

try:
    from BeautifulSoup import BeautifulStoneSoup as Soup
except ImportError:
    logging.critical(u"Error: BeautifulSoup was not found, unable to parse AniDB")

priority = 3


def _parse_local(title):
    """
    Try to find the anime ID (aid) in the dump file provided by AniDB
    """
    if not Utils.file_exists_in_resources('animetitles.dat'):
        logging.warning("AniDB database file not found, unable to poll AniDB at this time")
        logging.warning("Try using the --update-db option to download an copy of it")
        return -1

    title = title.lower()

    regex = Utils.regex_compile(r'(?P<aid>\d+)\|(?P<type>\d)\|(?P<lang>.+)\|(?P<title>.*)')

    sequence = difflib.SequenceMatcher(lambda x: x in punct, title.lower())

    guesses = []

    with Utils.open_file_in_resources('animetitles.dat') as f:
        for line in f:
            res = regex.search(line)

            if not res:
                continue

            original_title = Utils.encode(res.group('title').lower())
            clean_title = Utils.remove_punctuation(Utils.encode(res.group('title'))).lower()
            if title in (original_title, clean_title):
                return res.group('aid')

            sequence.set_seq2(clean_title.lower())
            ratio = sequence.ratio()

            if ratio > .80:
                guesses.append((ratio, res.group('aid'), original_title))

    if guesses:
        logging.info("{} possibilities".format(len(guesses)))
        guesses = sorted(guesses, key=lambda x: x.ratio)
        _, aid, name = guesses[0]
        logging.error("Closest show to '{}' is {} with id {}".format(title, name, aid))

        for guess in guesses[1:]:
            logging.info("Similar show {} [{}] also found".format(name, aid))

    return -1


def _connect_HTTP(aid):
    """
    Connect to AniDB using the public HTTP Api, this is used as an alternative to the UDP connection function
    """
    url = r'http://api.anidb.net:9001/httpapi?request=anime&client=eprenamer&clientver=1&protover=1&aid={}'.format(aid)

    resp = Utils.get_url_descriptor(url)

    if resp is None:
        return []

    soup = Soup(resp.content)

    if soup.find('error'):
        logging.error("Temporally banned from AniDB, most likely due to flooding")
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
            epList.append(Episode(Utils.encode(title), epNum, 1, epNum))
        else:
            epNum = int(e.epno.getText()[1:])
            epList.append(Special(Utils.encode(title), epNum, 'OVA'))

    return epList


def poll(title=""):
    try:
        Soup
    except NameError:
        return Utils.show_not_found

    aid = _parse_local(title.lower())

    if aid < 0:
        return Utils.show_not_found

    logging.info("Found AID: {}".format(aid))

    if Utils.able_to_poll('AniDB'):
        episodes = _connect_HTTP(aid)
        if episodes:
            return episodes

    return Utils.show_not_found

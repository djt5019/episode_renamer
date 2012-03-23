# -*- coding: utf-8 -*-
__author__ = 'Dan Tracy'
__email__ = 'djt5019 at gmail dot com'

import re
import difflib
import logging

from string import punctuation as punct

from eplist import utils

from eplist.episode import Episode, Special
from eplist.settings import Settings

try:
    from BeautifulSoup import BeautifulStoneSoup as Soup
except ImportError:
    logging.critical(u"Error: BeautifulSoup was not found, unable to parse AniDB")

priority = 3


def _parse_local(title):
    """
    Try to find the anime ID (aid) in the dump file provided by AniDB
    """
    if not utils.file_exists_in_resources('animetitles.dat'):
        logging.warning("AniDB database file not found, unable to poll AniDB at this time")
        logging.warning("Try using the --update-db option to download an copy of it")
        return -1

    title = title.lower()

    regex = re.compile(r'(?P<aid>\d+)\|(?P<type>\d)\|(?P<lang>.+)\|(?P<title>.*)')

    sequence = difflib.SequenceMatcher(lambda x: x in punct, title.lower())

    guesses = []

    with utils.open_file_in_resources('animetitles.dat') as f:
        for line in f:
            res = regex.search(line)

            if not res:
                continue

            original_title = utils.encode(res.group('title').lower())
            clean_title = utils.remove_punctuation(utils.encode(res.group('title'))).lower()

            if title in (original_title, clean_title):
                return res.group('aid')

            sequence.set_seq2(clean_title.lower())
            ratio = sequence.ratio()

            if ratio > .80:
                d = dict(ratio=ratio, aid=res.group('aid'), title=original_title)
                guesses.append(d)

    if guesses:
        logging.info("{} possibilities".format(len(guesses)))
        guesses = sorted(guesses, key=lambda x: x['ratio'])
        aid = guesses[0]['aid']
        name = guesses[0]['title']
        logging.error("Closest show to '{}' is '{}'' with id {}".format(title, name, aid))

        for guess in guesses[1:]:
            logging.info("Similar show {} [{}] also found".format(name, aid))

    return -1


def _connect_UDP(aid):
    ## Todo: make this work so we stop relying on the http protocol
    raise NotImplementedError("I will get to this later... promise.")

    if not Settings['anidb_username'] or not Settings['anidb_password']:
        raise ValueError("Username/Password required to poll AniDB")


def _connect_HTTP(aid):
    """
    Connect to AniDB using the public HTTP Api, this is used as an alternative to the UDP connection function
    """
    url = Settings['anidb_http_api'].format(aid)

    resp = utils.get_url_descriptor(url)

    if resp is None:
        return utils.show_not_found

    soup = Soup(resp.content)

    if soup.find('error'):
        logging.error("Temporally banned from AniDB, most likely due to flooding")
        return []

    episodes = soup.findAll('episode')

    if not episodes:
        return utils.show_not_found

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
            epList.append(Episode(utils.encode(title), epNum, 1, epNum))
        else:
            epNum = int(e.epno.getText()[1:])
            epList.append(Special(utils.encode(title), epNum, 'OVA'))

    return epList


def poll(title=""):
    try:
        Soup
    except NameError:
        return utils.show_not_found

    aid = _parse_local(title.lower())

    if aid < 0:
        return utils.show_not_found

    logging.info("Found AID: {}".format(aid))

    if utils.able_to_poll('AniDB'):
        episodes = _connect_HTTP(aid)
        if episodes:
            return episodes

    return utils.show_not_found

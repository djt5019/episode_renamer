import re
import os
import time
import urllib2
import difflib

import EpParser.src.Utils as Utils
import EpParser.src.Episode as Episode
import EpParser.src.Logger as Logger
import EpParser.src.Constants as Constants

from BeautifulSoup import BeautifulStoneSoup as Soup
from string import punctuation as punct

priority = 3

def _parse_local(title):
    '''Try to find the anime ID (aid) in the dump file provided by AniDB '''
    if not os.path.exists(os.path.join(Constants.RESOURCEPATH, 'animetitles.dat')):
        Logger.get_logger().warning("AniDB database file not found")
        return -1

    regex = re.compile(r'(?P<aid>\d+)\|(?P<type>\d)\|(?P<lang>.+)\|(?P<title>.*)', re.I)

    sequence = difflib.SequenceMatcher(lambda x: x in punct, title.lower(), "")

    guesses = []

    with open(os.path.join(Constants.RESOURCEPATH, 'animetitles.dat'), 'r') as f:
        for line in f:
            res = regex.search(line)

            if not res:
                continue

            foundTitle = Utils.encode(res.group('title'))

            sequence.set_seq2(foundTitle.lower())
            ratio = sequence.ratio()

            if ratio > .80:
                Logger.get_logger().info("Suitable guess for {} is: {}".format(title, foundTitle))
                guesses.append( (ratio, res.group('aid'), title) )

    aid = -1
    if guesses:
        _, aid, name = max(guesses)
        Logger.get_logger().info("Best choice is {} with id {}".format(name, aid))

    return aid, foundTitle

def _connect_UDP(aid):
    pass

def _connect_HTTP(aid, language='en'):
    url = r'http://api.anidb.net:9001/httpapi?request=anime&client=eprenamer&clientver=1&protover=1&aid={}'.format(aid)

    fd = Utils.get_URL_descriptor(url)

    if fd is None:
        return []

    with fd as resp:
        soup = Soup(resp.read())

    if soup.find('error'):
        Logger.get_logger().error("Temporally banned from AniDB, most likely due to flooding")
        return []

    episodes = soup.findAll('episode')

    if episodes == []:
        return []

    epList = []

    for e in episodes:
        if e.epno.attrs[0][1] != '1':
            continue

        epNum = int(e.epno.getText())
        title = e.find('title', {'xml:lang':'en'})
        title = title.getText()
        epList.append(Episode.Episode(Utils.encode(title), epNum, -1, epNum))

    return epList


def _able_to_poll():
    '''Check to see if a sufficent amount of time has passed since the last
    poll attempt.  This will prevent flooding'''   
    now = time.time()

    if now - _able_to_poll.last_poll > 2:
        Logger.get_logger().info("Able to poll AniDB")
        last_poll = now
        return True

    return False

_able_to_poll.last_poll = 0

def poll(title):
    aid, found_title = _parse_local(title)
    episodes = []

    if aid < 0:
        return "", []

    Logger.get_logger().info("Found AID: {}".format(aid))

    if _able_to_poll():
        episodes = _connect_HTTP(aid)
        if episodes:
            return found_title, episodes

    return "", []

import re
import os
import time
import urllib2 
import difflib

import EpParser.src.Utils as Utils
import EpParser.src.Episode as Episode
import EpParser.src.Logger as Logger

from BeautifulSoup import BeautifulStoneSoup as Soup
from string import punctuation as punct

priority = 3

def _parse_local(title):
    '''Try to find the anime ID (aid) in the dump file provided by AniDB '''    
    if not os.path.exists(os.path.join(Utils.RESOURCEPATH, 'animetitles.dat')):
        Logger.get_logger().warning("AniDB database file not found")
        return -1
        
    regex = re.compile(r'(?P<aid>\d+)\|(?P<type>\d)\|(?P<lang>.+)\|(?P<title>.*)', re.I)
    
    sequence = difflib.SequenceMatcher(lambda x: x in punct, title.lower(), "")
    
    with open(os.path.join(Utils.RESOURCEPATH, 'animetitles.dat'), 'r') as f:
        for line in f:            
            res = regex.search(line)
            
            if not res:
                continue
                
            foundTitle = Utils.encode(res.group('title'))
            
            sequence.set_seq2(foundTitle.lower())
            
            if sequence.ratio() > .80:
                Logger.get_logger().info("Best guess for {} is: {}".format(title, foundTitle))
                return res.group('aid')            
                
    return -1
    
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
    
    count = 1
    epList = []
    for e in episodes:
        if e.epno.attrs[0][1] != '1':
            continue
            
        epNum = int(e.epno.getText())
        title = e.find('title', {'xml:lang':'en'})
        title = title.getText()
        epList.append(Episode.Episode(Utils.encode(title), epNum, 1, count))
        count += 1
        
    return epList
    
    
_seconds_since_last_poll = 0
def _able_to_poll():
    '''Check to see if a sufficent amount of time has passed since the last 
    poll attempt.  This will prevent flooding'''
    global _seconds_since_last_poll
    now = time.time()
    
    if now - _seconds_since_last_poll > 2:
        Logger.get_logger().info("Able to poll AniDB")
        _seconds_since_last_poll = now
        return True
        
    return False
    
    
def poll(title):
    aid = _parse_local(title)
    episodes = []
    
    if aid < 0: 
        return []       
        
    Logger.get_logger().info("Found AID: {}".format(aid))
    
    if _able_to_poll():
        episodes = _connect_HTTP(aid)
        if episodes:
            return episodes   
            
    return []
        
        
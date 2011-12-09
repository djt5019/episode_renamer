import zipfile

import EpParser.src.Utils as Utils

from tempfile import TemporaryFile
from os.path import join
from urllib import quote_plus

from EpParser.src.Logger import get_logger
from EpParser.src.Episode import Episode
from EpParser.src.Constants import RESOURCEPATH

try:
    from BeautifulSoup import BeautifulStoneSoup as Soup
except ImportError:
    get_logger().critical(u"Error: BeautifulSoup was not found, unable to parse theTVdb")
    Soup = None
    pass

priority = 2

def poll(title):	    
    no_episodes = title, []

    try:
        with open( join(RESOURCEPATH,'tvdb.apikey') ,'r') as api:
            API_KEY = api.readline()
    except:
        get_logger().error( "The TvDB Api key file could not be found, unable to poll TvDB" )
        return

    if Soup is None:
        return no_episodes


    cleanTitle = quote_plus(title)

    #1) First we need to find the series ID
    seriesIdLoc = "http://www.thetvdb.com/api/GetSeries.php?seriesname={0}".format(cleanTitle)
    seriesFileDesc = Utils.get_URL_descriptor( seriesIdLoc )

    if seriesFileDesc is None:
        return no_episodes

    with seriesFileDesc as fd:
        seriesIdXml = Soup( fd.read(), convertEntities=Soup.HTML_ENTITIES )

    seriesIds = seriesIdXml.findAll('series')

    if not seriesIds: 
        return no_episodes

    if len(seriesIds) > 1:
        get_logger().warn( "Conflict with series title ID on TVdB" )
        for seriesName in seriesIdXml.findAll('seriesname'):
            get_logger().info( "Alternate series: {}".format(seriesName.getText()) )


    seriesID = seriesIds[0].seriesid.getString()
    seriesIdXml.close()

    #2) Get base info zip file
    infoLoc = "http://www.thetvdb.com/api/{0}/series/{1}/all/en.zip".format(API_KEY, seriesID)
    infoFileDesc = Utils.get_URL_descriptor(infoLoc)
    if infoFileDesc is None: 
        return no_episodes

    tempZip = TemporaryFile(suffix='.zip')
    tempZip.seek(0)

    with infoFileDesc as z:
        # download the entire zipfile into the tempfile
        while True:
            packet = z.read()
            if not packet:
                break
            tempZip.write(packet)

    with zipfile.ZipFile(tempZip, 'r') as z:
        if 'en.xml' not in z.namelist():
            get_logger().error("English episode list was not found")
            return no_episodes

        with z.open('en.xml') as d:
            soup = Soup( d, convertEntities=Soup.HTML_ENTITIES )

    #3) Now we have the xml data in the soup variable, just populate the list
    count = 1
    eps = []
    
    for data in soup.findAll('episode'):
        name = data.episodename.getText()
        season = int(data.seasonnumber.getText())
        num = int(data.episodenumber.getText())

        if name == "":
            get_logger().error("The name pulled from TvDB appears to be empty")
            continue

        if int(season) < 1: 
            continue

        eps.append(Episode(name, num, season, count))
        count += 1

    
    series_info = soup.find('series')
    if series_info:
        found_title = series_info.seriesname.getText()
        print "FOUND TITLE = {}".format(found_title)
        print len(eps)
    else:
        found_title = title
    soup.close()
    tempZip.close()

    return found_title, eps

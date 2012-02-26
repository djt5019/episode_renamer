# -*- coding: utf-8 -*-
__author__ = 'Dan Tracy'
__email__ = 'djt5019 at gmail dot com'

import zipfile

from urllib import quote_plus

import EpParser.src.Source_Poll_API as API

from EpParser.src.Logger import get_logger
from EpParser.src.Episode import Episode
from EpParser.src.Settings import Settings

try:
    from BeautifulSoup import BeautifulStoneSoup as Soup
except ImportError:
    get_logger().critical(u"Error: BeautifulSoup was not found, unable to parse theTVdb")
    Soup = None
    pass

priority = 1


def poll(title):
    if API.file_exists_in_resources(Settings['tvdb_key']):
        with API.open_file_in_resources(Settings['tvdb_key']) as f:
            API_KEY = f.readline().strip()
    else:
        get_logger().warn("The TvDB Api key was not found, unable to poll the TvDB")
        return API.show_not_found

    if Soup is None:
        return API.show_not_found

    cleanTitle = quote_plus(title)

    #1) First we need to find the series ID
    seriesIdLoc = "http://www.thetvdb.com/api/GetSeries.php?seriesname={0}".format(cleanTitle)
    seriesFileDesc = API.get_url_descriptor(seriesIdLoc)

    if seriesFileDesc is None:
        return API.show_not_found

    seriesIdXml = Soup(seriesFileDesc.content, convertEntities=Soup.HTML_ENTITIES)

    seriesIds = seriesIdXml.findAll('series')

    if not seriesIds:
        return API.show_not_found

    if len(seriesIds) > 1:
        get_logger().warn("Conflict with series title ID on TVdB")
        for seriesName in seriesIdXml.findAll('seriesname'):
            get_logger().info("Alternate series: {}".format(seriesName.getText()))

    seriesID = seriesIds[0].seriesid.getString()
    seriesIdXml.close()

    #2) Get base info zip file
    infoLoc = "http://www.thetvdb.com/api/{0}/series/{1}/all/en.zip".format(API_KEY, seriesID)
    infoFileDesc = API.get_url_descriptor(infoLoc)
    if infoFileDesc is None:
        return API.show_not_found

    tempZip = API.temporary_file(suffix='.zip')
    tempZip.seek(0)
    tempZip.write(infoFileDesc.content)

    with zipfile.ZipFile(tempZip) as z:
        if 'en.xml' not in z.namelist():
            get_logger().error("English episode list was not found")
            return API.show_not_found

        with z.open('en.xml') as d:
            soup = Soup(d, convertEntities=Soup.HTML_ENTITIES)

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

    soup.close()
    tempZip.close()

    return eps

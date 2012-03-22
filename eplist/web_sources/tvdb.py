# -*- coding: utf-8 -*-
__author__ = 'Dan Tracy'
__email__ = 'djt5019 at gmail dot com'

import zipfile
import logging
import tempfile

from urllib import quote_plus

from eplist import utils

from eplist.episode import Episode, Special
from eplist.settings import Settings

try:
    from BeautifulSoup import BeautifulStoneSoup as Soup
except ImportError:
    logging.critical(u"Error: BeautifulSoup was not found, unable to parse theTVdb")

priority = 1


def poll(title):
    try:
        API_KEY = Settings['tvdb_key']
    except KeyError:
        logging.warn("The TvDB Api key was not found, unable to poll the TvDB")
        return utils.show_not_found

    try:
        Soup
    except NameError:
        return utils.show_not_found

    cleanTitle = quote_plus(title)

    #1) First we need to find the series ID
    seriesIdLoc = "http://www.thetvdb.com/api/GetSeries.php?seriesname={0}".format(cleanTitle)
    seriesFileDesc = utils.get_url_descriptor(seriesIdLoc)

    if seriesFileDesc is None:
        return utils.show_not_found

    seriesIdXml = Soup(seriesFileDesc.content, convertEntities=Soup.HTML_ENTITIES)

    seriesIds = seriesIdXml.findAll('series')

    if not seriesIds:
        return utils.show_not_found

    ## TODO: Handle the series conflicts in a sane manner
    if len(seriesIds) > 1:
        logging.warn("Conflict with series title ID on TVdB")
        for seriesName in seriesIdXml.findAll('seriesname'):
            logging.info("Alternate series: {}".format(seriesName.getText()))

    seriesID = seriesIds[0].seriesid.getString()
    seriesIdXml.close()

    #2) Get base info zip file
    infoLoc = "http://www.thetvdb.com/api/{0}/series/{1}/all/en.zip".format(API_KEY, seriesID)
    infoFileDesc = utils.get_url_descriptor(infoLoc)
    if infoFileDesc is None:
        return utils.show_not_found

    tempZip = tempfile.TemporaryFile(suffix='.zip')
    tempZip.seek(0)
    tempZip.write(infoFileDesc.content)

    with zipfile.ZipFile(tempZip) as z:
        if 'en.xml' not in z.namelist():
            logging.error("English episode list was not found")
            return utils.show_not_found

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
            logging.info("The name pulled from TvDB appears to be empty")
            continue

        if 'commentary' in name.lower():
            continue

        if int(season) > 0:
            eps.append(Episode(name, num, season, count))
        else:
            eps.append(Special(name, num, 'OVA'))

        count += 1

    soup.close()
    tempZip.close()

    return eps

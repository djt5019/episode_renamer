# -*- coding: utf-8 -*-
# author:  Dan Tracy
# program: Utils.py

import EpParser
import os
import re
from itertools import izip
from urllib2 import Request, urlopen, URLError

_VIDEO_EXTS = set( ['.mkv', '.ogm', '.asf', '.asx', '.avi', '.flv',
					'.mov', '.mp4', '.mpg', '.rm',  '.swf', '.vob',
					'.wmv', '.mpeg'])
					
PROJECTPATH  = os.path.dirname(EpParser.__file__)
RESOURCEPATH = os.path.join( PROJECTPATH, 'resources')

## Common video naming formats
_REGEX = (  re.compile( r'^\[.*\][\.-_\s](?P<series>.*)[\.-_\s]+(?P<episode>\d+)', re.I),
			re.compile( r'^\[.*\][\.-_\s](?P<series>.*)[\.-_\s]+(?P<season>S\d+)[\.-_\s]+(?P<episode>\d+)', re.I ),
			re.compile( r'(?P<series>.*)[\s\._-]*S(?P<season>\d+)[\s\._-]*E(?P<episode>\d+)', re.I),
			re.compile( r'^(?P<series>.*)[\s\._-]*\[(?P<season>\d+)x(?P<episode>\d+)\]',re.I),
			re.compile( r'^(?P<series>.*) - Episode (?P<episode>\d+) - \w*', re.I), #My usual format
			re.compile( r'^(?P<series>.*) - Season (?P<season>\d+) - Episode (?P<episode>\d*) - \w*', re.I), #Also mine
			re.compile( r'^.*', re.I),
			)


class Show(object):
	'''A convenience class to keep track of the list of episodes as well as
	   to keep track of the custom formatter for those episodes'''
	def __init__(self, seriesTitle):
		self.title = encode(seriesTitle)
		self.properTitle = prepareTitle(self.title)
		self.episodeList = []
		self.formatter = EpisodeFormatter()

				
class Episode(object):
	''' A simple class to organize the episodes, an alternative would be
		to use a namedtuple though this is easier '''
	def __init__(self, series, title, epNumber, season, episodeCount):
		self.title = encode(title)
		self.series = encode( series.title() )
		self.season = season
		self.episode = epNumber
		self.count = episodeCount


class EpisodeFormatter(object):
	def __init__(self, fmt = None):
		'''Allows printing of custom formatted episode information'''
		if fmt is None:
			self.format = u"Season <season> - Episode <episode> - <title>"
		else:
			self.format = encode(fmt)

		self.tokens = self.format.split()
		self.episodeNumberTokens = set( ["<episode>", "<ep>"] )
		self.seasonTokens = set( [ "<season>", "<s>"] )
		self.episodeNameTokens = set( [ "<title>", "<name>", "<epname>"] )
		self.seriesNameTokens = set( ["<show>", "<series>"] )
		self.episodeCounterTokens = set( ["<count>", "<number>"] )

	def setFormat(self, fmt):
		'''Set the format string for the formatter'''
		if fmt is None: return
		self.format = encode( fmt )
		self.tokens = self.format.split()
		
	def display(self, ep):
		'''Displays the episode according to the users format'''
		output = self.format
		
		for t in self.tokens:
			t = t.lower()
			
			if t in self.episodeNumberTokens:
				output = output.replace( t, str(ep.episode), 1 )
				
			elif t in self.seasonTokens:
				output = output.replace( t, str(ep.season), 1 )
				
			elif t in self.episodeNameTokens:
				output = output.replace( t, ep.title, 1 )
				
			elif t in self.seriesNameTokens:
				output = output.replace( t, ep.series, 1 )
				
			elif t in self.episodeCounterTokens:
				output = output.replace( t, str(ep.count), 1 )
				
		return output


def getURLdescriptor(url):
	'''Returns a valid url descriptor or None, also deals with exceptions'''
	fd = None
	req = Request(url)

	try:
		fd = urlopen(req)
	except URLError as e:
		if hasattr(e, 'reason'):
			print 'ERROR: {0} appears to be down at the moment'.format(url)
		else:
			pass
		# 404 Not Found
		#elif hasattr(e, 'code'):
		#    print 'ERROR: {0} Responded with code {1}'.format(url,e.code)
	finally:
		return fd


## Renaming utility functions
def cleanFiles( path, files ):
	'''Attempts to extract order information about the files passed'''
	cleanFiles = []

	# Filter out anything that doesnt have the correct extenstion and
	# filter out any directories
	files = filter(lambda x: os.path.isfile(os.path.join(path,x)), files)
	files = filter(lambda x: os.path.splitext(x)[1].lower() in _VIDEO_EXTS, files)

	if files == []:
		print "No video files were found in {}".format( path )
		exit(1)
	
	# TODO: Fix this so that it takes into account seasons when sorting
	for f in files:
		for regex in _REGEX:
			g = regex.search( f )
			if g:
				try:
					ep = int(g.group('episode'))
					cleanFiles.append( (ep, os.path.join(path,f)) )
					break # This regex matched so we continue on to the next file
				except Exception as ex:
					print ex
					print g.groups()
					exit(1)
		
	cleanFiles = sorted(cleanFiles)
	_, cleanFiles = zip( *cleanFiles )
	
	return cleanFiles
	
	
def renameFiles( path, show):
	'''Rename the files located in 'path' to those in the list 'show' '''
	renamedFiles = []
	files = cleanFiles(path, os.listdir(path) )

	for f, n in izip(files, show.episodeList):
		fileName = f
		_, ext   = os.path.splitext(f)
		newName  = show.formatter.display(n) + ext
		newName  = replaceInvalidPathChars(newName)

		print (u"OLD: {0}".format( os.path.split(fileName)[1] ))
		print (u"NEW: {0}".format(newName))
		print ""

		fileName = os.path.join(path, fileName)
		newName  = os.path.join(path, newName)

		renamedFiles.append( (fileName, newName,) )

	resp = raw_input("\nDo you wish to rename these files [y|N]: ").lower()

	if not resp.startswith('y'):
		print "Changes were not commited to the files"
		exit(0)

	errors = []
	
	for old, new in renamedFiles:
		try:
			os.rename(old, new)
		except:
			errors.append(old)
	
	if errors:
		for e in errors:
			print "File {0} could not be renamed".format( os.path.split(e)[1] )
	else:
		print "Files were successfully renamed"


## Text based functions
def removePunc(title):
	'''Remove any punctuation and whitespace from the title'''
	name, ext = os.path.splitext(title)
	exclude = set('!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~')
	name = ''.join( ch for ch in name if ch not in exclude )
	return name+ext


def replaceInvalidPathChars(path, replacement='-'):
	'''Replace invalid path character with a different, acceptable, character'''
	exclude = set('\\/"?<>|*:')
	path = ''.join( ch if ch not in exclude else replacement for ch in path )
	return path


def prepareTitle(title):
	'''Remove any punctuation and whitespace from the title'''
	title = removePunc(title).split()
	if title == []: 
		return ""
		
	if title[0] == 'the':
		title.remove('the')
	return ''.join(title)


def encode(text, encoding='utf-8'):
	'''Returns a unicode representation of the string '''
	if isinstance(text, basestring):
		if not isinstance(text, unicode):
			text = unicode(text, encoding, "ignore")
	return text


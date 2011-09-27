# output display format, season is padded with zeros
# Season - Episode Number - Episode Title
# -*- encoding: utf-8 -*-

import os
from itertools import izip
from urllib2 import Request, urlopen, URLError

_VIDEO_EXTS = set( ['.mkv', '.ogm', '.asf', '.asx', '.avi', '.flv',
					'.mov', '.mp4', '.mpg', '.rm',  '.swf', '.vob',
					'.wmv', '.mpeg'])
					
class Show(object):
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
		if fmt is None:
			self.format = u"Season <season> - Episode <episode> - <title>"
		else:
			self.format = encode(fmt)

		self.tokens = self.format.split()
		self.episodeNumberTokens = set( ["<episode>", "<ep>"] )
		self.seasonTokens = set( [ "<season>", "<s>"] )
		self.episodeNameTokens = set( [ "<title>", "<name>"] )
		self.seriesNameTokens = set( ["<show>", "<series>"] )
		self.episodeCounterTokens = set( ["<count>", "<number>"] )

	def setFormat(self, fmt):
		if fmt is None: return
		self.format = encode( fmt )
		self.tokens = self.format.split()
		
	def display(self, ep):
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


def prepareTitle(title):
	'''Remove any punctuation and whitespace from the title'''
	title = removePunc(title).split()
	if title == []: 
		return ""
		
	if title[0] == 'the':
		title.remove('the')
	return ''.join(title)

def encode(text, encoding='utf-8'):
	if isinstance(text, basestring):
		if not isinstance(text, unicode):
			text = unicode(text, encoding, "ignore")
	return text

def getURLdescriptor(url):
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


def renameFiles( path, show):
	'''
	We will sort dictionary with respect to key value by
	removing all punctuation then adding each entry into
	a ordered dictionary to preserve sorted order.  We do
	this to ensure the file list is in somewhat of a natural
	ordering, otherwise we will have misnamed files
	'''

	global _VIDEO_EXTS

	files = os.listdir(path)
	renamedFiles = []

	# Filter out anything that doesnt have the correct extenstion and
	# filter out any directories
	files = filter(lambda x: os.path.isfile(os.path.join(path,x)), files)
	files = filter(lambda x: os.path.splitext(x)[1].lower() in _VIDEO_EXTS, files)

	clean = (removePunc(f) for f in files)

	cleanFiles = dict(izip(clean, files))
	cleanFiles = orderedDictSort(cleanFiles)

	for f, n in izip(cleanFiles.iterkeys(), show.episodeList):
		fileName = cleanFiles[f]
		_, ext   = os.path.splitext(f)
		newName  = show.formatter.display(n) + ext
		newName  = removeInvalidPathChars(newName)

		print (u"OLD: {0}".format(fileName))
		print (u"NEW: {0}".format(newName))
		print ""

		fileName = os.path.join(path, fileName)
		newName  = os.path.join(path, newName)

		renamedFiles.append( (fileName, newName,) )

	resp = raw_input("\nDo you wish to rename these files [y|N]: ").lower()

	if not resp.startswith('y'):
		print "Changes were not commited to the files"
		return

	errors = []
	
	for old, new in renamedFiles:
		try:
			os.rename(old, new)
		except:
			errors.append(old)
	
	if errors:
		for e in errors:
			print "File {0} could not be renamed".format( e )
	else:
		print "Files were successfully renamed"


def removePunc(title):
	'''Remove any punctuation and whitespace from the title'''
	name, ext = os.path.splitext(title)
	exclude = set('!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~')
	name = ''.join(ch for ch in name if ch not in exclude)
	return name+ext

def removeInvalidPathChars(path):
	exclude = set('\\/"?<>|*:')
	path = ''.join(ch for ch in path if ch not in exclude)
	return path

def orderedDictSort(dictionary):
	''' "Sorts" a dictionary by sorting keys then adding them
	into an ordered dict object'''
	from collections import OrderedDict
	keys = dictionary.keys()
	keys.sort()
	return OrderedDict(izip(keys, [dictionary[k] for k in keys]))

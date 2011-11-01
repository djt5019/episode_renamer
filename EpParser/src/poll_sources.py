# -*- coding: utf-8 -*-
# author:  Dan Tracy
# program: poll_sources.py

import sys
from os import listdir
from os.path import join
from Utils import PROJECTPATH, logger

def locate_show(title):
	'''Polls the web sources looking for the show'''
	episodes = []
	modules = []
	
	path = join(PROJECTPATH, 'src\\web_sources')
	sys.path.append(path)
	## This will import all the modules within the web_sources directory so that we
	## can easily plug in new sources for finding episode information
	mods = filter( lambda x: x.endswith('py') and not x.startswith('__'),  listdir(path))
	
	for m in mods:
		x =  __import__(m[:-3]) 
		modules.append(x)
	
	for source in modules:
		logger.info( "Polling {0}".format(source.__name__) )
			
		episodes = source.poll(title)
		
		if episodes:
			logger.info( "LOCATED {0}".format(title) )
			break
		logger.info( "Unable to locate {0} at {1}".format(title, source.__name__) )

	if episodes == []:
		logger.info("Unable to locate the show: " + title)
		
	return filter(lambda x: x.episode > 0, episodes)

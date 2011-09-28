# -*- coding: utf-8 -*-
# author:  Dan Tracy
# program: poll_sources.py

import sources.epguides as epguides
import sources.tvdb as tvdb

_modules = [tvdb, epguides]

def locate_show(title, verbose=False):
	episodes = []
	
	for source in _modules:
		if verbose: print "\nPolling {0}".format(source.__name__)
		episodes = source.poll(title)
		if episodes:
			if verbose: print "LOCATED {0}\n".format(title)
			break
		if verbose: print "FAILED to locate {0} at {1}\n".format(title, source.__name__)
		
	return episodes

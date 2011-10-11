import re 
from contextlib import closing

from EpParser.src.Utils import  Episode, getURLdescriptor, prepareTitle

pattern = r"""
			^		                # Start of the string
			(?:[\s]*?[\d]*\.?)	    # Number on list
			[\s]{2,}		        # Ignore whitespace
			(?P<season>[\d]*)	    # Season number
			-			            # Separator
			[\s]*		            # Optional whitespace
			(?P<episode>[\d]*)	    # Episode number
			[\s]{2,}		        # Whitespace
			(?P<product>.+|)	    # Product number
			[\s]{2,}		        # Whitespace
			(?P<airdate>[\w\s/]*?)  # Air-date
			[\s]{2,}		        # Ignore whitespace
			(?P<name>.*)	        # Episode name
			$			            # End of line
			"""

	
def poll(title):
	cleanTitle = prepareTitle(title)
	episodes = []
	url = "http://www.epguides.com/{0}".format(cleanTitle)
	fd  = getURLdescriptor(url)
	
	if fd is None: return []

	with closing( fd ) as request:
		data = request.readlines()
		
	regex = re.compile(pattern, re.X | re.I)

	for count, line in enumerate(data, start=1):
		info = regex.match(line)
		if info is not None:
			name = info.group('name')
			episode = info.group('episode')
			season = int(info.group('season'))
			name = re.sub('<.*?>', '', name).strip()               

			episodes.append( Episode(title, name, episode, season, count) )
			
	return episodes

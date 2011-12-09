import EpParser.src.Source_Poll_API as API
from EpParser.src.Episode import Episode

priority = 1

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
    cleanTitle = API.prepare_title(title)
    episodes = []
    url = "http://www.epguides.com/{0}".format(cleanTitle)
    fd = API.get_url_descriptor(url)
    
    if fd is None: 
        return API.show_not_found

    with fd as request:
        data = request.readlines()
        
    regex = API.regex_compile(pattern)

    count = 1
    for line in data:
        info = regex.match(line)
        if info is not None:
            name = info.group('name')
            episode = info.group('episode')
            season = int(info.group('season'))
            name = API.regex_sub('<.*?>', '', name).strip()

            episodes.append( Episode(name, episode, season, count) )
            count += 1
            
    return title, episodes

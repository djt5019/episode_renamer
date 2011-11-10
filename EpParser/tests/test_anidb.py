import EpParser.src.web_sources.anidb as anidb
from EpParser.src.Utils import get_logger

def test_local_file():
    assert( anidb._parse_local("FAKE SHOW") < 0 )
    assert( anidb._parse_local("black lagoon") == anidb._parse_local("BLACK LAGOON") )
    assert( anidb._parse_local("clannad") != anidb._parse_local("black lagoon") )
    
def test_poll_HTTP():
    files = anidb.poll('dragonball')
    assert( files != [] )
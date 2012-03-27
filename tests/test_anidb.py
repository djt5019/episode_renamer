# -*- coding: utf-8 -*-
__author__ = 'Dan Tracy'
__email__ = 'djt5019 at gmail dot com'

import unittest

from eplist.web_sources import anidb


class TestAniDB(unittest.TestCase):
    def test_local_file(self):
        assert(anidb._parse_local("FAKE SHOW") < 0)
        assert(anidb._parse_local("black lagoon") == anidb._parse_local("BLACK LAGOON"))
        assert(anidb._parse_local("clannad") != anidb._parse_local("black lagoon"))

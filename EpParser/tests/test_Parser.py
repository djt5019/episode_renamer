# -*- coding: utf-8 -*-
__author__='Dan Tracy'
__email__='djt5019 at gmail dot com'

import unittest
import EpParser.src.Parser as Parser

class testParser( unittest.TestCase ):
    def setUp(self):
        self.parser = Parser.EpParser('test', None)
        
    def tearDown(self):
        del self.parser
        
    def test(self):
        self.parser.setShow('test2')
        assert(self.parser.show.episodeList == [])
        
        
if __name__ == '__main__':
    unittest.main()
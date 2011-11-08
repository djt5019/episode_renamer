# -*- coding: utf-8 -*-
# author:  Dan Tracy
# program: test_Parser.py

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
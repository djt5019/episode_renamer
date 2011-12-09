# -*- coding: utf-8 -*-
#!/usr/bin/env python
__author__='Dan Tracy'
__email__='djt5019 at gmail dot com'

import unittest
import sqlite3
 
import EpParser.src.Cache as Cache


class TestCache( unittest.TestCase ):
   def __init__(self):
      self.cache = Cache.Cache(':memory:')
      
   
        
if __name__ == '__main__':
    unittest.main()
    
    
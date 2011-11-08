#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author:  Dan Tracy
# program: test_cache.py

import unittest
import sqlite3
 
import EpParser.src.Cache as Cache


class TestCache( unittest.TestCase ):
   def __init__(self):
      self.cache = Cache.Cache(':memory:')
      
   
        
if __name__ == '__main__':
    unittest.main()
    
    
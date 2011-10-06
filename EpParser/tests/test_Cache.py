#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author:  Dan Tracy
# program: test_cache.py

import unittest
import sqlite3
 
import EpParser.src.Cache


class TestCache( unittest.TestCase ):
   def setUp(self):
      unittest.TestCase.setUp(self)
      self.cache = EpParser.src.Cache(dbName = ":memory:")
       
   def tearDown(self):      
      unittest.TestCase.tearDown(self)
      self.cache.close()

   def testAddShow(self):
      show = ""
      self.cache.addShow()
   
        
if __name__ == '__main__':
    main()
    
    
# -*- coding: utf-8 -*-
__author__ = 'Dan Tracy'
__email__ = 'djt5019 at gmail dot com'

import unittest
from episode_renamer import Parser


class testParser(unittest.TestCase):
    def setUp(self):
        self.parser = Parser.EpParser('test', None)

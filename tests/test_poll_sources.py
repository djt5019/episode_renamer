# -*- coding: utf-8 -*-
__author__ = 'Dan Tracy'
__email__ = 'djt5019 at gmail dot com'

import unittest

from episode_parser import poll_sources


class TestPollSources(unittest.TestCase):
    def test(self):
        assert(poll_sources is not None)

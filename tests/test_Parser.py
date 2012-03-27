# -*- coding: utf-8 -*-
__author__ = 'Dan Tracy'
__email__ = 'djt5019 at gmail dot com'

from eplist.show_finder import Parser

from nose.tools import nottest


@nottest
class MockCache(object):
    """docstring for MockCache"""
    def __init__(self, arg):
        super(MockCache, self).__init__()
        self.arg = arg

    def add_specials(self, *args, **kwargs):
        return True

    def add_episodes(self, *args, **kwargs):
        return True

    def get_episodes(self, *args, **kwargs):
        return None

    def get_specials(self, *args, **kwargs):
        return None


@nottest
class MockPollSources(object):
    """docstring for MockPollSources"""
    def __init__(self, arg):
        super(MockPollSources, self).__init__()
        self.arg = arg

    def locate_show(self):
        return []


def test_get_show():
    parser = Parser()

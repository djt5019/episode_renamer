# -*- coding: utf-8 -*-
#!/usr/bin/env python
__author__ = 'Dan Tracy'
__email__ = 'djt5019 at gmail dot com'

import sqlite3

from nose.tools import assert_raises, assert_equal
from nose.tools import nottest

from episode_renamer.Cache import Cache
from episode_renamer.Settings import Settings


@nottest
class MockEpisode(object):
    def __init__(self, name, season, number):
        self.title = name
        self.season = season
        self.episode_number = number


@nottest
class MockSpecial(object):
    def __init__(self, name, num):
        self.title = name
        self.num = num
        self.type = "Movie"


@nottest
def make_series():
    eps = []
    spc = []
    for i in xrange(100):
        name = "Episode {}".format(i)  # single ascii letter name
        s_name = "Special {}".format(i)
        season = 1
        number = i

        eps.append(MockEpisode(name, season, number))
        spc.append(MockSpecial(s_name, number))

    return eps, spc


def test_good_connection():
    cache = Cache()
    assert cache is not None
    assert cache.connection is not None
    assert cache.cursor is not None

    cache.close()

    try:
        cache.cursor.execute("SELECT * FROM table")
        assert False
    except:
        assert True

    cache = Cache(":memory:")
    cache.recreate_cache()
    assert cache is not None
    assert cache.connection is not None
    assert cache.cursor is not None

    cache.close()


def test_bad_connection():
    assert_raises(ValueError, Cache, dbName=None)
    assert_raises(ValueError, Cache, dbName=1)
    assert_raises(ValueError, Cache, dbName=False)
    assert_raises(ValueError, Cache, dbName=True)
    assert_raises(ValueError, Cache, dbName=[1, 2, 3])
    assert_raises(sqlite3.OperationalError, Cache, dbName='../')


def test_update_old_entry():
    cache = Cache(":memory:")
    cache.recreate_cache()

    eps, spc = make_series()

    cache.add_show("test show", eps)
    cache.add_specials("test show", spc)

    old_val = Settings['db_update']
    Settings['db_update'] = 0

    eps = cache.get_episodes("test show")
    spc = cache.get_specials("test show")

    Settings['db_update'] = old_val

    cache.close()


def test_add_remove_eps():
    cache = Cache(":memory:")
    cache.recreate_cache()

    eps, spc = make_series()

    Settings['db_update'] = 7

    cache.add_show("test show", eps)
    cache.add_specials("test show", spc)

    eps = cache.get_episodes("test show")
    spc = cache.get_specials("test show")

    assert len(eps) == len(spc)

    for count, entry in enumerate(zip(eps, spc)):
        e, s = entry
        name = "Episode {}".format(count)  # single ascii letter name
        s_name = "Special {}".format(count)

        assert e.title == name
        assert e.episode_number == count
        assert e.season == 1

        assert s.title == s_name
        assert s.num == count

    cache.remove_show(1)
    cache.close()


def test_remove_fake_show():
    cache = Cache(":memory:")
    cache.recreate_cache()

    assert_raises(ValueError, cache.remove_show, sid=None)
    assert_raises(ValueError, cache.remove_show, sid=[])
    assert_raises(ValueError, cache.remove_show, sid={})
    assert_raises(ValueError, cache.remove_show, sid="")

    cache.close()


def test_bad_add_show_eps():
    cache = Cache(":memory:")
    cache.recreate_cache()

    eps, spc = make_series()

    assert_raises(ValueError, cache.add_show, showTitle="", episodes=eps)
    assert_raises(ValueError, cache.add_show, showTitle=None, episodes=None)
    assert_raises(ValueError, cache.add_show, showTitle="Show", episodes=None)
    assert_raises(ValueError, cache.add_show, showTitle="Show", episodes="Title")
    assert_raises(ValueError, cache.add_show, showTitle="Title", episodes=[])
    assert_raises(ValueError, cache.add_show, showTitle="Title", episodes={})
    assert_raises(ValueError, cache.add_show, showTitle="test", episodes=[])

    cache.close()


def test_bad_add_special_eps():
    cache = Cache(':memory:')

    eps, spc = make_series()

    assert_raises(ValueError, cache.add_specials, showTitle="", episodes=spc)
    assert_raises(ValueError, cache.add_specials, showTitle=None, episodes=None)
    assert_raises(ValueError, cache.add_specials, showTitle="Show", episodes=None)
    assert_raises(ValueError, cache.add_specials, showTitle="Show", episodes="Title")
    assert_raises(ValueError, cache.add_specials, showTitle="Title", episodes=[])
    assert_raises(ValueError, cache.add_specials, showTitle="Title", episodes={})
    assert_raises(ValueError, cache.add_specials, showTitle="test", episodes=[])

    cache.close()


def test_bad_get_episodes():
    cache = Cache(':memory:')

    assert_raises(ValueError, cache.get_episodes, showTitle=None)
    assert_raises(ValueError, cache.get_episodes, showTitle={})
    assert_raises(ValueError, cache.get_episodes, showTitle=[])
    assert_equal(cache.get_episodes(showTitle="FAKE"), [])
    assert_equal(cache.get_episodes(showTitle="test"), [])

    cache.close()


def test_bad_get_specials():
    cache = Cache(':memory:')

    assert_raises(ValueError, cache.get_specials, showTitle=None)
    assert_raises(ValueError, cache.get_specials, showTitle={})
    assert_raises(ValueError, cache.get_specials, showTitle=[])
    assert_equal(cache.get_specials("test"), [])
    assert_equal(cache.get_specials("FAKE"), [])

    cache.close()

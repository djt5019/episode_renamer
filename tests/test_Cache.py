# -*- coding: utf-8 -*-
#!/usr/bin/env python
__author__ = 'Dan Tracy'
__email__ = 'djt5019 at gmail dot com'

import sqlite3

from nose.tools import assert_raises, assert_equal
from nose.tools import nottest

from eplist.cache import Cache

# Mock settings dict
Settings = dict(db_update=7)


@nottest
class MockEpisode(object):
    def __init__(self, title, number, season, count=-1, type_="Episode"):
        self.title = title
        self.season = int(season)
        self.number = int(number)
        self.count = int(count)
        self.type = type_
        self.is_special = (type_.lower() != "episode")


@nottest
def make_series():
    eps = []
    spc = []

    for i in xrange(100):
        name = "Episode {}".format(i)  # single ascii letter name
        season = 1
        eps.append(MockEpisode(name, i, season, i))

    for i in xrange(10):
        name = "Special {}".format(i)
        season = 1
        spc.append(MockEpisode(name, i, season, i, "Special"))

    return eps, spc


def test_good_connection():
    cache = Cache(':memory:')

    assert cache is not None
    assert cache.connection is not None

    with cache.connection as conn:
        conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY);")
        conn.execute("INSERT INTO test VALUES (1)")
        conn.execute("INSERT INTO test VALUES (2)")
        curs = conn.execute("INSERT INTO test VALUES (3)")
        assert curs.lastrowid == 3

    cache.close()

    try:
        cache.cursor.execute("SELECT * FROM test")
        assert False  # Database should be scrapped
    except:
        assert True   # Database was successfully destroyed


def test_bad_connection():
    assert_raises(ValueError, Cache)
    assert_raises(ValueError, Cache, dbName=None)
    assert_raises(TypeError, Cache, dbName=1)
    assert_raises(ValueError, Cache, dbName=False)
    assert_raises(TypeError, Cache, dbName=True)
    assert_raises(TypeError, Cache, dbName=[1, 2, 3])
    assert_raises(sqlite3.OperationalError, Cache, dbName='../')


def test_update_old_entry():
    cache = Cache(":memory:")
    cache.recreate_cache()

    eps, spc = make_series()

    cache.add_show("test show", eps, spc)

    eps = cache.get_episodes("test show", -1)

    cache.close()


def test_add_remove_eps():
    cache = Cache(":memory:")
    cache.recreate_cache()

    eps, spc = make_series()

    Settings['db_update'] = 7

    cache.add_show("test show", eps, spc)

    eps = cache.get_episodes("test show")

    spc = filter(lambda x: x.is_special, eps)
    eps = filter(lambda x: not x.is_special, eps)

    for count, e in enumerate(eps):
        name = "Episode {}".format(count)  # single ascii letter name

        assert e.title == name
        assert e.number == count
        assert e.season == 1

    for count, s in enumerate(spc):
        s_name = "Special {}".format(count)
        assert s.title == s_name
        assert s.number == count

    cache.remove_show(1)
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
    assert_raises(ValueError, cache.add_show, showTitle="test", episodes=(1, 3))

    ## Specials
    assert_raises(ValueError, cache.add_show, showTitle=None, specials=None)
    assert_raises(ValueError, cache.add_show, showTitle="Show", specials=None)
    assert_raises(ValueError, cache.add_show, showTitle="Show", specials="Title")
    assert_raises(ValueError, cache.add_show, showTitle="Title", specials=[])
    assert_raises(ValueError, cache.add_show, showTitle="Title", specials={'title': 't'})
    assert_raises(ValueError, cache.add_show, showTitle="test", specials=[])

    cache.close()


def test_bad_get_episodes():
    cache = Cache(':memory:')

    assert_raises(ValueError, cache.get_episodes, showTitle=None)
    assert_raises(ValueError, cache.get_episodes, showTitle={})
    assert_raises(ValueError, cache.get_episodes, showTitle=[])
    assert_equal(cache.get_episodes(showTitle="FAKE"), [])
    assert_equal(cache.get_episodes(showTitle="test"), [])

    cache.close()

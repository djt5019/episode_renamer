# -*- coding: utf-8 -*-

__author__ = 'Dan Tracy'
__email__ = 'djt5019 at gmail dot com'

import shutil
import tempfile
import os
import time

from episode_renamer import utils

temp_dir = None


def create_temp_files(files):
    global temp_dir
    if not temp_dir:
        temp_dir = tempfile.mkdtemp()

        files = [open(os.path.join(temp_dir, f), 'w') for f in files]

    return files

def teardown():
    global temp_dir
    if temp_dir:
        print("Tearing down {}".format(temp_dir))
        shutil.rmtree(temp_dir)
        temp_dir = None


filenames = [
        "[group] series - 01[DEADBEEF].mkv",
        "[group]_series_-_02.mkv",
        "[group] series - S01E03.mkv",
        "[group] series - [01x04].mkv",
        "[group] series - episode 05.mkv",
        "[group] series - ep 06.mkv",
        "[group] series with spaces in title - 07.mkv",
        "[group] series with 1 in title - 08.mkv",
        "[group]   series with - 09 [DEADBEEF].mkv",
        "[group]series - 10 [h.264][720p][DEADBEEF].mkv",
        "series - season 1 - episode 11.mkv",
        "[group] series - DVD 12.mkv",
]


def test_get_url_descriptor():
    good_site = utils.get_url_descriptor("http://www.google.com")
    assert good_site != None
    assert good_site.ok == True

    bad_site = utils.get_url_descriptor("http://www.google.com/does_not_exist")
    assert bad_site == None


def test_is_valid_file():
    fake_files = [
    "C:\\Users\\SomeUser\\Files\\file1.mkv",
    "C:\\Users\\SomeUser\\Files\\file2.mov",
    "C:\\Users\\SomeUser\\Files\\file3.dvi",
    "/home/user/files/file3.avi",
    "/home/user/files/file4.mpeg"
    ]

    assert not all([utils.is_valid_file(f) for f in fake_files])

    temp_files = [
        utils.temporary_file(suffix=".mkv"),
        utils.temporary_file(suffix=".mov"),
        utils.temporary_file(suffix=".flv"),
        utils.temporary_file(suffix=".avi"),
        utils.temporary_file(suffix=".mpeg"),
    ]

    for f in temp_files:
        assert utils.is_valid_file(f.name)

    [f.close() for f in temp_files]


def test_regex_search():
    for episode, f in enumerate(filenames, 1):
        g = utils.regex_search(f)

        assert g is not None

        print f, g
        if 'sum' in g:
            assert g['sum'] == "DEADBEEF"

        if 'episode' in g:
            assert episode == int(g['episode'])

        if 'season' in g:
            assert int(g['season']) == 1

        if 'special' in g:
            assert g['special'] == "12"
            assert g['type'] == 'DVD'

test_regex_search.tags = ['regex', 'a']


def test_clean_filenames():
    create_temp_files(filenames)

    clean_files = utils.clean_filenames(temp_dir)

    assert clean_files is not None


def test_rename():
    create_temp_files(filenames)

    files = []
    for index, f in enumerate(os.listdir(temp_dir)):
        old = os.path.join(temp_dir, f)
        new = os.path.join(temp_dir, "{:02}.avi".format(index))
        files.append((old, new))

    assert utils.rename(files, 'y') == []

    for index, f in enumerate(os.listdir(temp_dir)):
        assert f == "{:02}.avi".format(index)

    files = utils.find_old_filenames(temp_dir)['file_list']

    assert utils.rename(files, 'y') == []

    for new in os.listdir(temp_dir):
        assert new in filenames

    teardown()


def test_remove_punctuation():
    string = "This-is_a/test\\string!@#$%$*&*(%)-=+_`~"
    expected = "Thisisateststring"

    assert utils.remove_punctuation(string) == expected

    string = "this is a test string"
    expected = "this is a test string"

    assert utils.remove_punctuation(string) == expected


def test_replace_invalid_path_chars():
    string = "file\\name?_<1>.exe"
    expected = "file-name-_-1-.exe"

    assert utils.replace_invalid_path_chars(string) == expected

    string = "file\\name?_<1>.exe"
    expected = "file=name=_=1=.exe"

    assert utils.replace_invalid_path_chars(string, replacement='=') == expected


def test_prepare_title():
    assert utils.prepare_title(None) == ""
    assert utils.prepare_title("Hawaii Five-O") == "HawaiiFiveO"
    assert utils.prepare_title("Breaking Bad") == "BreakingBad"
    assert utils.prepare_title("The Office!@#$%^&*()>_") == "Office"
    assert utils.prepare_title("The Big 10") == "Bigten"
    assert utils.prepare_title("The !!! 352") == "three_hundred_fifty_two"


def test_able_to_poll():
    assert utils.able_to_poll("http://www.google.com") == True
    ## It hasn't been at least two seconds since the last poll
    ## so it should fail
    assert utils.able_to_poll("http://www.google.com") == False
    time.sleep(2)
    assert utils.able_to_poll("http://www.google.com") == True
    assert utils.able_to_poll("http://www.google.com", wait=True) == True

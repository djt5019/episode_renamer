# -*- coding: utf-8 -*-

__author__ = 'Dan Tracy'
__email__ = 'djt5019 at gmail dot com'

import unittest
import shutil
import tempfile
import os
import time

from episode_parser import Utils


temp_dir = None


def create_temp_files(files):
    global temp_dir
    if not temp_dir:
        temp_dir = tempfile.mkdtemp()

        files = [open(os.path.join(temp_dir, f), 'w') for f in files]


def teardown():
    global temp_dir
    if temp_dir:
        print("Tearing down {}".format(temp_dir))
        shutil.rmtree(temp_dir)
        temp_dir = None


class TestUtils(unittest.TestCase):
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

    def test_get_url_descriptor(self):
        good_site = Utils.get_url_descriptor("http://www.google.com")
        assert good_site != None
        assert good_site.ok == True

        bad_site = Utils.get_url_descriptor("http://www.google.com/does_not_exist")
        assert bad_site == None

    def test_is_valid_file(self):
        fake_files = [
        "C:\\Users\\SomeUser\\Files\\file1.mkv",
        "C:\\Users\\SomeUser\\Files\\file2.mov",
        "C:\\Users\\SomeUser\\Files\\file3.dvi",
        "/home/user/files/file3.avi",
        "/home/user/files/file4.mpeg"
        ]

        assert not all([Utils.is_valid_file(f) for f in fake_files])

        temp_files = [
            Utils.temporary_file(suffix=".mkv"),
            Utils.temporary_file(suffix=".mov"),
            Utils.temporary_file(suffix=".flv"),
            Utils.temporary_file(suffix=".avi"),
            Utils.temporary_file(suffix=".mpeg"),
        ]

        for f in temp_files:
            assert Utils.is_valid_file(f.name)

        [f.close() for f in temp_files]

    def test_regex_search(self):
        for episode, f in enumerate(TestUtils.filenames, 1):
            g = Utils.regex_search(f)

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

    def test_clean_filenames(self):
        create_temp_files(TestUtils.filenames)

        clean_files = Utils.clean_filenames(temp_dir)

        assert clean_files is not None

    def test_rename(self):
        global temp_dir

        create_temp_files(TestUtils.filenames)

        files = []
        for index, f in enumerate(os.listdir(temp_dir)):
            old = os.path.join(temp_dir, f)
            new = os.path.join(temp_dir, "{:02}.avi".format(index))
            files.append((old, new))

        assert Utils.rename(files, 'y') == []

        for index, f in enumerate(os.listdir(temp_dir)):
            assert f == "{:02}.avi".format(index)

        files = Utils.load_last_renamed_files()

        assert Utils.rename(files, 'y') == []

        for new in os.listdir(temp_dir):
            assert new in TestUtils.filenames

        teardown()

    def test_remove_punctuation(self):
        string = "This-is_a/test\\string!@#$%$*&*(%)-=+_`~"
        expected = "Thisisateststring"

        assert Utils.remove_punctuation(string) == expected

        string = "this is a test string"
        expected = "this is a test string"

        assert Utils.remove_punctuation(string) == expected

    def test_replace_invalid_path_chars(self):
        string = "file\\name?_<1>.exe"
        expected = "file-name-_-1-.exe"

        assert Utils.replace_invalid_path_chars(string) == expected

        string = "file\\name?_<1>.exe"
        expected = "file=name=_=1=.exe"

        assert Utils.replace_invalid_path_chars(string, replacement='=') == expected

    def test_preapare_title(self):
        assert Utils.prepare_title(None) == ""
        assert Utils.prepare_title("Hawaii Five-O") == "HawaiiFiveO"
        assert Utils.prepare_title("Breaking Bad") == "BreakingBad"
        assert Utils.prepare_title("The Office!@#$%^&*()>_") == "Office"
        assert Utils.prepare_title("The Big 10") == "Bigten"
        assert Utils.prepare_title("The !!! 352") == "three_hundred_fifty_two"

    def test_able_to_poll(self):
        assert Utils.able_to_poll("http://www.google.com") == True
        ## It hasn't been at least two seconds since the last poll
        ## so it should fail
        assert Utils.able_to_poll("http://www.google.com") == False
        time.sleep(2)
        assert Utils.able_to_poll("http://www.google.com") == True
        assert Utils.able_to_poll("http://www.google.com", wait=True) == True

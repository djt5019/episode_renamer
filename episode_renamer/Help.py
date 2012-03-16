#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Dan Tracy'
__email__ = 'djt5019 at gmail dot com'


def display_help():
    helper = HelpClass()
    helper.display_help()


class HelpClass(object):
    def display_help(self):
        for fname in dir(HelpClass):
            if fname.startswith('help'):
                HelpClass.__dict__.get(fname)(self)

    def help_formatting(self):
        print """
        FORMATTING HELP:
        ----------------


        """

    def help_header(self):
        print "HEADER"

    def help_ranges(self):
        print "RANGES"

    def help_gui(self):
        print "GUI"

    def help_db_update(self):
        pass




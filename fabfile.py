#!/usr/bin/env python
# -*- coding: utf-8 -*-

from fabric.api import  local, env
import os

env['project_name'] = 'eplist'
env['path'] = os.getcwd()
env['env_path'] = os.path.join(env.path, 'env')
env['python'] = 'python2.7'


def test(src="all"):
    files = [f for f in os.listdir('tests') if f.endswith('py')]

    cmd = "nosetests -s --nologcapture -v --with-coverage \
            --cover-package=eplist.{} tests/test_{}.py"

    if src.lower() == "all":
        for f in files:
            local(cmd.format(f.lower(), f))
    else:
        local(cmd.format(src, src))


def make_venv():
    """
    create a new virtualenv
    """

    local('virtualenv %(env_path)s;' % env)
    local('%(env_path)s/bin/activate.bat;' % env)


def get_reqs():
    """
    Install the necessary requirements for our virtualenv
    """
    pass

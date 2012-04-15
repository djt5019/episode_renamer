from fabric.api import local
import os


def test(src="all"):
    files = [f for f in os.listdir('tests') if f.endswith('py')]

    cmd = "nosetests -s --nologcapture -v --with-coverage \
            --cover-package=eplist.{} tests/test_{}.py"

    if src.lower() == "all":
        for f in files:
            local(cmd.format(f.lower(), f))
    else:
        local(cmd.format(src, src))

#!/usr/bin/env python

import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "farnsworth.settings")
this_dir = os.path.abspath(os.path.dirname(__file__))
if this_dir not in sys.path:
    sys.path.insert(0, this_dir)

from django.test.utils import get_runner
from django.conf import settings

def runtests():
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=1, interactive=True, failfast=False)
    failures = test_runner.run_tests([
        "base",
        "threads",
        "events",
        "managers",
        "workshift",
        "elections",
        "rooms",
        ])
    sys.exit(bool(failures))

if __name__ == "__main__":
    runtests()

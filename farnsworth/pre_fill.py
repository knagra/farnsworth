#!/usr/bin/env python

from __future__ import absolute_import, print_function

import logging
import os
import sys

from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "farnsworth.settings")
this_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if this_dir not in sys.path:
    sys.path.insert(0, this_dir)

import django
if hasattr(django, "setup"):
    django.setup()

def _parse_args(args):
    import argparse

    parser = argparse.ArgumentParser(
        description="Fill the database with basic information, such as the "
        "manager position and workshifts",
        )
    parser.add_argument('--verbose', action='store_true')
    parser.add_argument('--managers', action='store_true')
    parser.add_argument('--requests', action='store_true')
    parser.add_argument('--workshift', action='store_true')

    return parser.parse_args(args=args)

def main(args):
    args = _parse_args(args)
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    # Add Managers
    if args.managers:
        from managers.fill import fill_managers
        fill_managers(verbose=args.verbose)

    # Add Requests
    if args.requests:
        from managers.fill import fill_requests
        fill_requests(verbose=args.verbose)

    if args.workshift and "workshift" in settings.INSTALLED_APPS:
        from workshift.fill import fill_regular_shifts, fill_humor_shifts, \
            fill_social_shifts, fill_workshift_types
        fill_workshift_types()
        fill_regular_shifts()
        fill_humor_shifts()
        fill_social_shifts()

if __name__ == "__main__":
    main(sys.argv[1:])

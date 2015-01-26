
from __future__ import absolute_import, print_function

import logging

from datetime import time

from managers.models import Manager
from workshift.models import Semester, WorkshiftPool, WorkshiftType, \
    RegularWorkshift
from workshift.utils import get_year_season, make_instances, \
    get_semester_start_end, make_workshift_pool_hours, \
    make_manager_workshifts

# Items of form (title, description, quick_tips, hours, rateable)
WORKSHIFT_TYPES = [
    ("Clean",
        """<ol>
        <li>Put away any perishables left out.</li>
        <li>clear all dishes from dining room into dishroom.</li>
        <li>Throw away yesterday's paper.</li>
        <li>Put away your cleaning supplies.<li>
        <li>Clean and sanitize all counters and tables with sponge and a spray bottle.</li>
        </ol>
        """, "", True),
    ("Food Put Away",
        """<ol>
        <li>Put away food.</li>
        <li>Place opened food in containers and label containers.</li>
        </ol>
        """, "", True),
    ("Pots",
        """<ol>
        <li>Wash and sanitize all pots.</li>
        <li>Clean up pots area after all pots are washed and sanitized.</li>
        <li>Soak any pots that you can't wash in soap water.</li>
        <li>Clean out all scraps from the disposals.</li>
        <li>Allow pots to air dry.</li>
        </ol>
        """, "", True),
    ("Basement / Laundry Room Clean",
        """<ol>
        <li>Take all dishes to the dishroom.</li>
        <li>Throw away any trash lying around.</li>
        <li>Organize the laundry room and maintenance hallway.</li>
        <li>Sweep laundry room floor.</li>
        <li>Organize free pile by category.  Throw away anything that's obviously trash.</li>
        <li>Make sure basement doors are closed.  These should never be left open.</li>
        </ol>
        """, "", True),
    ("Bathroom Clean",
        """<ol>
        <li>Clean all sinks, toilets and handles.</li>
        <li>Sweep and mop the floors.</li>
        <li>Scrub the grout and surfaces in the showers.</li>
        <li>Take out all trash, recycling, and compost.</li>
        </ol>
        """, "", True),
    ("Bike / Living / Study Room Clean",
        """<ol>
        <li>Clear out the rooms of any trash.</li>
        <li>Pick up dishes and food and move them to the dish room.</li>
        <li>Recycle any cans, bottles, or paper.</li>
        </ol>
        """, "", True),
    ("Roofdeck Clean & Top Two Floors",
        """
        """, "", True),
    ("Ramp and Amphitheater Clean", "", "", True),
    ("Ramp and Gazebo Clean", "", "", True),
    ("Pantry / Fridge Clean", "", "", True),
    ("Free Pile Clean", "", "", True),
    ("Bread Run", "", "", True),
    ("Brunch", "", "", True),
    ("Extra bagels", "", "", True),
    ("Dishes", "", "", True),
    ("Dairy / Non-perishables Run", "", "", True),
    ("Farmer's Market Run", "", "", True),
    ("Hummus", "", "", True),
    ("Granola", "", "", True),
    ("Laundry", "", "", True),
    ("Sweep & Mop", "", "", True),
    ("Cook", "", "", True),
    ("IKC", "", "", True),
    ("Main Entrance / Front Walk Clean", "", "", True),
    ("Mail Sort / Forward", "", "", True),
    ("Vacuum", "", "", True),
    ]

REGULAR_WORKSHIFTS = [
    ("Clean", 1, [0, 1, 2, 3, 4, 5, 6], 1, None, time(11)),
    ("Dishes", 1, [0, 1, 2, 3, 4, 5, 6], 1, None, time(11)),
    ("Pots", 2, [0, 1, 2, 3, 4, 5, 6], 1, time(10), time(11)),
    ("Dishes", 1, [0, 1, 2, 3, 4, 5, 6], 1, time(12), time(16)),
    ("Clean", 1, [0, 1, 2, 3, 4, 5, 6], 1, time(13), time(15)),
    ("Pots", 2, [0, 1, 2, 3, 4, 5, 6], 2, time(13), time(15)),
    ("Clean", 1, [0, 1, 2, 3, 4, 6], 1, time(18), time(19)),
    ("Dishes", 1, [0, 1, 2, 3, 4, 6], 1, time(17), time(19)),
    ("Dishes", 1, [1, 2, 0], 1, time(20), time(0)),
    ("Pots", 2, [1, 2, 0], 2, time(20), time(0)),
    ("Sweep & Mop", 1, [1, 2, 3], 1, time(21), time(0)),
    ("Main Entrance / Front Walk Clean", 1, [1, 3], 1, None, None),
    ("Basement / Laundry Room Clean", 1, [1, 4], 1, None, time(19)),
    ("Bike / Living / Study Room Clean", 1, [1, 4], 1, None, time(19)),
    ("Roofdeck Clean & Top Two Floors", 1, [1, 4], 1, None, time(19)),
    ("Ramp and Amphitheater Clean", 1, [2], 1, None, None),
    ("Ramp and Gazebo Clean", 0.5, [2], 1, None, None),
    ("Pantry / Fridge Clean", 0.5, [2], 1, None, time(20)),
    ("Free Pile Clean", 1.5, [2], 1, None, None),
    ("Laundry", 1, [2], 1, None, None),
    ("Vacuum", 2, [1, 4], 1, None, None),
    ("Food Put Away", 1, [0, 3], 1, None, None),
    ("Bread Run", 2, [3], 1, None, None),
    ("Dairy / Non-perishables Run", 2, [3], 2, None, None),
    ("Food Put Away", 1, [3], 1, time(15), time(19)),
    ("Cook", 3, [0, 1, 2, 3, 4, 6], 3, time(16), time(19)),
    ("IKC", 2, [0], 8, time(20), time(23)),
    ("IKC", 2, [3], 7, time(20), time(23)),
    ]

WEEK_LONG = (
    ("Extra bagels", 1, 1),
    ("Farmer's Market Run", 1, 1),
    ("Granola", 2, 1),
    ("Hummus", 2, 1),
    ("Mail Sort / Forward", 1, 1),
    )

HUMOR_WORKSHIFTS = [
    ("Pots", 2, [4, 5], time(20), time(0)),
    ("Sweep & Mop", 2, [4, 5], time(20), time(0)),
    ]

# TODO: Bathroom shifts

def _get_semester():
    # Start the Workshift Semester
    year, season = get_year_season()
    start_date, end_date = get_semester_start_end(year, season)
    try:
        semester = Semester.objects.get(current=True)
    except Semester.DoesNotExist:
        semester, created = Semester.objects.get_or_create(
            year=year,
            season=season,
            defaults=dict(start_date=start_date, end_date=end_date),
            )
    else:
        created = False

    if created:
        logging.info("Started a new workshift semester")

    return semester

def _fill_workshift_types():
    # Workshift Types
    for title, description, quick_tips, rateable in WORKSHIFT_TYPES:
        WorkshiftType.objects.get_or_create(
            title=title,
            defaults=dict(
                description=description,
                quick_tips=quick_tips,
                rateable=rateable,
                ),
            )

def fill_regular_shifts(regular_hours=5, semester=None):
    if semester is None:
        semester = _get_semester()

    _fill_workshift_types()

    # Regular Weekly Workshift Hours
    pool, created = WorkshiftPool.objects.get_or_create(
        semester=semester,
        is_primary=True,
        defaults=dict(hours=regular_hours, any_blown=True),
        )

    if created:
        pool.managers = Manager.objects.filter(workshift_manager=True)
        pool.save()

    make_workshift_pool_hours(semester, pools=[pool])

    # Regular Workshifts
    for type_title, hours, days, count, start, end in REGULAR_WORKSHIFTS:
        wtype = WorkshiftType.objects.get(title=type_title)
        for day in days:
            RegularWorkshift.objects.get_or_create(
                workshift_type=wtype,
                pool=pool,
                day=day,
                start_time=start,
                end_time=end,
                defaults=dict(
                    count=count,
                    hours=hours,
                    ),
                )

    for type_title, hours, count in WEEK_LONG:
        wtype = WorkshiftType.objects.get(title=type_title)
        RegularWorkshift.objects.get_or_create(
            workshift_type=wtype,
            pool=pool,
            count=count,
            week_long=True,
            defaults=dict(
                start_time=None,
                end_time=None,
                hours=hours,
                ),
            )

    make_instances(semester=semester)
    make_manager_workshifts(semester)

def fill_hi_shifts(hi_hours=5, semester=None):
    if semester is None:
        semester = _get_semester()

    # HI Hours
    hi_pool, created = WorkshiftPool.objects.get_or_create(
        title="Home Improvement",
        semester=semester,
        defaults=dict(hours=hi_hours, weeks_per_period=0),
        )
    if created:
        hi_pool.managers = Manager.objects.filter(title="Maintenance Manager")
        hi_pool.save()

    make_workshift_pool_hours(semester, pools=[hi_pool])

def fill_social_shifts(social_hours=1, semester=None):
    if semester is None:
        semester = _get_semester()

    # Social Hours
    social_pool, created = WorkshiftPool.objects.get_or_create(
        title="Social",
        semester=semester,
        defaults=dict(hours=social_hours, weeks_per_period=0),
        )

    if created:
        social_pool.managers = Manager.objects.filter(title="Social Manager")
        social_pool.save()

    make_workshift_pool_hours(semester, pools=[social_pool])

def fill_humor_shifts(humor_hours=2, semester=None):
    if semester is None:
        semester = _get_semester()

    # Humor Shift
    humor_pool, created = WorkshiftPool.objects.get_or_create(
        title="Humor Shift",
        semester=semester,
        defaults=dict(any_blown=True, hours=humor_hours, weeks_per_period=6),
        )

    if created:
        humor_pool.managers = Manager.objects.filter(workshift_manager=True)
        humor_pool.save()

    make_workshift_pool_hours(semester, pools=[humor_pool])

    # Humor Workshifts
    for type_title, hours, days, start, end in HUMOR_WORKSHIFTS:
        wtype = WorkshiftType.objects.get(title=type_title)
        for day in days:
            RegularWorkshift.objects.get_or_create(
                workshift_type=wtype,
                pool=humor_pool,
                day=day,
                defaults=dict(
                    start_time=start,
                    end_time=end,
                    hours=hours,
                    ),
                )

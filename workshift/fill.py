
from __future__ import absolute_import, print_function

import logging

from datetime import time

from managers.models import Manager
from workshift.models import Semester, WorkshiftPool, WorkshiftType, \
    RegularWorkshift
from workshift.utils import get_year_season, get_semester_start_end, \
    make_manager_workshifts

# Items of form (title, description, quick_tips, rateable)
WORKSHIFT_TYPES = [
    ("Kitchen / Dinning Room Clean",
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
    ("Dishroom Clean", "", "", True),
    ("Free Pile Clean", "", "", True),
    ("Fruit Cage / Bread Area Clean", "", "", True),
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
    ("Maintenance Assistant", "", "", True),
    ("CO Member Resource", "", "", False),
    ("CO WRM", "", "", False),
    ("CO Health Worker", "", "", False),
    ("ConComm", "", "", False),
    ("ConComm AA", "", "", False),
    ("BSC President", "", "", False),
]

# (type_title, hours, days, count, start, end)
REGULAR_WORKSHIFTS = [
    # Morning Clean
    ("Kitchen / Dinning Room Clean", 1, [0, 1, 2, 3, 4, 5, 6], 1, None, time(11)),
    # Afternoon Clean
    ("Kitchen / Dinning Room Clean", 0.5, [0, 1, 2, 3, 4, 5, 6], 1, time(13), time(15)),
    # After Dinner Clean
    ("Kitchen / Dinning Room Clean", 1, [1, 2, 4, 6], 1, time(20), time(21)),
    # Morning Pots
    ("Pots", 1, [0, 1, 2, 3, 4, 5, 6], 1, None, time(11)),
    # Afternoon Pots
    ("Pots", 1, [0, 2, 4, 5, 6], 2, time(13), time(17)),
    ("Pots", 1, [1, 3], 1, time(13), time(17)),
    # Evening Pots
    ("Pots", 2, [1, 2, 6], 2, time(20), None),
    # Morning Dishes
    ("Dishes", 1, [0, 1, 2, 3, 4, 5, 6], 1, None, time(11)),
    # Early Afternoon Dishes
    ("Dishes", 1, [0, 1, 2, 3, 4, 5, 6], 1, time(13), time(16)),
    # Before Dinner Dishes
    ("Dishes", 1, [0, 1, 2, 3, 4, 6], 1, time(17), time(19)),
    # Evening Dishes
    ("Dishes", 1, [1, 2, 4, 5, 6], 1, time(20), None),
    # Evening Sweep & Mop
    ("Sweep & Mop", 1.5, [1, 2, 6], 1, time(21), None),
    ("Main Entrance / Front Walk Clean", 1, [1, 3], 1, None, None),
    ("Bike / Living / Study Room Clean", 1, [1, 4], 1, None, time(21)),
    ("Roofdeck Clean & Top Two Floors", 1, [1, 4], 1, None, time(19)),
    ("Ramp and Amphitheater Clean", 1, [2], 1, None, None),
    ("Pantry / Fridge Clean", 1, [5], 1, time(20), None),
    ("Free Pile Clean", 1.5, [2], 1, None, None),
    ("Dishroom Clean", 1, [3], 1, None, time(22)),
    ("Vacuum", 2, [1, 6], 1, None, time(22)),
    ("Food Put Away", 0.5, [0, 3], 1, time(13), time(16)),
    # Afternoon Food Put Away
    ("Food Put Away", 1, [3], 1, time(16), time(19)),
    ("Fruit Cage / Bread Area Clean", 0.5, [2], 1, None, time(22)),
    ("Bread Run", 2, [3], 1, None, None),
    # ("Dairy / Non-perishables Run", 2, [3], 2, None, None),
    ("Cook", 3, [0, 1, 2, 3, 4, 6], 3, time(16), time(19)),
    # Monday IKC
    ("IKC", 2, [0], 7, time(20), time(23)),
    # Thursday IKC
    ("IKC", 2, [3], 7, time(20), time(23)),
]

# (type_title, hours, count)
WEEK_LONG = (
    ("Basement / Laundry Room Clean", 2, 1),
    ("Laundry", 1, 1),
    ("CO Member Resource", 5, 1),
    ("CO WRM", 5, 1),
    ("CO Health Worker", 5, 1),
    ("ConComm", 2, 1),
    ("ConComm AA", 2, 1),
    ("BSC President", 5, 1),
    ("Maintenance Assistant", 3, 1),
    ("Farmer's Market Run", 2, 1),
    ("Granola", 2, 1),
    ("Hummus", 2, 1),
    ("Mail Sort / Forward", 1, 1),
)

# (type_title, hours, days, count, start, end)
HUMOR_WORKSHIFTS = [
    ("Pots", 2, [4, 5], 2, time(20), time(0)),
    ("Sweep & Mop", 2, [4, 5], 1, time(20), time(0)),
]

# (type_title, hours, days, count, start, end)
BATHROOM_WORKSHIFTS = [
    ("Bathroom Clean", 2, [1, 3, 5], 3, None, None),
]

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

def reset_all_shifts(semester=None, pool=None):
    if semester is None:
        semester = _get_semester()

    shifts = RegularWorkshift.objects.filter(pool__semester=semester)

    if pool is not None:
        shifts = shifts.filter(pool=pool)

    shift_count = shifts.count()
    shifts.delete()

    make_manager_workshifts(semester)

    return shift_count

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
    else:
        pool.hours = regular_hours
        pool.weeks_per_period = 0

    pool.save()

    _fill_workshift_types()

    # Regular Workshifts
    for type_title, hours, days, count, start, end in REGULAR_WORKSHIFTS:
        wtype = WorkshiftType.objects.get(title=type_title)
        for day in days:
            shift, created = RegularWorkshift.objects.get_or_create(
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
            if not created:
                shift.hours = hours
                shift.count = count
                shift.save()

    for type_title, hours, count in WEEK_LONG:
        wtype = WorkshiftType.objects.get(title=type_title)
        shift, created = RegularWorkshift.objects.get_or_create(
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
        if not created:
            shift.hours = hours
            shift.count = count
            shift.save()

def fill_bathroom_shifts(bathroom_hours=4, semester=None):
    if semester is None:
        semester = _get_semester()

    pool, created = WorkshiftPool.objects.get_or_create(
        title="Bathroom Shift",
        semester=semester,
        defaults=dict(any_blown=True, hours=bathroom_hours, weeks_per_period=0),
    )

    if not created:
        pool.hours = pool
        pool.weeks_per_period = 0
        pool.save()

    _fill_workshift_types()

    for type_title, hours, days, count, start, end in BATHROOM_WORKSHIFTS:
        wtype = WorkshiftType.objects.get(title=type_title)
        for day in days:
            shift, created = RegularWorkshift.objects.get_or_create(
                workshift_type=wtype,
                pool=pool,
                day=day,
                defaults=dict(
                    start_time=start,
                    end_time=end,
                    hours=hours,
                    count=count,
                ),
            )
            if not created:
                shift.hours = hours
                shift.count = count
                shift.save()

def fill_hi_shifts(hi_hours=5, semester=None):
    if semester is None:
        semester = _get_semester()

    # HI Hours
    pool, created = WorkshiftPool.objects.get_or_create(
        title="Home Improvement",
        semester=semester,
        defaults=dict(hours=hi_hours, weeks_per_period=0),
    )

    if created:
        pool.managers = Manager.objects.filter(title="Maintenance Manager")
    else:
        pool.hours = hi_hours
        pool.weeks_per_period = 0

    pool.save()

def fill_social_shifts(social_hours=1, semester=None):
    if semester is None:
        semester = _get_semester()

    # Social Hours
    pool, created = WorkshiftPool.objects.get_or_create(
        title="Social",
        semester=semester,
        defaults=dict(hours=social_hours, weeks_per_period=0),
    )

    if created:
        pool.managers = Manager.objects.filter(title="Social Manager")
    else:
        pool.hours = social_hours
        pool.weeks_per_period = 0

    pool.save()

def fill_humor_shifts(humor_hours=2, semester=None):
    if semester is None:
        semester = _get_semester()

    # Humor Shift
    pool, created = WorkshiftPool.objects.get_or_create(
        title="Humor Shift",
        semester=semester,
        defaults=dict(any_blown=True, hours=humor_hours, weeks_per_period=6),
    )

    if created:
        pool.managers = Manager.objects.filter(workshift_manager=True)
    else:
        pool.hours = humor_hours
        pool.weeks_per_period = 0

    pool.save()

    _fill_workshift_types()

    # Humor Workshifts
    for type_title, hours, days, count, start, end in HUMOR_WORKSHIFTS:
        wtype = WorkshiftType.objects.get(title=type_title)
        for day in days:
            shift, created = RegularWorkshift.objects.get_or_create(
                workshift_type=wtype,
                pool=pool,
                day=day,
                defaults=dict(
                    start_time=start,
                    end_time=end,
                    hours=hours,
                    count=count,
                ),
            )
            if not created:
                shift.hours = hours
                shift.count = count
                shift.save()

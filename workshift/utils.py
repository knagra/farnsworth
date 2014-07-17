"""
Project: Farnsworth

Authors: Karandeep Singh Nagra and Nader Morshed
"""

from collections import defaultdict
from datetime import date, timedelta, time, datetime
import random

from django.conf import settings
from django.utils.timezone import now, utc

from weekday_field.utils import ADVANCED_DAY_CHOICES

from managers.models import Manager
from workshift.models import TimeBlock, ShiftLogEntry, WorkshiftInstance, \
     Semester, PoolHours, WorkshiftProfile, WorkshiftPool, \
     WorkshiftType, RegularWorkshift, AUTO_VERIFY, WorkshiftRating

def can_manage(user, semester=None):
    """
    Whether a user is allowed to manage a workshift semester. This includes the
    current workshift managers, that semester's workshift managers, and site
    superusers.
    """
    if semester and user in semester.workshift_managers.all():
        return True
    if Manager and Manager.objects.filter(incumbent__user=user) \
      .filter(workshift_manager=True).count() > 0:
        return True
    return user.is_superuser

def get_year_season(day=None):
    """
    Returns a guess of the year and season of the current semester.
    """
    if day is None:
        day = date.today()
    year = day.year

    if day.month > 3 and day.month <= 7:
        season = Semester.SUMMER
    elif day.month > 7 and day.month <= 10:
        season = Semester.FALL
    else:
        season = Semester.SPRING
        if day.month > 10:
            year += 1
    return year, season

def get_semester_start_end(year, season):
    """
    Returns a guess of the start and end dates for given semester.
    """
    if season == Semester.SPRING:
        start_month, start_day = 1, 20
        end_month, end_day = 5, 17
    elif season == Semester.SUMMER:
        start_month, start_day = 5, 25
        end_month, end_day = 8, 16
    else:
        start_month, start_day = 8, 24
        end_month, end_day = 12, 20

    return date(year, start_month, start_day), date(year, end_month, end_day)

def get_int_days(days):
    """
    Converts a string, or list of strings into integers for their respective
    days of the week.
    """
    if not isinstance(days, list) and not isinstance(days, tuple):
        days = [days]
    ret = []
    for day in days:
        day = [i[0] for i in ADVANCED_DAY_CHOICES if i[1] == day][0]
        if isinstance(day, int):
            ret.append(day)
        else:
            for value in day.strip("[]").split(","):
                value = int(value)
                if value not in ret:
                    ret.append(value)
    return ret

def _date_range(start, end, step):
    """
    'range' for datetime.date
    """
    while start <= end:
        yield start
        start += step

def make_instances(semester, shifts=None, start=None):
    if semester is None:
        semester = Semester.objects.get(current=True)
    if shifts is None:
        shifts = RegularWorkshift.objects.filter(pool__semester=semester)
    if start is None:
        start = now().date()
    new_instances = []
    for shift in shifts:
        if shift.week_long:
            # Workshifts have until Sunday to complete their shift
            days = [6]
        else:
            days = shift.days
        for weekday in days:
            next_day = start + timedelta(days=int(weekday) - start.weekday())
            for day in _date_range(next_day, semester.end_date, timedelta(weeks=1)):
                # Create new instances for the entire semester
                prev_instances = WorkshiftInstance.objects.filter(
                    weekly_workshift=shift, date=day, closed=False)
                for instance in prev_instances[shift.count:]:
                    instance.delete()
                assignees = shift.current_assignees.all()
                for i in range(prev_instances.count(), shift.count):
                    instance = WorkshiftInstance.objects.create(
                        weekly_workshift=shift,
                        date=day,
                        hours=shift.hours,
                        intended_hours=shift.hours,
                        )
                    if i < len(assignees):
                        instance.workshifter = assignees[i]
                        log = ShiftLogEntry.objects.create(
                            person=instance.workshifter,
                            entry_type=ShiftLogEntry.ASSIGNED,
                            )
                        instance.logs.add(log)
                        instance.save()
                    new_instances.append(instance)
    return new_instances

def make_workshift_pool_hours(semester=None, profiles=None, pools=None,
                              primary_hours=None):
    if semester is None:
        try:
            semester = Semester.objects.get(current=True)
        except Semester.DoesNotExist:
            return []
    if profiles is None:
        profiles = WorkshiftProfile.objects.filter(semester=semester)
    if pools is None:
        pools = WorkshiftPool.objects.filter(semester=semester)

    ret = []
    for profile in profiles:
        for pool in pools:
            if not profile.pool_hours.filter(pool=pool):
                if pool.is_primary and primary_hours:
                    hours = primary_hours
                else:
                    hours = pool.hours
                pool_hours = PoolHours.objects.create(
                    pool=pool,
                    hours=hours,
                    )
                profile.pool_hours.add(pool_hours)
                ret.append(pool_hours)
        profile.save()
    return ret

def make_manager_workshifts(semester=None, managers=None):
    if semester is None:
        try:
            semester = Semester.objects.get(current=True)
        except Semester.DoesNotExist:
            return []
    if managers is None:
        managers = Manager.objects.filter(active=True)
    shifts = []
    for manager in managers:
        if semester.season == Semester.SUMMER:
            hours = manager.summer_hours
        else:
            hours = manager.semester_hours
        wtype, new = WorkshiftType.objects.get_or_create(title=manager.title)
        if new:
            wtype.rateable = False
        wtype.description = manager.duties
        wtype.hours = hours
        wtype.save()
        shift, new = RegularWorkshift.objects.get_or_create(
            workshift_type=wtype,
            title=manager.title,
            pool=WorkshiftPool.objects.get(semester=semester, is_primary=True),
            )
        if new:
            shift.week_long = True
            shift.verify = AUTO_VERIFY
        shift.hours = wtype.hours
        if manager.incumbent:
            shift.current_assignee = WorkshiftProfile.objects.get(
                user=manager.incumbent.user,
                )
        shift.save()
        shifts.append(shift)
    make_instances(semester=semester, shifts=shifts)
    return shifts

def past_verify(instance, moment=None):
    if moment is None:
        moment = now()

    end_datetime = datetime.combine(
        instance.date,
        instance.end_time or time(0),
        )

    if instance.end_time is None:
        end_datetime += timedelta(days=1)

    if settings.USE_TZ:
        end_datetime = end_datetime.replace(tzinfo=utc)

    return moment > end_datetime + timedelta(hours=instance.pool.verify_cutoff)

def past_sign_out(instance, moment=None):
    if moment is None:
        moment = now()

    start_datetime = datetime.combine(
        instance.date,
        instance.start_time or time(0),
        )

    if settings.USE_TZ:
        start_datetime = start_datetime.replace(tzinfo=utc)

    return moment > start_datetime - timedelta(hours=instance.pool.sign_out_cutoff)

def collect_blown(semester=None, moment=None):
    if semester is None:
        try:
            semester = Semester.objects.get(current=True)
        except Semester.DoesNotExist:
            return []
    if moment is None:
        moment = now()
    closed, verified, blown = [], [], []
    today = date.today()
    instances = WorkshiftInstance.objects.filter(
        semester=semester, closed=False, date__lte=today,
        )
    for instance in instances:
        # Skip shifts not yet ended
        if not past_verify(instance, moment=moment):
            continue

        instance.closed = True

        workshifter = instance.workshifter or instance.liable

        # Skip shifts that have no assignees
        if workshifter is None:
            closed.append(instance)
        else:
            # Update the workshifter's standing
            pool_hours = workshifter.pool_hours.get(pool=instance.pool)

            if instance.verify != AUTO_VERIFY or instance.liable:
                pool_hours.standing -= instance.hours
                entry_type = ShiftLogEntry.BLOWN
                instance.blown = True
                blown.append(instance)
            else:
                pool_hours.standing += instance.hours
                entry_type = ShiftLogEntry.VERIFY
                verified.append(instance)

            pool_hours.save()

            # Make a log entry
            if entry_type:
                log = ShiftLogEntry.objects.create(
                    entry_type=entry_type,
                    )
                instance.logs.add(log)

        instance.save()

    return closed, verified, blown

def is_available(workshift_profile, regular_workshift):
    """
    Check whether a specified user is able to do a specified workshift.
    Parameters:
        workshift_profile is the workshift profile for a user
        regular_workshift is a weekly recurring workshift
    Returns:
        True if the user has enough free time between the shift's start time
            and end time to do the shift's required number of hours.
        False otherwise.
    """
    if regular_workshift.week_long:
        return True
    days = []
    for day in regular_workshift.days:
        start_time = regular_workshift.start_time
        end_time = regular_workshift.end_time
        relevant_blocks = list()
        for block in workshift_profile.time_blocks.all().order_by('start_time'):
            if block.day == day and block.preference == TimeBlock.BUSY \
              and block.start_time < end_time \
              and block.end_time > start_time:
                relevant_blocks.append(block)
        # Time blocks should be ordered; so go through and see if there is a wide
        # enough window for the shifter to do the shift.  If there is,
        # return True.
        hours = timedelta(hours=float(regular_workshift.hours))
        if not relevant_blocks:
            days.append(day)
            continue
        elif relevant_blocks[0].start_time - start_time >= hours:
            days.append(day)
            continue
        while len(relevant_blocks) > 0:
            first_block = relevant_blocks.pop(0)
            if len(relevant_blocks) == 0 \
              and end_time - first_block.end_tim >= hours:
              days.append(day)
              continue
            elif relevant_blocks[0].start_time - first_block.end_time >= hours:
              days.append(day)
              continue
    return days

def _frange(start, end, step):
    while start <= end:
        yield start
        start += step
    if start - step != end:
        yield end


def auto_assign_shifts(semester, pool=None, profiles=None, shifts=None):
    if pool is None:
        pool = WorkshiftPool.objects.get(semester=semester, is_primary=True)
    if profiles is None:
        # .order_by('preference_save_date')
        profiles = WorkshiftProfile.objects.filter(semester=semester)
    if shifts is None:
        shifts = RegularWorkshift.objects.filter(pool=pool)

    shifts = list(shifts)
    profiles = list(profiles)

    # TODO: Pre-process, rank shifts by their times / preferences
    hours_mapping = defaultdict(int)

    for i in _frange(0, pool.hours, 1):
        for profile in profiles:
            pool_hours = profile.pool_hours.get(pool=pool)
            rankings = defaultdict(list)
            for shift in shifts:
                if not is_available(profile, shift):
                    continue
                try:
                    rating = profile.ratings.get(
                        workshift_type=shift.workshift_type,
                        ).rating
                except WorkshiftRating.DoesNotExist:
                    rating = WorkshiftRating.INDIFFERENT
                if rating == WorkshiftRating.DISLIKE:
                    rank = 5
                elif rating == WorkshiftRating.INDIFFERENT:
                    rank = 3
                else:
                    rank = 1

                # If not preferred time:
                # rank += 1

                rankings[(profile, rank)].append(shift)

            for rank in range(1, 7):
                if rankings[(profile, rank)]:
                    # Select the shift, starting with those that take the most
                    # hours and fit the best into the workshifter's allotted hours
                    shift = random.choice(rankings[(profile, rank)])

                    # Assign the person to their shift
                    shift.current_assignees.add(profile)

                    hours_mapping[profile] += shift.hours

                    # Remove shift from shifts and update rankings accordingly
                    if shift.current_assignees.count() == shift.count:
                        pass

            # Remove profiles when their hours have all been assigned
            if pool_hours.hours <= hours_mapping[profile]:
                profiles.remove(profile)

    # Return profiles that were incompletely assigned shifts
    return profiles

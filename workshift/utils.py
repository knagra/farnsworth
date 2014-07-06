"""
Project: Farnsworth

Authors: Karandeep Singh Nagra and Nader Morshed
"""

from datetime import date, timedelta, time, datetime

from django.utils.timezone import utc

from weekday_field.utils import ADVANCED_DAY_CHOICES

from managers.models import Manager
from workshift.models import TimeBlock, ShiftLogEntry, WorkshiftInstance, \
     Semester, PoolHours, WorkshiftProfile, WorkshiftPool, \
     WorkshiftType, RegularWorkshift

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
    day = regular_workshift.day
    start_time = regular_workshift.start_time
    end_time = regular_workshift.end_time
    relevant_blocks = list()
    for block in workshift_profile.time_blocks.all():
        if block.day == day and block.preference == TimeBlock.BUSY \
          and block.start_time < end_time \
          and block.end_time > start_time:
            relevant_blocks.append(block)
    if not relevant_blocks:
        return True
    hours = regular_workshift.hours

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
    day = start
    while day <= end:
        yield day
        day += step

def make_instances(semester, shifts=None, now=None):
    if semester is None:
        semester = Semester.objects.get(current=True)
    if shifts is None:
        shifts = RegularWorkshift.objects.filter(pool__semester=semester)
    if now is None:
        now = date.today()
    new_instances = []
    for shift in shifts:
        if shift.week_long:
            # Workshifts have until Sunday to complete their shift
            days = [6]
        else:
            days = shift.days
        for weekday in days:
            next_day = now + timedelta(days=int(weekday) - now.weekday())
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
                        auto_verify=shift.auto_verify,
                        week_long=shift.week_long,
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
            shift.auto_verify = True
        shift.hours = wtype.hours
        if manager.incumbent:
            shift.current_assignee = WorkshiftProfile.objects.get(
                user=manager.incumbent.user,
                )
        shift.save()
        shifts.append(shift)
    make_instances(semester=semester, shifts=shifts)
    return shifts

def past_verify(instance, now=None):
    if now is None:
        now = datetime.now().replace(tzinfo=utc)

    if instance.end_time is not None:
        end_time = timedelta(
            hours=instance.end_time.hour,
            minutes=instance.end_time.minute,
            )
    else:
        end_time = timedelta(hours=24)

    end_datetime = (
        datetime.combine(instance.date, time(0)) +
        timedelta(hours=instance.pool.verify_cutoff) + end_time
        ).replace(tzinfo=utc)

    return now > end_datetime

def past_sign_out(instance, now=None):
    if now is None:
        now = datetime.now().replace(tzinfo=utc)

    if instance.start_time is not None:
        start_time = instance.start_time
    else:
        start_time = time(0)
    start_datetime = (
        datetime.combine(instance.date, start_time) -
         timedelta(hours=instance.pool.sign_out_cutoff)
        ).replace(tzinfo=utc)

    return now > start_datetime

def collect_blown(semester=None, now=None):
    if semester is None:
        try:
            semester = Semester.objects.get(current=True)
        except Semester.DoesNotExist:
            return []
    if now is None:
        now = datetime.now().replace(tzinfo=utc)
    closed, verified, blown = [], [], []
    today = date.today()
    instances = WorkshiftInstance.objects.filter(
        semester=semester, closed=False, date__lte=today,
        )
    for instance in instances:
        # Skip shifts not yet ended
        if not past_verify(instance, now=now):
            continue

        instance.closed = True

        workshifter = instance.workshifter or instance.liable

        # Skip shifts that have no assignees
        if workshifter is None:
            closed.append(instance)
        else:
            # Update the workshifter's standing
            pool_hours = workshifter.pool_hours.get(pool=instance.pool)

            if not instance.auto_verify or instance.liable:
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

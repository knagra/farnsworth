"""
Project: Farnsworth

Authors: Karandeep Singh Nagra and Nader Morshed
"""

from __future__ import division

from collections import defaultdict
from datetime import date, timedelta, time, datetime
from itertools import cycle
import random

from django.conf import settings
from django.db.models import Q
from django.utils.timezone import now, localtime

from notifications import notify
from pytz import timezone

from managers.models import Manager
from workshift.models import *

def can_manage(user, semester=None, pool=None):
    """
    Whether a user is allowed to manage a workshift semester. This includes the
    current workshift managers, that semester's workshift managers, and site
    superusers.
    """
    if semester and user in semester.workshift_managers.all():
        return True

    if Manager and Manager.objects.filter(
        incumbent__user=user, workshift_manager=True
    ).count() > 0:
        return True

    if pool and pool.managers.filter(incumbent__user=user).count() > 0:
        return True

    return user.is_superuser or user.is_staff

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

def _date_range(start, end, step):
    """
    'range' for datetime.date
    """
    while start <= end:
        yield start
        start += step

def make_instances(semester=None, shifts=None, start=None):
    if semester is None:
        semester = Semester.objects.get(current=True)
    if shifts is None:
        shifts = RegularWorkshift.objects.filter(pool__semester=semester)
    if start is None:
        start = max([localtime(now()).date(), semester.start_date])
    new_instances = []
    for shift in shifts:
        # Delete all old instances of this shift
        WorkshiftInstance.objects.filter(
            weekly_workshift=shift, closed=False,
        ).delete()

        # Figure out the day to start from for this shift
        if shift.day is None or shift.week_long:
            # Workshifts have until Sunday to complete their shift
            day = 6
        else:
            day = shift.day
        next_day = start + timedelta(days=int(day) - start.weekday())

        # Create new instances for the entire semester
        assignees = shift.current_assignees.all()
        for day in _date_range(next_day, semester.end_date, timedelta(weeks=1)):
            for i in range(shift.count):
                instance = WorkshiftInstance.objects.create(
                    weekly_workshift=shift,
                    date=day,
                    hours=shift.hours,
                    intended_hours=shift.hours,
                )
                if i < len(assignees):
                    instance.workshifter = assignees[i]
                    instance.save(update_fields=["workshifter"])
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
    return ret

def make_manager_workshifts(semester=None, managers=None):
    if semester is None:
        try:
            semester = Semester.objects.get(current=True)
        except Semester.DoesNotExist:
            return []
    try:
        pool = WorkshiftPool.objects.get(
            semester=semester,
            is_primary=True,
        )
    except WorkshiftPool.DoesNotExist:
        return []

    if managers is None:
        managers = Manager.objects.filter(active=True)

    shifts = []
    for manager in managers:
        if semester.season == Semester.SUMMER:
            hours = manager.summer_hours
        else:
            hours = manager.semester_hours
        wtype, new = WorkshiftType.objects.get_or_create(
            title=manager.title,
            defaults=dict(rateable=False, assignment=WorkshiftType.NO_ASSIGN),
        )
        wtype.description = manager.duties
        wtype.save(update_fields=["description"])
        shift, new = RegularWorkshift.objects.get_or_create(
            workshift_type=wtype,
            pool=pool,
            defaults=dict(week_long=True, verify=AUTO_VERIFY),
        )
        if not new:
            WorkshiftInstance.objects.filter(
                weekly_workshift=shift, closed=False,
            ).delete()
        shift.is_manager_shift = True
        shift.hours = hours
        if manager.incumbent:
            shift.current_assignees = WorkshiftProfile.objects.filter(
                user=manager.incumbent.user,
                semester=semester,
            )
        shift.active = manager.active
        shift.save(update_fields=["is_manager_shift", "hours", "active"])
        shifts.append(shift)

    return shifts

def past_verify(instance, moment=None):
    if moment is None:
        moment = localtime(now())

    end_datetime = datetime.combine(
        instance.date,
        instance.end_time or time(0),
    )

    if instance.end_time is None:
        end_datetime += timedelta(days=1)

    if settings.USE_TZ:
        end_datetime = end_datetime.replace(tzinfo=timezone(settings.TIME_ZONE))

    return moment > end_datetime + timedelta(hours=instance.pool.verify_cutoff)

def past_sign_out(instance, moment=None):
    if moment is None:
        moment = localtime(now())

    start_datetime = datetime.combine(
        instance.date,
        instance.start_time or time(0),
    )

    if settings.USE_TZ:
        start_datetime = start_datetime.replace(tzinfo=timezone(settings.TIME_ZONE))

    return moment > start_datetime - timedelta(hours=instance.pool.sign_out_cutoff)

def collect_blown(semester=None, moment=None):
    if semester is None:
        try:
            semester = Semester.objects.get(current=True)
        except (Semester.DoesNotExist, Semester.MultipleObjectsReturned):
            return []
    if moment is None:
        moment = localtime(now())

    closed, verified, blown = [], [], []
    today = moment.date()
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

            pool_hours.save(update_fields=["standing"])

            # Make a log entry
            if entry_type:
                log = ShiftLogEntry.objects.create(
                    entry_type=entry_type,
                )
                instance.logs.add(log)

            # Send out notifications
            targets = []
            targets.append(workshifter.user)
            for manager in instance.pool.managers.all():
                if manager.incumbent:
                    targets.append(manager.incumbent.user)
            for target in targets:
                notify.send(
                    instance,
                    verb="was automatically marked as blown",
                    recipient=target,
                )

        instance.save(update_fields=["closed", "blown"])

    return closed, verified, blown

def is_available(workshift_profile, shift):
    """
    Check whether a specified user is able to do a specified workshift.
    Parameters:
        workshift_profile is the workshift profile for a user
        shift is a weekly recurring workshift
    Returns:
        True if the user has enough free time between the shift's start time
            and end time to do the shift's required number of hours.
        False otherwise.
    """
    if shift.week_long:
        return True

    start_time = shift.start_time or time(hour=0)
    end_time = shift.end_time or time(hour=23, minute=59)
    relevant_blocks = list()

    for block in workshift_profile.time_blocks.order_by('start_time'):
        if block.day == shift.day and block.preference == TimeBlock.BUSY \
          and block.start_time < end_time \
          and block.end_time > start_time:
            relevant_blocks.append(block)

    # Time blocks should be ordered; so go through and see if there is a wide
    # enough window for the shifter to do the shift.  If there is,
    # return True.
    if not relevant_blocks:
        return True

    hours_delta = timedelta(hours=float(shift.hours))

    # Check the time between shift start and block start
    block = relevant_blocks.pop(0)
    start_delta = timedelta(
        hours=block.start_time.hour - start_time.hour,
        minutes=block.start_time.minute - start_time.minute,
    )

    if start_delta >= hours_delta:
        return True

    while len(relevant_blocks) > 0:
        block, prev_block = relevant_blocks.pop(0), block

        # Check the time between the last block and the next block
        # is larger than the length of the shift
        start_end_delta = timedelta(
            hours=block.start_time.hour - prev_block.end_time.hour,
            minutes=block.start_time.minute - prev_block.end_time.minute,
        )

        if start_end_delta >= hours_delta:
            return True

    # Check the time between the end of the time block to the end of the shift
    end_delta = timedelta(
        hours=end_time.hour - block.end_time.hour,
        minutes=end_time.minute - block.end_time.minute,
    )

    if end_delta >= hours_delta:
         return True

    return False

def auto_assign_shifts(semester=None, pool=None, profiles=None, shifts=None):
    if semester is None:
        try:
            semester = Semester.objects.get(current=True)
        except (Semester.DoesNotExist, Semester.MultipleObjectsReturned):
            return
    if pool is None:
        pool = WorkshiftPool.objects.get(
            semester=semester,
            is_primary=True,
        )
    if profiles is None:
        profiles = WorkshiftProfile.objects.filter(
            semester=semester,
        ).order_by('preference_save_time')
    if shifts is None:
        shifts = RegularWorkshift.objects.filter(
            pool=pool,
            workshift_type__assignment=WorkshiftType.AUTO_ASSIGN,
        )

    shifts = set([
        shift
        for shift in shifts
        if shift.current_assignees.count() < shift.count
    ])
    profiles = list(profiles)

    # List of hours assigned to each profile
    hours_mapping = defaultdict(float)

    # Pre-process, rank shifts by their times / preferences
    rankings = defaultdict(set)

    # Initialize with already-assigned shifts
    for profile in profiles:
        pool_hours = profile.pool_hours.get(pool=pool)
        hours_mapping[profile] = float(pool_hours.assigned_hours)

        for shift in shifts:
            # Skip shifts that put a member over their hour requirement
            if float(shift.hours) + hours_mapping[profile] > float(pool_hours.hours):
                continue

            # Check how well this shift fits the member's schedule
            status = is_available(profile, shift)
            if not status or status == TimeBlock.BUSY:
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

            if status != TimeBlock.PREFERRED:
                rank += 1

            rankings[profile, rank].add(shift)

    # Assign shifts in a round-robin manner, run until we can't assign anyone
    # any more shifts
    while any(rankings.values()):
        for profile in profiles[:]:
            pool_hours = profile.pool_hours.get(pool=pool)

            # Assign a shift, picking from the most preferable groups first
            for rank in range(1, 7):
                # Update the rankings with the list of available shifts
                rankings[profile, rank].intersection_update(shifts)

                if rankings[profile, rank]:
                    # Select the shift, starting with those that take the most
                    # hours and fit the best into the workshifter's allotted
                    # hours
                    shift = max(rankings[profile, rank], key=lambda x: x.hours)

                    # Assign the person to their shift
                    shift.current_assignees.add(profile)

                    hours_mapping[profile] += float(shift.hours)

                    # Remove shift from shifts if it has been completely filled
                    if shift.current_assignees.count() >= shift.count:
                        shifts.remove(shift)

                    break

            # Remove profiles when their hours have all been assigned
            if float(pool_hours.hours) <= hours_mapping[profile]:
                profiles.remove(profile)

                for rank in range(1, 7):
                    if (profile, rank) in rankings:
                        del rankings[profile, rank]

                continue

            # Otherwise, Remove shifts that put people above their weekly
            # allocation
            for rank in range(1, 7):
                rankings[profile, rank] = set(
                    shift
                    for shift in rankings[profile, rank]
                    if float(shift.hours) + hours_mapping[profile] <=
                    float(pool_hours.hours)
                )

    # Return profiles that were incompletely assigned shifts
    return profiles

def randomly_assign_instances(semester, pool, profiles=None, instances=None):
    """
    Randomly assigns workshift instances to profiles.

    Returns
    -------
    list of workshift.WorkshiftProfile
    list of workshift.WorkshiftInstance
    """
    if profiles is None:
        profiles = WorkshiftProfile.objects.filter(semester=semester)
    if instances is None:
        instances = WorkshiftInstance.objects.filter(
            Q(info__pool=pool) |
            Q(weekly_workshift__pool=pool),
            workshifter__isnull=True,
            closed=False,
        ).exclude(
            weekly_workshift__workshift_type__assignment=WorkshiftType.NO_ASSIGN,
        )

    instances = list(instances)
    profiles = list(profiles)

    # List of hours assigned to each profile
    hours_mapping = defaultdict(float)
    total_hours_owed = defaultdict(float)

    semester_weeks = (semester.end_date - semester.start_date).days / 7

    # Initialize with already-assigned instances
    for profile in profiles:
        for shift in profile.instance_workshifter.filter(
                Q(info__pool=pool) |
                Q(weekly_workshift__pool=pool)
            ):
            hours_mapping[profile] += float(shift.hours)
        pool_hours = profile.pool_hours.get(pool=pool)
        if pool.weeks_per_period == 0:
            total_hours_owed[profile] = pool_hours.hours
        else:
            total_hours_owed[profile] = \
              semester_weeks / pool.weeks_per_period * float(pool_hours.hours)

    while profiles and instances:
        for profile in profiles[:]:
            instance = random.choice(instances)
            instance.workshifter = profile

            instance.save(update_fields=["workshifter"])
            instances.remove(instance)

            hours_mapping[profile] += float(instance.hours)
            if hours_mapping[profile] >= total_hours_owed[profile]:
                profiles.remove(profile)
            if not instances:
                break

    return profiles, instances

def clear_all_assignments(semester=None, pool=None):
    if semester is None:
        try:
            semester = Semester.objects.get(current=True)
        except (Semester.DoesNotExist, Semester.MultipleObjectsReturned):
            return []
    if pool is None:
        pool = WorkshiftPool.objects.get(
            semester=semester,
            is_primary=True,
        )
    shifts = RegularWorkshift.objects.filter(
        pool=pool,
        is_manager_shift=False,
        workshift_type__assignment=WorkshiftType.AUTO_ASSIGN,
    )
    for shift in shifts:
        shift.current_assignees.clear()

def update_standings(semester=None, pool_hours=None, moment=None):
    if semester is None:
        try:
            semester = Semester.objects.get(current=True)
        except (Semester.DoesNotExist, Semester.MultipleObjectsReturned):
            return []
    if moment is None:
        moment = localtime(now())

    if pool_hours is None:
        pool_hours = PoolHours.objects.filter(pool__semester=semester)

    for hours in pool_hours:
        # Don't update hours after the semester ends
        if hours.last_updated and hours.last_updated.date() > semester.end_date:
            continue

        periods = 0

        # Calculate the number of periods since we last updated the standings
        if hours.pool.weeks_per_period == 0:
            # Only update this pool once
            if not hours.last_updated:
                periods = 1
        else:
            # Note, this will give periods > 0 on weeks starting on start_date's day,
            # rather than explicitly Sunday
            if not hours.last_updated:
                last_weeks = 0
            else:
                last_weeks = (hours.last_updated.date() - semester.start_date).days // 7

            sem_weeks = (moment.date() - semester.start_date).days // 7
            periods = (sem_weeks - last_weeks) // hours.pool.weeks_per_period

        # Update the actual standings
        if periods:
            hours.standing -= hours.hours * periods
            hours.last_updated = moment
            hours.save(update_fields=["standing", "last_updated"])

def reset_standings(semester=None, pool_hours=None):
    if semester is None:
        try:
            semester = Semester.objects.get(current=True)
        except (Semester.DoesNotExist, Semester.MultipleObjectsReturned):
            return
    if pool_hours is None:
        pool_hours = PoolHours.objects.filter(pool__semester=semester)

    for hours in pool_hours:
        hours.last_updated = None
        hours.standing = hours.hour_adjustment

        profile = WorkshiftProfile.objects.get(pool_hours=hours)

        for field in ["workshifter", "liable"]:
            instances = WorkshiftInstance.objects.filter(
                Q(weekly_workshift__pool=hours.pool) | Q(info__pool=hours.pool),
                closed=True,
                **{field: profile}
            )
            for instance in instances:
                if instance.blown:
                    hours.standing -= instance.hours
                else:
                    hours.standing += instance.hours

        hours.save(update_fields=["standing", "last_updated"])

    update_standings(
        semester=semester,
        pool_hours=pool_hours,
    )

def calculate_assigned_hours(profiles=None):
    """
    Recalculates PoolHour.assigned_hours from scratch.
    """
    if profiles is None:
        profiles = WorkshiftProfile.objects.all()
    for profile in profiles:
        for pool_hours in profile.pool_hours.all():
            shifts = RegularWorkshift.objects.filter(
                current_assignees=profile,
                pool=pool_hours.pool,
                active=True,
            )
            pool_hours.assigned_hours = sum(i.hours for i in shifts)
            pool_hours.save(update_fields=["assigned_hours"])

def reset_instance_assignments(semester=None, shifts=None):
    if semester is None:
        try:
            semester = Semester.objects.get(current=True)
        except (Semester.DoesNotExist, Semester.MultipleObjectsReturned):
            return
    if shifts is None:
        shifts = RegularWorkshift.objects.filter(
            pool__semester=semester,
        )

    for shift in shifts:
        instances = WorkshiftInstance.objects.filter(
            closed=False,
            weekly_workshift=shift,
        ).order_by("date")

        assignees = list(shift.current_assignees.all())
        assignees += [None] * (shift.count - len(assignees))
        dates = defaultdict(set)

        for assignee, instance in zip(cycle(assignees), instances):
            if assignee is not None:
                if instance.date in dates[assignee.pk]:
                    continue

                dates[assignee.pk].add(instance.date)

            instance.workshifter = assignee
            instance.liable = None
            instance.save(update_fields=["workshifter", "liable"])


from __future__ import division, absolute_import

from collections import defaultdict

from django.db.models import signals
from django.dispatch import receiver
from django.utils.timezone import now, localtime

from notifications import notify

from utils.variables import ANONYMOUS_USERNAME
from managers.models import Manager
from workshift.models import *
from workshift.fields import DAY_CHOICES
from workshift import utils


@receiver(signals.post_save, sender=UserProfile)
def create_workshift_profile(sender, instance, created, **kwargs):
    '''
    Function to add a workshift profile for every User that is created.
    Parameters:
        instance is an of UserProfile that was just saved.
    '''
    if instance.user.username == ANONYMOUS_USERNAME or \
       instance.status != UserProfile.RESIDENT:
        return

    try:
        semester = Semester.objects.get(current=True)
    except (Semester.DoesNotExist, Semester.MultipleObjectsReturned):
        pass
    else:
        profile, created = WorkshiftProfile.objects.get_or_create(
            user=instance.user,
            semester=semester,
        )
        if created:
            utils.make_workshift_pool_hours(
                semester=semester,
                profiles=[profile],
            )


@receiver(signals.post_save, sender=WorkshiftPool)
def create_workshift_pool_hours(sender, instance, **kwargs):
    pool = instance
    utils.make_workshift_pool_hours(
        semester=pool.semester,
        pools=[pool],
    )


@receiver(signals.post_save, sender=Semester)
def initialize_semester(sender, instance, created, **kwargs):
    if not created:
        return

    semester = instance
    semester.workshift_managers = [
        i.incumbent.user
        for i in Manager.objects.filter(workshift_manager=True)
    ]
    semester.preferences_open = True
    semester.save(update_fields=["preferences_open"])

    # Set current to false for previous semesters
    for prev_semester in Semester.objects.exclude(pk=semester.pk):
        prev_semester.current = False
        prev_semester.save(update_fields=["current"])

    # Create the primary workshift pool
    pool, created = WorkshiftPool.objects.get_or_create(
        semester=semester,
        is_primary=True,
    )
    if created:
        pool.managers = Manager.objects.filter(workshift_manager=True)

    # Create this semester's workshift profiles
    for uprofile in UserProfile.objects.filter(
            status=UserProfile.RESIDENT,
    ).exclude(user__username=ANONYMOUS_USERNAME):
        WorkshiftProfile.objects.create(
            user=uprofile.user,
            semester=semester,
        )

    utils.make_workshift_pool_hours(semester=semester)
    utils.make_manager_workshifts(semester=semester)


@receiver(signals.pre_save, sender=WorkshiftPool)
def update_pool_hours(sender, instance, **kwargs):
    pool = instance
    old_pool = None

    if pool.id:
        old_pool = sender.objects.get(pk=pool.id)

    for pool_hours in PoolHours.objects.filter(pool=pool):
        if old_pool is None or pool_hours.hours == old_pool.hours:
            pool_hours.hours = pool.hours
            pool_hours.save(update_fields=["hours"])


@receiver(signals.post_save, sender=WorkshiftPool)
def make_pool_hours(sender, instance, created, **kwargs):
    pool = instance

    if created:
        utils.make_workshift_pool_hours(pool.semester, pools=[pool])


def _check_field_changed(instance, old_instance, field_name, update_fields=None):
    """
    Examines update_fields and an attribute of an instance to determine if
    that attribute has changed prior to the instance being saved.

    Parameters
    ----------
    field_name : str
    instance : object
    old_instance : object
    update_fields : list of str, optional
    """
    if update_fields is not None and field_name not in update_fields:
        return False

    return getattr(instance, field_name) != getattr(old_instance, field_name)


@receiver(signals.post_save, sender=WorkshiftInstance)
def log_entry_create(sender, instance, created, **kwargs):
    if created:
        # Don't create the log until after the instance is created, we can't use a
        # many-to-many relationship otherwise
        if instance.workshifter:
            instance.logs.add(
                ShiftLogEntry.objects.create(
                    person=instance.workshifter,
                    entry_type=ShiftLogEntry.ASSIGNED,
                    note="Initial assignment.",
                )
            )


@receiver(signals.pre_save, sender=PoolHours)
def manual_hour_adjustment(sender, instance, update_fields=None, **kwargs):
    pool_hours = instance

    # Subtract previously given adjustment hours
    if pool_hours.id:
        old_pool_hours = sender.objects.get(pk=pool_hours.id)

        reset_hours = _check_field_changed(
            pool_hours, old_pool_hours, "hours",
            update_fields=update_fields,
        )
        reset_adjustment = _check_field_changed(
            pool_hours, old_pool_hours, "hour_adjustment",
            update_fields=update_fields,
        )

        if reset_hours:
            # Reset and recalculate standings from all sources
            utils.reset_standings(
                semester=pool_hours.pool.semester,
                pool_hours=[pool_hours],
            )
        elif reset_adjustment:
            change = pool_hours.hour_adjustment - old_pool_hours.hour_adjustment
            pool_hours.standing += change


@receiver(signals.post_save, sender=PoolHours)
def set_initial_standing(sender, instance, created, **kwargs):
    if created:
        pool_hours = instance
        pool_hours.standing += pool_hours.hour_adjustment
        pool_hours.save(update_fields=["standing"])


@receiver(signals.pre_delete, sender=Semester)
def clear_semester(sender, instance, **kwargs):
    semester = instance
    WorkshiftProfile.objects.filter(semester=semester).delete()
    WorkshiftPool.objects.filter(semester=semester).delete()
    WorkshiftInstance.objects.filter(semester=semester).delete()
    RegularWorkshift.objects.filter(pool__semester=semester).delete()


@receiver(signals.post_save, sender=Manager)
def create_manager_workshifts(sender, instance, created, **kwargs):
    manager = instance
    try:
        semester = Semester.objects.get(current=True)
    except (Semester.DoesNotExist, Semester.MultipleObjectsReturned):
        pass
    else:
        utils.make_manager_workshifts(semester=semester, managers=[manager])


@receiver(signals.post_save, sender=RegularWorkshift)
def create_workshift_instances(sender, instance, created, **kwargs):
    shift = instance
    if shift.active:
        if created:
            # Make instances for newly created shifts
            utils.make_instances(shift.pool.semester, shifts=[shift])
    else:
        WorkshiftInstance.objects.filter(
            weekly_workshift=shift,
            closed=False,
        ).delete()


@receiver(signals.pre_delete, sender=RegularWorkshift)
def delete_workshift_instances(sender, instance, **kwargs):
    shift = instance
    instances = WorkshiftInstance.objects.filter(
        weekly_workshift=shift,
    )
    info = InstanceInfo.objects.create(
        title=shift.workshift_type.title,
        description=shift.workshift_type.description,
        pool=shift.pool,
        start_time=shift.start_time,
        end_time=shift.end_time,
    )
    for instance in instances:
        if instance.closed:
            instance.weekly_workshift = None
            instance.info = info
            instance.closed = True
            instance.save(update_fields=["weekly_workshift", "info", "closed"])
        else:
            instance.delete()

    if shift.active:
        for assignee in shift.current_assignees.all():
            pool_hours = assignee.pool_hours.get(pool=shift.pool)
            pool_hours.assigned_hours -= shift.hours
            pool_hours.save(update_fields=["assigned_hours"])


@receiver(signals.m2m_changed, sender=RegularWorkshift.current_assignees.through)
def update_assigned_hours(sender, instance, action, reverse, model, pk_set, **kwargs):
    shift = instance

    if shift.active:
        # Update workshifter assigned hours
        if action in ["pre_remove", "pre_clear"]:
            if not pk_set:
                assignees = shift.current_assignees.all()
            else:
                assignees = WorkshiftProfile.objects.filter(pk__in=pk_set)

            for assignee in assignees:
                pool_hours = assignee.pool_hours.get(pool=shift.pool)
                pool_hours.assigned_hours -= shift.hours
                pool_hours.save(update_fields=["assigned_hours"])

                notify.send(
                    shift,
                    verb="You were removed from",
                    action_object=shift,
                    recipient=assignee.user,
                )

        elif action in ["post_add"]:
            # Add shift's hours to current assignees
            assignees = WorkshiftProfile.objects.filter(pk__in=pk_set)

            for assignee in assignees:
                pool_hours = assignee.pool_hours.get(pool=shift.pool)
                pool_hours.assigned_hours += shift.hours
                pool_hours.save(update_fields=["assigned_hours"])

                notify.send(
                    shift,
                    verb="You were assigned to",
                    action_object=shift,
                    recipient=assignee.user,
                )

        instances = WorkshiftInstance.objects.filter(
                weekly_workshift=shift,
                date__gte=localtime(now()).date(),
                closed=False,
            ).order_by("date")
        # Update instances
        if action in ["post_remove", "post_clear"]:
            # Unassign these people from any instances they were assigned to
            for instance in instances:
                if not pk_set or instance.workshifter.pk in pk_set:
                    instance.workshifter = None
                    instance.liable = None
                    instance.save(update_fields=["workshifter", "liable"])

        elif action in ["post_add"]:
            # Assign these people to any instances of this shift if they are
            # not assigned an instance on that day or have already signed out
            # of one on that day
            dates = defaultdict(set)
            assignees = WorkshiftProfile.objects.filter(pk__in=pk_set)

            for instance in instances:
                # Check if member is assigned to shift
                if instance.workshifter is not None:
                    if instance.workshifter.pk in pk_set:
                        dates[instance.workshifter.pk].add(instance.date)

                # If an assignee already signed out of a shift on this day,
                # don't re-assign them to it
                signed_out = instance.logs.filter(
                    person__pk__in=pk_set,
                    entry_type=ShiftLogEntry.SIGNOUT,
                )

                for person in signed_out:
                    dates[person.pk].add(instance.date)

            for instance in instances.filter(workshifter__isnull=True):
                # Find a member who is not yet assigned to an instance on this
                # day and assign them to this one
                for assignee in assignees:
                    if instance.date in dates[assignee.pk]:
                        continue

                    instance.workshifter = assignee
                    instance.liable = None
                    instance.save(update_fields=["workshifter", "liable"])

                    instance.logs.add(
                        ShiftLogEntry.objects.create(
                            person=instance.workshifter,
                            entry_type=ShiftLogEntry.ASSIGNED,
                        )
                    )

                    dates[assignee.pk].add(instance.date)

                    break


@receiver(signals.pre_save, sender=RegularWorkshift)
def pre_process_shift(sender, instance, update_fields=None, **kwargs):
    shift = instance

    # Set week_long if day not set
    shift.week_long = shift.day not in [i[0] for i in DAY_CHOICES]

    # Create instances if shift is being changed from inactive to active
    if shift.id and shift.active:
        old_shift = sender.objects.get(pk=shift.id)
        if _check_field_changed(
                shift, old_shift, "active",
                update_fields=update_fields,
        ):
            utils.make_instances(shift.pool.semester, shifts=[shift])


@receiver(signals.pre_delete, sender=WorkshiftInstance)
def subtract_instance_hours(sender, instance, **kwargs):
    # Subtract this workshift from a person's hours if necessary
    if instance.closed and instance.workshifter:
        pool_hours = instance.workshifter.pool_hours.get(pool=instance.pool)
        pool_hours.standing -= instance.hours
        pool_hours.save(update_fields=["standing"])

    # Delete any associated information
    if instance.info:
        instance.info.delete()

    instance.logs.all().delete()

@receiver(signals.pre_delete, sender=WorkshiftProfile)
def delete_associated_hours(sender, instance, **kwargs):
    profile = instance

    # Delete associated model instances
    profile.time_blocks.all().delete()
    profile.ratings.all().delete()
    profile.pool_hours.all().delete()

# TODO: Auto-notify manager and workshifter when they are >= 10 hours down
# TODO: Auto-email central when workshifters are >= 15 hours down?

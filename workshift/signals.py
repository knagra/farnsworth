
from django.dispatch import receiver
from django.db.models import signals
from django.utils.timezone import now

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
    semester.workshift_managers = \
      [i.incumbent.user for i in Manager.objects.filter(workshift_manager=True)]
    semester.preferences_open = True
    semester.save()

    # Set current to false for previous semesters
    for prev_semester in Semester.objects.exclude(pk=semester.pk):
        prev_semester.current = False
        prev_semester.save()

    # Create the primary workshift pool
    pool, created = WorkshiftPool.objects.get_or_create(
        semester=semester,
        is_primary=True,
    )
    if created:
        pool.managers = Manager.objects.filter(workshift_manager=True)

    # Create this semester's workshift profiles
    for uprofile in UserProfile.objects.filter(status=UserProfile.RESIDENT):
        if uprofile.user.username == ANONYMOUS_USERNAME:
            continue
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
            pool_hours.save()

@receiver(signals.post_save, sender=WorkshiftPool)
def make_pool_hours(sender, instance, created, **kwargs):
    pool = instance

    if created:
        utils.make_workshift_pool_hours(pool.semester, pools=[pool])

@receiver(signals.pre_save, sender=WorkshiftInstance)
def log_entry_assign(sender, instance, **kwargs):
    old_instance = None

    if instance.id:
        old_instance = sender.objects.get(pk=instance.id)

        # TODO: Cover other log entries here, too?
        if instance.workshifter and \
           old_instance.workshifter != instance.workshifter:
            log = ShiftLogEntry.objects.create(
                person=instance.workshifter,
                entry_type=ShiftLogEntry.ASSIGNED,
            )
            instance.logs.add(log)

@receiver(signals.post_save, sender=WorkshiftInstance)
def log_entry_create(sender, instance, created, **kwargs):
    if created:
        # Don't create the log until after the instance is created, we can use a
        # many-to-many relationship otherwise
        if instance.workshifter:
            log = ShiftLogEntry.objects.create(
                person=instance.workshifter,
                entry_type=ShiftLogEntry.ASSIGNED,
            )
            instance.logs.add(log)

@receiver(signals.pre_save, sender=PoolHours)
def manual_hour_adjustment(sender, instance, **kwargs):
    pool_hours = instance

    # Subtract previously given adjustment hours
    if pool_hours.id:
        old_pool_hours = sender.objects.get(pk=pool_hours.id)

        if old_pool_hours.hours != pool_hours.hours:
            # Reset and recalculate standings from all sources
            signals.pre_save.disconnect(
                manual_hour_adjustment,
            )
            utils.reset_standings(
                semester=pool_hours.pool.semester,
                pool_hours=[pool_hours],
            )
            signals.pre_save.connect(
                manual_hour_adjustment,
                sneder=PoolHours,
            )
        elif old_pool_hours.hour_adjustment != pool_hours.hour_adjustment:
            pool_hours.standing += pool_hours.hour_adjustment - \
                                   old_pool_hours.hour_adjustment

@receiver(signals.post_save, sender=PoolHours)
def set_initial_standing(sender, instance, created, **kwargs):
    if created:
        pool_hours = instance
        pool_hours.standing += pool_hours.hour_adjustment
        pool_hours.save(update_fields=["standing"])

@receiver(signals.pre_delete, sender=Semester)
def clear_semester(sender, instance, **kwargs):
    semester = instance
    ShiftLogEntry.objects.filter(person__semester=semester).delete()
    WorkshiftInstance.objects.filter(semester=semester).delete()
    InstanceInfo.objects.filter(pool__semester=semester).delete()
    RegularWorkshift.objects.filter(pool__semester=semester).delete()
    PoolHours.objects.filter(pool__semester=semester).delete()
    WorkshiftProfile.objects.filter(semester=semester).delete()
    WorkshiftPool.objects.filter(semester=semester).delete()

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
            utils.make_instances(shift.pool.semester, shifts=[instance])
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
            instance.save()
        else:
            instance.delete()

    if shift.active:
        for assignee in shift.current_assignees.all():
            pool_hours = assignee.pool_hours.get(pool=shift.pool)
            pool_hours.assigned_hours -= shift.hours
            pool_hours.save()

@receiver(signals.m2m_changed, sender=RegularWorkshift.current_assignees.through)
def update_assigned_hours(sender, instance, action, reverse, model, pk_set, **kwargs):
    shift = instance

    if action in ["pre_remove", "pre_clear"]:
        if not pk_set:
            assignees = shift.current_assignees.all()
        else:
            assignees = WorkshiftProfile.objects.filter(pk__in=pk_set)

        for assignee in assignees:
            pool_hours = assignee.pool_hours.get(pool=shift.pool)
            pool_hours.assigned_hours -= shift.hours
            pool_hours.save()

    elif action in ["post_add"]:
        # Add shift's hours to current assignees
        assignees = WorkshiftProfile.objects.filter(pk__in=pk_set)

        for assignee in assignees:
            pool_hours = assignee.pool_hours.get(pool=shift.pool)
            pool_hours.assigned_hours += shift.hours
            pool_hours.save()

    if action in ["post_remove", "post_clear"]:
        # ...
        instances = WorkshiftInstance.objects.filter(
            weekly_workshift=shift,
            closed=False,
        ).order_by("date")

        for instance in instances:
            if not pk_set or instance.workshifter.pk in pk_set:
                instance.workshifter = None
                instance.liable = None
                instance.save()

    elif action in ["post_add"]:
        # ...
        utils.reset_instance_assignments(
            semester=shift.pool.semester,
            shifts=[shift],
        )

@receiver(signals.pre_save, sender=RegularWorkshift)
def set_week_long(sender, instance, **kwargs):
    shift = instance
    shift.week_long = shift.day not in [i[0] for i in DAY_CHOICES]

@receiver(signals.pre_delete, sender=WorkshiftInstance)
def subtract_instance_hours(sender, instance, **kwargs):
    if instance.closed and instance.workshifter:
        pool_hours = instance.workshifter.pool_hours.get(pool=instance.pool)
        pool_hours.standing -= instance.hours
        pool_hours.save()

# TODO: Auto-notify manager and workshifter when they are >= 10 hours down
# TODO: Auto-email central when workshifters are >= 15 hours down?

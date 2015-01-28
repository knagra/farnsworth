
from django.dispatch import receiver
from django.db.models import signals

from workshift.models import *
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
    utils.make_manager_workshifts(
        semester=pool.semester,
    )

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
        utils.make_instances(shift.pool.semester, shifts=[instance])
    else:
        delete_workshift_instances(sender=sender, instance=shift)

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

@receiver(signals.pre_save, sender=RegularWorkshift)
def subtract_workshift_pool_hours(sender, instance, **kwargs):
    shift = instance

    # Subtract previously given hours
    if shift.id:
        old_shift = sender.objects.get(pk=shift.id)
        delete_regular_workshift(sender, old_shift)

@receiver(signals.post_save, sender=RegularWorkshift)
def add_workshift_pool_hours(sender, instance, **kwargs):
    shift = instance

    # Add shift's hours to current assignees
    for assignee in shift.current_assignees.all():
        pool_hours = assignee.pool_hours.get(pool=shift.pool)
        pool_hours.assigned_hours += shift.hours
        pool_hours.save()

@receiver(signals.pre_delete, sender=RegularWorkshift)
def delete_regular_workshift(sender, instance, **kwargs):
    shift = instance

    for assignee in shift.current_assignees.all():
        pool_hours = assignee.pool_hours.get(pool=shift.pool)
        pool_hours.assigned_hours -= shift.hours
        pool_hours.save()

@receiver(signals.pre_save, sender=RegularWorkshift)
def set_week_long(sender, instance, **kwargs):
    shift = instance
    shift.week_long = shift.day is None

# TODO: Auto-notify manager and workshifter when they are >= 10 hours down
# TODO: Auto-email central when workshifters are >= 15 hours down?

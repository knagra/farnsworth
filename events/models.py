'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''

from django.core.urlresolvers import reverse
from django.db import models

from base.models import UserProfile
from managers.models import Manager

class Event(models.Model):
    '''
    The Event model.  Contains an owner, a description, and an event date-time, along
    with a post_date and a title.
    '''
    owner = models.ForeignKey(
        UserProfile,
        help_text="The user who posted this event.",
        related_name="poster",
        )
    title = models.CharField(
        blank=False,
        null=False,
        max_length=255,
        help_text="The title of this event.",
        )
    description = models.TextField(
        blank=False,
        help_text="Description of this event.",
        )
    location = models.CharField(
        blank=True,
        null=True,
        max_length=255,
        help_text="Location of event.",
        )
    start_time = models.DateTimeField(
        blank=False,
        null=False,
        help_text="When this event starts.",
        )
    end_time = models.DateTimeField(
        blank=False,
        null=False,
        help_text="When this event ends.",
        )
    post_date = models.DateTimeField(
        auto_now_add=True,
        help_text="The date this event was posted.",
        )
    change_date = models.DateTimeField(
        auto_now=True,
        help_text="The date this event was last modified.",
        )
    cancelled = models.BooleanField(
        default=False,
        help_text="Optional cancellation field.",
        )
    as_manager = models.ForeignKey(
        Manager,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        help_text="The manager position this event is posted, if this is a manager event.",
        )
    rsvps = models.ManyToManyField(
        UserProfile,
        blank=True,
        null=True,
        help_text="The users who plan to attend this event.",
        related_name="rsvps",
        )
    public = models.BooleanField(
        default=False,
        help_text="Whether this event can be seen by non-members.",
        )

    def __unicode__(self):
        return self.title

    class Meta:
        # could also do -start_time, -end_time, post_date but opting for the
        # slight performance increase
        ordering = ['-start_time']

    def is_event(self):
        return True

    def get_view_url(self):
        return reverse("events:view", kwargs={"event_pk": self.pk})

    def get_edit_url(self):
        return reverse("events:edit", kwargs={"event_pk": self.pk})

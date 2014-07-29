'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''

from django.contrib.auth.models import User, Group, Permission
from django.core.urlresolvers import reverse
from django.db import models

from base.models import UserProfile

class Thread(models.Model):
    '''
    The Thread model.  Used to group messages.
    '''
    owner = models.ForeignKey(
        UserProfile,
        help_text="The user who started this thread.",
        )
    subject = models.CharField(
        blank=False,
        null=False,
        max_length=254,
        help_text="Subject of this thread.",
        )
    start_date = models.DateTimeField(
        auto_now_add=True,
        help_text="The date this thread was started.",
        )
    change_date = models.DateTimeField(
        auto_now=True,
        help_text="The last time this thread was modified.",
        )
    number_of_messages = models.PositiveSmallIntegerField(
        default=1,
        help_text="The number of messages in this thread.",
        )
    active = models.BooleanField(
        default=True,
        help_text="Whether this thread is still active.",
        )
    views = models.PositiveIntegerField(
        default=0,
        help_text="The number times this thread has been viewed.",
        )
    followers = models.ManyToManyField(
        User,
        blank=True,
        null=True,
        related_name="following",
        help_text="Users following this thread",
        )

    def __unicode__(self):
        return self.subject

    class Meta:
        ordering = ['-change_date']

    def is_thread(self):
        return True

    def get_view_url(self):
        return reverse("threads:view_thread", kwargs={"pk": self.pk})

class Message(models.Model):
    '''
    The Message model.  Contains a body, owner, and post_date, referenced by thread.
    '''
    body = models.TextField(
        blank=False,
        null=False,
        help_text="Body of this message.",
        )
    owner = models.ForeignKey(
        UserProfile,
        help_text="The user who posted this message.",
        )
    post_date = models.DateTimeField(
        auto_now_add=True,
        help_text="The date this message was posted.",
        )
    thread = models.ForeignKey(
        Thread,
        help_text="The thread to which this message belongs.",
        )

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return self.body

    class Meta:
        ordering = ['post_date']

    def is_message(self):
        return True

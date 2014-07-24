'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''

from django.db import models
from django.contrib.auth.models import User, Group, Permission

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
        help_text="The number times this thread has been viewed.",
        )

    def __unicode__(self):
        return self.subject

    class Meta:
        ordering = ['-change_date']

    def is_thread(self):
        return True

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

    def __unicode__(self):
        return "Message by %s on thread %s, posted %s" % (self.owner, self.thread.subject, self.post_date)

    class Meta:
        ordering = ['post_date']

    def is_message(self):
        return True

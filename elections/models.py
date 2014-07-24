"""
Project: Farnsworth

Authors: Karandeep Singh Nagra and Nader Morshed
"""

from django.db import models

from base.models import UserProfile
from managers.models import Manager

class Petition(models.Model):
    """ Petition model. """
    title = models.CharField(
        blank=False,
        null=False,
        max_length=255,
        help_text="The title for this petition."
        )
    owner = models.ForeignKey(
        UserProfile,
        help_text="Person who initiated this petition."
        )
    description = models.TextField(
        blank=False,
        null=False,
        help_text="Description of this petition and what it entails."
        )
    signatures = models.ManyToManyField(
        UserProfile,
        null=True,
        blank=True,
        help_text="Members who have signed onto this petition.",
        related_name="signatures"
        )
    post_date = models.DateTimeField(
        blank=False,
        null=False,
        help_text="Date this petition was posted."
        )
    end_date = models.DateTimeField(
        blank=False,
        null=False,
        help_text="Date when this petition ends."
        )
    closed = models.BooleanField(
        default=False,
        help_text="Whether this petition is closed to signatures."
        )
    
    def __unicode__(self):
        return self.title
    
    def is_petition(self):
        return True

class PetitionComment(models.Model):
    """ Model for a comment on a petition. """
    owner = models.ForeignKey(
        UserProfile,
        help_text="Person who posted this comment."
        )
    body = models.TextField(
        blank=False,
        null=False,
        help_text="The body of this comment."
        )
    post_date = models.DateTimeField(
        blank=False,
        null=False,
        help_text="When this comment was posted."
        )
    petition = models.ForeignKey(
        Petition,
        help_text="The corresponding petition."
        )
    
    def __unicode__(self):
        return "{0} comment".format(self.petition)
    
    def is_petition_comment(self):
        return True

class Poll(models.Model):
    """ Poll model. """
    title = models.CharField(
        blank=False,
        null=False,
        max_length=255,
        help_text="The title for this poll."
        )
    owner = models.ForeignKey(
        UserProfile,
        help_text="Person who posted this poll."
        )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="A description for this poll."
        )
    post_date = models.DateTimeField(
        blank=False,
        null=False,
        help_text="When this poll was posted."
        )
    close_date = models.DateTimeField(
        blank=False,
        null=False,
        help_text="When this poll closes."
        )
    closed = models.BooleanField(
        default=False,
        help_text="Whether this poll has closed."
        )
    anonymity_allowed = models.BooleanField(
        default=False,
        help_text="Whether anonymity is allowed."
        )
    alumni_allowed = models.BooleanField(
        default=False,
        help_text="Whether alumni are allowed to participate."
        )
    election = models.BooleanField(
        default=False,
        help_text="Treat this poll as a formal election."
        )
    
    def __unicode__(self):
        return self.title
    
    def is_poll(self):
        return True

class PollSettings(models.Model):
    """
    Settings for someone who has filled a petition.
    Also used to see who had filled a poll, as settings are only
    stored for those who have done a poll.
    """
    poll = models.ForeignKey(
        Poll,
        help_text="The relevant poll."
        )
    owner = models.ForeignKey(
        UserProfile,
        help_text="The user whose settings these are."
        )
    anonymous = models.BooleanField(
        default=False,
        help_text="Whether this user decided to be anonymous for this poll."
        )
    complete_date = models.DateTimeField(
        blank=False,
        null=False,
        auto_now_add=True,
        help_text="When this user finished the poll."
        )
    updated = models.DateTimeField(
        blank=False,
        null=False,
        auto_now_add=True,
        auto_now=True,
        help_text="When this user last updated her/his input for this poll."
        )

class PollQuestion(models.Model):
    """ Poll question model. """
    poll = models.ForeignKey(
        Poll,
        null=False,
        blank=False,
        help_text="The corresponding poll."
        )
    body = models.CharField(
        max_length=511,
        null=False,
        blank=False,
        help_text="The body of this question."
        )
    CHOICE = 'C'
    BOOLEAN = 'B'
    TEXT = 'T'
    RANK = 'R'
    TYPE_CHOICES = (
        (CHOICE, "Multiple Choice"),
        (BOOLEAN, "Yes/No"),
        (TEXT, "Text Input"),
        (RANK, "Ranked Choice")
    )
    question_type = models.CharField(
        max_length=1,
        choices=TYPE_CHOICES,
        default=TEXT,
        help_text="The type of question this is."
        )
    yes_answers = models.ManyToManyField(
        UserProfile,
        null=True,
        blank=True,
        help_text="Yes votes for this question, if a yes/no question.",
        related_name="yes_answers"
        )
    no_answers = models.ManyToManyField(
        UserProfile,
        null=True,
        blank=True,
        help_text="No votes for this question, if a yes/no question.",
        related_name="no_answers"
        )
    write_ins_allowed = models.BooleanField(
        default=False,
        help_text="Whether write-ins are allowed, if this is a multiple choice question."
        )
    
    def __unicode__(self):
        return self.body
    
    def is_poll_question(self):
        return True

class PollChoice(models.Model):
    """ A possible choice to a CHOICE type question. """
    question = models.ForeignKey(
        PollQuestion,
        null=False,
        blank=False,
        help_text="The corresponding question."
        )
    body = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        help_text="The text body for this choice."
        )
    voters = models.ManyToManyField(
        UserProfile,
        null=True,
        blank=True,
        help_text="Those who have voted for this choice."
        )
    
    def __unicode__(self):
        return self.body
    
    def is_poll_choice(self):
        return True

class PollAnswer(models.Model):
    """ Text answer to a TEXT type question. """
    question = models.ForeignKey(
        PollQuestion,
        null=False,
        blank=False,
        help_text="The question being answered."
        )
    body = models.TextField(
        null=False,
        blank=False,
        help_text="Text body for this poll answer."
        )
    owner = models.ForeignKey(
        UserProfile,
        null=False,
        blank=False,
        help_text="User who posted this answer."
        )

    def __unicode__(self):
        return self.owner

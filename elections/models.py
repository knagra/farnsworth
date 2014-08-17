"""
Project: Farnsworth

Authors: Karandeep Singh Nagra and Nader Morshed
"""

from django.contrib.auth.models import User
from django.db import models

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
        User,
        help_text="Person who initiated this petition."
        )
    description = models.TextField(
        blank=False,
        null=False,
        help_text="Description of this petition and what it entails."
        )
    signatures = models.ManyToManyField(
        User,
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
    number_or_comments = models.PositiveIntegerField(
        default=0,
        help_text="Number of comments on this petition."
        )

    def __unicode__(self):
        return self.title

    def is_petition(self):
        return True

class PetitionComment(models.Model):
    """ Model for a comment on a petition. """
    owner = models.ForeignKey(
        User,
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
        User,
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
    voc = models.BooleanField(
        default=False,
        help_text="Treat this poll as a \"Votes of Confidence\" election.",
        )

    def __str__(self):
        return self.__unicode__()

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
        User,
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
    CHECKBOXES = 'B'
    TEXT = 'T'
    RANK = 'R'
    RANGE = 'G'
    TYPE_CHOICES = (
        (CHOICE, "Multiple Choice, Select One"),
        (CHECKBOXES, "Checkboxes, Select Multiple"),
        (TEXT, "Text Input"),
        (RANK, "Rank Choices in Comparison to Each Other"),
        (RANGE, "0 to n Range for Each Choice"),
        )
    question_type = models.CharField(
        max_length=1,
        choices=TYPE_CHOICES,
        default=TEXT,
        help_text="The type of question this is."
        )
    range_upper_limit = models.PositiveIntegerField(
        default=10,
        null=True,
        blank=True,
        help_text="Upper limit if this is a range type question."
        )
    required = models.BooleanField(
        default=True,
        help_text="Whether an answer to this question is required."
        )
    write_ins_allowed = models.BooleanField(
        default=False,
        help_text="Whether write-ins are allowed, if this is a multiple choice question."
        )

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return self.body

    def is_poll_question(self):
        return True

class PollChoice(models.Model):
    """ A possible choice to a CHOICE or CHECKBOXES type question. """
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
        User,
        null=True,
        blank=True,
        help_text="Those who have voted for this choice."
        )

    def __str__(self):
        return self.__unicode__()

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
        User,
        null=False,
        blank=False,
        help_text="User who posted this answer."
        )

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return self.owner

class PollRanks(models.Model):
    """
    Ordered rankings for RANK or RANGE type question.
    Rankings are represented by a list of integers,
    with integer position in the list representing
    the relative primary key of the question choices.
    
    This class's rankings property returns a list of
    tuples of form (choice, ranking) for the user who
    submitted this ranking.
    
    It also includes a few functions for creating and
    normalizing ratings.
    
    A higher rating indicates a preference over a
    lower rating.
    """
    question = models.ForeignKey(
        PollQuestion,
        null=False,
        blank=False,
        help_text="The question being answered."
        )
    rankings = models.CommaSeparatedIntegerField(
        max_length=1023,
        null=False,
        blank=False,
        help_text="Rankings for the choices for this question."
        )
    owner = models.ForeignKey(
        User,
        null=False,
        blank=False,
        help_text="User who posted this ranking."
        )

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return self.owner

    @property
    def rankings(self):
        rankings_list = [int(s) for x in self.rankings.split(',')]
        return [(choice, rankings_list.pop(0)) for choice in self.question.choice_set.order_by('pk')]

    def create_ranking(ranking_tuples):
        """
        Create and return a string suitable for the rankings
        field when given tuples of choices and rankings.
        Parameters:     ranking_tuples should be an iterable
                            of tuples of form (choice, ranking)
        """
        return ",".join([str(r) for c, r in sorted(
                ranking_tuples,
                key=lambda x: x[0].pk
                )])

    def normalize_ranking(ranking_tuples):
        """
        Normalize rankings by reducing them to the simplest
        order.  E.g.:
            If the rankings for 2 choices are -244 and 4,
            this function will normalize them to 0 and 1,
            respectively.
        Parameters:     ranking_tuples should be an iterable
                            of tuples of form (choice, ranking)
        Return a list of tuples of form (choice, ranking), with
        the ranking normalized.
        """
        ranking_tuples = sorted(ranking_tuples, key=lambda x: x[1])
        normalized = [(ranking_tuples.pop(0)[0], 0)]
        while ranking_tuples:
            current = ranking_tuples.pop(0)
            normalized.append((
                current[0],
                normalized[-1][1] if current[1] = normalized[-1][1] \
                    else normalized[-1][1] + 1,
                ))
        return normalized

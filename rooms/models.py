"""
Project: Farnsworth

Authors: Karandeep Singh Nagra and Nader Morshed
"""


from django.core.validators import RegexValidator, MinValueValidator
from django.db import models

alphanumeric = RegexValidator(r'^[0-9A-Za-z]+$', 'Only alphanumeric characters are allowed.')

class Room(models.Model):
    """ Model for a resident room in the house. """
    title = models.CharField(
        unique=True,
        blank=False,
        null=False,
        max_length=100,
        validators=[alphanumeric],
        help_text="The title of the room (i.e. '2E'). Characters A-Z, 0-9.",
        )
    unofficial_name = models.CharField(
        blank=True,
        null=True,
        max_length=100,
        help_text="The unofficial name of the room (i.e. 'Starry Night')",
        )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="The description of this room.",
        )
    occupancy = models.IntegerField(
        default=1,
        validators=[MinValueValidator(0)],
        help_text="The total number of people that this room should house.",
        )
    current_residents = models.ManyToManyField(
        UserProfile,
        null=True,
        blank=True,
        help_text="The current residents of this room."
        )

    def __unicode__(self):
        return self.title

    def __str__(self):
        return self.__unicode__()

class PreviousResidence(models.Model):
    """ Model to represent a previous residence in a room. """
    room = models.ForeignKey(
        Room,
        null=False,
        blank=False,
        help_text="The relevant room."
        )
    resident = models.ForeignKey(
        UserProfile,
        null=False,
        blank=False,
        help_text="The resident."
        )
    start_date = models.DateField(
        null=False,
        blank=False,
        auto_now_add=False,
        auto_now=False,
        help-text="Start date of this person's residence in this room."
        )
    end_date = models.DateField(
        null=False,
        blank=False,
        auto_now_add=False,
        auto_now=False,
        help-text="End date of this person's residence in this room."
        )

    def __unicode__(self):
        return self.room.title

    def __str__(self):
        return self.__unicode__()

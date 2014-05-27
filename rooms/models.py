
from django.core.validators import RegexValidator, MinValueValidator
from django.db import models

from base.models import UserProfile

alphanumeric = RegexValidator(r'^[0-9A-Z]+$', 'Only uppercase alphanumeric characters are allowed.')

class Room(models.Model):
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
	residents = models.ManyToManyField(
        UserProfile,
        blank=True,
        help_text="Members who currently live in this room.",
        )

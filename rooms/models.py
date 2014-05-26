
from django.core.validators import RegexValidator
from django.db import models

from base.models import UserProfile

alphanumeric = RegexValidator(r'^[0-9a-zA-Z]*$', 'Only alphanumeric characters are allowed.')

class Room(models.Model):
	title = models.CharField(unique=True, blank=False, null=False, max_length=100, help_text="The title of the room (i.e. '2E'). Characters A-Z, a-z, 0-9.", validators=[alphanumeric])
	unofficial_name  = models.TextField(blank=True, null=True, help_text="The unofficial name of the room (i.e. 'Starry Night')")
	description = models.TextField(blank=True, null=True, help_text="The description of this room.")
	occupancy = models.IntegerField(default=1, help_text="The total number of people that this room should house.")
	residents = models.ManyToManyField(UserProfile, help_text="Members who live in this room.")

'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''

from django.db import models
from threads.models import UserProfile

class Event(models.Model):
	'''
	The Event model.  Contains an owner, a description, and an event date-time, along
	with a post_date and a title.
	'''
	owner = models.ForeignKey(UserProfile, help_text="The user who posted this event.")
	title = models.CharField(blank=False, null=False, max_length=255, help_text="The title of this event.")
	description = models.TextField(blank=False, help_text="Description of this event.")
	start_time = models.DateTimeField(blank=False, null=False, help_text="When this event starts.")
	end_time = models.DateTimeField(blank=False, null=False, help_text="When this event ends."
	post_date = models.DateTimeField(auto_now_add=True, help_text="The date this event was posted.")
	
	def __unicode__(self):
		return "%s on %s, posted by %s" % (self.title, self.date_time, self.owner)



'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''

from django.db import models
from threads.models import UserProfile
from requests.models import Manager

class Event(models.Model):
	'''
	The Event model.  Contains an owner, a description, and an event date-time, along
	with a post_date and a title.
	'''
	owner = models.ForeignKey(UserProfile, help_text="The user who posted this event.", related_name="poster")
	title = models.CharField(blank=False, null=False, max_length=255, help_text="The title of this event.")
	description = models.TextField(blank=False, help_text="Description of this event.")
	location = models.CharField(blank=True, null=True, max_length=255, help_text="Location of event.")
	start_time = models.DateTimeField(blank=False, null=False, help_text="When this event starts.")
	end_time = models.DateTimeField(blank=False, null=False, help_text="When this event ends.")
	post_date = models.DateTimeField(auto_now_add=True, help_text="The date this event was posted.")
	change_date = models.DateTimeField(auto_now_add=True, auto_now=True, help_text="The date this event was last modified.")
	cancelled = models.BooleanField(default=True, help_text="Optional cancellation field.")
	as_manager = models.ForeignKey(Manager, blank=True, null=True, on_delete=models.SET_NULL, help_text="The manager position this event is posted, if this is a manager event.")
	rsvps = models.ManyToManyField(UserProfile, blank=True, null=True, help_text="The users who plan to attend this event.", related_name="rsvps")
	
	def __unicode__(self):
		return "%s on %s, posted by %s" % (self.title, self.date_time, self.owner)
	
	class Meta:
		ordering = ['-start_time']	# could also do -start_time, -end_time, post_date but opting for the slight performance increase

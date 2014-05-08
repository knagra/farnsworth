'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''

from django.db import models
from threads.models import UserProfile

class Manager(models.Model):
	'''
	The Manager model.  Contains title, incumbent, and duties.
	'''
	title = models.CharField(unique=True, blank=False, null=False, max_length=255, help_text="The title of this management position.")
	incumbent = models.ForeignKey(UserProfile, blank=True, null=True, on_delete=models.SET_NULL, help_text="The incumbent for this position.")
	compensation = models.TextField(blank=True, null=True, help_text="The compensation for this manager.")
	duties = models.TextField(blank=True, null=True, help_text="The duties of this manager.")
	email = models.EmailField(blank=True, null=True, max_length=255, help_text="The e-mail address of this manager.")
	
	def __unicode__(self):
		return "%s" % self.title
	
	def is_manager(self):
		return True

class RequestType(models.Model):
	'''
	A request type to specify relevant managers and name.
	'''
	name = models.CharField(max_length=255, blank=False, null=False, help_text="Name of the request type, lowercase with _ in place of space.")
	managers = models.ManyToManyField(Manager, help_text="Managers to whom this type of request is made.")
	enabled = models.BooleanField(default=True, help_text="Whether this type of request is currently accepted. Toggle this to off to temporarily disable accepting this type of request.")
	glyphicon = models.CharField(max_length=100, blank=True, null=True, help_text="Glyphicon for this request type (e.g., cutlery).  Check Bootstrap documentation for more info.")
	
	def __unicode__(self):
		return "%s RequestType" % self.name
	
	def human_readable_name(self):
		return self.name.replace('_', ' ')
	
	def is_requesttype(self):
		return True

class Request(models.Model):
	'''
	The Request model.  Contains an owner, body, post_date, change_date, and relevant
	manager.
	'''
	owner = models.ForeignKey(UserProfile, blank=False, null=False, help_text="The user who made this request.")
	body = models.TextField(blank=False, null=False, help_text="The body of this request.")
	post_date = models.DateTimeField(auto_now_add=True, help_text="The date this request was posted.")
	change_date = models.DateTimeField(auto_now_add=True, help_text="The last time this request was modified.")
	request_type = models.ForeignKey(RequestType, blank=False, null=False, help_text="The type of request this is.")
	filled = models.BooleanField(default=False, help_text="Whether the manager deems this request filled.")
	closed = models.BooleanField(default=False, help_text="Whether the manager has closed this request.")
	number_of_responses = models.PositiveSmallIntegerField(default=0, help_text="The number of responses to this request.")
	upvotes = models.ManyToManyField(UserProfile, null=True, blank=True, help_text="Up votes for this request.", related_name="up_votes")
	downvotes = models.ManyToManyField(UserProfile, null=True, blank=True, help_text="Down votes for this request.", related_name="down_votes")
	
	def __unicode__(self):
		return "%s request by %s on %s" % (self.request_type.name, self.owner, self.post_date)
	
	class Meta:
		ordering = ['-post_date']
	
	def is_request(self):
		return True

class Response(models.Model):
	'''
	The Response model.  A response to a request.  Very similar to Request.
	'''
	owner = models.ForeignKey(UserProfile, blank=False, null=False, help_text="The user who posted this response.")
	body = models.TextField(blank=False, null=False, help_text="The body of this response.")
	post_date = models.DateTimeField(auto_now_add=True, help_text="The date this response was posted.")
	request = models.ForeignKey(Request, blank=False, null=False, help_text="The request to which this is a response.")
	manager = models.BooleanField(default=False, help_text="Whether this is a relevant manager response.")
	
	def __unicode__(self):
		return "Response by %s to: %s" % (self.owner, self.request)
	
	class Meta:
		ordering = ['post_date']
	
	def is_response(self):
		return True

class ProfileRequest(models.Model):
	'''
	The ProfileRequest model.  A request to create a user account on the site.
	'''
	username = models.CharField(blank=False, null=True, max_length=100, help_text="Username if this user is created.")
	first_name = models.CharField(blank=False, null=False, max_length=100, help_text="First name if user is created.")
	last_name = models.CharField(blank=False, null=False, max_length=100, help_text="Last name if user is created.")
	email = models.CharField(blank=False, null=False, max_length=255, help_text="E-mail address if user is created.")
	request_date = models.DateTimeField(auto_now_add=True, help_text="Whether this request has been granted.")
	affiliation = models.CharField(max_length=1, choices=UserProfile.STATUS_CHOICES, default=UserProfile.RESIDENT, help_text="User's affiliation with the house.")
	
	def __unicode__(self):
		return "Profile request for account '%s %s (%s)' on %s" % (self.first_name, self.last_name, self.username, self.request_date)
	
	def is_profilerequest(self):
		return True

class Announcement(models.Model):
	'''
	Model for manager announcements.
	'''
	manager = models.ForeignKey(Manager, blank=False, null=False, help_text="The manager who made this announcement.")
	incumbent = models.ForeignKey(UserProfile, blank=False, null=False, help_text="The incumbent who made this announcement.")
	body = models.TextField(blank=False, null=False, help_text="The body of the announcement.")
	post_date = models.DateTimeField(auto_now_add=True, help_text="The date this announcement was posted.")
	pinned = models.BooleanField(default=False, help_text="Whether this announcment should be pinned permanently.")
	change_date = models.DateTimeField(auto_now_add=True, help_text="The last time this request was modified.")
	
	def __unicode__(self):
		return "Announcement by %s as %s on %s" % (self.incumbent, self.manager, self.post_date)
	
	class Meta:
		ordering = ['-post_date']
	
	def is_announcement(self):
		return True

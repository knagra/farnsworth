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
	duties = models.TextField(blank=True, null=True, help_text="The duties of this manager.")
	email = models.EmailField(blank=True, null=True, max_length=255, help_text="The e-mail address of this manager.")
	
	def __unicode__(self):
		return "%s" % self.title

class Request(models.Model):
	'''
	The Request model.  Contains an owner, body, post_date, change_date, and relevant
	manager.
	'''
	owner = models.ForeignKey(UserProfile, blank=False, null=False, help_text="The user who made this request.")
	body = models.TextField(blank=False, null=False, help_text="The body of this request.")
	post_date = models.DateTimeField(auto_now_add=True, help_text="The date this request was posted.")
	change_date = models.DateTimeField(auto_now_add=True, auto_now=True, help_text="The last time this request was modified.")
	request_type = models.CharField(max_length=255, blank=False, null=False, help_text="The type of request.")
	managers = models.ManyToManyField(Manager, help_text="Managers to whom this request was made.")
	filled = models.BooleanField(default=False, help_text="Whether the manager deems this request filled.")
	
	def __unicode__(self):
		return "%s request by %s on %s" % (self.request_type, self.owner, self.post_date)
	
	class Meta:
		ordering = ['-post_date']

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
		ordering = ['-post_date']

class ProfileRequest(models.Model):
	'''
	The ProfileRequest model.  A request to create a user account on the site.
	'''
	username = models.CharField(blank=False, null=True, max_length=100, help_text="Username if this user is created.")
	first_name = models.CharField(blank=False, null=False, max_length=100, help_text="First name if user is created.")
	last_name = models.CharField(blank=False, null=False, max_length=100, help_text="Last name if user is created.")
	email = models.CharField(blank=False, null=False, max_length=255, help_text="E-mail address if user is created.")
	approved = models.BooleanField(default=False, help_text="Change this to true to automatically create user.")
	request_date = models.DateTimeField(auto_now_add=True, help_text="Whether this request has been granted.")
	
	def __unicode__(self):
		return "Profile request for account '%s %s (%s)' on %s" % (self.first_name, self.last_name, self.username, self.request_date)

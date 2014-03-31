'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''

from django.db import models
from django.contrib.auth.models import User, Group, Permission
import unicodedata

class UserProfile(models.Model):
	'''
	The UserProfile model.  Tied to a unique User.  Contains current room number, former
	room numbers, and phone number.
	'''
	user = models.OneToOneField(User)
	current_room = models.CharField(blank=True, null=True, max_length=100, help_text="User's current room number")
	former_rooms = models.CharField(blank=True, null=True, max_length=100, help_text="List of User's former room numbers")
	phone_number = models.CharField(blank=True, null=True, max_length=20, help_text="User's phone number.")
	current_member = models.BooleanField(default=False, help_text="Whether this user is a current member.")
	
	def __unicode__(self):
		return "%s %s (Username: %s)" % (self.user.first_name, self.user.last_name, self.user.username)

class Thread(models.Model):
	'''
	The Thread model.  Used to group messages.
	'''
	owner = models.ForeignKey(UserProfile, help_text="The user who started this thread.")
	subject = models.CharField(blank=False, null=False, max_length=255, help_text="Subject of this thread.")
	start_date = models.DateTimeField(auto_now_add=True, help_text="The date this thread was started.")
	change_date = models.DateTimeField(auto_now_add=True, auto_now=True, help_text="The last time this thread was modified.")
	number_of_messages = models.PositiveSmallIntegerField(default=1, help_text="The number of messages in this thread.")
	active = models.BooleanField(default=True, help_text="Whether this thread is still active.")
	
	def __unicode__(self):
		return "%s by %s, started %s" % (self.subject, self.owner, self.start_date)
	
	class Meta:
		ordering = ['-change_date', '-start_date']

class Message(models.Model):
	'''
	The Message model.  Contains a body, owner, and post_date, referenced by thread.
	'''
	body = models.TextField(blank=False, null=False, help_text="Body of this message.")
	owner = models.ForeignKey(UserProfile, help_text="The user who posted this message.")
	post_date = models.DateTimeField(auto_now_add=True, help_text="The date this message was posted.")
	thread = models.ForeignKey(Thread, help_text="The thread to which this message belongs.")
	
	def __unicode__(self):
		return "Message by %s on thread %s, posted %s" % (self.owner, self.thread.subject, self.post_date)
	
	class Meta:
		ordering = ['-post_date']

def create_user_profile(sender, instance, created, **kwargs):
	'''
	Function to add a user profile for every User that is created.
	Parameters:
		instance is an of User that was just saved.
	'''
	if created:
		UserProfile.objects.create(user=instance)

# Connect signals with their respective functions from above.
# When a user is created, create a user profile associated with that user.
models.signals.post_save.connect(create_user_profile, sender=User)

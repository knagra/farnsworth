'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''

from django.db import models
from django.contrib.auth.models import User, Group, Permission, AbstractBaseUser
import unicodedata

class UserProfile(models.Model):
	'''
	The UserProfile model.  Tied to a unique User.  Contains current room number, former
	room numbers, and phone number.
	'''
	user = models.OneToOneField(User)
	current_room = models.CharField(blank=True, null=True, max_length=100, help_text="User's current room number")
	former_rooms = models.CharField(blank=True, null=True, max_length=100, help_text="List of user's former room numbers")
	former_houses = models.CharField(blank=True, null=True, max_length=100, help_text="List of user's former BSC houses")
	phone_number = models.CharField(blank=True, null=True, max_length=20, help_text="User's phone number")
	email_visible = models.BooleanField(default=False, help_text="Whether the email is visible in the directory")
	phone_visible = models.BooleanField(default=False, help_text="Whether the phone number is visible in the directory")
	RESIDENT = 'R'
	BOARDER = 'B'
	ALUMNUS = 'A'
	STATUS_CHOICES = (
		(RESIDENT, 'Current Resident'),
		(BOARDER, 'Current Boarder'),
		(ALUMNUS, 'Alumnus'),
	)
	status = models.CharField(max_length=1, choices=STATUS_CHOICES, default=RESIDENT, help_text="Member status (resident, boarder, alumnus)")
	
	def __unicode__(self):
		return "%s %s (Username: %s)" % (self.user.first_name, self.user.last_name, self.user.username)
""" Some work on implementing own user model.  Might be a bad idea.
class CustomUserManager(BaseUserManager):
	def create_user(self, email, first_name, last_name, password, is_staff=False, is_superuser=False, is_active=False):

class CustomUser(AbstractBaseUser):
	'''
	The CustomUser model.  Uses email as username, adds other fields to model.
	'''
	email = models.EmailField(max_length=254, blank=False, unique=True, help_text="User's e-mail.")
	first_name = models.CharField(max_length=30, blank=False, null=False, help_text="User's first name.")
	last_name = models.CharField(max_length=30, blank=False, null=False, help_text="User's last name.")
	current_room = models.CharField(blank=True, null=True, max_length=100, help_text="User's current room number.")
	former_rooms = models.CharField(blank=True, null=True, max_length=100, help_text="List of user's former room numbers.")
	other_houses = models.CharField(blank=True, null=True, max_length=100, help_text="List of user's other BSC house affiliations.")
	phone_number = models.CharField(blank=True, null=True, max_length=20, help_text="User's phone number.")
	email_visible = models.BooleanField(default=False, help_text="Whether the email is visible in the directory.")
	phone_visible = models.BooleanField(default=False, help_text="Whether the phone number is visible in the directory.")
	RESIDENT = 'R'
	BOARDER = 'B'
	ALUMNUS = 'A'
	STATUS_CHOICES = (
		(RESIDENT, 'Current Resident'),
		(BOARDER, 'Current Boarder'),
		(ALUMNUS, 'Alumnus'),
	)
	status = models.CharField(max_length=1, choices=STATUS_CHOICES, default=RESIDENT, help_text="Member status (resident, boarder, alumnus).")
	is_staff = models.BooleanField(default=False, help_text="Whether the user can access admin pages.")
	is_superuser = models.BooleanField(default=False, help_text="Whether user has all permissions.")
	is_active = models.BooleanField(default=False, help_text="Whether the user is active.  Turn this off rather than delete the user.")
	
	USERNAME_FIELD = 'email'
	REQUIRED_FIELDS = ['first_name', 'last_name', 'status']
	
	def __unicode__(self):
		return "%s %s (Username: %s)" % (self.user.first_name, self.user.last_name, self.user.username)
"""
class Thread(models.Model):
	'''
	The Thread model.  Used to group messages.
	'''
	owner = models.ForeignKey(UserProfile, help_text="The user who started this thread.")
	subject = models.CharField(blank=False, null=False, max_length=254, help_text="Subject of this thread.")
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

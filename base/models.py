'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''

from django.conf import settings
from django.db import models
from django.contrib.auth.models import User, Group, Permission

from social.utils import setting_name

UID_LENGTH = getattr(settings, setting_name('UID_LENGTH'), 255)

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
		return self.user.get_full_name()
	
	def is_userprofile(self):
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
	password = models.CharField(blank=True, max_length=255, help_text="User's password.  Stored as hash")
	provider = models.CharField(blank=True, max_length=32)
	uid = models.CharField(blank=True, max_length=UID_LENGTH)

	def __unicode__(self):
		return "Profile request for account '%s %s (%s)' on %s" % (self.first_name, self.last_name, self.username, self.request_date)

	def is_profilerequest(self):
		return True

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

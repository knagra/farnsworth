'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''

from django.conf import settings
from django.contrib.auth.models import User, Group, Permission
from django.core.urlresolvers import reverse
from django.db import models

from phonenumber_field.modelfields import PhoneNumberField

from social.utils import setting_name

UID_LENGTH = getattr(settings, setting_name('UID_LENGTH'), 255)

def _get_user_view_url(user):
    return reverse("member_profile", kwargs={"targetUsername": user.username})

User.get_view_url = _get_user_view_url

class UserProfile(models.Model):
    '''
    The UserProfile model.  Tied to a unique User.  Contains e-mail settings
    and phone number.
    '''
    user = models.OneToOneField(User)
    former_houses = models.CharField(
        blank=True,
        null=True,
        max_length=100,
        help_text="List of user's former BSC houses",
        )
    phone_number = PhoneNumberField(
        null=True,
        blank=True,
        default='',
        help_text="This should be of the form +1 (xxx) xxx-xxx",
        )
    email_visible = models.BooleanField(
        default=False,
        help_text="Whether the email is visible in the directory",
        )
    phone_visible = models.BooleanField(
        default=False,
        help_text="Whether the phone number is visible in the directory",
        )
    RESIDENT = 'R'
    BOARDER = 'B'
    ALUMNUS = 'A'
    STATUS_CHOICES = (
        (RESIDENT, 'Current Resident'),
        (BOARDER, 'Current Boarder'),
        (ALUMNUS, 'Alumna/Alumnus'),
    )
    status = models.CharField(
        max_length=1,
        choices=STATUS_CHOICES,
        default=RESIDENT,
        help_text="Member status (resident, boarder, alumnus)",
        )
    email_announcement_notifications = models.BooleanField(
        default=True,
        help_text="Whether important manager announcements are e-mailed to you.",
        )
    email_request_notifications = models.BooleanField(
        default=False,
        help_text="Whether notifications are e-mailed to you about request updates.",
        )
    email_thread_notifications = models.BooleanField(
        default=False,
        help_text="Whether notifications are e-mailed to you about thread updates.",
        )
    email_workshift_notifications = models.BooleanField(
        default=True,
        help_text="Whether notifications are e-mailed to you about workshift updates.",
        )

    def __unicode__(self):
        return self.user.get_full_name()

    def get_email(self):
        return self.user.email

    def get_info(self):
        return "{0.first_name} {0.last_name}".format(self.user)

    def get_first(self):
        return self.user.first_name

    def get_last(self):
        return self.user.last_name

    def get_user(self):
        return self.user.username

    def get_full(self):
        return self.get_info()

    def is_userprofile(self):
        return True

class ProfileRequest(models.Model):
    '''
    The ProfileRequest model.  A request to create a user account on the site.
    '''
    username = models.CharField(
        blank=False,
        null=True,
        max_length=100,
        help_text="Username if this user is created.",
        )
    first_name = models.CharField(
        blank=False,
        null=False,
        max_length=100,
        help_text="First name if user is created.",
        )
    last_name = models.CharField(
        blank=False,
        null=False,
        max_length=100,
        help_text="Last name if user is created.",
        )
    email = models.CharField(
        blank=False,
        null=False,
        max_length=255,
        help_text="E-mail address if user is created.",
        )
    request_date = models.DateTimeField(
        auto_now_add=True,
        help_text="Whether this request has been granted.",
        )
    affiliation = models.CharField(
        max_length=1,
        choices=UserProfile.STATUS_CHOICES,
        default=UserProfile.RESIDENT,
        help_text="User's affiliation with the house.",
        )
    password = models.CharField(
        blank=True,
        max_length=255,
        help_text="User's password.  Stored as hash",
        )
    provider = models.CharField(
        blank=True,
        max_length=32,
        )
    uid = models.CharField(
        blank=True,
        max_length=UID_LENGTH,
        )
    message = models.CharField(
        blank=True,
        max_length=255,
        default="",
        help_text="Details on how you're affiliated with us.  Optional.",
        )

    def __unicode__(self):
        return "Profile request for account '{0.first_name} {0.last_name} ({0.username})' on {0.request_date}".format(self)

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

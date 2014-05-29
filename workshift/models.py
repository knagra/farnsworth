'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''

from django.db import models
from django.contrib.auth.models import User

from farnsworth.settings import DEFAULT_SEMESTER_HOURS, DEFAULT_CUTOFF, DEFAULT_WORKSHIFT_HOURS
from base.models import UserProfile
from managers.models import Manager
from workshift.fields import DayField

class Semester(models.Model):
	'''
	A semester instance, used to hold records, settings, and to separate workshifts into contained units.
	'''
	SPRING = 0
	SUMMER = 1
	FALL = 2
	SEASON_CHOICES = (
		(SPRING, 'Spring'),
		(SUMMER, 'Summer'),
		(FALL, 'Fall')
		)
	season = models.PositiveSmallIntegerField(
		max_length=1,
		choices=SEASON_CHOICES,
		default=SPRING,
		help_text="Season of the year (spring, summer, fall) of this semester.",
		)
	year = models.PositiveSmallIntegerField(
		max_length=4,
		help_text="Year of this semester.",
		)
	workshift_managers = models.ManyToManyField(
		User,
		null=True,
		blank=True,
		help_text="The users who were/are Workshift Managers for this semester.",
		)
	rate = models.DecimalField(
		null=True,
		blank=True,
		help_text="Workshift rate for this semester.",
		)
	policy = models.URLField(
		max_length=255,
		null=True,
		blank=True,
		help_text="Link to the workshift policy for this semester.",
		)
	start_date = models.DateField(
		help_text="Start date of this semester.",
		)
	end_date = models.DateField(
		help_text="End date of this semester.",
		)
	first_fine_date = models.DateField(
		null=True,
		blank=True,
		help_text="First fine date for this semester, optional.",
		)
	second_fine_date = models.DateField(
		null=True,
		blank=True,
		help_text="Second fine date for this semester, optional.",
		)
	third_fine_date = models.DateField(
		null=True,
		blank=True,
		help_text="Third fine date for this semester, optional.",
		)
	preferences_open = models.BooleanField(
		default=False,
		help_text="Whether members can enter their workshift preferences",
		)

	class Meta:
		unique_together = ("season", "year")

	def __unicode__(self):
		return "%s %s" % (self.get_season_display, self.year)

class WorkshiftPool(models.Model):
	title = models.CharField(
		max_length=100,
		default="Regular Workshift",
		help_text="The title of this workshift pool (i.e. HI Hours)",
		)
	semester = models.ForeignKey(
		Semester,
		help_text="The semester associated with this pool of workshift hours.",
		)
	managers = models.ManyToManyField(
		Manager,
		help_text="Managers who are able to control this workshift category."
		)
	sign_out_cutoff = models.PositiveSmallIntegerField(
		default=DEFAULT_CUTOFF,
		help_text="Cut-off for signing out of workshifts without requiring "
		"a substitute, in hours.",
		)
	hours = models.DecimalField(
		max_length=2,
		default=DEFAULT_SEMESTER_HOURS,
		help_text="Default regular workshift hours required per week.",
		)
	hours = models.PositiveSmallIntegerField(
		default=DEFAULT_SEMESTER_HOURS,
		help_text="Hours required, either recurring or semesterly."
		)
	weeks_per_period = models.PositiveSmallIntegerField(
		default=1,
		help_text="Number of weeks for each pass of required hours. "
		"0 makes this a semesterly requirement",
		)

	class Meta:
		unique_together = ("semester", "title")

	def __unicode__(self):
		return "{0}"

class WorkshiftType(models.Model):
	'''
	A workshift type; for example, a "Pots" workshift type.
	'''
	title = models.CharField(blank=False, null=False, unique=True, max_length=255,
		help_text='The title of this workshift type (e.g., "Pots"), must be unique.')
	description = models.TextField(blank=True, null=True, help_text="A description for this workshift type.")
	quick_tips = models.TextField(blank=True, null=True, help_text="Quick tips to the workshifter.")
	hours = models.DecimalField(default=1, help_text="Default hours for these types of shifts, helpful for pre-filling workshifts.")
	rateable = models.BooleanField(default=True, help_text="Whether this workshift type is shown in preferences.")

	def __unicode__(self):
		return self.name

class TimeBlock(models.Model):
	'''
	A time block to represent member availability during a particular day.
	Used to reduce database size by creating references to existing time blocks for users.
	These objects should never be directly created on their own.  They be created and retrieved for use.
	'''
	BUSY = 0
	FREE = 1
	PREFERRED = 2
	PREFERENCE_CHOICES = (
		(BUSY, "Busy"),
		(FREE, "Free"),
		(PREFERRED, "Preferred"),
		)
	preference = models.PositiveSmallIntegerField(max_length=1, choices=PREFERENCE_CHOICES, default=FREE, help_text="The user's preference for this time block.")
	day = DayField(help_text="Day of the week for this time block.")
	start_time = models.TimeField(help_text="Start time for this time block.")
	end_time = models.TimeField(help_text="End time for this time block.")

class WorkshiftRating(models.Model):
	'''
	A preference for a workshift type.  Used to reduce database size by creating references to existing ratings for users.
	These objects should never be directly created on their own.  They be created and retrieved for use.
	'''
	DISLIKE = 0
	INDIFFERENT = 1
	LIKE = 2
	RATING_CHOICES = (
		(DISLIKE, "Dislike"),
		(INDIFFERENT, "Indifferent"),
		(LIKE, "Like")
		)
	rating = models.PositiveSmallIntegerField(max_length=1, choices=RATING_CHOICES, help_text="Rating for the workshift type.")
	workshift_type = models.ForeignKey(WorkshiftType, help_text="The workshift type being rated.")

class WorkshiftProfile(models.Model):
	''' A workshift profile for a user for a given semester. '''
	user = models.ForeignKey(User, help_text="The user for this workshift profile.")
	semester = models.ForeignKey(Semester, help_text="The semester for this workshift profile.")
	time_blocks = models.ManyToManyField(TimeBlock, null=True, blank=True, help_text="The time blocks for this workshift profile.")
	ratings = models.ManyToManyField(WorkshiftRating, null=True, blank=True, help_text="The workshift ratings for this workshift profile.")
	hours = models.DecimalField(max_length=2, default=DEFAULT_SEMESTER_HOURS, help_text="Number of weekly hours required for this profile.")
	standing = models.DecimalField(default=0, help_text="Current hours standing for this workshift profile.")
	hour_adjustment = models.DecimalField(default=0, help_text="Manual hour adjustment for this workshift profile.")
	note = models.TextField(null=True, blank=True, help_text="Note for this profile. For communication between the workshifter and the workshift manager(s).")
	first_date_fine = models.DecimalField(null=True, blank=True, default=0,
		help_text="The fines or repayment for this profile at the first fine date. Stored in a field for manual adjustment.")
	second_date_fine = models.DecimalField(null=True, blank=True, default=0,
		help_text="The fines or repayment for this profile at the second fine date. Stored in a field for manual adjustment.")
	third_date_fine = models.DecimalField(null=True, blank=True, default=0,
		help_text="The fines or repayment for this profile at the third fine date. Stored in a field for manual adjustment.")

	def __unicode__(self):
		return "%s, %s" % (self.user.get_full_name(), self.semester)

class RegularWorkshift(models.Model):
	''' A weekly workshift for a semester.  Used to generate individual instances of workshifts. '''
	workshift_type = models.ForeignKey(WorkshiftType, help_text="The workshift type for this weekly workshift.")
	title = models.CharField(max_length=255, help_text="The title for this weekly workshift.")
	day = DayField(help_text="The day of the week when this workshift takes place.")
	hours = models.DecimalField(max_length=2, default=DEFAULT_WORKSHIFT_HOURS, help_text="Number of hours for this shift.")
	active = models.BooleanField(default=True,
		help_text="Whether this shift is actively being used currently (displayed in list of shifts, given hours, etc.).")
	current_assignee = models.ForeignKey(WorkshiftProfile, null=True, blank=True,
		help_text="The workshifter currently assigned to this weekly workshift.")
	start_time = models.TimeField(help_text="Start time for this workshift.")
	end_time = models.TimeField(help_text="End time for this workshift.")
	addendum = models.TextField(help_text="Addendum to the description for this workshift.")

	def __unicode__(self):
		return "%s, %s" % (self.title, self.get_day_display)

class AssignmentEntry(models.Model):
	''' Entries for sign-ins, sign-outs, and verification. '''
	person = models.ForeignKey(
		WorkshiftProfile,
		help_text="Relevant person.",
		)
	entry_time = models.DateTimeField(
		auto_now_add=True,
		help_text="Time this entry was made."
		)
	SIGNIN = 'I'
	SIGNOUT = 'O'
	VERIFY = 'V'
	ENTRY_CHOICES = (
		(SIGNIN, 'Sign In'),
		(SIGNOUT, 'Sign Out'),
		(VERIFY, 'Verify'),
	)
	entry_type = models.CharField(
		max_length=1,
		choices=ENTRY_CHOICES,
		default=VERIFY,
		)

	def __unicode__(self):
		return "<{0}, {1}, {2}>".format(
			self.instance,
			self.person,
			self.entry_type,
			)

class WorkshiftInstance(models.Model):
	''' An instance of a weekly workshift. '''
	weekly_workshift = models.ForeignKey(
		RegularWorkshift,
		help_text="The weekly workshift of which this is an instance.",
		)
	pool = models.ForeignKey(
		WorkshiftPool,
		help_text="The workshift pool for this instance.",
		)
	date = models.DateField(
		help_text="Date of this workshift.",
		)
	workshifter = models.ForeignKey(
		WorkshiftProfile,
		null=True,
		blank=True,
		related_name="workshifter",
		help_text="Workshifter who was signed into this shift at the time "
		"it started.",
		)
	closed = models.BooleanField(
		default=False,
		help_text="If this shift has been completed.",
		)
	blown = models.BooleanField(
		default=False,
		help_text="If this shift has been blown.",
		)
	assignment_entries = models.ManyToManyField(
		AssignmentEntry,
		null=True,
		blank=True,
		help_text="The entries for sign ins, sign outs, and verification.",
		)

	def __unicode__(self):
		return "%s, %s" % (self.weekly_workshift.title, self.date)

class OneTimeWorkshift(models.Model):
	''' A one-time workshift. '''
	title = models.CharField(
		max_length=255,
		help_text="Title for this shift.",
		)
	description = models.TextField(
		null=True,
		blank=True,
		help_text="Description of the shift.",
		)
	date = models.DateField(
		help_text="Date of this workshift.",
		)
	hours = models.DecimalField(
		default=DEFAULT_WORKSHIFT_HOURS,
		help_text="Hours given for this shift.",
		)
	workshifter = models.ForeignKey(
		WorkshiftProfile,
		null=True,
		blank=True,
		related_name="workshifter",
		help_text="Workshifter who was signed into this shift at the time "
		"it started.",
		)
	closed = models.BooleanField(
		default=False,
		help_text="If this shift has been completed.",
		)
	blown = models.BooleanField(
		default=False,
		help_text="If this shift has been blown.",
		)
	assignment_entries = models.ManyToManyField(
		AssignmentEntry,
		null=True,
		blank=True,
		help_text="The entries for sign ins, sign outs, and verification.",
		)

	def __unicode__(self):
		return "%s, %s" % (self.title, self.date)

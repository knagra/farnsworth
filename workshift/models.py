'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''

from django.db import models
from django.contrib.auth.models import User

from threads.models import UserProfile
	
class Semester(models.Model):
	'''
	A semester instance, used to hold records, settings, and to separate workshifts into contained units.
	'''
	SPRING = 'P'
	SUMMER = 'U'
	FALL = 'F'
	SEASON_CHOICES = (
		(SPRING, 'Spring'),
		(SUMMER, 'Summer'),
		(FALL, 'Fall')
		)
	season = models.Charfield(max_length=1, default=SPRING, help_text="Season of the year (spring, summer, fall) of this semester.")
	year = models.PositiveSmallIntegerField(max_length=4, help_text="Year of this semester.")
	workshift_managers = models.ManyToManyField(User, null=True, blank=True, help_text="The users who were/are Workshift Managers for this semester.")
	required_hours = models.PositiveSmallIntegerField(max_length=1, default=5, help_text="Default regular workshift hours required per week.")
	rate = models.DecimalField(null=True, blank=True, help_text="Workshift rate for this semester.")
	start_date = models.DateField(help_text="Start date of this semester.")
	end_date = models.DateField(help_text="End date of this semester.")
	first_fine_date = models.DateField(null=True, blank=True, help_text="First fine date for this semester, optional.")
	second_fine_date = models.DateField(null=True, blank=True, help_text="Second fine date for this semester, optional.")
	third_fine_date = models.DateField(null=True, blank=True, help_text="Third fine date for this semester, optional.")
	
	class Meta:
		unique_together = ("season", "year")
		
	def __unicode__(self):
		return self.get_season_display + ' ' + str(self.year)

class WorkshiftType(models.Model):
	'''
	A workshift type; for example, a "Pots" workshift type.
	'''
	name = models.CharField(blank=False, null=False, unique=True, max_length=255, help_text='The name of this workshift type (e.g., "Pots"), must be unique.')
	description = models.TextField(blank=True, null=True, help_text="A description for this workshift type.")
	quick_tips = models.TextField(blank=True, null=True, help_text="Quick tips to the workshifter.")
	hours = models.PositiveSmallIntegerField(default=1, help_text="Default hours for these types of shifts, helpful for pre-filling workshifts.")
	rateable = models.BooleanField(default=True, help_text="Whether this workshift type is shown in preferences.")
	
	def __unicode__(self):
		return self.name
	
	def __unicode__(self):
		return self.name

WorkshiftProfile (user foreign key, Semester, timeblocks, workshift ratings, weekly hours required [pre-fill], standing, hour adjustment, manager note,
		list of tuples of form (fine date, standing))
	e.g., "Karandeep Nagra, Summer 2014, <list of time blocks>, 5, up 5 hours, -2 hours adjusted, 'gone for a few days in the semester',
		[(30 July 2014, +250 hours), (15 August 2014, +500 hours)])"

WeeklyWorkshift (WorkshiftType foreign key, title [pre-fill], day-of-week, hours [pre-fill], active boolean [pre-fill], current_assignee (workshift profile),
		start_time, end_time, description addendum)
	e.g., "Pots, Afternoon Pots, Saturday, 1 hour, active, Karandeep Nagra"

WeeklyWorkShiftInstance (WeeklyWorkshift, semester, date, workshifter [workshift profile], verifier [workshift profile], completed boolean)

SemesterlyWorkshift (WorkshiftType [optional], description/addendum, number required per semester, title, hours, active)

SemesteryWorkshiftInstance (SemesterlyWorkshift, semester, start_time, end_time, assignee [workshift profile])

OneTimeWorkshift (description, assignee [workshift profile], hours, datetime)

class RegularWorkshift(models.Model):
	'''
	A regular, weekly recurring workshift.
	'''
	workshift_type = models.ForeignKey(WorkshiftType, help_text="The workshift type of this workshift.")
	hours = models.SmallPositiveIntegerField(blank=True, null=True, help_text="The number of hours this shift is worth.")
	auto_assign = models.BooleanField(default=False, help_text="Whether assignment for this shift is handled by the computer.")

class ManagerWorkshift(models.Model):
	'''
	A manager workshift.  Used to make transitioning from semester to semester more concise.  Doesn't require a WorkshiftType.
	'''
	manager = models.ForeignKey(Manager, help_text="The manager that gets this workshift")
	semester_hours = models.SmallIntegerField(blank=True, null=True, help_text="The number of hours this position is comped regular semesters.")
	summer_hours = models.SmallIntegerField(blank=True, null=True, help_text="The number of hours this position is comped during summer.")

class OneTimeWorkshift(models.Model):
	'''
	A one-time workshift; for example, one time bathroom shifts, hallway shifts.
	'''
	workshift_type = models.ForeignKey(WorkshiftType, help_text="The workshift type of this workshift.")

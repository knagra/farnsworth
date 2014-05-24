'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''

from django.db import models

from threads.models import UserProfile
from managers.models import Manager
from workshift.fields import MultipleDatesField

Semester ("Summer" | "Fall" | "Spring", Year, Workshift Managers [manytomany user], default required hours, workshift rate, start date, end date,
		fine dates)
	Unique together: "Fall" etc. & Year
	e.g., "Summer, 2014, So-and-So workshift manager, 5 hours per week standard, 13.30"
	
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
	fine_dates = MultipleDatesField(help_text="Fine dates for this semester.")
	
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
	
	def __unicode__(self):
		return self.name	

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

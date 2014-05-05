'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''

from django.db import models
from threads.models import UserProfile
from requests.models import Manager

class WorkshiftType(models.Model):
	'''
	A workshift type; for example, a "Pots" workshift type.
	'''
	name = models.CharField(blank=False, null=False, unique=True, max_length=255, help_text='The name of this workshift type (e.g., "Pots"), must be unique')
	description = models.TextField(blank=True, null=True, help_text="A description for this workshift")
	quick_tips = models.TextField(blank=True, null=True, help_text="Quick tips to the workshifter")
	
	def __unicode__(self):
		return self.name	

class RegularWorkshift(models.Model):
	'''
	A regular, weekly recurring workshift.
	'''
	workshift_type = models.ForeignKey(WorkshiftType, help_text="The workshift type of this workshift")
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
	

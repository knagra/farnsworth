'''
Project: Farnsworth

Author: Karandeep Singh Nagra

Custom fields for workshift models.
'''

from __future__ import absolute_import

from django.db import models

from weekday_field.utils import DAY_CHOICES

class DayField(models.PositiveSmallIntegerField):
	'''
	Field to represent a day of the week.
	Extends PositiveSmallIntegerField.
	'''
	def __init__(self, *args, **kwargs):
		kwargs['choices'] = DAY_CHOICES
		kwargs['max_length'] = 1
		super(DayField, self).__init__(*args, **kwargs)

'''
Project: Farnsworth

Author: Karandeep Singh Nagra

Custom fields for workshift models.
'''

import datetime
from ast import literal_eval

from django.db import models

class MultipleDatesField(models.fields.CommaSeparatedIntegerField):
	'''
	The year field.  Extends CommaSeparatedIntegerField.
	Dates are stored as integers separated by commas, with the integers representing days since 1 January 2000.
	Dates are converted by subtracting/adding 1 January 2000 from/to the date each integer represents.
	'''
	__metaclass__ = models.SubfieldBase
	
	def to_python(self, value):
		'''
		Convert the database representation (integers separated by commas) to a python object (list of Python dates)
		'''
		if not value:
			return None
		elif isinstance(value, basestring):
			int_list = literal_eval(value)
			date_list = list()
			for val in int_list:
				date_list.append(datetime.date(2000, 1, 1) + datetime.timedelta(days=val))
			return date_list
		elif all(isinstance(n, int) for n in value):
			date_list = list()
			for val in value:
				date_list.append(datetime.date(2000, 1, 1) + datetime.timedelta(days=val))
			return date_list
	
	def __init__(self, *args, **kwargs):
		self.max_leng

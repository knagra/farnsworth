'''
Project: Farnsworth

Author: Karandeep Singh Nagra

Custom fields for workshift models.
'''

from django.db import models
from utils.variables import DAYS

class DayField(models.PositiveSmallIntegerField):
	'''
	Field to represent a day of the week.
	Extends PositiveSmallIntegerField.
	'''
    def __init__(self, *args, **kwargs):
        kwargs['choices'] = DAYS
        kwargs['max_length'] = 1 
        super(DayOfTheWeekField,self).__init__(*args, **kwargs)

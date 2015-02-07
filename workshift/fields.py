'''
Project: Farnsworth

Author: Karandeep Singh Nagra

Custom fields for workshift models.
'''

from __future__ import absolute_import, unicode_literals

from django.db import models

from django_select2 import AutoModelSelect2MultipleField

DAY_CHOICES = [
    (0, "Monday"),
    (1, "Tuesday"),
    (2, "Wednesday"),
    (3, "Thursday"),
    (4, "Friday"),
    (5, "Saturday"),
    (6, "Sunday"),
]

class DayField(models.PositiveSmallIntegerField):
    '''
    Field to represent a day of the week.
    Extends PositiveSmallIntegerField.
    '''
    def __init__(self, *args, **kwargs):
        kwargs['choices'] = DAY_CHOICES
        kwargs['max_length'] = 1
        super(DayField, self).__init__(*args, **kwargs)

"""
Project: Farnsworth

Author: Karandeep Singh Nagra

Legacy Kingman site admin pages.
"""


from django.contrib import admin

from legacy.models import TeacherRequest, TeacherResponse, TeacherNote, \
    TeacherEvent


for p in [TeacherRequest, TeacherResponse, TeacherNote, TeacherEvent]:
    admin.site.register(p)

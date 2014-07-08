"""
Project: Farnsworth

Authors: Karandeep Singh Nagra and Nader Morshed


Registrations for models for the Django admin pages.
"""

from django.contrib import admin
from workshift.models import Semester, WorkshiftPool, WorkshiftType, \
    TimeBlock, WorkshiftRating, PoolHours, WorkshiftProfile, \
    RegularWorkshift, ShiftLogEntry, InstanceInfo, WorkshiftInstance

class SemesterAdmin(admin.ModelAdmin):
    list_display = ('season', 'year', 'start_date', 'end_date')
    search_fields = ('season', 'year', 'rate', 'start_date', 'end_date')
    list_filter = ('season', 'year', 'rate')
    ordering = ('-year',)
admin.site.register(Semester, SemesterAdmin)

class WorkshiftPoolAdmin(admin.ModelAdmin):
    list_display = ('title', 'semester', 'hours', 'is_primary')
    search_fields = ('title', 'semester', 'hours')
    list_filter = ('title', 'hours')
    ordering = ('title',)
admin.site.register(WorkshiftPool, WorkshiftPoolAdmin)

class WorkshiftTypeAdmin(admin.ModelAdmin):
    list_display = ('title', 'hours', 'rateable')
    search_fields = ('title', 'hours',)
    list_filter = ('title', 'hours', 'rateable')
    ordering = ('title',)
admin.site.register(WorkshiftType, WorkshiftTypeAdmin)

class TimeBlockAdmin(admin.ModelAdmin):
    list_display = ('preference', 'day', 'start_time', 'end_time')
    search_fields = ('preference', 'day', 'start_time', 'end_time')
    list_filter = ('preference', 'day')
    ordering = ('day',)
admin.site.register(TimeBlock, TimeBlockAdmin)

class WorkshiftRatingAdmin(admin.ModelAdmin):
    list_display = ('rating', 'workshift_type')
    search_fields = ('rating', 'workshift_type')
    list_filter = ('rating', 'workshift_type')
    ordering = ('rating',)
admin.site.register(WorkshiftRating, WorkshiftRatingAdmin)

class PoolHoursAdmin(admin.ModelAdmin):
    list_display = ('pool', 'hours', 'standing')
    search_fields = ('pool', 'hours', 'standing')
    list_filter = ('pool', 'hours',)
    ordering = ('pool',)
admin.site.register(PoolHours, PoolHoursAdmin)

class WorkshiftProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'semester',)
    search_fields = ('user', 'semester',)
    list_filter = ('user', 'semester')
    ordering = ('semester', 'user')
admin.site.register(WorkshiftProfile, WorkshiftProfileAdmin)

class RegularWorkshiftAdmin(admin.ModelAdmin):
    list_display = ('workshift_type', 'pool', 'title', 'active',)
    search_fields = ('workshift_type', 'pool', 'title', 'hours', 'start_time', 'end_time', 'addendum')
    list_filter = ('workshift_type', 'title')
    ordering = ('workshift_type', 'title')
admin.site.register(RegularWorkshift, RegularWorkshiftAdmin)

class InstanceInfoAdmin(admin.ModelAdmin):
    list_display = ('title', 'pool',)
    search_fields = ('title', 'description', 'pool', 'start_time', 'end_time')
    list_filter = ('title', 'pool')
    ordering = ('title',)
admin.site.register(InstanceInfo, InstanceInfoAdmin)

class WorkshiftInstanceAdmin(admin.ModelAdmin):
    list_display = ('semester', 'date', 'workshifter')
    search_fields = ('semester', 'date', 'workshifter', 'verifier')
    list_filter = ('semester',)
    ordering = ('date', 'workshifter')
admin.site.register(WorkshiftInstance, WorkshiftInstanceAdmin)

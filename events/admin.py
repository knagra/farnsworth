'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''

from django.contrib import admin
from events.models import Event

class EventAdmin(admin.ModelAdmin):
	list_display = ('owner', 'title', 'date_time', 'post_date')
	search_fields = ('title', 'owner', 'description', 'date_time', 'post_date')
	list_filter = ('owner', 'title', 'date_time', 'post_date')
	date_hierarchy = 'date_time'
	ordering = ('-date_time',)
	readonly_fields = ('owner', 'title', 'description', 'date_time', 'post_date',)

admin.site.register(Event, EventAdmin)

'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''

from django.contrib import admin
from threads.models import UserProfile, Thread, Message

admin.site.register(UserProfile)

class ThreadAdmin(admin.ModelAdmin):
	list_display = ('subject', 'owner', 'start_date', 'change_date', 'active')
	search_fields = ('subect', 'owner')
	list_filter = ('start_date', 'change_date', 'active', 'owner')
	date_hierarchy = 'start_date'
	ordering = ('-start_date',)
	readonly_fields = ('subject', 'owner', 'start_date', 'number_of_messages', 'change_date',)

class MessageAdmin(admin.ModelAdmin):
	list_display = ('thread', 'owner', 'post_date')
	search_fields = ('thread', 'owner', 'body')
	list_filter = ('post_date', 'thread', 'owner')
	date_hierarchy = 'post_date'
	ordering = ('-post_date',)
	readonly_fields = ('body', 'owner', 'post_date', 'thread',)

admin.site.register(Thread, ThreadAdmin)
admin.site.register(Message, ServerAdmin)

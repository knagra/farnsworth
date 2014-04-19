'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''

from django.contrib import admin
from threads.models import UserProfile, Thread, Message

class UserProfileAdmin(admin.ModelAdmin):
	list_display = ('user', 'get_info', 'status', 'get_email', 'phone_number', 'current_room')
	search_fields = ('get_last', 'get_first', 'get_user', 'get_email', 'phone_number', 'current_room')
	list_filter = ('status', 'current_room')
	ordering = ('-status', )
	
	def get_email(self, obj):
		return obj.user.email
	
	def get_info(self, obj):
		return "%s %s" % (obj.user.first_name, obj.user.last_name)
	
	def get_first(self, obj):
		return obj.user.first_name
	
	def get_last(self, obj):
		return obj.user.last_name
	
	def get_user(self, obj):
		return obj.user.username
	
	get_email.short_description = 'E-mail'
	get_info.short_description = 'First Last'
	get_first.short_description = 'First name'
	get_last.short_description = 'Last name'
	get_user.short_description = 'Username'

class ThreadAdmin(admin.ModelAdmin):
	list_display = ('subject', 'owner', 'start_date', 'change_date', 'active')
	search_fields = ('subect', 'owner')
	list_filter = ('start_date', 'change_date', 'active', 'owner')
	date_hierarchy = 'start_date'
	ordering = ('-start_date',)
	readonly_fields = ('subject', 'owner', 'start_date', 'change_date',)

class MessageAdmin(admin.ModelAdmin):
	list_display = ('thread', 'owner', 'post_date')
	search_fields = ('thread', 'owner', 'body')
	list_filter = ('post_date', 'thread', 'owner')
	date_hierarchy = 'post_date'
	ordering = ('-post_date',)
	readonly_fields = ('body', 'owner', 'post_date', 'thread',)

admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Thread, ThreadAdmin)
admin.site.register(Message, MessageAdmin)

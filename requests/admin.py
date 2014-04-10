'''
Project: Farnswroth

Author: Karandeep Singh Nagra
'''

from django.contrib import admin
from requests.models import Manager, Request, Response, ProfileRequest

class ManagerAdmin(admin.ModelAdmin):
	list_display = ('title', 'incumbent', 'email')
	search_fields = ('title', 'incumbent', 'email', 'duties')
	list_filter = ('email',)

class RequestAdmin(admin.ModelAdmin):
	list_display = ('owner', 'post_date', 'filled')
	search_fields = ('owner', 'body', 'post_date', 'change_date')
	list_filter = ('post_date', 'change_date', 'filled', 'owner')
	date_hierarchy = 'post_date'
	ordering = ('-post_date',)
	readonly_fields = ('owner', 'post_date', 'body')

class ResponseAdmin(admin.ModelAdmin):
	list_display = ('owner', 'post_date', 'request')
	search_fields = ('owner', 'body', 'request')
	list_filter = ('post_date', 'request', 'owner')
	date_hierarchy = 'post_date'
	ordering = ('-post_date',)
	readonly_fields = ('body', 'owner', 'post_date', 'request')

class ProfileRequestAdmin(admin.ModelAdmin):
	list_display = ('username', 'last_name', 'first_name', 'email')
	search_fields = ('username', 'last_name', 'first_name', 'email')
	date_hierarchy = 'request_date'
	list_filter = ('approved',)
	ordering = ('-approved',)
	readonly_fields = ('username', 'last_name', 'first_name', 'email')

admin.site.register(Manager, ManagerAdmin)
admin.site.register(Request, RequestAdmin)
admin.site.register(Response, ResponseAdmin)
admin.site.register(ProfileRequest, ProfileRequestAdmin)

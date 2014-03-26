'''
Project: Farnswroth

Author: Karandeep Singh Nagra
'''

from django.contrib import admin
from requests.models import Manager, Request, Response

class ManagerAdmin(admin.ModelAdmin):
	list_display = ('title', 'incumbent', 'email')
	search_fields = ('title', 'incumbent', 'email', 'duties')
	list_filter = ('email',)

class RequestAdmin(admin.ModelAdmin):
	list_display = ('owner', 'post_date', 'manager', 'filled')
	search_fields = ('owner', 'body', 'post_date', 'change_date', 'manager')
	list_filter = ('post_date', 'change_date', 'filled', 'manager', 'owner')
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

admin.site.register(Manager, ManagerAdmin)
admin.site.register(Request, RequestAdmin)
admin.site.register(Response, ResponseAdmin)

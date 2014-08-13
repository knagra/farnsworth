'''
Project: Farnswroth

Author: Karandeep Singh Nagra
'''

from django.contrib import admin
from managers.models import Manager, RequestType, Request, Response, Announcement

class ManagerAdmin(admin.ModelAdmin):
    list_display = ('title', 'incumbent', 'email')
    search_fields = ('title', 'incumbent', 'email', 'duties')
    list_filter = ('email',)
admin.site.register(Manager, ManagerAdmin)

class RequestTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'enabled')
    search_fields = ('name', 'managers')
    list_filter = ('name', 'managers')
admin.site.register(RequestType, RequestTypeAdmin)

class RequestAdmin(admin.ModelAdmin):
    list_display = ('owner', 'post_date', 'status')
    search_fields = ('owner', 'body', 'post_date', 'change_date', 'status')
    list_filter = ('status',)
    date_hierarchy = 'post_date'
    ordering = ('-post_date',)
    readonly_fields = ('post_date', 'change_date')
admin.site.register(Request, RequestAdmin)

class ResponseAdmin(admin.ModelAdmin):
    list_display = ('owner', 'post_date', 'request', 'action')
    search_fields = ('owner', 'body', 'request', 'action')
    list_filter = ('action',)
    date_hierarchy = 'post_date'
    ordering = ('-post_date',)
    readonly_fields = ('post_date',)
admin.site.register(Response, ResponseAdmin)

class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('manager', 'incumbent', 'post_date', 'pinned')
    search_fields = ('manager', 'incumbent', 'body')
    date_hierarchy = 'post_date'
    list_filter = ('pinned',)
    ordering = ('-post_date', 'pinned')
    readonly_fields = ('manager', 'incumbent', 'post_date', 'body')
admin.site.register(Announcement, AnnouncementAdmin)

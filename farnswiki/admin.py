'''
Project: Farnsworth

Authors: Karandeep Singh Nagra and Nader Morshed

XXX:
This module is deprecated and marked for replacement.
'''

from django.contrib import admin

from wiki.models import Page, Revision

class PageAdmin(admin.ModelAdmin):
    list_display = ('slug',)
    search_fields = ('slug',)
    list_filter = ('slug',)
    ordering = ('slug',)

admin.site.register(Page, PageAdmin)

class RevisionAdmin(admin.ModelAdmin):
    list_display = ('page', 'content', 'message', 'created_ip', 'created_at',
                    'created_by')
    search_fields = ('page', 'content', 'message', 'created_ip', 'created_at',
                     'created_by')
    date_hierarchy = 'created_at'
    list_filter = ('created_at',)
    ordering = ('-created_at',)
    readonly_fields = ('created_ip', 'created_at', 'created_by',)

admin.site.register(Revision, RevisionAdmin)

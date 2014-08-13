'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''

from django.contrib import admin
from base.models import UserProfile, ProfileRequest

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_info', 'status', 'get_email', 'phone_number')
    search_fields = ('get_last', 'get_first', 'get_user', 'get_email', 'phone_number')
    list_filter = ('status', )
    ordering = ('-status', )

    def get_email(self, obj):
        return obj.user.email

    def get_info(self, obj):
        return "{0.first_name} {0.last_name}".format(obj.user)

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
admin.site.register(UserProfile, UserProfileAdmin)

class ProfileRequestAdmin(admin.ModelAdmin):
    list_display = ('username', 'last_name', 'first_name', 'email')
    search_fields = ('username', 'last_name', 'first_name', 'email')
    date_hierarchy = 'request_date'
    list_filter = ('request_date',)
    ordering = ('request_date',)
    readonly_fields = ('username', 'last_name', 'first_name', 'email')
admin.site.register(ProfileRequest, ProfileRequestAdmin)

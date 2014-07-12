"""
Project: Farnsworth

Authors: Karandeep Singh Nagra and Nader Morshed
"""

from django.contrib import admin

from rooms.models import Room, PreviousResidence

class RoomProfileAdmin(admin.ModelAdmin):
    list_display = ('title', 'unofficial_name', 'occupancy')
    search_fields = ('title', 'unofficial_name', 'description', 'current_residents')
    list_filter = ('occupancy', )
    ordering = ('title',)

admin.site.register(Room, RoomProfileAdmin)

class PreviousResidenceAdmin(admin.ModelAdmin):
    list_display = ('room', 'resident', 'start_date', 'end_date')
    search_fields = list_display
    ordergin = ('room',)

admin.site.register(PreviousResidence, PreviousResidenceAdmin)

"""
Project: Farnsworth

Authors: Karandeep Singh Nagra and Nader Morshed
"""

from django import forms

from rooms.models import Room

class RoomForm(forms.ModelForm):
    ''' Form to create or edit a room. '''
    class Meta:
        model = Room
        fields = "__all__"

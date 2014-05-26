
from django import forms
from django.core.validators import RegexValidator

from base.models import UserProfile
from rooms.models import Room

alphanumeric = RegexValidator(r'^[0-9a-zA-Z]*$', 'Only alphanumeric characters are allowed.')

class AddRoomForm(forms.ModelForm):
	''' Form to create a room. '''
	class Meta:
		model = Room
		fields = ("title", "unofficial_name", "description", "occupancy")
	residents = forms.ModelChoiceField(queryset=UserProfile.objects.filter(status=UserProfile.RESIDENT), help_text="The current residents of this room.")

class EditRoomForm(forms.ModelForm):
	''' Form to create a room. '''
	class Meta:
		model = Room
		fields = ("unofficial_name", "description", "occupancy")
	residents = forms.ModelChoiceField(queryset=UserProfile.objects.filter(status=UserProfile.RESIDENT), help_text="The current residents of this room.")

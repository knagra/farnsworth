
from django import forms
from django.core.validators import RegexValidator

from base.models import UserProfile
from rooms.models import Room

class AddRoomForm(forms.ModelForm):
	''' Form to create a room. '''
	class Meta:
		model = Room
		fields = "__all__"

class EditRoomForm(forms.ModelForm):
	''' Form to create a room. '''
	class Meta:
		model = Room
		exclude = ("title",)

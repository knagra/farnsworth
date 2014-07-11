
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

from base.models import UserProfile
from rooms.models import Room

class RoomForm(forms.ModelForm):
	''' Form to create or edit a room. '''
	class Meta:
		model = Room
		fields = "__all__"

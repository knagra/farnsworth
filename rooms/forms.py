
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

from base.models import UserProfile
from rooms.models import Room

class AddRoomForm(forms.ModelForm):
	''' Form to create or edit a room. '''
	class Meta:
		model = Room
		fields = "__all__"
	def clean_title(self):
		title = self.cleaned_data['title']
		if Room.objects.filter(title=title).count() > 0:
			raise ValidationError('This room title is already in use.')
		return title

class EditRoomForm(forms.ModelForm):
	''' Form to create or edit a room. '''
	class Meta:
		model = Room
		fields = "__all__"

	def clean_title(self):
		title = self.cleaned_data['title']
		if Room.objects.filter(title=title).count() > 1:
			raise ValidationError('This room title is already in use.')
		return title

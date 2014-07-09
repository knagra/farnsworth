'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''
from datetime import datetime

from django import forms
from django.conf import settings
from django.utils.timezone import utc

from utils.variables import time_formats, ANONYMOUS_USERNAME, MESSAGES
from managers.models import Manager
from events.models import Event

class EventForm(forms.Form):
	''' A form to post an event. '''
	title = forms.CharField(max_length=100, widget=forms.TextInput())
	description = forms.CharField(widget=forms.Textarea())
	location = forms.CharField(max_length=100, widget=forms.TextInput())
	rsvp = forms.BooleanField(required=False, label="RSVP")
	start_time = forms.DateTimeField(widget=forms.DateTimeInput(format=time_formats[0]),
					 input_formats=time_formats)
	end_time = forms.DateTimeField(widget=forms.DateTimeInput(format=time_formats[0]),
								   input_formats=time_formats)
	as_manager = forms.ModelChoiceField(required=False, queryset=Manager.objects.none(),
										label="As manager (if manager event)")
	cancelled = forms.BooleanField(required=False, label="Mark Cancelled")

	def __init__(self, *args, **kwargs):
		self.profile = kwargs.pop("profile")
		self.manager_positions = Manager.objects.filter(incumbent=self.profile)
		if 'instance' in kwargs:
			self.instance = kwargs.pop('instance')
			if 'initial' not in kwargs:
				rsvpd = (self.profile in self.instance.rsvps.all())
				kwargs['initial'] = {
					'title': self.instance.title,
					'description': self.instance.description,
					'location': self.instance.location,
					'rsvp': rsvpd,
					'start_time': self.instance.start_time,
					'end_time': self.instance.end_time,
					'as_manager': self.instance.as_manager,
					'cancelled': self.instance.cancelled
					}
		else:
			self.instance = None
		if 'initial' not in kwargs:
			kwargs['initial'] = {
				"rsvp": True,
				"location": settings.HOUSE,
				}
		super(EventForm, self).__init__(*args, **kwargs)
		if self.manager_positions:
			self.fields['as_manager'].queryset = self.manager_positions
			self.fields["as_manager"].empty_label = "------"
			self.fields["as_manager"].initial = self.manager_positions[0].pk
		else:
			self.fields["as_manager"].widget = forms.HiddenInput()
			self.fields["as_manager"].queryset = Manager.objects.none()
		if self.profile.user.username == ANONYMOUS_USERNAME:
			self.fields["rsvp"].widget = forms.HiddenInput()
		if not self.instance:
			self.fields["cancelled"].widget = forms.HiddenInput()

	def is_valid(self):
		if not super(EventForm, self).is_valid():
			return False
		start_time = self.cleaned_data['start_time']
		end_time = self.cleaned_data['end_time']
		if start_time > end_time:
			self.errors['__all__'] = self.error_class(["Start time is later than end time. Unless this event involves time travel, please change the start or end time."])
			return False
		return True

	def save(self):
		if not self.instance:
			event = Event(
				owner=self.profile,
				title=self.cleaned_data['title'],
				description=self.cleaned_data['description'],
				location=self.cleaned_data['location'],
				start_time=self.cleaned_data['start_time'],
				end_time=self.cleaned_data['end_time'],
				)
		else:
			self.instance.title = self.cleaned_data['title']
			self.instance.description = self.cleaned_data['description']
			self.instance.location = self.cleaned_data['location']
			self.instance.start_time = self.cleaned_data['start_time']
			self.instance.end_time = self.cleaned_data['end_time']
			self.instance.cancelled = self.cleaned_data['cancelled']
			event = self.instance
		event.save()
		if self.cleaned_data['rsvp'] and \
		  self.profile.user.username != ANONYMOUS_USERNAME:
			event.rsvps.add(self.profile)
		as_manager = self.cleaned_data['as_manager']
		if as_manager:
			event.as_manager = as_manager
		else:
			event.as_manager = None
		event.save()
		return event

class RsvpForm(forms.Form):
	''' Form to RSVP or un-RSVP from an event. '''
	event_pk = forms.IntegerField(widget=forms.HiddenInput())

	def __init__(self, *args, **kwargs):
		self.instance = kwargs.pop('instance', None)
		super(RsvpForm, self).__init__(*args, **kwargs)
		if self.instance:
			self.fields.pop('event_pk')

	def clean_event_pk(self):
		event_pk = self.cleaned_data['event_pk']
		try:
			event = Event.objects.get(pk=event_pk)
		except Event.DoesNotExist:
			raise forms.ValidationError("Event does not exist.")
		return event

	def clean(self):
		event = self.instance or self.cleaned_data.get('event_pk', None)
		if event:
			now = datetime.utcnow().replace(tzinfo=utc)
			if event.end_time <= now:
				raise forms.ValidationError(MESSAGES['ALREADY_PAST'])
		return self.cleaned_data

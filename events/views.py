'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django import forms
from models import Event
from django.core.urlresolvers import reverse
from threads.models import UserProfile
from requests.models import Manager
from threads.views import red_ext, red_home
from farnsworth.settings import NO_PROFILE, ADMINS_ONLY, UNKNOWN_FORM, house
import datetime
from django.utils.timezone import utc

time_formats = ['%m/%d/%Y %I:%M %p', '%m/%d/%Y %I:%M:%S %p', '%Y-%m-%d %H:%M:%S']

def list_events_view(request):
	''' A list view of upcoming events. '''
	page_name = "Upcoming Events"
	if request.user.is_authenticated():
		userProfile = None
		try:
			userProfile = UserProfile.objects.get(user=request.user)
		except:
			return red_home(request, NO_PROFILE)
	else:
		return HttpResponseRedirect(reverse('login'))
	manager_positions = Manager.objects.filter(incumbent=userProfile)
	class EventForm(forms.Form):
		title = forms.CharField(max_length=100, widget=forms.TextInput())
		description = forms.CharField(widget=forms.Textarea())
		location = forms.CharField(max_length=100, widget=forms.TextInput())
		rsvp = forms.BooleanField(required=False, label="RSVP")
		start_time = forms.DateTimeField(widget=forms.DateTimeInput, input_formats=time_formats)
		end_time = forms.DateTimeField(widget=forms.DateTimeInput, input_formats=time_formats)
		as_manager = forms.ModelChoiceField(queryset=manager_positions, required=False, label="As manager (if manager event)")
	class RsvpForm(forms.Form):
		event_pk = forms.IntegerField()
	event_form = EventForm(initial={'rsvp': True, 'location': house})
	if not manager_positions:
		event_form.fields['as_manager'].widget = forms.HiddenInput()
	if request.method == 'POST':
		if 'post_event' in request.POST:
			event_form = EventForm(request.POST)
			if event_form.is_valid():
				title = event_form.cleaned_data['title']
				description = event_form.cleaned_data['description']
				location = event_form.cleaned_data['location']
				rsvp = event_form.cleaned_data['rsvp']
				start_time = event_form.cleaned_data['start_time']
				end_time = event_form.cleaned_data['end_time']
				as_manager = event_form.cleaned_data['as_manager']
				new_event = Event(owner=userProfile, title=title, description=description, location=location, start_time=start_time, end_time=end_time)
				new_event.save()
				if rsvp:
					new_event.rsvps.add(userProfile)
				if as_manager:
					new_event.as_manager = as_manager
				new_event.save()
				return HttpResponseRedirect(reverse('events'))
		elif 'rsvp' in request.POST:
			rsvp_form = RsvpForm(request.POST)
			if rsvp_form.is_valid():
				event_pk = rsvp_form.cleaned_data['event_pk']
				relevant_event = Event.objects.get(pk=event_pk)
				if userProfile in relevant_event.rsvps.all():
					relevant_event.rsvps.remove(userProfile)
				else:
					relevant_event.rsvps.add(userProfile)
				relevant_event.save()
				return HttpResponseRedirect(reverse('events'))
		else:
			return red_home(request, UNKNOWN_FORM)
	now = datetime.datetime.utcnow().replace(tzinfo=utc)
	upcoming_events = Event.objects.filter(end_time__gte=now)
	events_dict = list() # a pseudo-dictionary, actually a list with items of form (event, ongoing, rsvpd, rsvp_form), where ongoing is a boolean of whether the event is currently ongoing, rsvpd is a boolean of whether the user has rsvp'd to the event
	for event in upcoming_events:
		form = RsvpForm(initial={'event_pk': event.pk})
		form.fields['event_pk'].widget = forms.HiddenInput()
		ongoing = ((event.start_time <= now) and (event.end_time >= now))
		rsvpd = (userProfile in event.rsvps.all())
		events_dict.append((event, ongoing, rsvpd, form))
	return render_to_response('list_events.html', {'page_name': page_name, 'events_dict': events_dict, 'now': now, 'event_form': event_form}, context_instance=RequestContext(request))

def list_all_events_view(request):
	''' A list view of all events.  Part of archives. '''
	page_name = "Archives - All Events"
	if request.user.is_authenticated():
		userProfile = None
		try:
			userProfile = UserProfile.objects.get(user=request.user)
		except:
			return red_home(request, NO_PROFILE)
	else:
		return HttpResponseRedirect(reverse('login'))
	manager_positions = Manager.objects.filter(incumbent=userProfile)
	class EventForm(forms.Form):
		title = forms.CharField(max_length=100, widget=forms.TextInput())
		description = forms.CharField(widget=forms.Textarea())
		location = forms.CharField(max_length=100, widget=forms.TextInput())
		rsvp = forms.BooleanField(required=False, label="RSVP")
		start_time = forms.DateTimeField(widget=forms.DateTimeInput, input_formats=time_formats)
		end_time = forms.DateTimeField(widget=forms.DateTimeInput, input_formats=time_formats)
		as_manager = forms.ModelChoiceField(queryset=manager_positions, required=False, label="As manager (if manager event)")
	class RsvpForm(forms.Form):
		event_pk = forms.IntegerField()
	event_form = EventForm(initial={'rsvp': True, 'location': house})
	if not manager_positions:
		event_form.fields['as_manager'].widget = forms.HiddenInput()
	if request.method == 'POST':
		if 'post_event' in request.POST:
			event_form = EventForm(request.POST)
			if event_form.is_valid():
				title = event_form.cleaned_data['title']
				description = event_form.cleaned_data['description']
				location = event_form.cleaned_data['location']
				rsvp = event_form.cleaned_data['rsvp']
				start_time = event_form.cleaned_data['start_time']
				end_time = event_form.cleaned_data['end_time']
				as_manager = event_form.cleaned_data['as_manager']
				new_event = Event(owner=userProfile, title=title, description=description, location=location, start_time=start_time, end_time=end_time)
				new_event.save()
				if rsvp:
					new_event.rsvps.add(userProfile)
				if as_manager:
					new_event.as_manager = as_manager
				new_event.save()
				return HttpResponseRedirect(reverse('all_events'))
		elif 'rsvp' in request.POST:
			rsvp_form = RsvpForm(request.POST)
			if rsvp_form.is_valid():
				event_pk = rsvp_form.cleaned_data['event_pk']
				relevant_event = Event.objects.get(pk=event_pk)
				if userProfile in relevant_event.rsvps.all():
					relevant_event.rsvps.remove(userProfile)
				else:
					relevant_event.rsvps.add(userProfile)
				relevant_event.save()
				return HttpResponseRedirect(reverse('all_events'))
		else:
			return red_home(request, UNKNOWN_FORM)
	now = datetime.datetime.utcnow().replace(tzinfo=utc)
	all_events = Event.objects.all()
	events_dict = list() # a pseudo-dictionary, actually a list with items of form (event, ongoing, rsvpd, rsvp_form), where ongoing is a boolean of whether the event is currently ongoing, rsvpd is a boolean of whether the user has rsvp'd to the event
	for event in all_events:
		form = RsvpForm(initial={'event_pk': event.pk})
		form.fields['event_pk'].widget = forms.HiddenInput()
		ongoing = ((event.start_time <= now) and (event.end_time >= now))
		rsvpd = (userProfile in event.rsvps.all())
		events_dict.append((event, ongoing, rsvpd, form))
	return render_to_response('list_events.html', {'page_name': page_name, 'events_dict': events_dict, 'now': now, 'event_form': event_form}, context_instance=RequestContext(request))

def edit_event_view(request, event_pk):
	''' The view to edit an event. '''
	page_name = "Edit Event"
	if request.user.is_authenticated():
		userProfile = None
		try:
			userProfile = UserProfile.objects.get(user=request.user)
		except:
			return red_home(request, NO_PROFILE)
	else:
		return HttpResponseRedirect(reverse('login'))
	try:
		event = Event.objects.get(pk=event_pk)
	except:
		return HttpResponseRedirect(reverse('events'))
	if not ((event.owner == userProfile) or (request.user.is_superuser)):
		return HttpResponseRedirect(reverse('events'))
	manager_positions = Manager.objects.filter(incumbent=event.owner)
	class EventForm(forms.Form):
		title = forms.CharField(max_length=100, widget=forms.TextInput())
		description = forms.CharField(widget=forms.Textarea())
		location = forms.CharField(max_length=100, widget=forms.TextInput())
		rsvp = forms.BooleanField(required=False, label="RSVP")
		cancelled = forms.BooleanField(required=False, label="Mark Cancelled")
		start_time = forms.DateTimeField(widget=forms.DateTimeInput, input_formats=time_formats)
		end_time = forms.DateTimeField(widget=forms.DateTimeInput, input_formats=time_formats)
		as_manager = forms.ModelChoiceField(queryset=manager_positions, required=False, label="As manager (if manager event)")
	rsvpd = (userProfile in event.rsvps.all())
	event_form = EventForm(initial={'title': event.title, 'description': event.description, 'location': event.location, 'rsvp': rsvpd, 'start_time': event.start_time, 'end_time': event.end_time, 'as_manager': event.as_manager, 'cancelled': event.cancelled})
	if not manager_positions:
		event_form.fields['as_manager'].widget = forms.HiddenInput()
	if request.method == 'POST':
		event_form = EventForm(request.POST)
		if event_form.is_valid():
			title = event_form.cleaned_data['title']
			description = event_form.cleaned_data['description']
			location = event_form.cleaned_data['location']
			rsvp = event_form.cleaned_data['rsvp']
			cancelled = event_form.cleaned_data['cancelled']
			start_time = event_form.cleaned_data['start_time']
			end_time = event_form.cleaned_data['end_time']
			as_manager = event_form.cleaned_data['as_manager']
			event.title = title
			event.description = description
			event.location = location
			event.cancelled = cancelled
			event.start_time = start_time
			event.end_time = end_time
			event.save()
			if rsvp:
				event.rsvps.add(userProfile)
			if as_manager:
				event.as_manager = as_manager
			event.save()
			return HttpResponseRedirect(reverse('events'))
	return render_to_response('edit_event.html', {'page_name': page_name, 'event_form': event_form}, context_instance=RequestContext(request))

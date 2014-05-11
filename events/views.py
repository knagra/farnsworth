'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''

import datetime
from django.utils.timezone import utc
from django.contrib import messages
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django import forms
from django.core.urlresolvers import reverse
from threads.models import UserProfile
from managers.models import Manager
from threads.decorators import profile_required
from threads.redirects import red_home, red_ext
# Standard messages:
from farnsworth.settings import MESSAGES
from events.models import Event
from events.forms import EventForm, RsvpForm

@profile_required
def list_events_view(request):
	''' A list view of upcoming events. '''
	page_name = "Upcoming Events"
	userProfile = UserProfile.objects.get(user=request.user)
	manager_positions = Manager.objects.filter(incumbent=userProfile)
	event_form = EventForm(manager_positions)
	if not manager_positions:
		event_form.fields['as_manager'].widget = forms.HiddenInput()
	if request.method == 'POST':
		if 'post_event' in request.POST:
			event_form = EventForm(manager_positions, post=request.POST)
			if event_form.is_valid():
				title = event_form.cleaned_data['title']
				description = event_form.cleaned_data['description']
				location = event_form.cleaned_data['location']
				rsvp = event_form.cleaned_data['rsvp']
				start_time = event_form.cleaned_data['start_time']
				end_time = event_form.cleaned_data['end_time']
				as_manager = event_form.cleaned_data['as_manager']
				if start_time > end_time:
					messages.add_message(request, messages.ERROR, "Something went wrong.  Please try again.")
					event_form.errors['__all__'] = event_form.error_class(["Start time is later than end time.  Unless this event involves time travel, please change the start or end time."])
				else:
					new_event = Event(owner=userProfile, title=title, description=description, location=location, start_time=start_time, end_time=end_time)
					new_event.save()
					if rsvp:
						new_event.rsvps.add(userProfile)
					if as_manager:
						new_event.as_manager = as_manager
					new_event.save()
					return HttpResponseRedirect(reverse('events'))
			else:
				messages.add_message(request, messages.ERROR, MESSAGES['EVENT_ERROR'])
		elif 'rsvp' in request.POST:
			rsvp_form = RsvpForm(request.POST)
			if rsvp_form.is_valid():
				if relevant_event.end_time <= now:
					messages.add_message(request, messages.ERROR, MESSAGES['ALREADY_PAST'])
				else:
					event_pk = rsvp_form.cleaned_data['event_pk']
					relevant_event = Event.objects.get(pk=event_pk)
					if userProfile in relevant_event.rsvps.all():
						relevant_event.rsvps.remove(userProfile)
						message = MESSAGES['RSVP_REMOVE'].format(event=relevant_event.title)
						messages.add_message(request, messages.SUCCESS, message)
					else:
						relevant_event.rsvps.add(userProfile)
						message = MESSAGES['RSVP_ADD'].format(event=relevant_event.title)
						messages.add_message(request, messages.SUCCESS, message)
					relevant_event.save()
				return HttpResponseRedirect(reverse('events'))
		else:
			return red_home(request, MESSAGES['UNKNOWN_FORM'])
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

@profile_required
def list_all_events_view(request):
	''' A list view of all events.  Part of archives. '''
	page_name = "Archives - All Events"
	userProfile = UserProfile.objects.get(user=request.user)
	manager_positions = Manager.objects.filter(incumbent=userProfile)
	event_form = EventForm(manager_positions)
	now = datetime.datetime.utcnow().replace(tzinfo=utc)
	if not manager_positions:
		event_form.fields['as_manager'].widget = forms.HiddenInput()
	if request.method == 'POST':
		if 'post_event' in request.POST:
			event_form = EventForm(manager_positions, post=request.POST)
			if event_form.is_valid():
				title = event_form.cleaned_data['title']
				description = event_form.cleaned_data['description']
				location = event_form.cleaned_data['location']
				rsvp = event_form.cleaned_data['rsvp']
				start_time = event_form.cleaned_data['start_time']
				end_time = event_form.cleaned_data['end_time']
				as_manager = event_form.cleaned_data['as_manager']
				if start_time > end_time:
					messages.add_message(request, messages.ERROR, "Something went wrong.  Please try again.")
					event_form.errors['__all__'] = event_form.error_class(["Start time is later than end time.  Unless this event involves time travel, please change the start or end time."])
				else:
					new_event = Event(owner=userProfile, title=title, description=description, location=location, start_time=start_time, end_time=end_time)
					new_event.save()
					if rsvp:
						new_event.rsvps.add(userProfile)
					if as_manager:
						new_event.as_manager = as_manager
					new_event.save()
					return HttpResponseRedirect(reverse('all_events'))
			else:
				messages.add_message(request, messages.SUCCESS, MESSAGES['EVENT_ERROR'])
		elif 'rsvp' in request.POST:
			rsvp_form = RsvpForm(request.POST)
			if rsvp_form.is_valid():
				if relevant_event.end_time <= now:
					messages.add_message(request, messages.ERROR, MESSAGES['ALREADY_PAST'])
				else:
					event_pk = rsvp_form.cleaned_data['event_pk']
					relevant_event = Event.objects.get(pk=event_pk)
					if userProfile in relevant_event.rsvps.all():
						relevant_event.rsvps.remove(userProfile)
						message = MESSAGES['RSVP_REMOVE'].format(event=relevant_event.title)
						messages.add_message(request, messages.SUCCESS, message)
					else:
						relevant_event.rsvps.add(userProfile)
						message = MESSAGES['RSVP_ADD'].format(event=relevant_event.title)
						messages.add_message(request, messages.SUCCESS, message)
					relevant_event.save()
				return HttpResponseRedirect(reverse('all_events'))
		else:
			return red_home(request, MESSAGES['UNKNOWN_FORM'])
	all_events = Event.objects.all()
	events_dict = list() # a pseudo-dictionary, actually a list with items of form (event, ongoing, rsvpd, rsvp_form, already_past), where ongoing is a boolean of whether the event is currently ongoing, rsvpd is a boolean of whether the user has rsvp'd to the event
	for event in all_events:
		form = RsvpForm(initial={'event_pk': event.pk})
		form.fields['event_pk'].widget = forms.HiddenInput()
		ongoing = ((event.start_time <= now) and (event.end_time >= now))
		rsvpd = (userProfile in event.rsvps.all())
		already_past = (event.end_time <= now)
		events_dict.append((event, ongoing, rsvpd, form, already_past))
	return render_to_response('list_events.html', {'page_name': page_name, 'events_dict': events_dict, 'now': now, 'event_form': event_form}, context_instance=RequestContext(request))

@profile_required
def edit_event_view(request, event_pk):
	''' The view to edit an event. '''
	page_name = "Edit Event"
	userProfile = UserProfile.objects.get(user=request.user)
	try:
		event = Event.objects.get(pk=event_pk)
	except Event.DoesNotExist:
		return HttpResponseRedirect(reverse('events'))
	if not ((event.owner == userProfile) or (request.user.is_superuser)):
		return HttpResponseRedirect(reverse('events'))
	manager_positions = Manager.objects.filter(incumbent=event.owner)
	rsvpd = (userProfile in event.rsvps.all())
	event_form = EventForm(manager_positions, initial={
			'title': event.title,
			'description': event.description,
			'location': event.location,
			'rsvp': rsvpd,
			'start_time': event.start_time,
			'end_time': event.end_time,
			'as_manager': event.as_manager,
			'cancelled': event.cancelled
			})
	if not manager_positions:
		event_form.fields['as_manager'].widget = forms.HiddenInput()
	if request.method == 'POST':
		event_form = EventForm(manager_positions, post=request.POST)
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
			message = MESSAGES['EVENT_UPDATED'].format(event=title)
			messages.add_message(request, messages.SUCCESS, message)
			return HttpResponseRedirect(reverse('events'))
	return render_to_response('edit_event.html', {'page_name': page_name, 'event_form': event_form}, context_instance=RequestContext(request))

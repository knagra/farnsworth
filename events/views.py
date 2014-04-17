'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django import forms
from models import Event
from django.core.urlresolvers import reverse
from threads.models import UserProfile
from threads.views import red_ext, red_home
from farnsworth.settings import NO_PROFILE, ADMINS_ONLY, UNKNOWN_FORM, house
import datetime
from django.utils.timezone import utc

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
		description = forms.CharField(widget=forms.Texarea())
		location = forms.CharField(max_length=100, widget=forms.TextInput())
		rsvp = forms.BooleanField(required=False)
		start_time = forms.DateTimeField(widget=forms.DateTimeInput)
		end_time = forms.DateTimeField(widget=forms.DateTimeInput)
		as_manager = forms.ModelChoiceField(queryset=manager_positions, required=False, label="As manager (optional)")
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
				rsvp = event_form.cleaned_data['rsvp']
				start_time = event_form.cleaned_data['start_time']
				end_time = event_form.cleaned_data['end_time']
				as_manager = event_form.cleaned_data['as_manager']
				new_event = Event(owner=userProfile, title=title, description=description, start_time=start_time, end_time=end_time)
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
				if userProfile in relevant_event.rsvps:
					relevant_event.rsvps.remove(userProfile)
				else:
					relevant_event.rsvps.add(userProfile)
				relevant_event.save()
				return HttpResponseRedirect(reverse('events'))
		else:
			return red_home(request, UNKNOWN_FORM)
	now = datetime.datetime.utcnow().replace(tzinfo=utc)
	upcoming_events = Event.objects.filter(start_time>now)
	event_dict = list() # a pseudo-dictionary, actually a list with items of form (event, ongoing, rsvpd, rsvp_form), where ongoing is a boolean of whether the event is currently ongoing, rsvpd is a boolean of whether the user has rsvp'd to the event
	for event in upcoming_events:
		form = RsvpForm(initial={'event_pk': event.pk})
		form.fields['event_pk'].widget = forms.HiddenInput()
		ongoing = ((event.start_time <= now) and (event.end_time >= now))
		rsvpd = (userProfile in event.rsvps.all())
		event_dict.append((event, ongoing, rsvpd, form))
	return render_to_response('list_events.html', {'page_name': page_name, 'event_dict': event_dict, 'now': now, 'event_form': event_form}, context_instance=RequestContext(request))

def list_all_events_view(request):
	''' A list view of all events.  Part of archives. '''
	page_name = "Archives - All Events" 

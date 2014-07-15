'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''

import datetime
from django.utils.timezone import utc
from django.contrib import messages
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.core.urlresolvers import reverse

from utils.variables import MESSAGES
from base.decorators import profile_required
from base.models import UserProfile
from events.models import Event
from events.forms import EventForm, RsvpForm

@profile_required
def list_events_view(request):
    ''' A list view of upcoming events. '''
    page_name = "Upcoming Events"
    profile = UserProfile.objects.get(user=request.user)
    event_form = EventForm(
        request.POST if 'post_event' in request.POST else None,
        profile=profile,
        )
    now = datetime.datetime.utcnow().replace(tzinfo=utc)
    if event_form.is_valid():
        event_form.save()
        return HttpResponseRedirect(reverse('events:list'))
    # a pseudo-dictionary, actually a list with items of form (event, ongoing,
    # rsvpd, rsvp_form), where ongoing is a boolean of whether the event is
    # currently ongoing, rsvpd is a boolean of whether the user has rsvp'd to
    # the event
    events_dict = list()
    for event in Event.objects.filter(end_time__gte=now):
        rsvp_form = RsvpForm(
            request.POST if "rsvp-{0}".format(event.pk) in request.POST else None,
            instance=event,
            profile=profile,
            )
        if rsvp_form.is_valid():
            rsvpd = rsvp_form.save()
            if rsvpd:
                message = MESSAGES['RSVP_ADD'].format(event=event.title)
            else:
                message = MESSAGES['RSVP_REMOVE'].format(event=event.title)
            messages.add_message(request, messages.SUCCESS, message)
            return HttpResponseRedirect(reverse('events:list'))

        ongoing = ((event.start_time <= now) and (event.end_time >= now))
        rsvpd = (profile in event.rsvps.all())
        events_dict.append((event, ongoing, rsvpd, rsvp_form))

    return render_to_response('list_events.html', {
        'page_name': page_name,
        'events_dict': events_dict,
        'now': now,
        'event_form': event_form,
        }, context_instance=RequestContext(request))

@profile_required
def list_all_events_view(request):
    ''' A list view of all events.  Part of archives. '''
    page_name = "Archives - All Events"
    profile = UserProfile.objects.get(user=request.user)

    event_form = EventForm(
        request.POST if "post_event" in request.POST else None,
        profile=profile,
        )

    if event_form.is_valid():
        event_form.save()
        return HttpResponseRedirect(reverse('events:all'))

    # a pseudo-dictionary, actually a list with items of form (event, ongoing,
    # rsvpd, rsvp_form, already_past), where ongoing is a boolean of whether the
    # event is currently ongoing, rsvpd is a boolean of whether the user has
    # rsvp'd to the event
    events_dict = list()
    now = datetime.datetime.utcnow().replace(tzinfo=utc)
    for event in Event.objects.all():
        rsvp_form = None
        if event.end_time > now:
            rsvp_form = RsvpForm(
                request.POST if "rsvp-{0}".format(event.pk) in request.POST else None,
                instance=event,
                profile=profile,
                )
            if rsvp_form.is_valid():
                rsvpd = rsvp_form.save()
                if rsvpd:
                    message = MESSAGES['RSVP_ADD'].format(event=event.title)
                else:
                    message = MESSAGES['RSVP_REMOVE'].format(event=event.title)
                messages.add_message(request, messages.SUCCESS, message)
                return HttpResponseRedirect(reverse('events:all'))

        ongoing = event.start_time <= now and event.end_time >= now
        rsvpd = profile in event.rsvps.all()
        events_dict.append(
            (event, ongoing, rsvpd, rsvp_form)
            )

    return render_to_response('list_events.html', {
        'page_name': page_name,
        'events_dict': events_dict,
        'now': now,
        'event_form': event_form,
        }, context_instance=RequestContext(request))

@profile_required
def event_view(request, event_pk):
    event = get_object_or_404(Event, pk=event_pk)
    profile = UserProfile.objects.get(user=request.user)
    can_edit = (event.owner == profile or request.user.is_superuser)
    now = datetime.datetime.utcnow().replace(tzinfo=utc)
    ongoing = event.start_time <= now and event.end_time >= now
    rsvpd = profile in event.rsvps.all()
    rsvp_form = RsvpForm(
        request.POST if "rsvp" in request.POST else None,
        instance=event,
        profile=profile,
        )
    already_passed = event.end_time <= now
    if rsvp_form.is_valid():
        rsvpd = rsvp_form.save()
        if rsvpd:
            message = MESSAGES['RSVP_ADD'].format(event=event.title)
        else:
            message = MESSAGES['RSVP_REMOVE'].format(event=event.title)
        messages.add_message(request, messages.SUCCESS, message)
        return HttpResponseRedirect(
            reverse('events:view', kwargs={"event_pk": event_pk}),
            )

    return render_to_response('view_event.html', {
        'page_name': event.title,
        'can_edit': can_edit,
        'event': event,
        'ongoing': ongoing,
        'rsvp_form': rsvp_form,
        'rsvpd': rsvpd,
        'already_passed': already_passed,
        }, context_instance=RequestContext(request))

@profile_required
def edit_event_view(request, event_pk):
    ''' The view to edit an event. '''
    page_name = "Edit Event"
    profile = UserProfile.objects.get(user=request.user)
    event = get_object_or_404(Event, pk=event_pk)
    if event.owner != profile and not request.user.is_superuser:
        return HttpResponseRedirect(
            reverse('events:view', kwargs={"event_pk": event_pk}),
            )
    event_form = EventForm(
        request.POST or None,
        profile=profile,
        instance=event,
        )
    if event_form.is_valid():
        event = event_form.save()
        messages.add_message(
            request, messages.SUCCESS,
            MESSAGES['EVENT_UPDATED'].format(event=event.title),
            )
        return HttpResponseRedirect(
            reverse('events:view', kwargs={"event_pk": event_pk}),
            )
    return render_to_response('edit_event.html', {
        'page_name': page_name,
        'event_form': event_form,
        }, context_instance=RequestContext(request))

'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''

import json

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.timezone import now

import inflect
p = inflect.engine()

from utils.variables import MESSAGES
from base.decorators import profile_required, ajax_capable
from base.models import UserProfile
from events.models import Event
from events.forms import EventForm, RsvpForm
from events.ajax import build_ajax_rsvps

def add_archive_context(request):
    event_count = Event.objects.all().count()
    nodes = [
        "{} {}".format(event_count, p.plural("event", event_count)),
        ]
    render_list = [
        (
            "All Events",
            reverse("events:all"),
            "glyphicon-comment",
            event_count,
        ),
        ]
    return nodes, render_list

@profile_required
def list_events_view(request):
    ''' A list view of upcoming events. '''
    page_name = "Upcoming Events"
    profile = UserProfile.objects.get(user=request.user)
    event_form = EventForm(
        request.POST if 'post_event' in request.POST else None,
        profile=profile,
        )
    if event_form.is_valid():
        event_form.save()
        return HttpResponseRedirect(reverse('events:list'))
    # a pseudo-dictionary, actually a list with items of form (event, ongoing,
    # rsvpd, rsvp_form), where ongoing is a boolean of whether the event is
    # currently ongoing, rsvpd is a boolean of whether the user has rsvp'd to
    # the event
    events_dict = list()
    for event in Event.objects.filter(end_time__gte=now()):
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

        ongoing = ((event.start_time <= now()) and (event.end_time >= now()))
        rsvpd = (profile in event.rsvps.all())
        events_dict.append((event, ongoing, rsvpd, rsvp_form))

    if request.method == "POST":
        messages.add_message(request, messages.ERROR, MESSAGES["EVENT_ERROR"])

    return render_to_response('list_events.html', {
        'page_name': page_name,
        'events_dict': events_dict,
        'now': now(),
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
    for event in Event.objects.all():
        rsvp_form = None
        if event.end_time > now():
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

        ongoing = event.start_time <= now() and event.end_time >= now()
        rsvpd = profile in event.rsvps.all()
        events_dict.append(
            (event, ongoing, rsvpd, rsvp_form)
            )

    if request.method == "POST":
        messages.add_message(request, messages.ERROR, MESSAGES["EVENT_ERROR"])

    return render_to_response('list_events.html', {
        'page_name': page_name,
        'events_dict': events_dict,
        'now': now(),
        'event_form': event_form,
        }, context_instance=RequestContext(request))

@profile_required
@ajax_capable
def event_view(request, event_pk):
    if not request.user.is_authenticated():
        return HttpResponse(json.dumps(dict()),
                            content_type="application/json")

    event = get_object_or_404(Event, pk=event_pk)
    profile = UserProfile.objects.get(user=request.user)

    rsvp_form = RsvpForm(
        request.POST if "rsvp" in request.POST else None,
        instance=event,
        profile=profile,
        )

    if rsvp_form.is_valid():
        rsvpd = rsvp_form.save()
        if request.is_ajax():
            link_string = 'rsvp_link_{pk}'.format(pk=event.pk)
            list_string = 'rsvp_list_{pk}'.format(pk=event.pk)
            response = dict()
            response[link_string], response[list_string] = build_ajax_rsvps(
                event,
                profile
            )
            return HttpResponse(json.dumps(response),
                                content_type="application/json")

        if rsvpd:
            message = MESSAGES['RSVP_ADD'].format(event=event.title)
        else:
            message = MESSAGES['RSVP_REMOVE'].format(event=event.title)
        messages.add_message(request, messages.SUCCESS, message)
        return HttpResponseRedirect(
            reverse('events:view', kwargs={"event_pk": event_pk}),
        )

    elif request.is_ajax():
        raise Http404

    if request.method == "POST":
        messages.add_message(request, messages.ERROR, MESSAGES["EVENT_ERROR"])

    already_passed = event.end_time <= now()
    can_edit = event.owner == profile or request.user.is_superuser
    ongoing = event.start_time <= now() and event.end_time >= now()
    rsvpd = profile in event.rsvps.all()

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

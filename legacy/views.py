"""
Project: Farnsworth

Author: Karandeep Singh Nagra

Legacy Kingman site views.
"""


from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import Http404
from django.shortcuts import render_to_response
from django.template import RequestContext

from base.decorators import profile_required
from legacy.models import TeacherRequest, TeacherResponse, TeacherNote, \
    TeacherEvent


@profile_required
def legacy_notes_view(request):
    """
    View to see legacy notes.
    """
    notes = TeacherNote.objects.all()
    note_count = notes.count()
    paginator = Paginator(notes, 100)

    page = request.GET.get('page')
    try:
        notes = paginator.page(page)
    except PageNotAnInteger:
        notes = paginator.page(1)
    except EmptyPage:
        notes = paginator.page(paginator.num_pages)
    return render_to_response(
        'teacher_notes.html',
        {'page_name': "Legacy Notes",
         'notes': notes,
         'note_count': note_count,},
        context_instance=RequestContext(request)
    )

@profile_required
def legacy_events_view(request):
    """
    View to see legacy events.
    """
    events = TeacherEvent.objects.all()
    event_count = events.count()
    paginator = Paginator(events, 100)

    page = request.GET.get('page')
    try:
        events = paginator.page(page)
    except PageNotAnInteger:
        events = paginator.page(1)
    except EmptyPage:
        events = paginator.page(paginator.num_pages)
    return render_to_response(
        'teacher_events.html',
        {'page_name': "Legacy Events",
         'events': events,
         'event_count': event_count,},
        context_instance=RequestContext(request)
    )

@profile_required
def legacy_requests_view(request, rtype):
    """
    View to see legacy requests of rtype request type, which should be either
    'food' or 'maintenance'.
    """
    if not rtype in ['food', 'maintenance']:
        raise Http404
    requests_dict = [] # [(req, [req_responses]), (req2, [req2_responses]), ...]
    requests = TeacherRequest.objects.filter(request_type=rtype)
    request_count = requests.count()
    paginator = Paginator(requests, 50)

    page = request.GET.get('page')
    try:
        requests = paginator.page(page)
    except PageNotAnInteger:
        requests = paginator.page(1)
    except EmptyPage:
        requests = paginator.page(paginator.num_pages)
    for req in requests:
        requests_dict.append(
            (req, TeacherResponse.objects.filter(request=req),)
        )
    return render_to_response(
        'teacher_requests.html',
        {'page_name': "Legacy {rtype} Requests".format(rtype=rtype.title()),
         'requests_dict': requests_dict,
         'requests': requests,
         'request_type': rtype.title(),
         'request_count': request_count,},
        context_instance=RequestContext(request)
    )

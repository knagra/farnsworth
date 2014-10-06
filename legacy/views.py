"""
Project: Farnsworth

Author: Karandeep Singh Nagra

Legacy Kingman site views.
"""


from django.http import Http404
from django.shortcuts import render_to_response

from base.decorators import profile_required
from legacy.models import TeacherRequest, TeacherResponse, TeacherNote, \
    TeacherEvent


@login_required
def legacy_notes_view(request):
    """
    View to see legacy notes.
    """
    return render_to_response(
        'teacher_notes.html',
        {'page_name': "Legacy Notes",
         'notes': TeacherNote.objects.all(),},
        context_instance=RequestContext(request)
    )

@login_required
def legacy_events_view(request):
    """
    View to see legacy events.
    """
    return render_to_response(
        'teacher_events.html',
        {'page_name': "Legacy Events",
         'events': TeacherEvent.objects.all(),},
        context_instance=RequestContext(request)
    )

@login_required
def legacy_requests_view(request, rtype):
    """
    View to see legacy requests of rtype request type, which should be either
    'food' or 'maintenance'.
    """
    if not rtype in ['food', 'maintenance']:
        raise Http404
    requests_dict = [] # [(req, [req_responses]), (req2, [req2_responses]), ...]
    for req in TeacherRequest.objects.filter(request_type=rtype):
        requests_dict.append(
            req,
            TeacherResponse.objects.filter(request=req),
        )
    return render_to_response(
        'teacher_requests.html',
        {'page_name': "Legacy {rtype} Requests".format(rtype=rtype.title()),
         'requests_dict': requests_dict,},
        context_instance=RequestContext(request)
    )

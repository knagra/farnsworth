'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext

from utils.variables import MESSAGES
from base.models import UserProfile
from base.decorators import profile_required
from threads.models import Thread, Message
from threads.forms import ThreadForm, MessageForm, EditMessageForm

def _threads_dict(threads, limited=False):
    # A pseudo-dictionary, actually a list with items of form
    # (thread.subject, [thread_messages_list], thread.pk, number_of_more_messages)
    threads_dict = list()
    x = 0
    for thread in threads:
        y = 0 # number of messages loaded
        thread_messages = list()
        for message in Message.objects.filter(thread=thread).reverse():
            thread_messages.append(message)
            y += 1
            if y >= settings.MAX_MESSAGES:
                break
        more_messages = thread.number_of_messages - settings.MAX_MESSAGES
        if more_messages < 0:
            more_messages = 0
        thread_messages.reverse()
        threads_dict.append((thread.subject, thread_messages, thread.pk, more_messages))
        x += 1
        if x >= settings.MAX_THREADS and limited:
            break
    return threads_dict

@profile_required
def list_user_threads_view(request, targetUsername):
    ''' View of threads a user has created. '''
    targetUser = get_object_or_404(User, username=targetUsername)
    targetProfile = get_object_or_404(UserProfile, user=targetUser)
    threads = Thread.objects.filter(owner=targetProfile)
    page_name = "{0}'s Threads".format(targetUser.get_full_name())
    return render_to_response('list_threads.html', {
        'page_name': page_name,
        'threads': threads,
        'targetUsername': targetUsername,
        }, context_instance=RequestContext(request))

@profile_required
def list_user_messages_view(request, targetUsername):
    ''' View of threads a user has posted in. '''
    targetUser = get_object_or_404(User, username=targetUsername)
    targetProfile = get_object_or_404(UserProfile, user=targetUser)
    user_messages = Message.objects.filter(owner=targetProfile)
    thread_pks = list(set([i.thread.pk for i in user_messages]))
    threads = Thread.objects.filter(pk__in=thread_pks)
    page_name = "Threads {0} has posted in".format(targetUser.get_full_name())
    return render_to_response('list_threads.html', {
        'page_name': page_name,
        'threads': threads,
        'targetUsername': targetUsername,
        }, context_instance=RequestContext(request))

@profile_required
def list_all_threads_view(request):
    ''' View of all threads. '''
    threads = Thread.objects.all()
    return render_to_response('list_threads.html', {
        'page_name': "Archives - All Threads",
        'threads': threads,
        }, context_instance=RequestContext(request))

@profile_required
def thread_view(request, thread_pk):
    ''' View an individual thread. '''
    userProfile = UserProfile.objects.get(user=request.user)
    thread = get_object_or_404(Thread, pk=thread_pk)
    messages_list = Message.objects.filter(thread=thread)

    message_form = MessageForm(
        request.POST or None,
        profile=userProfile,
        initial={'thread_pk': thread_pk},
        )
    # message_form = EditMessageForm(
    #     request.POST if "edit" in request.POST else None,
    #     instance=message,
    #     )
    # thread_form = EditThreadForm(
    #     request.POST if "edit" in request.POST else None,
    #     instance=thread,
    #     )

    if message_form.is_valid():
        message_form.save()
        return HttpResponseRedirect(reverse('threads:view_thread', kwargs={
            'thread_pk': thread_pk,
            }))
    elif 'submit_message_form' in request.POST:
        messages.add_message(request, messages.ERROR, MESSAGES['MESSAGE_ERROR'])
    return render_to_response('view_thread.html', {
            'thread': thread,
            'page_name': thread.subject,
            'messages_list': messages_list,
            }, context_instance=RequestContext(request))

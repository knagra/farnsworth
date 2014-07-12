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
def member_forums_view(request):
    ''' Forums for current members. '''
    page_name = "Member Forums"
    userProfile = UserProfile.objects.get(user=request.user)
    thread_form = ThreadForm(
        request.POST if 'submit_thread_form' in request.POST else None,
        profile=userProfile,
        )
    message_form = MessageForm(
        request.POST if 'submit_message_form' in request.POST else None,
        profile=userProfile,
        )
    if thread_form.is_valid():
        thread_form.save()
        return HttpResponseRedirect(reverse('member_forums'))
    elif 'submit_thread_form' in request.POST:
        messages.add_message(request, messages.ERROR, MESSAGES['THREAD_ERROR'])
    if message_form.is_valid():
        message_form.save()
        return HttpResponseRedirect(reverse('member_forums'))
    elif 'submit_message_form' in request.POST:
        messages.add_message(request, messages.ERROR, MESSAGES['MESSAGE_ERROR'])
    threads_dict = _threads_dict(Thread.objects.all(), limited=True)
    return render_to_response('threads.html', {
            'page_name': page_name,
            'thread_title': 'Active Threads',
            'threads_dict': threads_dict,
            'thread_form': thread_form,
            }, context_instance=RequestContext(request))

@profile_required
def all_threads_view(request):
    ''' View of all threads. '''
    page_name = "Archives - All Threads"
    userProfile = UserProfile.objects.get(user=request.user)
    thread_form = ThreadForm(
        request.POST if 'submit_thread_form' in request.POST else None,
        profile=userProfile,
        )
    message_form = MessageForm(
        request.POST if 'submit_message_form' in request.POST else None,
        profile=userProfile,
        )

    if thread_form.is_valid():
        thread_form.save()
        return HttpResponseRedirect(reverse('all_threads'))
    elif 'submit_thread_form' in request.POST:
        messages.add_message(request, messages.ERROR, MESSAGES['THREAD_ERROR'])
    if message_form.is_valid():
        message_form.save()
        return HttpResponseRedirect(reverse('all_threads'))
    elif 'submit_message_form' in request.POST:
        messages.add_message(request, messages.ERROR, MESSAGES['MESSAGE_ERROR'])

    threads_dict = _threads_dict(Thread.objects.all())
    return render_to_response('threads.html', {
            'page_name': page_name,
            'thread_title': 'Archives - All Threads',
            'threads_dict': threads_dict,
            'thread_form': thread_form,
            }, context_instance=RequestContext(request))

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
    if message_form.is_valid():
        message_form.save()
        return HttpResponseRedirect(reverse('view_thread', kwargs={
                    'thread_pk': thread_pk,
                    }))
    elif 'submit_message_form' in request.POST:
        messages.add_message(request, messages.ERROR, MESSAGES['MESSAGE_ERROR'])
    return render_to_response('view_thread.html', {
            'thread': thread,
            'page_name': thread.subject,
            'messages_list': messages_list,
            }, context_instance=RequestContext(request))

@profile_required
def edit_message_view(request, message_pk):
    ''' View an individual message.'''
    userProfile = UserProfile.objects.get(user=request.user)
    message = get_object_or_404(Message, pk=message_pk)
    if message.owner != userProfile and not request.user.is_superuser:
        messages.add_message(request, messages.ERROR, "Permission denied.")
        return HttpResponseRedirect(reverse('threads:view_message',
                                            kwargs={"message_pk": message_pk}))

    message_form = EditMessageForm(
        request.POST if "edit" in request.POST else None,
        instance=message,
        )
    if "delete" in request.POST:
        thread = message.thread
        message.delete()
        thread.number_of_messages -= 1
        if thread.number_of_messages == 0:
            thread.delete()
            return HttpResponseRedirect(reverse('threads:list_all_threads'))
        else:
            thread.save()
            messages.add_message(request, messages.INFO, "Message deleted.")
            return HttpResponseRedirect(reverse('threads:view_thread',
                                                kwargs={"thread_pk": thread.pk}))
    elif message_form and message_form.is_valid():
        message = message_form.save()
        messages.add_message(request, messages.INFO, "Message edited.")
        return HttpResponseRedirect(reverse('threads:view_message',
                                            kwargs={"message_pk": message_pk}))

    page_name = "Edit Message".format(userProfile, message.thread.subject)

    return render_to_response('edit_message.html', {
        'message': message,
        'message_form': message_form,
        'page_name': page_name,
        }, context_instance=RequestContext(request))

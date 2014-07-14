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

from base.models import UserProfile
from utils.variables import MESSAGES
from base.decorators import profile_required
from threads.models import Thread, Message
from threads.forms import ThreadForm, MessageForm, EditMessageForm, \
     EditThreadForm, DeleteMessageForm

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
def list_all_threads_view(request):
    ''' View of all threads. '''
    threads = Thread.objects.all()
    form = ThreadForm(
        request.POST if "submit_thread_form" in request.POST else None,
        profile=UserProfile.objects.get(user=request.user),
        )

    if form.is_valid():
        thread = form.save()
        return HttpResponseRedirect(reverse("threads:list_all_threads"))
    elif request.method == "POST":
        messages.add_message(request, messages.ERROR, MESSAGES['THREAD_ERROR'])

    return render_to_response('list_threads.html', {
        'page_name': "All Threads",
        'threads': threads,
        }, context_instance=RequestContext(request))

@profile_required
def thread_view(request, thread_pk):
    ''' View an individual thread. '''
    userProfile = UserProfile.objects.get(user=request.user)
    thread = get_object_or_404(Thread, pk=thread_pk)
    messages_list = Message.objects.filter(thread=thread)

    forms = []

    for message in messages_list:
        edit_message_form, delete_message_form = None, None
        if message.owner == userProfile or userProfile.user.is_superuser:
            edit_message_form = EditMessageForm(
                request.POST or None,
                instance=message,
                prefix="edit-{0}".format(message.pk),
                )
            delete_message_form = DeleteMessageForm(
                request.POST or None,
                instance=message,
                prefix="delete-{0}".format(message.pk),
                )
            if edit_message_form.is_valid():
                edit_message_form.save()
                messages.add_message(request, messages.INFO, "Message updated.")
                return HttpResponseRedirect(reverse("threads:view_thread", kwargs={
                    "thread_pk": thread_pk,
                    }))
            if delete_message_form.is_valid():
                thread = delete_message_form.save()
                messages.add_message(request, messages.INFO, "Message deleted.")
                if thread is None:
                    return HttpResponseRedirect(reverse("threads:list_all_threads"))
                return HttpResponseRedirect(reverse("threads:view_thread", kwargs={
                    "thread_pk": thread.pk,
                    }))

        forms.append((edit_message_form, delete_message_form))

    edit_thread_form = None
    if thread.owner == userProfile or request.user.is_superuser:
        edit_thread_form = EditThreadForm(
            request.POST or None,
            instance=thread,
            prefix="edit-thread",
            )

    add_message_form = MessageForm(
        request.POST or None,
        profile=userProfile,
        thread=thread,
        prefix="add-message",
        )

    if add_message_form.is_valid():
        add_message_form.save()
        return HttpResponseRedirect(reverse('threads:view_thread', kwargs={
            'thread_pk': thread_pk,
            }))
    elif request.method == "POST":
        messages.add_message(request, messages.ERROR, MESSAGES['MESSAGE_ERROR'])

    if edit_thread_form and edit_thread_form.is_valid():
        thread = edit_thread_form.save()
        return HttpResponseRedirect(reverse("threads:view_thread", kwargs={
            "thread_pk": thread.pk,
            }))

    return render_to_response('view_thread.html', {
        'thread': thread,
        'page_name': thread.subject,
        'messages_list': zip(messages_list, forms),
        "add_message_form": add_message_form,
        "edit_thread_form": edit_thread_form,
        }, context_instance=RequestContext(request))

@profile_required
def list_user_threads_view(request, targetUsername):
    ''' View of threads a user has created. '''
    targetUser = get_object_or_404(User, username=targetUsername)
    targetProfile = get_object_or_404(UserProfile, user=targetUser)
    threads = Thread.objects.filter(owner=targetProfile)
    page_name = "{0}'s Threads".format(targetUser.get_full_name())
    form = ThreadForm(
        request.POST if "submit_thread_form" in request.POST else None,
        profile=UserProfile.objects.get(user=request.user),
        )

    if form.is_valid():
        thread = form.save()
        return HttpResponseRedirect(reverse("threads:list_all_threads"))
    elif request.method == "POST":
        messages.add_message(request, messages.ERROR, MESSAGES['THREAD_ERROR'])

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

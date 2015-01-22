'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''

import json

from django.contrib.auth.models import User
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext

import inflect
p = inflect.engine()

from base.models import UserProfile
from utils.variables import MESSAGES
from base.decorators import profile_required, ajax_capable
from threads.models import Thread, Message
from threads.forms import ThreadForm, MessageForm, EditMessageForm, \
    EditThreadForm, DeleteMessageForm, FollowThreadForm

def add_archive_context(request):
    thread_count = Thread.objects.all().count()
    message_count = Message.objects.all().count()
    nodes = [
        "{} {}".format(thread_count, p.plural("thread", thread_count)),
        "{} {}".format(message_count, p.plural("message", message_count)),
    ]
    render_list = [
        (
            "All Threads",
            reverse("threads:list_all_threads"),
            "glyphicon-comment",
            Thread.objects.all().count()
        ),
    ]
    return nodes, render_list

@profile_required
def list_all_threads_view(request):
    ''' View of all threads. '''
    threads = Thread.objects.all()

    create_form = ThreadForm(
        request.POST if "submit_thread_form" in request.POST else None,
        profile=UserProfile.objects.get(user=request.user),
        )

    if create_form.is_valid():
        thread = create_form.save()
        return HttpResponseRedirect(reverse("threads:view_thread",
                                            kwargs={"pk": thread.pk}))
    elif request.method == "POST":
        messages.add_message(request, messages.ERROR, MESSAGES['THREAD_ERROR'])

    return render_to_response('list_threads.html', {
        'page_name': "All Threads",
        "create_form": create_form,
        'threads': threads,
        }, context_instance=RequestContext(request))

@profile_required
@ajax_capable
def thread_view(request, pk):
    ''' View an individual thread. '''
    if request.is_ajax():
        if not request.user.is_authenticated():
            return HttpResponse(json.dumps(dict()),
                                content_type="application/json")
        try:
            user_profile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            return HttpResponse(json.dumps(dict()),
                                content_type="application/json")
        try:
            thread = Thread.objects.get(pk=pk)
        except Thread.DoesNotExist:
            return HttpResponse(json.dumps(dict()),
                                content_type="application/json")
        follow_form = FollowThreadForm(
            request.POST if "follow_thread" in request.POST else None,
            instance=thread,
            profile=user_profile,
        )
        if follow_form.is_valid():
            following = follow_form.save()
            response = dict(
                following=following,
                num_of_followers=thread.followers.all().count()
            )
            return HttpResponse(json.dumps(response),
                                content_type="application/json")
        raise Http404
    userProfile = UserProfile.objects.get(user=request.user)
    thread = get_object_or_404(Thread, pk=pk)
    messages_list = Message.objects.filter(thread=thread)

    follow_form = FollowThreadForm(
        request.POST if "follow_thread" in request.POST else None,
        instance=thread,
        profile=userProfile,
        )

    if follow_form.is_valid():
        following = follow_form.save()
        if following:
            message = "You are now following this thread."
        else:
            message = "You are no longer following this thread."
        messages.add_message(request, messages.INFO, message)
        return HttpResponseRedirect(reverse("threads:view_thread",
                                            kwargs={"pk": pk}))

    edit_forms, delete_forms = [], []

    for message in messages_list:
        edit_message_form, delete_message_form = None, None
        if message.owner == userProfile or userProfile.user.is_superuser:
            edit_message_form = EditMessageForm(
                request.POST if "edit_message-{0}".format(message.pk) in request.POST else None,
                instance=message,
                prefix="edit-{0}".format(message.pk),
                )
            delete_message_form = DeleteMessageForm(
                request.POST if "delete_message-{0}".format(message.pk) in request.POST else None,
                instance=message,
                )
            if edit_message_form.is_valid():
                edit_message_form.save()
                messages.add_message(request, messages.INFO, "Message updated.")
                return HttpResponseRedirect(reverse("threads:view_thread", kwargs={
                    "pk": pk,
                    }))
            if delete_message_form.is_valid():
                thread = delete_message_form.save()
                messages.add_message(request, messages.INFO, "Message deleted.")
                if thread is None:
                    return HttpResponseRedirect(reverse("threads:list_all_threads"))
                return HttpResponseRedirect(reverse("threads:view_thread", kwargs={
                    "pk": thread.pk,
                    }))

        edit_forms.append(edit_message_form)
        delete_forms.append(delete_message_form)

    edit_thread_form = None
    if thread.owner == userProfile or request.user.is_superuser:
        edit_thread_form = EditThreadForm(
            request.POST if "edit_thread" in request.POST else None,
            instance=thread,
            )

    add_message_form = MessageForm(
        request.POST if "add_message" in request.POST else None,
        profile=userProfile,
        thread=thread,
        )

    if edit_thread_form and edit_thread_form.is_valid():
        thread = edit_thread_form.save()
        return HttpResponseRedirect(reverse("threads:view_thread", kwargs={
            "pk": thread.pk,
            }))
    elif add_message_form.is_valid():
        add_message_form.save()
        return HttpResponseRedirect(reverse('threads:view_thread', kwargs={
            'pk': pk,
            }))
    elif request.method == "POST":
        messages.add_message(request, messages.ERROR, MESSAGES['MESSAGE_ERROR'])


    thread.views += 1
    thread.save()

    following = request.user in thread.followers.all()

    return render_to_response('view_thread.html', {
        'thread': thread,
        'page_name': thread.subject,
        'messages_list': zip(messages_list, edit_forms, delete_forms),
        "add_message_form": add_message_form,
        "edit_thread_form": edit_thread_form,
        "following": following,
        "follow_form": follow_form,
        }, context_instance=RequestContext(request))

@profile_required
def list_user_threads_view(request, targetUsername):
    ''' View of threads a user has created. '''
    targetUser = get_object_or_404(User, username=targetUsername)
    targetProfile = get_object_or_404(UserProfile, user=targetUser)
    threads = Thread.objects.filter(owner=targetProfile)
    page_name = "{0}'s Threads".format(targetUser.get_full_name())
    create_form = ThreadForm(
        request.POST if "submit_thread_form" in request.POST else None,
        profile=UserProfile.objects.get(user=request.user),
        prefix="create",
        )

    if create_form.is_valid():
        thread = create_form.save()
        return HttpResponseRedirect(reverse("threads:view_thread", kwargs={"pk": thread.pk}))
    elif request.method == "POST":
        messages.add_message(request, messages.ERROR, MESSAGES['THREAD_ERROR'])

    return render_to_response('list_threads.html', {
        'page_name': page_name,
        'threads': threads,
        "create_form": create_form,
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

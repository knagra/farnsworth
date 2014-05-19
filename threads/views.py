'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''

from django.shortcuts import render_to_response, render, get_object_or_404
from django.http import HttpResponseRedirect
from django import forms
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.contrib.auth import logout, login, authenticate, hashers
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta
from django.utils.timezone import utc
from django.contrib import messages

from farnsworth.settings import house, ADMINS, max_threads, max_messages, \
    home_max_announcements, home_max_threads
from utils.variables import ANONYMOUS_USERNAME, MESSAGES
from base.models import UserProfile
from base.decorators import profile_required, admin_required
from threads.models import Thread, Message
from threads.forms import *

@profile_required
def member_forums_view(request):
	''' Forums for current members. '''
	page_name = "Member Forums"
	userProfile = UserProfile.objects.get(user=request.user)
	thread_form = ThreadForm(request.POST or None)
	message_form = MessageForm(request.POST or None)

	if 'submit_thread_form' in request.POST:
		if thread_form.is_valid():
			subject = thread_form.cleaned_data['subject']
			body = thread_form.cleaned_data['body']
			thread = Thread(owner=userProfile, subject=subject, number_of_messages=1, active=True)
			thread.save()
			message = Message(body=body, owner=userProfile, thread=thread)
			message.save()
			return HttpResponseRedirect(reverse('member_forums'))
		else:
			messages.add_message(request, messages.ERROR, MESSAGES['THREAD_ERROR'])
	elif 'submit_message_form' in request.POST:
		if message_form.is_valid():
			thread_pk = message_form.cleaned_data['thread_pk']
			body = message_form.cleaned_data['body']
			thread = Thread.objects.get(pk=thread_pk)
			message = Message(body=body, owner=userProfile, thread=thread)
			message.save()
			thread.number_of_messages += 1
			thread.change_date = datetime.utcnow().replace(tzinfo=utc)
			thread.save()
			return HttpResponseRedirect(reverse('member_forums'))
		else:
			messages.add_message(request, messages.ERROR, MESSAGES['MESSAGE_ERROR'])
	elif request.method == 'POST':
		messages.add_message(request, messages.ERROR, MESSAGES['UNKNOWN_FORM'])
	x = 0 # number of threads loaded
	threads_dict = list()
	# A pseudo-dictionary, actually a list with items of form:
	# (thread.subject, [thread_messages_list], thread.pk, number_of_more_messages)
	for thread in Thread.objects.all():
		y = 0 # number of messages loaded
		thread_messages = list()
		for message in Message.objects.filter(thread=thread).reverse():
			thread_messages.append(message)
			y += 1
			if y >= max_messages:
				break
		more_messages = thread.number_of_messages - max_messages
		if more_messages < 0:
			more_messages = 0
		thread_messages.reverse()
		threads_dict.append((thread.subject, thread_messages, thread.pk, more_messages))
		x += 1
		if x >= max_threads:
			break
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
	thread_form = ThreadForm(request.POST or None)
	message_form = MessageForm(request.POST or None)

	if 'submit_thread_form' in request.POST:
		if thread_form.is_valid():
			subject = thread_form.cleaned_data['subject']
			body = thread_form.cleaned_data['body']
			thread = Thread(owner=userProfile, subject=subject, number_of_messages=1, active=True)
			thread.save()
			message = Message(body=body, owner=userProfile, thread=thread)
			message.save()
			return HttpResponseRedirect(reverse('all_threads'))
		else:
			messages.add_message(request, messages.ERROR, MESSAGES['THREAD_ERROR'])
	elif 'submit_message_form' in request.POST:
		if message_form.is_valid():
			thread_pk = message_form.cleaned_data['thread_pk']
			body = message_form.cleaned_data['body']
			thread = Thread.objects.get(pk=thread_pk)
			message = Message(body=body, owner=userProfile, thread=thread)
			message.save()
			thread.number_of_messages += 1
			thread.change_date = datetime.utcnow().replace(tzinfo=utc)
			thread.save()
			return HttpResponseRedirect(reverse('all_threads'))
		else:
			messages.add_message(request, messages.ERROR, MESSAGES['MESSAGE_ERROR'])
	elif request.method == 'POST':
		messages.add_message(request, messages.ERROR, MESSAGES['UNKNOWN_FORM'])
	# A pseudo-dictionary, actually a list with items of form
	# (thread.subject, [thread_messages_list], thread.pk, number_of_more_messages)
	threads_dict = list()
	for thread in Thread.objects.all():
		y = 0 # number of messages loaded
		thread_messages = list()
		for message in Message.objects.filter(thread=thread).reverse():
			thread_messages.append(message)
			y += 1
			if y >= max_messages:
				break
		more_messages = thread.number_of_messages - max_messages
		if more_messages < 0:
			more_messages = 0
		thread_messages.reverse()
		threads_dict.append((thread.subject, thread_messages, thread.pk, more_messages))
	return render_to_response('threads.html', {
			'page_name': page_name,
			'thread_title': 'Archives - All Threads',
			'threads_dict': threads_dict,
			'thread_form': thread_form,
			}, context_instance=RequestContext(request))

@profile_required
def my_threads_view(request):
	''' View of my threads. '''
	page_name = "My Threads"
	userProfile = UserProfile.objects.get(user=request.user)
	thread_form = ThreadForm(request.POST or None)
	message_form = MessageForm(request.POST or None)

	if 'submit_thread_form' in request.POST:
		if thread_form.is_valid():
			subject = thread_form.cleaned_data['subject']
			body = thread_form.cleaned_data['body']
			thread = Thread(owner=userProfile, subject=subject, number_of_messages=1, active=True)
			thread.save()
			message = Message(body=body, owner=userProfile, thread=thread)
			message.save()
			return HttpResponseRedirect(reverse('my_threads'))
		else:
			messages.add_message(request, messages.ERROR, MESSAGES['THREAD_ERROR'])
	elif 'submit_message_form' in request.POST:
		if message_form.is_valid():
			thread_pk = message_form.cleaned_data['thread_pk']
			body = message_form.cleaned_data['body']
			thread = Thread.objects.get(pk=thread_pk)
			message = Message(body=body, owner=userProfile, thread=thread)
			message.save()
			thread.number_of_messages += 1
			thread.change_date = datetime.utcnow().replace(tzinfo=utc)
			thread.save()
			return HttpResponseRedirect(reverse('my_threads'))
		else:
			messages.add_message(request, messages.ERROR, MESSAGES['MESSAGE_ERROR'])
	elif request.method == 'POST':
		messages.add_message(request, messages.ERROR, MESSAGES['UNKNOWN_FORM'])
	x = 0 # number of threads loaded
	# A pseudo-dictionary, actually a list with items of form:
	# (thread.subject, [thread_messages_list], thread.pk, number_of_more_messages)
	threads_dict = list()
	for thread in Thread.objects.filter(owner=userProfile):
		y = 0 # number of messages loaded
		thread_messages = list()
		for message in Message.objects.filter(thread=thread).reverse():
			thread_messages.append(message)
			y += 1
			if y >= max_messages:
				break
		more_messages = thread.number_of_messages - max_messages
		if more_messages < 0:
			more_messages = 0
		thread_messages.reverse()
		threads_dict.append((thread.subject, thread_messages, thread.pk, more_messages))
		x += 1
		if x >= max_threads:
			break
	return render_to_response('threads.html', {
			'page_name': page_name,
			'thread_title': 'My Threads',
			'threads_dict': threads_dict,
			'thread_form': thread_form,
			}, context_instance=RequestContext(request))

@profile_required
def list_my_threads_view(request):
	''' View of my threads. '''
	userProfile = UserProfile.objects.get(user=request.user)
	threads = Thread.objects.filter(owner=userProfile)
	return render_to_response('list_threads.html', {
			'page_name': "My Threads", 
			'threads': threads,
			}, context_instance=RequestContext(request))

@profile_required
def list_user_threads_view(request, targetUsername):
	''' View of my threads. '''
	if targetUsername == request.user.username:
		return list_my_threads_view(request)
	targetUser = get_object_or_404(User, username=targetUsername)
	targetProfile = get_object_or_404(UserProfile, user=targetUser)
	threads = Thread.objects.filter(owner=targetProfile)
	page_name = "%s's Threads" % targetUsername
	return render_to_response('list_threads.html', {
			'page_name': page_name,
			'threads': threads, 
			'targetUsername': targetUsername,
			}, context_instance=RequestContext(request))

@profile_required
def list_all_threads_view(request):
	''' View of my threads. '''
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
	message_form = MessageForm(request.POST or None, initial={
			'thread_pk': thread_pk,
			})
	if message_form.is_valid():
		thread_pk = message_form.cleaned_data['thread_pk']
		body = message_form.cleaned_data['body']
		thread = Thread.objects.get(pk=thread_pk)
		message = Message(body=body, owner=userProfile, thread=thread)
		message.save()
		thread.number_of_messages += 1
		thread.change_date = datetime.utcnow().replace(tzinfo=utc)
		thread.save()
		return HttpResponseRedirect(reverse('view_thread', kwargs={
					'thread_pk': thread_pk,
					}))
	elif request.method == 'POST':
		messages.add_message(request, messages.ERROR, MESSAGES['MESSAGE_ERROR'])
	return render_to_response('view_thread.html', {
			'thread': thread, 
			'page_name': "View Thread", 
			'messages_list': messages_list,
			}, context_instance=RequestContext(request))

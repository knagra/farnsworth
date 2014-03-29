'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''

from django.shortcuts import render_to_response, render
from django.http import HttpResponseRedirect
from django import forms
from django.core.urlresolvers import reverse
from django.template import RequestContext
from farnsworth.settings import house
from django.contrib.auth import logout, login, authenticate
from models import UserProfile, Message
import datetime

def red_ext(request, function_locals):
	'''
	Convenience function for redirecting users who don't have site access to the external page.
	Parameters:
		request - the request in the calling function
		function_locals - the output of locals() in the calling function
	'''
	return render_to_response('external.html', function_locals, context_instance=RequestContext(request))

def red_home(request, function_locals):
	'''
	Convenience function for redirecting users who don't have access to a page to the home page.
	Parameters:
		request - the request in the calling function
		function_locals - the output of locals() in the calling function
	'''
	return render_to_response('homepage.html', function_locals, context_instance=RequestContext(request))

def homepage_view(request):
	''' The view of the homepage. '''
	homepage = True
	pagename = "homepage"
	house_name = house
	if request.user.is_authenticated():
		user = request.user
		staff = user.is_staff
		return red_home(request, locals())
	else:
		user = None
		staff = False
		return red_ext(request, locals())

def external_view(request):
	''' The external landing. '''
	homepage = True
	pagename = "homepage"
	house_name = house
	if request.user.is_authenticated():
		user = request.user
		staff = user.is_staff
	else:
		user = None
		staff = False
	return red_ext(request, locals())

def help_view(request):
	''' The view of the helppage. '''
	pagename = "Help Page"
	house_name = house
	if request.user.is_authenticated():
		user = request.user
		staff = user.is_staff
	else:
		user = None
		staff = False
	return render_to_response('helppage.html', locals(), context_instance=RequestContext(request))

def login_view(request):
	''' The view of the login page. '''
	pagename = "Login Page"
	house_name = house
	if request.user.is_authenticated():
		return HttpResponseRedirect(reverse('homepage'))
	user = None
	staff = False
	class loginForm(forms.Form):
		username = forms.CharField(max_length=100)
		password = forms.CharField(max_length=100, widget=forms.PasswordInput())
	if request.method == 'POST':
		form = loginForm(request.POST)
		if form.is_valid():
			username = form.cleaned_data['username']
			password = form.cleaned_data['password']
			user = authenticate(username=username, password=password)
			if user is not None:
				if user.is_active:
					login(request, user)
					return HttpResponseRedirect(reverse('homepage'))
				else:
					non_field_error = "Your account is not active.  Please contact the site administrator to activate your account."
			else:
				non_field_error = "Invalid username/password combo"
	else:
		form = loginForm()
	return render(request, 'login.html', locals())

def logout_view(request):
	''' Log the user out. '''
	logout(request)
	return HttpResponseRedirect(reverse('homepage'))

def member_forums_view(request):
	''' Forums for current members. '''
	pagename = "Member Forums"
	house_name = house
	userProfile = None
	if request.user.is_authenticated():
		user = request.user
		staff = user.is_staff
		for profile in UserProfile.objects.all():
			if profile.user == user:
				userProfile = profile
				break
		if not userProfile:
			message = "A profile for you could not be found.  Please contact an admin for support."
			return red_ext(request, locals())
	else:
		user = None
		staff = False
		return red_ext(request, locals())
	if not userProfile.current_member:
		message = "These forums are reserved for current members only."
		return red_ext(request, locals())
	week_ago = datetime.now() - datetime.timedelta(days=7)
	active_messages = list()
	my_messages = list()
	for message in Message.objects.all():
		if week_ago < message.post_date:
			active_messages.append(message)
		if message.owner.user = user:
			my_messages.append(message)
	active_threads = list()
	my_threads = list()
	for message in active_messages:
		if message.thread not in active_threads:
			active_threads.append(message.thread)
	for message in my_messages:
		if message.thread not in my_threads:
			my_threads.append(message.thread)
	return render_to_response('member_forums.html', locals(), context_instance=RequestContext(request))

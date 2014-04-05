'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''

from django.shortcuts import render_to_response, render
from django.http import HttpResponseRedirect
from django import forms
from django.core.urlresolvers import reverse
from django.template import RequestContext
from farnsworth.settings import house, ADMINS
from django.contrib.auth import logout, login, authenticate, hashers
from models import UserProfile, Thread, Message
from django.utils import timezone
from django.contrib.auth.models import User
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
	pagename = "Home Page"
	house_name = house
	admin = ADMINS[0]
	if request.user.is_authenticated():
		user = request.user
		return red_home(request, locals())
	else:
		user = None
		return red_ext(request, locals())

def external_view(request):
	''' The external landing. '''
	homepage = True
	pagename = "External"
	admin = ADMINS[0]
	house_name = house
	if request.user.is_authenticated():
		user = request.user
	else:
		user = None
	return red_ext(request, locals())

def help_view(request):
	''' The view of the helppage. '''
	pagename = "Help Page"
	house_name = house
	admin = ADMINS[0]
	if request.user.is_authenticated():
		user = request.user
	else:
		user = None
	return render_to_response('helppage.html', locals(), context_instance=RequestContext(request))

def site_map_view(request):
	''' The view of the site map. '''
	pagename = "Site Map"
	house_name = house
	admin = ADMINS[0]
	if request.user.is_authenticated():
		user = request.user
	else:
		user = None
	return render_to_response('site_map.html', locals(), context_instance=RequestContext(request))

def my_profile_view(request):
	''' The view of the profile page. '''
	pagename = "Profile Page"
	house_name = house
	admin = ADMINS[0]
	if request.user.is_authenticated():
		user = request.user
		userProfile = user.get_profile()
		if not userProfile:
			message = "A profile for you could not be found.  Please contact an admin for support."
			return red_ext(request, locals())
	else:
		user = None
		userProfile = None
		homepage = True
		pagename = "External"
		return red_ext(request, locals())
	class ChangePasswordForm(forms.Form):
		current_password = forms.CharField(max_length=100, widget=forms.PasswordInput(attrs={'size':'50'}))
		new_password = forms.CharField(max_length=100, widget=forms.PasswordInput(attrs={'size':'50'}))
		confirm_password = forms.CharField(max_length=100, widget=forms.PasswordInput(attrs={'size':'50'}))
	class UpdateProfileForm(forms.Form):
		current_room = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}), required=False)
		former_rooms = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}), required=False)
		former_houses = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}), required=False)
		email = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'size':'50'}), required=False)
		email_visible_to_others = forms.BooleanField(required=False)
		phone_number = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'size':'50'}), required=False)
		phone_visible_to_others = forms.BooleanField(required=False)
		enter_password = forms.CharField(max_length=100, widget=forms.PasswordInput(attrs={'size':'50'}))
	change_password_form = ChangePasswordForm()
	update_profile_form = UpdateProfileForm(initial={'current_room': userProfile.current_room, 'former_rooms': userProfile.former_rooms, 'former_houses': userProfile.former_houses, 'email': user.email, 'email_visible_to_others': userProfile.email_visible, 'phone_number': userProfile.phone_number, 'phone_visible_to_others': userProfile.phone_visible})
	if request.method == 'POST':
		if 'submit_password_form' in request.POST:
			change_password_form = ChangePasswordForm(request.POST)
			if change_password_form.is_valid():
				current_password = change_password_form.cleaned_data['current_password']
				new_password = change_password_form.cleaned_data['new_password']
				confirm_password = change_password_form.cleaned_data['confirm_password']
				if hashers.check_password(current_password, user.password):
					if new_password == confirm_password:
						hashed_password = hashers.make_password(new_password)
						if hashers.is_password_usable(hashed_password):
							user.password = hashed_password
							user.save()
							password_non_field_error = "Your password has been changed."
							change_password_form = ChangePasswordForm()
						else:
							password_non_field_error = "Password didn't hash properly.  Please try again."
					else:
						change_password_form._errors['new_password'] = forms.util.ErrorList([u"Passwords don't match."])
						change_password_form._errors['confirm_password'] = forms.util.ErrorList([u"Passwords don't match."])
				else:
					change_password_form._errors['current_password'] = forms.util.ErrorList([u"Wrong password."])
		elif 'submit_profile_form' in request.POST:
			update_profile_form = UpdateProfileForm(request.POST)
			if update_profile_form.is_valid():
				current_room = update_profile_form.cleaned_data['current_room']
				former_rooms = update_profile_form.cleaned_data['former_rooms']
				former_houses = update_profile_form.cleaned_data['former_houses']
				email = update_profile_form.cleaned_data['email']
				email_visible_to_others = update_profile_form.cleaned_data['email_visible_to_others']
				phone_number = update_profile_form.cleaned_data['phone_number']
				phone_visible_to_others = update_profile_form.cleaned_data['phone_visible_to_others']
				enter_password = update_profile_form.cleaned_data['enter_password']
				if hashers.check_password(enter_password, user.password):
					userProfile.current_room = current_room
					userProfile.former_rooms = former_rooms
					userProfile.former_houses = former_houses
					user.email = email
					userProfile.email_visible = email_visible_to_others
					userProfile.phone_number = phone_number
					userProfile.phone_visible = phone_visible_to_others
					userProfile.save()
					profile_non_field_error = "Your profile has been updated."
					update_profile_form = UpdateProfileForm(initial={'current_room': userProfile.current_room, 'former_rooms': userProfile.former_rooms, 'email': user.email, 'email_visible_to_others': userProfile.email_visible, 'phone_number': userProfile.phone_number, 'phone_visible_to_others': userProfile.phone_visible})
				else:
					update_profile_form._errors['enter_password'] = forms.util.ErrorList([u"Wrong password"])
		else:
			pagename = "Home Page"
			message = "Your request at /profile/ could not be processed.  Please contact an admin for support."
			return red_home(request, locals())
	return render_to_response('my_profile.html', locals(), context_instance=RequestContext(request))

def login_view(request):
	''' The view of the login page. '''
	pagename = "Login Page"
	house_name = house
	admin = ADMINS[0]
	if request.user.is_authenticated():
		return HttpResponseRedirect(reverse('homepage'))
	user = None
	class loginForm(forms.Form):
		username = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}))
		password = forms.CharField(max_length=100, widget=forms.PasswordInput(attrs={'size':'50'}))
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
	admin = ADMINS[0]
	userProfile = None
	if request.user.is_authenticated():
		user = request.user
		userProfile = user.get_profile()
		if not userProfile:
			pagename = "Home Page"
			homepage = True
			message = "A profile for you could not be found.  Please contact an admin for support."
			return red_ext(request, locals())
	else:
		user = None
		pagename = "External"
		homepage = True
		return red_ext(request, locals())
	class ThreadForm(forms.Form):
		subject = forms.CharField(max_length=300, widget=forms.TextInput(attrs={'size':'100'}))
		body = forms.CharField(widget=forms.Textarea(attrs={'class':'thread'}))
	class MessageForm(forms.Form):
		thread_pk = forms.IntegerField()
		body = forms.CharField(widget=forms.Textarea(attrs={'class':'message'}))
	if request.method == 'POST':
		if 'submit_thread_form' in request.POST:
			thread_form = ThreadForm(request.POST)
			if thread_form.is_valid():
				subject = thread_form.cleaned_data['subject']
				body = thread_form.cleaned_data['body']
				thread = Thread(owner=userProfile, subject=subject, number_of_messages=0, active=True)
				thread.number_of_messages = 1
				thread.save()
				message = Message(body=body, owner=userProfile, thread=thread)
				message.save()
		elif 'submit_message_form' in request.POST:
			message_form = MessageForm(request.POST)
			if message_form.is_valid():
				thread_pk = message_form.cleaned_data['thread_pk']
				body = message_form.cleaned_data['body']
				thread = Thread.objects.get(pk=thread_pk)
				message = Message(body=body, owner=userProfile, thread=thread)
				message.save()
				thread.number_of_messages += 1
				thread.save()
		else:
			pagename = "Home Page"
			homepage = True
			message = "Your request at /member_forums/ could not be processed.  Please contact an admin for support."
			return red_home(request, locals())
	week_ago = timezone.now() - datetime.timedelta(days=7)
	active_messages = list()
	my_messages = list()
	for message in Message.objects.all():
		if week_ago < message.post_date:
			active_messages.append(message)
		if message.owner.user == user:
			my_messages.append(message)
	active_threads = list()
	my_threads = list()
	for message in active_messages:
		if message.thread not in active_threads:
			active_threads.append(message.thread)
	x = 0
	for message in my_messages:
		if x >= 10:
			break
		if message.thread not in my_threads:
			my_threads.append(message.thread)
			x +=1
	active_message_forms = list()
	my_message_forms = list()
	for thread in active_threads:
		form = MessageForm(initial={'thread_pk': thread.pk})
		form.fields['thread_pk'].widget = forms.HiddenInput()
		active_message_forms.append(form)
		for message in Message.objects.all():
			if (message not in active_messages) and (message.thread == thread):
				active_messages.append(message)
	for thread in my_threads:
		form = MessageForm(initial={'thread_pk': thread.pk})
		form.fields['thread_pk'].widget = forms.HiddenInput()
		my_message_forms.append(form)
		for message in Message.objects.all():
			if (message not in my_messages) and (message.thread == thread):
				my_messages.append(message)
	thread_form = ThreadForm()
	return render_to_response('member_forums.html', locals(), context_instance=RequestContext(request))

def all_threads_view(request):
	''' View of all threads. '''
	pagename = "All Threads"
	house_name = house
	admin = ADMINS[0]
	userProfile = None
	if request.user.is_authenticated():
		user = request.user
		userProfile = user.get_profile()
		if not userProfile:
			pagename = "Home Page"
			homepage = True
			message = "A profile for you could not be found.  Please contact an admin for support."
			return red_ext(request, locals())
	else:
		pagename = "External"
		homepage = True
		user = None
		return red_ext(request, locals())
	class ThreadForm(forms.Form):
		subject = forms.CharField(max_length=300, widget=forms.TextInput(attrs={'size':'100'}))
		body = forms.CharField(widget=forms.Textarea(attrs={'class':'thread'}))
	class MessageForm(forms.Form):
		thread_pk = forms.IntegerField()
		body = forms.CharField(widget=forms.Textarea(attrs={'class':'message'}))
	if request.method == 'POST':
		if 'submit_thread_form' in request.POST:
			thread_form = ThreadForm(request.POST)
			if thread_form.is_valid():
				subject = thread_form.cleaned_data['subject']
				body = thread_form.cleaned_data['body']
				thread = Thread(owner=userProfile, subject=subject, number_of_messages=0, active=True)
				thread.number_of_messages = 1
				thread.save()
				message = Message(body=body, owner=userProfile, thread=thread)
				message.save()
		elif 'submit_message_form' in request.POST:
			message_form = MessageForm(request.POST)
			if message_form.is_valid():
				thread_pk = message_form.cleaned_data['thread_pk']
				body = message_form.cleaned_data['body']
				thread = Thread.objects.get(pk=thread_pk)
				message = Message(body=body, owner=userProfile, thread=thread)
				message.save()
				thread.number_of_messages += 1
				thread.save()
		else:
			pagename = "Home Page"
			homepage = True
			message = "Your request at /all_threads/ could not be processed.  Please contact an admin for support."
			return red_home(request, locals())
	all_threads = Thread.objects.all()
	all_messages = Message.objects.all()
	message_forms = list()
	for thread in all_threads:
		form = MessageForm(initial={'thread_pk': thread.pk})
		form.fields['thread_pk'].widget = forms.HiddenInput()
		message_forms.append(form)
	thread_form = ThreadForm()
	return render_to_response('all_threads.html', locals(), context_instance=RequestContext(request))

def my_threads_view(request):
	''' View of my threads. '''
	pagename = "My Threads"
	house_name = house
	admin = ADMINS[0]
	userProfile = None
	if request.user.is_authenticated():
		user = request.user
		userProfile = user.get_profile()
		if not userProfile:
			pagename = "Home Page"
			homepage = True
			message = "A profile for you could not be found.  Please contact an admin for support."
			return red_ext(request, locals())
	else:
		pagename = "External"
		homepage = True
		user = None
		return red_ext(request, locals())
	class ThreadForm(forms.Form):
		subject = forms.CharField(max_length=300, widget=forms.TextInput(attrs={'size':'100'}))
		body = forms.CharField(widget=forms.Textarea(attrs={'class':'thread'}))
	class MessageForm(forms.Form):
		thread_pk = forms.IntegerField()
		body = forms.CharField(widget=forms.Textarea(attrs={'class':'message'}))
	if request.method == 'POST':
		if 'submit_thread_form' in request.POST:
			thread_form = ThreadForm(request.POST)
			if thread_form.is_valid():
				subject = thread_form.cleaned_data['subject']
				body = thread_form.cleaned_data['body']
				thread = Thread(owner=userProfile, subject=subject, number_of_messages=0, active=True)
				thread.number_of_messages = 1
				thread.save()
				message = Message(body=body, owner=userProfile, thread=thread)
				message.save()
		elif 'submit_message_form' in request.POST:
			message_form = MessageForm(request.POST)
			if message_form.is_valid():
				thread_pk = message_form.cleaned_data['thread_pk']
				body = message_form.cleaned_data['body']
				thread = Thread.objects.get(pk=thread_pk)
				message = Message(body=body, owner=userProfile, thread=thread)
				message.save()
				thread.number_of_messages += 1
				thread.save()
		else:
			pagename = "Home Page"
			homepage = True
			message = "Your request at /my_threads/ could not be processed.  Please contact an admin for support."
			return red_home(request, locals())
	my_messages = list()
	my_threads = list()
	message_forms = list()
	my_thread_messages = list()
	for message in Message.objects.all():
		if message.owner.user == user:
			my_messages.append(message)
	for message in my_messages:
		if message.thread not in my_threads:
			my_threads.append(message.thread)
	for thread in my_threads:
		form = MessageForm(initial={'thread_pk': thread.pk})
		form.fields['thread_pk'].widget = forms.HiddenInput()
		message_forms.append(form)
		for message in Message.objects.all():
			if (message not in my_thread_messages) and (message.thread == thread):
				my_thread_messages.append(message)
	thread_form = ThreadForm()
	return render_to_response('my_threads.html', locals(), context_instance=RequestContext(request))

def member_directory_view(request):
	''' View of member directory. '''
	pagename = "Member Directory"
	house_name = house
	admin = ADMINS[0]
	if request.user.is_authenticated():
		user = request.user
	else:
		pagename = "External"
		homepage = True
		user = None
		return red_ext(request, locals())
	residents = list()
	boarders = list()
	alumni = list()
	for profile in UserProfile.objects.all():
		if profile.status == UserProfile.RESIDENT:
			residents.append(profile)
		elif profile.status == UserProfile.BOARDER:
			boarderss.append(profile)
		elif profile.status == UserProfile.ALUMNUS:
			alumni.append(profile)
	return render_to_response('member_directory.html', locals(), context_instance=RequestContext(request))

def member_profile_view(request, targetUsername):
	''' View a member's Profile. '''
	pagename = "%s's Profile" % targetUsername
	house_name = house
	admin = ADMINS[0]
	userProfile = None
	if request.user.is_authenticated():
		user = request.user
		userProfile = user.get_profile()
	else:
		pagename = "External"
		homepage = True
		user = None
		return red_ext(request, locals())
	try:
		targetUser = User.objects.get(username=targetUsername)
	except:
		pagename = "User Not Found"
		message = "User %s does not exist or could not be found." % targetUsername
		return render_to_response('member_profile.html', locals(), context_instance=RequestContext(request))
	try:
		targetProfile = targetUser.get_profile()
	except:
		pagename = "Profile Not Found"
		message = "Profile for user %s could not be found." % targetUsername
		return render_to_response('member_profile.html', locals(), context_instance=RequestContext(request))
	if targetProfile == user.get_profile():
		return HttpResponseRedirect(reverse('my_profile'))
	else:
		return render_to_response('member_profile.html', locals(), context_instance=RequestContext(request))

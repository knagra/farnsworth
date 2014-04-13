'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''

from django.shortcuts import render_to_response, render
from django.http import HttpResponseRedirect
from django import forms
from django.core.urlresolvers import reverse
from django.template import RequestContext
from farnsworth.settings import house, ADMINS, max_threads, max_messages
from django.contrib.auth import logout, login, authenticate, hashers
from models import UserProfile, Thread, Message
from django.contrib.auth.models import User

def red_ext(request, message=None):
	'''
	The external landing.
	Also a convenience function for redirecting users who don't have site access to the external page.
	Parameters:
		request - the request in the calling function
		message - a message from the caller function
	'''
	if message:
		return render_to_response('external.html', {'message': message, 'house': house, 'admin': ADMINS[0], 'page_name': "External"}, context_instance=RequestContext(request))
	else:
		return render_to_response('external.html', {'house': house, 'admin': ADMINS[0], 'page_name': "External"}, context_instance=RequestContext(request))


def red_home(request, message):
	'''
	Convenience function for redirecting users who don't have access to a page to the home page.
	Parameters:
		request - the request in the calling function
		message - a message from the caller function
	'''
	return HttpResponseRedirect(reverse('member_forums'))
	#return render_to_response('homepage.html', function_locals, context_instance=RequestContext(request))

def homepage_view(request):
	''' The view of the homepage. '''
	if request.user.is_authenticated():
		return red_home(request, None)
	else:
		return red_ext(request, None)

def help_view(request):
	''' The view of the helppage. '''
	page_name = "Help Page"
	return render_to_response('helppage.html', {'house': house, 'page_name': page_name, 'admin': ADMINS[0]},  context_instance=RequestContext(request))

def site_map_view(request):
	''' The view of the site map. '''
	page_name = "Site Map"
	return render_to_response('site_map.html', {'house': house, 'page_name': page_name, 'admin': ADMINS[0]}, context_instance=RequestContext(request))

def my_profile_view(request):
	''' The view of the profile page. '''
	page_name = "Profile Page"
	if request.user.is_authenticated():
		user = request.user
		userProfile = request.user.get_profile()
		if not userProfile:
			message = "A profile for you could not be found.  Please contact an admin for support."
			return red_ext(request, message)
	else:
		return HttpResponseRedirect(reverse('login'))
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
							return HttpResponseRedirect(reverse('my_profile'))
							#change_password_form = ChangePasswordForm()
						else:
							password_non_field_error = "Password didn't hash properly.  Please try again."
							return render_to_response('my_profile.html', {'page_name': page_name, 'admin': ADMINS[0], 'house': house, 'update_profile_form': update_profile_form, 'change_password_form': change_password_form, 'password_non_field_error': password_non_field_error}, context_instance=RequestContext(request))
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
					return HttpResponseRedirect(reverse('my_profile'))
					#update_profile_form = UpdateProfileForm(initial={'current_room': userProfile.current_room, 'former_rooms': userProfile.former_rooms, 'email': user.email, 'email_visible_to_others': userProfile.email_visible, 'phone_number': userProfile.phone_number, 'phone_visible_to_others': userProfile.phone_visible})
					#return render_to_response('my_profile.html', {'page_name': page_name, 'admin': ADMINS[0], 'house': house, 'update_profile_form': update_profile_form, 'change_password_form': change_password_form, 'profile_non_field_error': profile_non_field_error}, context_instance=RequestContext(request))
				else:
					update_profile_form._errors['enter_password'] = forms.util.ErrorList([u"Wrong password"])
		else:
			message = "Your request at /profile/ could not be processed.  Please contact an admin for support."
			return red_home(request, message)
	return render_to_response('my_profile.html', {'page_name': page_name, 'admin': ADMINS[0], 'house': house, 'update_profile_form': update_profile_form, 'change_password_form': change_password_form}, context_instance=RequestContext(request))

def login_view(request):
	''' The view of the login page. '''
	page_name = "Login Page"
	non_field_error = None
	if request.user.is_authenticated():
		return HttpResponseRedirect(reverse('homepage'))
	class LoginForm(forms.Form):
		username = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}))
		password = forms.CharField(max_length=100, widget=forms.PasswordInput(attrs={'size':'50'}))
	if request.method == 'POST':
		form = LoginForm(request.POST)
		if form.is_valid():
			username = form.cleaned_data['username']
			password = form.cleaned_data['password']
			try:
				temp_user = User.objects.get(username=username)
				if temp_user is not None:
					if temp_user.is_active:
						user = authenticate(username=username, password=password)
						if user is not None:
							login(request, user)
							return HttpResponseRedirect(reverse('homepage'))
						else:
							non_field_error = "Invalid username/password combo"
					else:
						non_field_error = "Your account is not active.  Please contact the site administrator to activate your account."
			except:
				non_field_error = "User not found"
	else:
		form = LoginForm()
	if non_field_error:
		return render_to_response('login.html', {'page_name': page_name, 'admin': ADMINS[0], 'house': house, 'form': form, 'non_field_error': non_field_error}, context_instance=RequestContext(request))
	else:
		return render_to_response('login.html', {'page_name': page_name, 'admin': ADMINS[0], 'house': house, 'form': form}, context_instance=RequestContext(request))

def logout_view(request):
	''' Log the user out. '''
	logout(request)
	return HttpResponseRedirect(reverse('homepage'))

def member_forums_view(request):
	''' Forums for current members. '''
	page_name = "Member Forums"
	if request.user.is_authenticated():
		userProfile = request.user.get_profile()
		if not userProfile:
			message = "A profile for you could not be found.  Please contact an admin for support."
			return red_ext(request, message)
	else:
		return HttpResponseRedirect(reverse('login'))
	class ThreadForm(forms.Form):
		subject = forms.CharField(max_length=300, widget=forms.TextInput(attrs={'size':'100'}), required=False)
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
				return HttpResponseRedirect(reverse('member_forums'))
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
				return HttpResponseRedirect(reverse('member_forums'))
		else:
			message = "Your request at /member_forums/ could not be processed.  Please contact an admin for support."
			return red_home(request, message)
	x = 0 # number of threads loaded
	threads_dict = list() # A pseudo-dictionary, actually a list with items of form (thread.subject, [thread_messages_list], thread.pk)
	for thread in Thread.objects.all():
		thread_messages = Message.objects.filter(thread=thread)
		threads_dict.append((thread.subject, thread_messages, thread.pk))
		x += 1
		if x >= max_threads:
			break
	thread_form = ThreadForm()
	return render_to_response('member_forums.html', {'house': house, 'page_name': page_name, "thread_title": "Active Threads", 'admin': ADMINS[0], 'threads_dict': threads_dict, 'thread_form': thread_form}, context_instance=RequestContext(request))

def all_threads_view(request):
	''' View of all threads. '''
	page_name = "All Threads"
	if request.user.is_authenticated():
		userProfile = request.user.get_profile()
		if not userProfile:
			message = "A profile for you could not be found.  Please contact an admin for support."
			return red_ext(request, message)
	else:
		return HttpResponseRedirect(reverse('login'))
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
				return HttpResponseRedirect(reverse('all_threads'))
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
				return HttpResponseRedirect(reverse('all_threads'))
		else:
			message = "Your request at /all_threads/ could not be processed.  Please contact an admin for support."
			return red_home(request, message)
	all_threads = Thread.objects.all()
	all_messages = Message.objects.all()
	message_forms = list()
	for thread in all_threads:
		form = MessageForm(initial={'thread_pk': thread.pk})
		form.fields['thread_pk'].widget = forms.HiddenInput()
		message_forms.append(form)
	thread_form = ThreadForm()
	return render_to_response('member_forums.html', {'house': house, 'admin': ADMINS[0], 'page_name': page_name, "thread_title": "All Threads", 'threads': all_threads, 'messages': all_messages, 'message_forms': message_forms, 'thread_form': thread_form}, context_instance=RequestContext(request))

def my_threads_view(request):
	''' View of my threads. '''
	page_name = "My Threads"
	if request.user.is_authenticated():
		userProfile = request.user.get_profile()
		if not userProfile:
			message = "A profile for you could not be found.  Please contact an admin for support."
			return red_ext(request, message)
	else:
		return HttpResponseRedirect(reverse('login'))
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
				return HttpResponseRedirect(reverse('my_threads'))
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
				return HttpResponseRedirect(reverse('my_threads'))
		else:
			message = "Your request at /my_threads/ could not be processed.  Please contact an admin for support."
			return red_home(request, message)
	my_messages = list()
	my_threads = list()
	message_forms = list()
	my_thread_messages = list()
	for message in Message.objects.all():
		if message.owner.user == request.user:
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
	return render_to_response('my_threads.html', {'house': house, 'page_name': page_name, 'admin': ADMINS[0], 'my_messages': my_messages, 'my_threads': my_threads, 'message_forms': message_forms, 'my_thread_messages': my_thread_messages, 'thread_form': thread_form}, context_instance=RequestContext(request))

def member_directory_view(request):
	''' View of member directory. '''
	page_name = "Member Directory"
	if not request.user.is_authenticated():
		return HttpResponseRedirect(reverse('login'))
	residents = list()
	boarders = list()
	alumni = list()
	for profile in UserProfile.objects.all():
		if profile.status == UserProfile.RESIDENT:
			residents.append(profile)
		elif profile.status == UserProfile.BOARDER:
			boarders.append(profile)
		elif profile.status == UserProfile.ALUMNUS:
			alumni.append(profile)
	return render_to_response('member_directory.html', {'house': house, 'page_name': page_name, 'admin': ADMINS[0], 'residents': residents, 'boarders': boarders, 'alumni': alumni}, context_instance=RequestContext(request))

def member_profile_view(request, targetUsername):
	''' View a member's Profile. '''
	page_name = "%s's Profile" % targetUsername
	if request.user.is_authenticated():
		userProfile = request.user.get_profile()
	else:
		return HttpResponseRedirect(reverse('login'))
	try:
		targetUser = User.objects.get(username=targetUsername)
	except:
		page_name = "User Not Found"
		message = "User %s does not exist or could not be found." % targetUsername
		return render_to_response('member_profile.html', {'house': house, 'page_name': page_name, 'admin': ADMINS[0], 'message': message}, context_instance=RequestContext(request))
	try:
		targetProfile = targetUser.get_profile()
	except:
		page_name = "Profile Not Found"
		message = "Profile for user %s could not be found." % targetUsername
		return render_to_response('member_profile.html', {'house': house, 'page_name': page_name, 'admin': ADMINS[0], 'message': message}, context_instance=RequestContext(request))
	if targetProfile == request.user.get_profile():
		return HttpResponseRedirect(reverse('my_profile'))
	else:
		return render_to_response('member_profile.html', {'house': house, 'page_name': page_name, 'admin': ADMINS[0], 'targetUser': targetUser, 'targetProfile': targetProfile}, context_instance=RequestContext(request))

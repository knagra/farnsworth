'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''

from django.shortcuts import render_to_response, render
from django.http import HttpResponseRedirect
from django import forms
from django.core.urlresolvers import reverse
from django.contrib.auth import hashers, logout, login
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from farnsworth.settings import house, short_house, ADMINS, max_requests, max_responses, ANONYMOUS_USERNAME
# Stardard messages:
from farnsworth.settings import NO_PROFILE, ADMINS_ONLY, UNKNOWN_FORM, USER_ADDED, PREQ_DEL, USER_PROFILE_SAVED, USER_PW_CHANGED, ANONYMOUS_EDIT, ANONYMOUS_DENIED, ANONYMOUS_LOGIN, RECOUNTED
from models import Manager, RequestType, ProfileRequest, Request, Response, Announcement
from threads.models import UserProfile, Thread, Message
from threads.views import red_ext, red_home
from datetime import datetime
from django.utils.timezone import utc
from django.contrib import messages

def add_context(request):
	''' Add variables to all dictionaries passed to templates. '''
	return {'REQUEST_TYPES': RequestType.objects.filter(enabled=True), 'HOUSE': house, 'ANONYMOUS_USERNAME': ANONYMOUS_USERNAME, 'SHORT_HOUSE': short_house, 'ADMIN': ADMINS[0], 'NUM_OF_PROFILE_REQUESTS': ProfileRequest.objects.all().count()}

def request_profile_view(request):
	''' The page to request a user profile on the site. '''
	page_name = "Profile Request Page"
	if request.user.is_authenticated():
		return HttpResponseRedirect(reverse('homepage'))
	class ProfileRequestForm(forms.Form):
		username = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}))
		first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}))
		last_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}))
		email = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'size':'50'}))
		affiliation_with_the_house = forms.ChoiceField(choices=UserProfile.STATUS_CHOICES)
	if request.method == 'POST':
		form = ProfileRequestForm(request.POST)
		if form.is_valid():
			username = form.cleaned_data['username']
			first_name = form.cleaned_data['first_name']
			last_name = form.cleaned_data['last_name']
			email = form.cleaned_data['email']
			affiliation = form.cleaned_data['affiliation_with_the_house']
			for profile in UserProfile.objects.all():
				if profile.user.username == username:
					non_field_error = "This usename is taken.  Try one of %s_1 through %s_10." % (username, username)
					form.errors['__all__'] = form.error_class([non_field_error])
					return render(request, 'request_profile.html', {'page_name': page_name, 'form': form})
			profile_request = ProfileRequest(username=username, first_name=first_name, last_name=last_name, email=email, affiliation=affiliation)
			profile_request.save()
			messages.add_message(request, messages.SUCCESS, "Your request has been submitted.  An admin will contact you soon.")
			return HttpResponseRedirect(reverse('external'))
		else:
			return render(request, 'request_profile.html', {'form': form, 'page_name': page_name})
	else:
		form = ProfileRequestForm()
	return render(request, 'request_profile.html', {'form': form, 'page_name': page_name})

@login_required
def manage_profile_requests_view(request):
	''' The page to manager user profile requests. '''
	page_name = "Admin - Manage Profile Requests"
	if not request.user.is_superuser:
		return red_home(request, ADMINS_ONLY)
	profile_requests = ProfileRequest.objects.all()
	return render_to_response('manage_profile_requests.html', {'page_name': page_name, 'choices': UserProfile.STATUS_CHOICES, 'profile_requests': profile_requests}, context_instance=RequestContext(request))

@login_required
def modify_profile_request_view(request, request_pk):
	''' The page to modify a user's profile request. request_pk is the pk of the profile request. '''
	page_name = "Admin - Profile Request"
	if not request.user.is_superuser:
		return red_home(request, ADMINS_ONLY)
	profile_request = ProfileRequest.objects.get(pk=request_pk)
	class AddUserForm(forms.Form):
		username = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}))
		first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}))
		last_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}))
		email = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'size':'50'}))
		email_visible_to_others = forms.BooleanField(required=False)
		phone_number = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'size':'50'}))
		phone_visible_to_others = forms.BooleanField(required=False)
		status = forms.ChoiceField(choices=UserProfile.STATUS_CHOICES)
		current_room = forms.CharField(max_length=30, widget=forms.TextInput(attrs={'size':'50'}), required=False)
		former_rooms = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}), required=False)
		former_houses = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size': '50'}), required=False)
		is_active = forms.BooleanField(required=False)
		is_staff = forms.BooleanField(required=False)
		is_superuser = forms.BooleanField(required=False)
		groups = forms.ModelMultipleChoiceField(queryset=Group.objects.all(), required=False)
		user_password = forms.CharField(max_length=100, widget=forms.PasswordInput(attrs={'size':'50'}))
		confirm_password = forms.CharField(max_length=100, widget=forms.PasswordInput(attrs={'size':'50'}))
	add_user_form = AddUserForm(initial={'status': profile_request.affiliation, 'username': profile_request.username, 'first_name': profile_request.first_name, 'last_name': profile_request.last_name, 'email': profile_request.email})
	if request.method == 'POST':
		add_user_form = AddUserForm(request.POST)
		if 'delete_request' in request.POST:
			message = PREQ_DEL.format(first_name=profile_request.first_name, last_name=profile_request.last_name, username=profile_request.username)
			messages.add_message(request, messages.WARNING, message)
			profile_request.delete()
			return HttpResponseRedirect(reverse('manage_profile_requests'))
		elif 'add_user' in request.POST:
			if add_user_form.is_valid():
				username = add_user_form.cleaned_data['username']
				first_name = add_user_form.cleaned_data['first_name']
				last_name = add_user_form.cleaned_data['last_name']
				email = add_user_form.cleaned_data['email']
				email_visible_to_others = add_user_form.cleaned_data['email_visible_to_others']
				phone_number = add_user_form.cleaned_data['phone_number']
				phone_visible_to_others = add_user_form.cleaned_data['phone_visible_to_others']
				status = add_user_form.cleaned_data['status']
				current_room = add_user_form.cleaned_data['current_room']
				former_rooms = add_user_form.cleaned_data['former_rooms']
				former_houses = add_user_form.cleaned_data['former_houses']
				is_active = add_user_form.cleaned_data['is_active']
				is_staff = add_user_form.cleaned_data['is_staff']
				is_superuser = add_user_form.cleaned_data['is_superuser']
				groups = add_user_form.cleaned_data['groups']
				user_password = add_user_form.cleaned_data['user_password']
				confirm_password = add_user_form.cleaned_data['confirm_password']
				for usr in User.objects.all():
					if usr.username == username:
						non_field_error = "This username is taken.  Try one of %s_1 through %s_10." % (username, username)
						add_user_form.errors['__all__'] = add_user_form.error_class([non_field_error])
						return render(request, 'custom_add_user.html', {'page_name': page_name, 'add_user_form': add_user_form})
					if (usr.first_name == first_name) and (usr.last_name == last_name):
						non_field_error = "A profile for %s %s already exists with username %s." % (first_name, last_name, usr.username)
						add_user_form.errors['__all__'] = add_user_form.error_class([non_field_error])
						return render(request, 'custom_add_user.html', {'page_name': page_name, 'add_user_form': add_user_form})
				if user_password == confirm_password:
					new_user = User.objects.create_user(username=username, email=email, first_name=first_name, last_name=last_name, password=user_password)
					new_user.is_active = is_active
					new_user.is_staff = is_staff
					new_user.is_superuser = is_superuser
					new_user.save()
					for group in groups:
						group.user_set.add(new_user)
					new_user_profile = UserProfile.objects.get(user=new_user)
					new_user_profile.email_visible = email_visible_to_others
					new_user_profile.phone_number = phone_number
					new_user_profile.phone_visible = phone_visible_to_others
					new_user_profile.status = status
					new_user_profile.current_room = current_room
					new_user_profile.former_rooms = former_rooms
					new_user_profile.former_houses = former_houses
					new_user_profile.save()
					profile_request.delete()
					message = USER_ADDED.format(username=username)
					messages.add_message(request, messages.SUCCESS, message)
					return HttpResponseRedirect(reverse('manage_profile_requests'))
				else:
					add_user_form._errors['user_password'] = forms.util.ErrorList([u"Passwords don't match."])
					add_user_form._errors['confirm_password'] = forms.util.ErrorList([u"Passwords don't match."])
	return render_to_response('modify_profile_request.html', {'page_name': page_name, 'add_user_form': add_user_form}, context_instance=RequestContext(request))

@login_required
def custom_manage_users_view(request):
	page_name = "Admin - Manage Users"
	if not request.user.is_superuser:
		return red_home(request, ADMINS_ONLY)
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
	return render_to_response('custom_manage_users.html', {'page_name': page_name, 'residents': residents, 'boarders': boarders, 'alumni': alumni}, context_instance=RequestContext(request))

@login_required
def custom_modify_user_view(request, targetUsername):
	''' The page to modify a user. '''
	if targetUsername == ANONYMOUS_USERNAME:
		messages.add_message(request, messages.WARNING, ANONYMOUS_EDIT)
	page_name = "Admin - Modify User"
	if not request.user.is_superuser:
		return red_home(request, ADMINS_ONLY)
	try:
		targetUser = User.objects.get(username=targetUsername)
	except:
		page_name = "User Not Found"
		message = "User %s does not exist or could not be found." % targetUsername
		return render_to_response('custom_modify_user.html', {'page_name': page_name, 'message': message}, context_instance=RequestContext(request))
	try:
		targetProfile = UserProfile.objects.get(user=targetUser)
	except:
		page_name = "Profile Not Found"
		message = "Profile for user %s could not be found." % targetUsername
		return render_to_response('custom_modify_user.html', {'page_name': page_name, 'message': message}, context_instance=RequestContext(request))	
	class ModifyUserForm(forms.Form):
		first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}))
		last_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}))
		email = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'size':'50'}), required=False)
		email_visible_to_others = forms.BooleanField(required=False)
		phone_number = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'size':'50'}))
		phone_visible_to_others = forms.BooleanField(required=False)
		status = forms.ChoiceField(choices=UserProfile.STATUS_CHOICES)
		current_room = forms.CharField(max_length=30, widget=forms.TextInput(attrs={'size':'50'}), required=False)
		former_rooms = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}), required=False)
		former_houses = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}), required=False)
		is_active = forms.BooleanField(required=False)
		is_staff = forms.BooleanField(required=False)
		is_superuser = forms.BooleanField(required=False)
		groups = forms.ModelMultipleChoiceField(queryset=Group.objects.all(), required=False)
	class ChangeUserPasswordForm(forms.Form):
		user_password = forms.CharField(max_length=100, widget=forms.PasswordInput(attrs={'size':'50'}))
		confirm_password = forms.CharField(max_length=100, widget=forms.PasswordInput(attrs={'size':'50'}))
	groups_dict = {}
	for grp in Group.objects.all():
		if grp in targetUser.groups.all():
			groups_dict[grp.id] = True
	modify_user_form = ModifyUserForm(initial={'first_name': targetUser.first_name, 'last_name': targetUser.last_name, 'email': targetUser.email, 'email_visible_to_others': targetProfile.email_visible, 'phone_number': targetProfile.phone_number, 'phone_visible_to_others': targetProfile.phone_visible, 'status': targetProfile.status, 'current_room': targetProfile.current_room, 'former_rooms': targetProfile.former_rooms, 'former_houses': targetProfile.former_houses, 'is_active': targetUser.is_active, 'is_staff': targetUser.is_staff, 'is_superuser': targetUser.is_superuser, 'groups': groups_dict})
	change_user_password_form = ChangeUserPasswordForm()
	if request.method == 'POST':
		if 'update_user_profile' in request.POST:
			modify_user_form = ModifyUserForm(request.POST)
			if modify_user_form.is_valid():
				first_name = modify_user_form.cleaned_data['first_name']
				last_name = modify_user_form.cleaned_data['last_name']
				email = modify_user_form.cleaned_data['email']
				email_visible_to_others = modify_user_form.cleaned_data['email_visible_to_others']
				phone_number = modify_user_form.cleaned_data['phone_number']
				phone_visible_to_others = modify_user_form.cleaned_data['phone_visible_to_others']
				status = modify_user_form.cleaned_data['status']
				current_room = modify_user_form.cleaned_data['current_room']
				former_rooms = modify_user_form.cleaned_data['former_rooms']
				former_houses = modify_user_form.cleaned_data['former_houses']
				is_active = modify_user_form.cleaned_data['is_active']
				is_staff = modify_user_form.cleaned_data['is_staff']
				is_superuser = modify_user_form.cleaned_data['is_superuser']
				groups = modify_user_form.cleaned_data['groups']
				targetUser.first_name = first_name
				targetUser.last_name = last_name
				targetUser.email = email
				targetUser.is_active = is_active
				targetUser.is_staff = is_staff
				targetUser.is_superuser = is_superuser
				targetUser.save()
				for group in groups:
					group.user_set.add(targetUser)
				targetProfile.email_visible = email_visible_to_others
				targetProfile.phone_number = phone_number
				targetProfile.phone_visible = phone_visible_to_others
				targetProfile.status = status
				targetProfile.current_room = current_room
				targetProfile.former_rooms = former_rooms
				targetProfile.former_houses = former_houses
				targetProfile.save()
				message = USER_PROFILE_SAVED.format(username=targetUser.username)
				messages.add_message(request, messages.SUCCESS, message)
				return HttpResponseRedirect(reverse('custom_modify_user', kwargs={'targetUsername': targetUsername}))
		elif 'change_user_password' in request.POST:
			change_user_password_form = ChangeUserPasswordForm(request.POST)
			if change_user_password_form.is_valid():
				user_password = change_user_password_form.cleaned_data['user_password']
				confirm_password = change_user_password_form.cleaned_data['confirm_password']
				if user_password == confirm_password:
					hashed_password = hashers.make_password(user_password)
					if hashers.is_password_usable(hashed_password):
						targetUser.password = hashed_password
						targetUser.save()
						message = USER_PW_CHANGED.format(username=targetUser.username)
						messages.add_message(request, messages.SUCCESS, message)
						return HttpResponseRedirect(reverse('custom_modify_user', kwargs={'targetUsername': targetUsername}))
					else:
						error = "Could not hash password.  Please try again."
						change_user_password_form.errors['__all__'] = change_user_password_form.error_class([error])
				else:
					change_user_password_form._errors['user_password'] = forms.util.ErrorList([u"Passwords don't match"])
					change_user_password_form._errors['confirm_password'] = forms.util.ErrorList([u"Passwords don't match"])
	return render_to_response('custom_modify_user.html', {'targetUser': targetUser, 'targetProfile': targetProfile, 'page_name': page_name, 'modify_user_form': modify_user_form, 'change_user_password_form': change_user_password_form}, context_instance=RequestContext(request))

@login_required
def custom_add_user_view(request):
	''' The page to add a new user. '''
	page_name = "Admin - Add User"
	if not request.user.is_superuser:
		return red_home(request, ADMINS_ONLY)
	class AddUserForm(forms.Form):
		username = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}))
		first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}))
		last_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}))
		email = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'size':'50'}), required=False)
		email_visible_to_others = forms.BooleanField(required=False)
		phone_number = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'size':'50'}))
		phone_visible_to_others = forms.BooleanField(required=False)
		status = forms.ChoiceField(choices=UserProfile.STATUS_CHOICES)
		current_room = forms.CharField(max_length=30, widget=forms.TextInput(attrs={'size':'50'}), required=False)
		former_rooms = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}), required=False)
		former_houses = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size': '50'}), required=False)
		is_active = forms.BooleanField(required=False)
		is_staff = forms.BooleanField(required=False)
		is_superuser = forms.BooleanField(required=False)
		groups = forms.ModelMultipleChoiceField(queryset=Group.objects.all(), required=False)
		user_password = forms.CharField(max_length=100, widget=forms.PasswordInput(attrs={'size':'50'}))
		confirm_password = forms.CharField(max_length=100, widget=forms.PasswordInput(attrs={'size':'50'}))
	if request.method == 'POST':
		add_user_form = AddUserForm(request.POST)
		if add_user_form.is_valid():
			username = add_user_form.cleaned_data['username']
			first_name = add_user_form.cleaned_data['first_name']
			last_name = add_user_form.cleaned_data['last_name']
			email = add_user_form.cleaned_data['email']
			email_visible_to_others = add_user_form.cleaned_data['email_visible_to_others']
			phone_number = add_user_form.cleaned_data['phone_number']
			phone_visible_to_others = add_user_form.cleaned_data['phone_visible_to_others']
			status = add_user_form.cleaned_data['status']
			current_room = add_user_form.cleaned_data['current_room']
			former_rooms = add_user_form.cleaned_data['former_rooms']
			former_houses = add_user_form.cleaned_data['former_houses']
			is_active = add_user_form.cleaned_data['is_active']
			is_staff = add_user_form.cleaned_data['is_staff']
			is_superuser = add_user_form.cleaned_data['is_superuser']
			groups = add_user_form.cleaned_data['groups']
			user_password = add_user_form.cleaned_data['user_password']
			confirm_password = add_user_form.cleaned_data['confirm_password']
			for usr in User.objects.all():
				if usr.username == username:
					non_field_error = "This username is taken.  Try one of %s_1 through %s_10." % (username, username)
					add_user_form.errors['__all__'] = add_user_form.error_class([non_field_error])
					return render(request, 'custom_add_user.html', {'page_name': page_name, 'add_user_form': add_user_form})
				if (usr.first_name == first_name) and (usr.last_name == last_name):
					non_field_error = "A profile for %s %s already exists with username %s." % (first_name, last_name, usr.username)
					add_user_form.errors['__all__'] = add_user_form.error_class([non_field_error])
					return render(request, 'custom_add_user.html', {'page_name': page_name, 'add_user_form': add_user_form})
			if user_password == confirm_password:
				new_user = User.objects.create_user(username=username, email=email, first_name=first_name, last_name=last_name, password=user_password)
				new_user.is_active = is_active
				new_user.is_staff = is_staff
				new_user.is_superuser = is_superuser
				new_user.save()
				for group in groups:
					group.user_set.add(new_user)
				new_user_profile = UserProfile.objects.get(user=new_user)
				new_user_profile.email_visible = email_visible_to_others
				new_user_profile.phone_number = phone_number
				new_user_profile.phone_visible = phone_visible_to_others
				new_user_profile.status = status
				new_user_profile.current_room = current_room
				new_user_profile.former_rooms = former_rooms
				new_user_profile.former_houses = former_houses
				message = USER_ADDED.format(username=username)
				messages.add_message(request, messages.SUCCESS, message)
				return HttpResponseRedirect(reverse('custom_add_user'))
			else:
				add_user_form._errors['user_password'] = forms.util.ErrorList([u"Passwords don't match."])
				add_user_form._errors['confirm_password'] = forms.util.ErrorList([u"Passwords don't match."])
	else:
		add_user_form = AddUserForm(initial={'status': UserProfile.RESIDENT})
	return render_to_response('custom_add_user.html', {'page_name': page_name, 'add_user_form': add_user_form}, context_instance=RequestContext(request))

@login_required
def utilities_view(request):
	''' View for an admin to do maintenance tasks on the site. '''
	if not request.user.is_superuser:
		return red_home(request, ADMINS_ONLY)
	logout_url = request.build_absolute_uri(reverse('logout'))
	return render_to_response('utilities.html', {'page_name': "Site Utilities", 'logout_url': logout_url}, context_instance=RequestContext(request))

@login_required
def anonymous_login_view(request):
	''' View for an admin to log her/himself out and login the anonymous user. '''
	if not request.user.is_superuser:
		return red_home(request, ANONYMOUS_DENIED)
	logout(request)
	try:
		spineless = User.objects.get(username=ANONYMOUS_USERNAME)
	except:
		random_password = User.objects.make_random_password()
		spineless = User.objects.create_user(username=ANONYMOUS_USERNAME, first_name="Anonymous", last_name="Coward", password=random_password)
		spineless.is_active = False
		spineless.save()
		spineless_profile = UserProfile.objects.get(user=spineless)
		spineless_profile.status = UserProfile.ALUMNUS
		spineless_profile.save()
	spineless.backend = 'django.contrib.auth.backends.ModelBackend'
	login(request, spineless)
	messages.add_message(request, messages.INFO, ANONYMOUS_LOGIN)
	return HttpResponseRedirect(reverse('homepage'))

@login_required
def recount_view(request):
	''' Recount number_of_messages for all threads and number_of_responses for all requests. '''
	if not request.user.is_superuser:
		return red_home(request, ADMINS_ONLY)
	for req in Request.objects.all():
		req.number_of_responses = Response.objects.filter(request=req).count()
		req.save()
	for thread in Thread.objects.all():
		thread.number_of_messages = Message.objects.filter(thread=thread).count()
		thread.save()
	messages.add_message(request, messages.SUCCESS, RECOUNTED)
	return HttpResponseRedirect(reverse('utilities'))

@login_required
def requests_view(request, requestType):
	'''
	Generic request view.  Parameters:
		request is the HTTP request
		requestType is name of a RequestType.
			e.g. "food", "maintenance", "network", "site" 
	'''
	try:
		userProfile = UserProfile.objects.get(user=request.user)
	except:
		return red_home(request, NO_PROFILE)
	try:
		request_type = RequestType.objects.get(name=requestType)
	except:
		message = "No request type '%s' found." % requestType
		return red_home(request, message)
		#return render_to_response('requests.html', {'page_name': 'Invalid Request Type', 'invalid_request_type': True}, context_instance=RequestContext(request))
	page_name = "%s Requests" % request_type.human_readable_name().title()
	if not request_type.enabled:
		message = "%s requests have been disabled." % request_type.human_readable_name().title()
		return red_home(request, message)
		#return render_to_response('requests.html', {'page_name': page_name, 'request_disabled': True}, context_instance=RequestContext(request))
	relevant_managers = request_type.managers.all()
	manager = False #if the user is a relevant manager
	for position in relevant_managers:
		if position.incumbent == userProfile:
			manager = True
			break
	class RequestForm(forms.Form):
		body = forms.CharField(widget=forms.Textarea())
	if manager:
		class ResponseForm(forms.Form):
			request_pk = forms.IntegerField()
			body = forms.CharField(widget=forms.Textarea(), required=False)
			mark_filled = forms.BooleanField(required=False)
			mark_closed = forms.BooleanField(required=False)
	else:
		class ResponseForm(forms.Form):
			request_pk = forms.IntegerField()
			body = forms.CharField(widget=forms.Textarea())
	if request.method == 'POST':
		if 'submit_request' in request.POST:
			request_form = RequestForm(request.POST)
			if request_form.is_valid():
				body = request_form.cleaned_data['body']
				new_request = Request(owner=userProfile, body=body, request_type=request_type)
				new_request.save()
				return HttpResponseRedirect(reverse('requests', kwargs={'requestType': requestType}))
		elif 'add_response' in request.POST:
			response_form = ResponseForm(request.POST)
			if response_form.is_valid():
				request_pk = response_form.cleaned_data['request_pk']
				body = response_form.cleaned_data['body']
				relevant_request = Request.objects.get(pk=request_pk)
				new_response = Response(owner=userProfile, body=body, request=relevant_request)
				if manager:
					mark_filled = response_form.cleaned_data['mark_filled']
					mark_closed = response_form.cleaned_data['mark_closed']
					relevant_request.closed = mark_closed
					relevant_request.filled = mark_filled
					new_response.manager = True
				relevant_request.change_date = datetime.utcnow().replace(tzinfo=utc)
				relevant_request.save()
				new_response.save()
				return HttpResponseRedirect(reverse('requests', kwargs={'requestType': requestType}))
		else:
			return red_home(request, UNKNOWN_FORM)
	request_form = RequestForm()
	x = 0 # number of requests loaded
	requests_dict = list() # A pseudo-dictionary, actually a list with items of form (request, [request_responses_list])
	for req in Request.objects.filter(request_type=request_type):
		request_responses = Response.objects.filter(request=req)
		if manager:
			form = ResponseForm(initial={'request_pk': req.pk, 'mark_filled': req.filled, 'mark_closed': req.closed})
		else:
			form = ResponseForm(initial={'request_pk': req.pk})
		form.fields['request_pk'].widget = forms.HiddenInput()
		requests_dict.append((req, request_responses, form))
		x += 1
		if x >= max_requests:
			break
	return render_to_response('requests.html', {'manager': manager, 'request_type': request_type.human_readable_name(), 'page_name': page_name, 'request_form': request_form, 'requests_dict': requests_dict}, context_instance=RequestContext(request))

@login_required
def my_requests_view(request):
	'''
	Show user his/her requests, sorted by request_type.
	'''
	page_name = "My Requests"
	try:
		userProfile = UserProfile.objects.get(user=request.user)
	except:
		return red_home(request, NO_PROFILE)
	class RequestForm(forms.Form):
		type_pk = forms.IntegerField()
		body = forms.CharField(widget=forms.Textarea())
	class ResponseForm(forms.Form):
		request_pk = forms.IntegerField()
		body = forms.CharField(widget=forms.Textarea())
		mark_filled = forms.BooleanField(required=False)
		mark_closed = forms.BooleanField(required=False)
	if request.method == 'POST':
		if 'submit_request' in request.POST:
			request_form = RequestForm(request.POST)
			if request_form.is_valid():
				type_pk = request_form.cleaned_data['type_pk']
				body = request_form.cleaned_data['body']
				try:
					request_type = RequestType.objects.get(pk=type_pk)
				except:
					message = "The request type was not recognized.  Please contact an admin for support."
					return red_home(request, message)
				new_request = Request(owner=userProfile, body=body, request_type=request_type)
				new_request.save()
				return HttpResponseRedirect(reverse('my_requests'))
		elif 'add_response' in request.POST:
			response_form = ResponseForm(request.POST)
			if response_form.is_valid():
				request_pk = response_form.cleaned_data['request_pk']
				body = response_form.cleaned_data['body']
				relevant_request = Request.objects.get(pk=request_pk)
				new_response = Response(owner=userProfile, body=body, request=relevant_request)
				for manager_position in relevant_request.request_type.managers.all():
					if manager_position.incumbent == userProfile:
						mark_filled = response_form.cleaned_data['mark_filled']
						mark_closed = response_form.cleaned_data['mark_closed']
						relevant_request.filled = mark_filled
						relevant_request.closed = mark_closed
						relevant_request.change_date = datetime.utcnow().replace(tzinfo=utc)
						relevant_request.save()
						new_response.manager = True
						break
				new_response.save()
		else:
			return red_home(request, UNKNOWN_FORM)
	my_requests = Request.objects.filter(owner=userProfile)
	request_dict = list() # A pseudo dictionary, actually a list with items of form (request_type.human_readable_name, request_form, type_manager, [(request, [list_of_request_responses], response_form),...])
	for request_type in RequestType.objects.all():
		if request_type.enabled:
			type_manager = False
			for position in request_type.managers.all():
				if position.incumbent == userProfile:
					type_manager = True
					break
			requests_list = list() # Items are of form (request, [list_of_request_responses], response_form),...])
			type_requests = my_requests.filter(request_type=request_type)
			for req in type_requests:
				responses_list = Response.objects.filter(request=req)
				if type_manager:
					form = ResponseForm(initial={'request_pk': req.pk, 'mark_filled': req.filled, 'mark_closed': req.closed})
				else:
					form = ResponseForm(initial={'request_pk': req.pk})
					form.fields['mark_filled'].widget = forms.HiddenInput()
					form.fields['mark_closed'].widget = forms.HiddenInput()
				form.fields['request_pk'].widget = forms.HiddenInput()
				requests_list.append((req, responses_list, form))
			request_form = RequestForm(initial={'type_pk': request_type.pk})
			request_form.fields['type_pk'].widget = forms.HiddenInput()
			request_dict.append((request_type.human_readable_name(), request_form, type_manager, requests_list))
	return render_to_response('my_requests.html', {'page_name': page_name, 'request_dict': request_dict}, context_instance=RequestContext(request))

@login_required
def list_my_requests_view(request):
	'''
	Show user his/her requests in list form.
	'''
	page_name = "My Requests"
	try:
		userProfile = UserProfile.objects.get(user=request.user)
	except:
		return red_home(request, NO_PROFILE)
	requests = Request.objects.filter(owner=userProfile)
	return render_to_response('list_requests.html', {'page_name': page_name, 'requests': requests}, context_instance=RequestContext(request))

@login_required
def list_user_requests_view(request, targetUsername):
	'''
	Show user his/her requests in list form.
	'''
	if targetUsername == request.user.username:
		return list_my_requests_view(request)
	try:
		targetUser = User.objects.get(username=targetUsername)
		targetProfile = UserProfile.objects.get(user=targetUser)
	except:
		return render_to_response('list_requests.html', {'page_name': "User Not Found"}, context_instance=RequestContext(request))
	page_name = "%s's Requests" % targetUsername
	requests = Request.objects.filter(owner=targetProfile)
	return render_to_response('list_requests.html', {'page_name': page_name, 'requests': requests}, context_instance=RequestContext(request))

@login_required
def list_all_requests_view(request, requestType):
	'''
	Show user his/her requests in list form.
	'''
	page_name = "My Requests"
	try:
		request_type = RequestType.objects.get(name=requestType)
	except:
		return render_to_response('list_request.html', {'page_name': "Request Type Not Found"}, context_instance=RequestContext(request))
	requests = Request.objects.filter(request_type=request_type)
	return render_to_response('list_requests.html', {'page_name': page_name, 'requests': requests}, context_instance=RequestContext(request))

@login_required
def announcements_view(request):
	''' The view of manager announcements. '''
	page_name = "Manager Announcements"
	userProfile = None
	try:
		userProfile = UserProfile.objects.get(user=request.user)
	except:
		return red_home(request, NO_PROFILE)
	announcement_form = None
	manager_positions = Manager.objects.filter(incumbent=userProfile)
	if manager_positions:
		class AnnouncementForm(forms.Form):
			as_manager = forms.ModelChoiceField(queryset=manager_positions)
			body = forms.CharField(widget=forms.Textarea())
		class UnpinForm(forms.Form):
			announcement_pk = forms.IntegerField()
		announcement_form = AnnouncementForm(initial={'as_manager': manager_positions[0].pk})
	if request.method == 'POST':
		if 'unpin' in request.POST:
			unpin_form = UnpinForm(request.POST)
			if unpin_form.is_valid():
				announcement_pk = unpin_form.cleaned_data['announcement_pk']
				relevant_announcement = Announcement.objects.get(pk=announcement_pk)
				relevant_announcement.pinned = False
				relevant_announcement.save()
				return HttpResponseRedirect(reverse('announcements'))
		elif 'post_announcement' in request.POST:
			announcement_form = AnnouncementForm(request.POST)
			if announcement_form.is_valid():
				body = announcement_form.cleaned_data['body']
				manager = announcement_form.cleaned_data['as_manager']
				new_announcement = Announcement(manager=manager, body=body, incumbent=userProfile, pinned=True)
				new_announcement.save()
				return HttpResponseRedirect(reverse('announcements'))
	announcements = Announcement.objects.filter(pinned=True)
	announcements_dict = list() # A pseudo-dictionary, actually a list with items of form (announcement, announcement_unpin_form)
	for a in announcements:
		unpin_form = None
		if (a.manager.incumbent == userProfile) or request.user.is_superuser:
			unpin_form = UnpinForm(initial={'announcement_pk': a.pk})
			unpin_form.fields['announcement_pk'].widget = forms.HiddenInput()
		announcements_dict.append((a, unpin_form))
	return render_to_response('announcements.html', {'page_name': page_name, 'manager_positions': manager_positions, 'announcements_dict': announcements_dict, 'announcement_form': announcement_form}, context_instance=RequestContext(request))

@login_required
def all_announcements_view(request):
	''' The view of manager announcements. '''
	page_name = "Archives - All Announcements"
	try:
		userProfile = UserProfile.objects.get(user=request.user)
	except:
		return red_home(request, NO_PROFILE)
	announcement_form = None
	manager_positions = Manager.objects.filter(incumbent=userProfile)
	if manager_positions:
		class AnnouncementForm(forms.Form):
			as_manager = forms.ModelChoiceField(queryset=manager_positions)
			body = forms.CharField(widget=forms.Textarea())
		class UnpinForm(forms.Form):
			announcement_pk = forms.IntegerField()
		class RepinForm(forms.Form):
			announcement_pk = forms.IntegerField()
		announcement_form = AnnouncementForm(initial={'as_manager': manager_positions[0].pk})
	if request.method == 'POST':
		if 'unpin' in request.POST:
			unpin_form = UnpinForm(request.POST)
			if unpin_form.is_valid():
				announcement_pk = unpin_form.cleaned_data['announcement_pk']
				relevant_announcement = Announcement.objects.get(pk=announcement_pk)
				if relevant_announcement.pinned:
					relevant_announcement.pinned = False
				else:
					relevant_announcement.pinned = True
				relevant_announcement.save()
				return HttpResponseRedirect(reverse('all_announcements'))
		elif ('post_announcement' in request.POST) and manager_positions:
			announcement_form = AnnouncementForm(request.POST)
			if announcement_form.is_valid():
				body = announcement_form.cleaned_data['body']
				manager = announcement_form.cleaned_data['as_manager']
				new_announcement = Announcement(manager=manager, body=body, incumbent=userProfile, pinned=True)
				new_announcement.save()
				return HttpResponseRedirect(reverse('all_announcements'))
	announcements = Announcement.objects.all()
	announcements_dict = list() # A pseudo-dictionary, actually a list with items of form (announcement, announcement_pin_form)
	for a in announcements:
		form = None
		if ((a.manager.incumbent == userProfile) or request.user.is_superuser) and not a.pinned:
			form = UnpinForm(initial={'announcement_pk': a.pk})
			form.fields['announcement_pk'].widget = forms.HiddenInput()
		elif ((a.manager.incumbent == userProfile) or request.user.is_superuser) and a.pinned:
			form = UnpinForm(initial={'announcement_pk': a.pk})
			form.fields['announcement_pk'].widget = forms.HiddenInput()
		announcements_dict.append((a, form))
	return render_to_response('announcements.html', {'page_name': page_name, 'manager_positions': manager_positions, 'announcements_dict': announcements_dict, 'announcement_form': announcement_form}, context_instance=RequestContext(request))

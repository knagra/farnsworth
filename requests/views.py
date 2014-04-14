'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''

from django.shortcuts import render_to_response, render
from django.http import HttpResponseRedirect
from django import forms
from django.core.urlresolvers import reverse
from django.contrib.auth import hashers
from django.contrib.auth.models import User, Group
from django.template import RequestContext
from farnsworth.settings import house, ADMINS, max_requests, max_responses
from models import Manager, RequestType, ProfileRequest, Request, Response
from threads.models import UserProfile
from threads.views import red_ext, red_home

def add_context(request):
	''' Add variables to all dictionaries passed to templates. '''
	return {'REQUEST_TYPES': RequestType.objects.filter(enabled=True), 'HOUSE': house, 'ADMIN': ADMINS[0]}

def request_profile_view(request):
	''' The page to request a user profile on the site. '''
	page_name = "Profile Request Page"
	if request.user.is_authenticated():
		return HttpResponseRedirect(reverse('homepage'))
	class profileRequestForm(forms.Form):
		username = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}))
		first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}))
		last_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}))
		email = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'size':'50'}))
		affiliation_with_the_house = forms.ChoiceField(choices=UserProfile.STATUS_CHOICES)
	if request.method == 'POST':
		form = profileRequestForm(request.POST)
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
			profile_request = ProfileRequest(username=username, first_name=first_name, last_name=last_name, email=email, approved=False, affiliation=affiliation)
			profile_request.save()
			return HttpResponseRedirect(reverse('external'))
		else:
			return render(request, 'request_profile.html', {'form': form, 'page_name': page_name})

	else:
		form = profileRequestForm()
	return render(request, 'request_profile.html', {'form': form, 'page_name': page_name})

def manage_profile_requests_view(request):
	''' The page to manager user profile requests. '''
	page_name = "Admin - Manage Profile Requests"
	if request.user.is_authenticated():
		if not request.user.is_superuser:
			message = "The page /custom_admin/manage_profile_requests/ is restricted to superadmins."
			return red_home(request, message)
	else:
		return HttpResponseRedirect(reverse('login'))
	profile_requests = ProfileRequest.objects.all()
	return render_to_response('manage_profile_requests.html', {'page_name': page_name, 'profile_requests': profile_requests}, context_instance=RequestContext(request))

def custom_manage_users_view(request):
	page_name = "Admin - Manage Users"
	if request.user.is_authenticated():
		print request.user.is_superuser
		if not request.user.is_superuser:
			message = "The page /custom_admin/manage_users/ is restrcited to superadmins."
			return red_home(request, message)
	else:
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
	return render_to_response('custom_manage_users.html', {'page_name': page_name, 'residents': residents, 'boarders': boarders, 'alumni': alumni}, context_instance=RequestContext(request))

def custom_modify_user_view(request, targetUsername):
	''' The page to modify a user. '''
	page_name = "Admin - Modify User"
	if request.user.is_authenticated():
		if not request.user.is_superuser:
			message = "The page /custom_admin/modify_user/ is restricted to superadmins."
			return red_home(request, message)
	else:
		return HttpResponseRedirect(reverse('login'))
	try:
		targetUser = User.objects.get(username=targetUsername)
	except:
		page_name = "User Not Found"
		message = "User %s does not exist or could not be found." % targetUsername
		return render_to_response('custom_modify_user.html', {'page_name': page_name, 'message': message}, context_instance=RequestContext(request))
	try:
		targetProfile = targetUser.get_profile()
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
						return HttpResponseRedirect(reverse('custom_modify_user', kwargs={'targetUsername': targetUsername}))
					else:
						error = "Could not hash password.  Please try again."
						change_user_password_form.errors['__all__'] = change_user_password_form.error_class([error])
				else:
					change_user_password_form._errors['user_password'] = forms.util.ErrorList([u"Passwords don't match"])
					change_user_password_form._errors['confirm_password'] = forms.util.ErrorList([u"Passwords don't match"])
	return render_to_response('custom_modify_user.html', {'targetUser': targetUser, 'targetProfile': targetProfile, 'page_name': page_name, 'modify_user_form': modify_user_form, 'change_user_password_form': change_user_password_form}, context_instance=RequestContext(request))

def custom_add_user_view(request):
	''' The page to add a new user. '''
	page_name = "Admin - Add User"
	if request.user.is_authenticated():
		if not request.user.is_superuser:
			message = "The page /custom_admin/add_user/ is restricted to superadmins."
			return red_home(request, message)
	else:
		return HttpResponseRedirect(reverse('login'))
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
	add_user_form = AddUserForm(initial={'status': UserProfile.RESIDENT})
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
					return render(request, 'custom_add_user.html', {'page_name': page_name, 'add_user_form': add_user_form, 'admin': ADMINS[0], 'house': house})
				if (usr.first_name == first_name) and (usr.last_name == last_name):
					non_field_error = "A profile for %s %s already exists with username %s." % (first_name, last_name, usr.username)
					add_user_form.errors['__all__'] = add_user_form.error_class([non_field_error])
					return render(request, 'custom_add_user.html', {'page_name': page_name, 'add_user_form': add_user_form, 'admin': ADMINS[0], 'house': house})
			if user_password == confirm_password:
				new_user = User.objects.create_user(username=username, email=email, first_name=first_name, last_name=last_name, password=user_password)
				new_user.is_active = is_active
				new_user.is_staff = is_staff
				new_user.is_superuser = is_superuser
				new_user.save()
				for group in groups:
					group.user_set.add(new_user)
				new_user_profile = new_user.get_profile()
				new_user_profile.email_visible = email_visible_to_others
				new_user_profile.phone_number = phone_number
				new_user_profile.phone_visible = phone_visible_to_others
				new_user_profile.status = status
				new_user_profile.current_room = current_room
				new_user_profile.former_rooms = former_rooms
				new_user_profile.former_houses = former_houses
				return HttpResponseRedirect(reverse('custom_add_user'))
			else:
				add_user_form._errors['user_password'] = forms.util.ErrorList([u"Passwords don't match."])
				add_user_form._errors['confirm_password'] = forms.util.ErrorList([u"Passwords don't match."])
	return render_to_response('custom_add_user.html', {'page_name': page_name, 'add_user_form': add_user_form}, context_instance=RequestContext(request))

def requests_view(request, requestType):
	'''
	Generic request view.  Parameters:
		request is the HTTP request
		requestType is name of a RequestType.
			e.g. "food", "maintenance", "network", "site" 
	'''
	if request.user.is_authenticated():
		userProfile = None
		try:
			userProfile = request.user.get_profile()
		except:
			message = "No profile for you could be found.  Please contact a site admin."
			return red_home(request, message)
	else:
		return HttpResponseRedirect(reverse('login'))
	try:
		request_type = RequestType.objects.get(name=requestType)
	except:
		message = "No request type '%s' found." % requestType
		return red_home(request, message)
		#return render_to_response('requests.html', {'page_name': 'Invalid Request Type', 'invalid_request_type': True}, context_instance=RequestContext(request))
	page_name = "%s Requests" % requestType.capitalize()
	if not request_type.enabled:
		message = "%s requests have been disabled." % requestType.capitalize()
		return red_home(request, message)
		#return render_to_response('requests.html', {'page_name': page_name, 'request_disabled': True}, context_instance=RequestContext(request))
	relevant_managers = request_type.managers.all()
	manager = False #if the user is a relevant manager
	for position in relevant_managers:
		if position.incumbent == userProfile:
			manager = True
			break
	class RequestForm(forms.Form):
		body = forms.CharField(widget=forms.Textarea(attrs={'class': 'request'}))
	if manager:
		class ResponseForm(forms.Form):
			request_pk = forms.IntegerField()
			body = forms.CharField(widget=forms.Textarea(attrs={'class': 'response'}), required=False)
			mark_filled = forms.BooleanField(required=False)
			mark_closed = forms.BooleanField(required=False)
	else:
		class ResponseForm(forms.Form):
			request_pk = forms.IntegerField()
			body = forms.CharField(widget=forms.Textarea(attrs={'class': 'response'}))
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
				relevant_request.save()
				new_response.save()
				return HttpResponseRedirect(reverse('requests', kwargs={'requestType': requestType}))
		else:
			message = "Uhhh...Something went wrong.  Please contact an admin for support."
			return red_home(request, message)
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
	return render_to_response('requests.html', {'manager': manager, 'request_type': requestType, 'page_name': page_name, 'request_form': request_form, 'requests_dict': requests_dict}, context_instance=RequestContext(request))

def my_requests_view(request):
	'''
	Show user his/her requests, sorted by request_type.
	'''
	page_name = "My Requests"
	if request.user.is_authenticated():
		userProfile = None
		try:
			userProfile = request.user.get_profile()
		except:
			message = "No profile for you could be found.  Please contact a site admin."
			return red_home(request, message)
	else:
		return HttpResponseRedirect(reverse('login'))
	class RequestForm(forms.Form):
		type_pk = forms.IntegerField()
		body = forms.CharField(widget=forms.Textarea(attrs={'class': 'request'}))
	class ResponseForm(forms.Form):
		request_pk = forms.IntegerField()
		body = forms.CharField(widget=forms.Textarea(attrs={'class': 'response'}))
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
					message = "Uhh...the request type was not recognized.  Please contact an admin for support."
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
						new_response.filled = mark_filled
						new_response.closed = mark_closed
						new_response.manager = True
						break
				new_response.save()
		else:
			message = "Uhhh...Something went wrong.  Please contact an admin for support."
			return red_home(request, message)
	my_requests = Request.objects.filter(owner=userProfile)
	request_dict = list() # A pseudo dictionary, actually a list with items of form (request_type.name, request_form, type_manager, [(request, [list_of_request_responses], response_form),...])
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
			request_dict.append((request_type.name, request_form, type_manager, requests_list))
	return render_to_response('my_requests.html', {'page_name': page_name, 'request_dict': request_dict}, context_instance=RequestContext(request))


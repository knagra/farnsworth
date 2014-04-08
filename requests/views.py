'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''

from django.shortcuts import render_to_response, render
from django.http import HttpResponseRedirect
from django import forms
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User, Group
from django.template import RequestContext
from farnsworth.settings import house, ADMINS
from models import ProfileRequest
from threads.models import UserProfile
from threads.views import red_ext, red_home

def request_profile_view(request):
	''' The page to request a user profile on the site. '''
	pagename = "Profile Request Page"
	house_name = house
	admin = ADMINS[0]
	if request.user.is_authenticated():
		return HttpResponseRedirect(reverse('homepage'))
	else:
		user = None
		staff = False
	class profileRequestForm(forms.Form):
		username = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}))
		first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}))
		last_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}))
		email = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'size':'50'}))
	if request.method == 'POST':
		form = profileRequestForm(request.POST)
		if form.is_valid():
			username = form.cleaned_data['username']
			first_name = form.cleaned_data['first_name']
			last_name = form.cleaned_data['last_name']
			email = form.cleaned_data['email']
			for profile in UserProfile.objects.all():
				if profile.user.username == username:
					non_field_error = "This usename is taken.  Try one of %s_1 through %s_10." % (username, username)
					return render(request, 'request_profile.html', locals())
			profile_request = ProfileRequest(username=username, first_name=first_name, last_name=last_name, email=email, approved=False)
			profile_request.save()
			homepage = True
			return render_to_response('external.html', {'homepage': homepage, 'house_name': house_name, 'user': user, 'staff': staff, 'message': 'Your request for a profile has been submitted.  An admin will e-mail you soon.'})
		else:
			non_field_error = "Uh...Something went wrong in your input.  Please try again."
	else:
		form = profileRequestForm()
	return render(request, 'request_profile.html', locals())

def manage_profile_requests_view(request):
	''' The page to manager user profile requests. '''
	pagename = "Profile Request Page"
	house_name = house
	admin = ADMINS[0]
	if request.user.is_authenticated():
		return HttpResponseRedirect(reverse('homepage'))
	else:
		user = None
		staff = False

def add_user_view(request):
	''' The page to add a new user. '''
	pagename = "Admin - Add User"
	house_name = house
	admin = ADMINS[0]
	if request.user.is_authenticated():
		user = request.user
		if not user.is_superuser:
			pagename = "Home Page"
			homepage = True
			message = "The page /custom_admin/add_user/ is restricted to superadmins."
			red_home(request, locals())
	else:
		pagename = "Home Page"
		homepage = True	
		red_home(request, locals())
	class addUserForm(forms.Form):
		username = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}))
		first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}))
		last_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}))
		email = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'size':'50'}))
		email_visible_to_others = forms.BooleanField(required=False)
		phone = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'size':'50'}))
		phone_visible_to_others = forms.BooleanField(required=False)
		status = forms.ChoiceField(choices=UserProfile.STATUS_CHOICES)
		current_room = forms.CharField(max_length=30, widget=forms.TextInput(attrs={'size':'50'}))
		former_rooms = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}))
		is_active = forms.BooleanField(required=False)
		is_staff = forms.BooleanField(required=False)
		is_superuser = forms.BooleanField(required=False)
		groups = forms.MultipleChoiceField(choices=Group.objects.all(), widget=forms.widgets.SelectMultiple, required=False)
		user_password = forms.CharField(max_length=100, widget=forms.PasswordInput(attrs={'size':'50'}))
		confirm_password = forms.CharField(max_length=100, widget=forms.PasswordInput(attrs={'size':'50'}))
	add_user_form = addUserForm(initial={'status': UserProfile.RESIDENT)
	if request.method == 'POST':
		add_user_form = addUserForm(request.POST):
		if add_user_form.is_valid():
			username = add_user_form.cleaned_data['username']
			first_name = add_user_form.cleaned_data['first_name']
			last_name = add_user_form.cleaned_data['last_name']
			email = add_user_form.cleaned_data['email']
			email_visible_to_others = add_user_form.cleaned_data['email_visible_to_others']
			phone = add_user_form.cleaned_data['phone']
			phone_visible_to_others = add_user_form.cleaned_data['phone_visible_to_others']
			status = add_user_form.cleaned_data['status']
			current_room = add_user_form.cleaned_data['current_room']
			former_rooms = add_user_form.cleaned_data['former_rooms']
			is_active = add_user_form.cleaned_data['is_active']
			is_staff = add_user_form.cleaned_data['is_staff']
			is_superuser = add_user_form.cleaned_data['is_superuser']
			groups = add_user_form.cleaned_data['groups']
			user_password = add_user_form.cleaned_data['user_password']
			confirm_password = add_user_form.cleaned_data['confirm_password']
			

def generic_requests_view(request, caller_locals):
	'''
	Generic request view.  caller_locals should include the page name, a list of
	relevant managers in relevant managers, 
	'''
	house_name = house
	admin = ADMINS[0]
	if request.user.is_authenticated():
		user = request.user
		userProfile = None
		try:
			userProfile = user.get_profile()
		except:
			pagename = "Home Page"
			homepage = True
			message = "No profile for you could be found.  Please contact a site admin."
			return red_home(request, locals())
	else:
		user = None
		pagename = "External"
		homepage = True
		return red_ext(request, locals())
	manager = False; #if the user is a relevant manager
	for position in caller_locals['relevant_managers']:
		if position.incumbent == userProfile:
			manager = True
	

def food_requests_view(request):
	'''
	Food requests page.  All requests generated here are alotted to Kitchen Manager 1,
	and Kitchen Manager 2.  This can be changed with by changing request_managers and
	the managers it contains.
	'''
	pagename = "Profile Request Page"
	relevant_managers = list()
	km1 = Manager.objects.get_or_create(title="Kitchen Manager 1")
	km2 = Manager.objects.get_or_create(title="Kitchen Manager 2")
	relevant_managers.append(km1)
	relevant_managers.append(km2)
	return generic_requests_view(request, locals())

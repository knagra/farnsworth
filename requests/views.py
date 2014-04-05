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

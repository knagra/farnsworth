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
from models import ProfileRequest
from threads.models import UserProfile

def request_profile_view(request):
	''' The page to request a user profile on the site. '''
	pagename = "Profile Request Page"
	house_name = house
	if request.user.is_authenticated():
		return HttpResponseRedirect(reverse('homepage'))
	else:
		user = None
		staff = False
	class profileRequestForm(forms.Form):
		username = forms.CharField(max_length=100)
		first_name = forms.CharField(max_length=100)
		last_name = forms.CharField(max_length=100)
		email = forms.CharField(max_length=255)
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

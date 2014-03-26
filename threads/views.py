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

def homepage_view(request):
	''' The view of the homepage. '''
	homepage = True
	pagename = "homepage"
	house_name = house
	if request.user.is_authenticated():
		user = request.user
		staff = user.is_staff
	else:
		user = None
		staff = False
	return render_to_response('homepage.html', locals(), context_instance=RequestContext(request))

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
					form = loginForm()
					return render(request, 'login.html', locals())
			else:
				form = loginForm()
				#message = "Invalid username/password combo."
				return render(request, 'login.html', locals())
		else:
			form = loginForm()
			#message = "Invalid username/password combo." 
			return render(request, 'login.html', locals())
	else:
		form = loginForm()
		return render(request, 'login.html', locals())

def logout_view(request):
	''' Log the user out. '''
	logout(request)
	return HttpResponseRedirect(reverse('homepage'))

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

def homepage(request):
	'''
	The view of the homepage.
	'''
	homepage = True
	house_name = house
	if request.user.is_authenticated():
		user = request.user
		staff = user.is_staff
	else:
		user = None
		staff = False
	return render_to_response('homepage.html', locals(), context_instance=RequestContext(request))

def helppage(request):
	'''
	The view of the helppage.
	'''
	pagename = "Help Page"
	house_name = house
	if request.user.is_authenticated():
		user = request.user
		staff = user.is_staff
	else:
		user = None
		staff = False
	return render_to_response('helppage.html', locals(), context_instance=RequestContext(request))


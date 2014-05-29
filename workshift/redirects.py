
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

def red_workshift(request, message=None):
	'''
    Redirects to the base workshift page for users who are logged in
	'''
	if message:
		messages.add_message(request, messages.ERROR, message)
	return HttpResponseRedirect(reverse('workshift:view_semester'))

'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''

from django.http import HttpResponseRedirect

from threads.models import UserProfile
from threads.views import red_home

def profile_exists(function):
	def wrap(request, *args, **kwargs):
		if request.user.is_authenticated():
			try:
				UserProfile.objects.get(user=request.user)
			except UserProfile.DoesNotExist:
				return red_home(request, MESSAGES['NO_PROFILE'])
		else:
			return HttpResponseRedirect(reverse('login'))
		return function(request, *args, **kwargs)
	return wrap


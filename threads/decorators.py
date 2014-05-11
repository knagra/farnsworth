'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''

from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from threads.models import UserProfile
from threads.redirects import red_home

def profile_exists(redirect_user='login', redirect_profile=red_home):
	def real_decorator(view_func):
		def wrap(request, *args, **kwargs):
			if not request.user.is_authenticated():
				return HttpResponseRedirect(reverse(redirect_user))
			try:
				UserProfile.objects.get(user=request.user)
			except UserProfile.DoesNotExist:
				return redirect_profile(request, MESSAGES['NO_PROFILE'])
			else:
				return view_func(request, *args, **kwargs)
		return wrap
	return real_decorator


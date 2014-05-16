'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''

from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from utils.variables import MESSAGES
from base.redirects import red_home
from threads.models import UserProfile
from managers.models import Manager

def profile_required(function=None, redirect_user='login', redirect_profile=red_home):
	def real_decorator(view_func):
		def wrap(request, *args, **kwargs):
			if not request.user.is_authenticated():
				return HttpResponseRedirect(reverse(redirect_user))
			try:
				UserProfile.objects.get(user=request.user)
			except UserProfile.DoesNotExist:
				return redirect_profile(request, MESSAGES['NO_PROFILE'])
			return view_func(request, *args, **kwargs)
		return wrap
	if function:
		return real_decorator(function)
	return real_decorator

def admin_required(function=None, redirect_user='login', redirect_profile=red_home):
	def real_decorator(view_func):
		def wrap(request, *args, **kwargs):
			if not request.user.is_authenticated():
				return HttpResponseRedirect(reverse(redirect_user))
			try:
				UserProfile.objects.get(user=request.user)
			except UserProfile.DoesNotExist:
				return redirect_profile(request, MESSAGES['NO_PROFILE'])
			if not request.user.is_superuser:
				return redirect_profile(request, MESSAGES['ADMINS_ONLY'])
			return view_func(request, *args, **kwargs)
		return wrap
	if function:
		return real_decorator(function)
	return real_decorator

def president_admin_required(function=None, redirect_user='login', redirect_profile=red_home):
	def real_decorator(view_func):
		def wrap(request, *args, **kwargs):
			if not request.user.is_authenticated():
				return HttpResponseRedirect(reverse(redirect_user))
			try:
				userProfile = UserProfile.objects.get(user=request.user)
			except UserProfile.DoesNotExist:
				return redirect_profile(request, MESSAGES['NO_PROFILE'])
			president = False # whether the user has president privileges
			for pos in Manager.objects.filter(incumbent=userProfile):
				if pos.president:
					president = True
					break
			if (not request.user.is_superuser) and (not president):
				return redirect_profile(request, MESSAGES['PRESIDENTS_ONLY'])
			return view_func(request, *args, **kwargs)
		return wrap
	if function:
		return real_decorator(function)
	return real_decorator

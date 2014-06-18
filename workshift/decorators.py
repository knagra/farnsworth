
from __future__ import absolute_import
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404

from utils.variables import MESSAGES
from base.redirects import red_home
from workshift.models import WorkshiftProfile, Semester
from workshift.redirects import red_workshift
from workshift.utils import can_manage

def _extract_semester(kwargs):
	sem_url = kwargs.pop("sem_url", None)
	if sem_url is not None:
		if len(sem_url) < 3:
			raise Http404
		season = sem_url[:2] if sem_url else None
		year = sem_url[2:] if sem_url else None
		kwargs["semester"] = get_object_or_404(Semester, season=season, year=year)
	else:
		try:
			kwargs["semester"] = Semester.objects.get(current=True)
		except Semester.DoesNotExist:
			return HttpResponseRedirect(reverse('workshift:start_semester'))
		except Semester.MultipleObjectsReturned:
			kwargs["semester"] = Semester.objects.filter(current=True).latest('start_date')

def get_workshift_profile(function=None, redirect_no_user='login',
						  redirect_no_profile=red_home):
	def real_decorator(view_func):
		def wrap(request, *args, **kwargs):
			if not request.user.is_authenticated():
				redirect_to = reverse(redirect_no_user)
				if redirect_no_user == "login":
					redirect_to += "?next=" + request.path
				return HttpResponseRedirect(redirect_to)

			ret = _extract_semester(kwargs)
			if ret is not None:
				return ret
			request.semester = kwargs["semester"]

			try:
				kwargs["profile"] = WorkshiftProfile.objects.get(
					user=request.user, semester=request.semester,
					)
			except WorkshiftProfile.DoesNotExist:
				profile = None

			return view_func(request, *args, **kwargs)

		return wrap

	if function:
		return real_decorator(function)

	return real_decorator

def workshift_manager_required(function=None, redirect_no_user='login',
							   redirect_no_profile=red_home,
							   redirect_profile=red_workshift):
	def real_decorator(view_func):
		def wrap(request, *args, **kwargs):
			if not request.user.is_authenticated():
				redirect_to = reverse(redirect_no_user)
				if redirect_no_user == "login":
					redirect_to += "?next=" + request.path
				return HttpResponseRedirect(redirect_to)

			if not can_manage(request, kwargs.get("semester", None)):
				messages = MESSAGES['ADMINS_ONLY']
				if Semester.objects.filter(current=True).count() == 0:
					messages = "Workshift semester has not been created yet. " + messages
					return red_home(request, messages)
				return redirect_profile(request, messages)

			return view_func(request, *args, **kwargs)

		return wrap

	if function:
		return real_decorator(function)

	return real_decorator

def semester_required(function=None):
	def real_decorator(view_func):
		def wrap(request, *args, **kwargs):
			ret = _extract_semester(kwargs)
			if ret is not None:
				return ret
			request.semester = kwargs["semester"]

			return view_func(request, *args, **kwargs)

		return wrap

	if function:
		return real_decorator(function)

	return real_decorator

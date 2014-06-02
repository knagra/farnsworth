
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404

from utils.variables import MESSAGES
from base.redirects import red_home
from base.models import UserProfile
from managers.models import Manager
from workshift.models import WorkshiftProfile, Semester
from workshift.redirects import red_workshift

def _extract_semester(kwargs):
	if "sem_url" in kwargs and kwargs["sem_url"] is not None:
		sem_url = kwargs.pop("sem_url")
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

def workshift_profile_required(function=None, redirect_no_user='login',
                               redirect_no_profile=red_home):
	def real_decorator(view_func):
		def wrap(request, *args, **kwargs):
			if not request.user.is_authenticated():
				redirect_to = reverse(redirect_no_user)
				if redirect_no_user == "login":
					redirect_to += "?next=" + request.path
				return HttpResponseRedirect(redirect_to)

			_extract_semester(kwargs)
			request.semester = kwargs["semester"]

			try:
				profile = WorkshiftProfile.objects.get(user=request.user,
													   semester=kwargs["semester"])
			except WorkshiftProfile.DoesNotExist:
				return redirect_no_profile(request, MESSAGES['NO_WORKSHIFT'])
			except KeyError:
				return HttpResponseRedirect(reverse('workshift:start_semester'))

			kwargs["profile"] = profile

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

			try:
				userProfile = UserProfile.objects.get(user=request.user)
			except UserProfile.DoesNotExist:
				return redirect_no_profile(request, MESSAGES['NO_WORKSHIFT'])

			workshift = Manager.objects.filter(incumbent=userProfile) \
			  .filter(workshift_manager=True).count() > 0

			if (not request.user.is_superuser) and (not workshift):
				messages = MESSAGES['ADMINS_ONLY']
				if Semester.objects.filter(current=True).count() == 0:
					messages = "Workshift semester has not been created yet. " + messages
				return redirect_profile(request, messages)

			return view_func(request, *args, **kwargs)

		return wrap

	if function:
		return real_decorator(function)

	return real_decorator

def semester_required(function=None):
	def real_decorator(view_func):
		def wrap(request, *args, **kwargs):
			_extract_semester(kwargs)
			request.semester = kwargs["semester"]

			return view_func(request, *args, **kwargs)

		return wrap

	if function:
		return real_decorator(function)

	return real_decorator

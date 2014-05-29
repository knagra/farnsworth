
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404

from utils.variables import MESSAGES
from base.redirects import red_home
from workshift.models import WorkshiftProfile, Semester
from workshift.utils import current_semester

def workshift_profile_required(function=None, redirect_no_user='login',
                               redirect_profile=red_home):
	def real_decorator(view_func):
		def wrap(request, *args, **kwargs):
			if not request.user.is_authenticated():
				redirect_to = reverse(redirect_no_user)
				if redirect_no_user == "login":
					redirect_to += "?next=" + request.path
				return HttpResponseRedirect(redirect_to)

			if "sem_url" in kwargs:
				sem_url = kwargs.pop("sem_url")
				if len(sem_url) < 3:
					raise Http404
				season = sem_url[:2] if sem_url else None
				year = sum_url[2:] if sem_url else None
				semester = get_object_or_404(Semester, season=season, year=year)
			else:
				semester = current_semester()

			try:
				profile = WorkshiftProfile.objects.get(user=request.user, semester=semester)
			except WorkshiftProfile.DoesNotExist:
				return redirect_profile(request, MESSAGES['NO_WORKSHIFT'])

			kwargs["semester"] = semester
			kwargs["profile"] = profile

			return view_func(request, *args, **kwargs)

		return wrap

	if function:
		return real_decorator(function)

	return real_decorator

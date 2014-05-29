"""
Project: Farnsworth

Authors: Karandeep Singh Nagra and Nader Morshed
"""


from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext

from base.models import UserProfile
from workshift.decorators import workshift_profile_required, \
	workshift_manager_required, semester_required
from workshift.models import Semester, WorkshiftProfile

@workshift_manager_required
def start_semester_view(request):
	"""
	Initiates a semester's worth of workshift, with the option to copy workshift
	types from the previous semester.
	"""
	page_name = "Start Semester"
	return render_to_response("start_semester.html", {
		"page_name": page_name,
	}, context_instance=RequestContext(request))

@workshift_profile_required
def view_semester(request, semester, profile):
	"""
	Displays a table of the workshifts for the week, shift assignees,
	accumulated statistics (Down hours), reminders for any upcoming shifts, and
	links to sign off on shifts. Also links to the rest of the workshift pages.
	"""
	season_name = [j for i, j in SEASON_CHOICES if i == semester.season][0]
	page_name = "Workshift for {0} {1}".format(season_name, semester.year)
	return render_to_response("semester.html", {
		"page_name": page_name,
		"profile": profile,
	}, context_instance=RequestContext(request))

@workshift_profile_required
def profile_view(request, semester, profile):
	"""
	Show the user their workshift history for the current semester as well as
	upcoming shifts.
	"""
	return render_to_response("preferences.html", {
		"page_name": page_name,
		"profile": profile,
	}, context_instance=RequestContext(request))

@workshift_profile_required
def preferences_view(request, semester, profile):
	"""
	Show the user their preferences for the given semester.
	"""
	page_name = "Workshift Preferences"
	return render_to_response("preferences.html", {
		"page_name": page_name,
		"profile": profile,
	}, context_instance=RequestContext(request))

@workshift_manager_required
@semester_required
def manage_view(request, semester):
	"""
	View all members' preferences. This view also includes forms to create an
	entire semester's worth of weekly workshifts.
	"""
	page_name = "Manage Workshift"
	return render_to_response("manage.html", {
		"page_name": page_name,
	}, context_instance=RequestContext(request))

@workshift_manager_required
@semester_required
def add_shift_view(request):
	"""
	View for the workshift manager to create new types of workshifts.
	"""
	page_name = "Add Workshift"
	return render_to_response("add_workshift.html", {
		"page_name": page_name,
	}, context_instance=RequestContext(request))

@workshift_profile_required
def shift_view(request, semester, profile):
	pass

@workshift_profile_required
def edit_shift_view(request, semester, profile):
	pass

@workshift_profile_required
def instance_view(request, semester, profile):
	pass

@workshift_profile_required
def edit_instance_view(request, semester, profile):
	pass

@workshift_profile_required
def one_off_view(request, semester, profile):
	pass

@workshift_profile_required
def edit_one_off_view(request, semester, profile):
	pass

@workshift_profile_required
def type_view(request, semester, profile):
	pass

@workshift_profile_required
def edit_type_view(request, semester, profile):
	pass

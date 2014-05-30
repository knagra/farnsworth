"""
Project: Farnsworth

Authors: Karandeep Singh Nagra and Nader Morshed
"""


from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext

from datetime import date, datetime, timedelta

from utils.variables import MESSAGES
from base.models import UserProfile
from managers.models import Manager
from workshift.decorators import workshift_profile_required, \
	workshift_manager_required, semester_required
from workshift.models import *

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
	Displays a table of the workshifts for the week, shift assignments,
	accumulated statistics (Down hours), reminders for any upcoming shifts, and
	links to sign off on shifts. Also links to the rest of the workshift pages.
	"""
	season_name = [j for i, j in Semester.SEASON_CHOICES if i == semester.season][0]
	page_name = "Workshift for {0} {1}".format(season_name, semester.year)

	# Verifier Form

	# We want a form for verification, a notification of upcoming shifts, and a
	# chart displaying the entire house's workshift for the day as well as
	# weekly shifts. The chart should have left and right arrows on the sides to
	# switch the day, with a dropdown menu to select the day from a calendar.
	# Ideally, switching days should use AJAX to appear more seemless to users.

	# Recent History
	today = date.today()
	todays_shifts = WorkshiftInstance.objects.filter(date=today)

	last_sunday = today - timedelta(days=today.weekday() + 1)
	next_sunday = last_sunday + timedelta(weeks=1)
	week_shifts = WorkshiftInstance.objects.filter(date__gt=last_sunday) \
	  .filter(date__lt=next_sunday)

	return render_to_response("semester.html", {
		"page_name": page_name,
		"profile": profile,
		"todays_shifts": todays_shifts,
		"week_shifts": week_shifts,
	}, context_instance=RequestContext(request))

@workshift_profile_required
def profile_view(request, semester, profile, pk):
	"""
	Show the user their workshift history for the current semester as well as
	upcoming shifts.
	"""
	wprofile = get_object_or_404(WorkshiftProfile, pk=pk)
	page_name = "{0}'s Workshift Profile".format(wprofile.user.get_full_name())
	return render_to_response("profile.html", {
		"page_name": page_name,
		"profile": wprofile,
	}, context_instance=RequestContext(request))

@workshift_profile_required
def preferences_view(request, semester, profile, pk):
	"""
	Show the user their preferences for the given semester.
	"""
	wprofile = get_object_or_404(WorkshiftProfile, pk=pk)
	user_profile = UserProfile.objects.get(user=request.user)
	managers = Manager.objects.filter(incumbent=user_profile) \
	  .filter(workshift_manager=True)

	if wprofile.user != request.user and not managers.count() and \
	  not request.user.is_superuser:
		messages.add_message(request, messages.ERROR,
							 MESSAGES['ADMINS_ONLY'])
		return HttpResponseRedirect(reverse('workshift:view_semester'))

	page_name = "{0}'s Workshift Preferences".format(
		wprofile.user.get_full_name())
	return render_to_response("preferences.html", {
		"page_name": page_name,
		"profile": profile,
	}, context_instance=RequestContext(request))

@workshift_profile_required
def manage_view(request, semester, profile):
	"""
	View all members' preferences. This view also includes forms to create an
	entire semester's worth of weekly workshifts.
	"""
	page_name = "Manage Workshift"
	pools = WorkshiftPool.objects.filter(semester=semester)
	user_profile = UserProfile.objects.get(user=request.user)
	managers = Manager.objects.filter(incumbent=user_profile) \
	  .filter(workshift_manager=True)
	full_management = request.user.is_superuser or managers.count()

	if not full_management:
		pools = pools.filter(managers__incumbent=user_profile)
		if not pools.count():
			messages.add_message(request, messages.ERROR,
								 MESSAGES['ADMINS_ONLY'])
			return HttpResponseRedirect(reverse('workshift:view_semester'))

	return render_to_response("manage.html", {
		"page_name": page_name,
		"pools": pools,
		"full_management": full_management,
	}, context_instance=RequestContext(request))

@workshift_manager_required
@semester_required
def assign_shifts_view(request, semester):
	"""
	View all members' preferences. This view also includes forms to create an
	entire semester's worth of weekly workshifts.
	"""
	page_name = "Assign Shifts"
	return render_to_response("assign_shifts.html", {
		"page_name": page_name,
	}, context_instance=RequestContext(request))

@workshift_manager_required
def add_shift_view(request):
	"""
	View for the workshift manager to create new types of workshifts.
	"""
	page_name = "Add Workshift"
	return render_to_response("add_shift.html", {
		"page_name": page_name,
	}, context_instance=RequestContext(request))

@workshift_profile_required
def shift_view(request, semester, profile, pk):
	"""
	View the details of a particular RegularWorkshift.
	"""
	shift = get_object_or_404(RegularWorkshift, pk=pk)
	page_name = shift.title

	return render_to_response("view_shift.html", {
		"page_name": page_name,
		"shift": shift,
	}, context_instance=RequestContext(request))

@workshift_profile_required
def edit_shift_view(request, semester, profile, pk):
	"""
	View for a manager to edit the details of a particular RegularWorkshift.
	"""
	shift = get_object_or_404(RegularWorkshift, pk=pk)

	user_profile = UserProfile.objects.get(user=request.user)
	managers = shift.pool.managers.filter(incumbent=user_profile)

	if not request.user.is_superuser and not managers.count():
		messages.add_message(request, messages.ERROR,
							 MESSAGES['ADMINS_ONLY'])
		return HttpResponseRedirect(reverse('workshift:view_semester'))

	page_name = "Edit " + shift.title

	return render_to_response("edit_shift.html", {
		"page_name": page_name,
		"shift": shift,
	}, context_instance=RequestContext(request))

@workshift_profile_required
def instance_view(request, semester, profile, pk):
	"""
	View the details of a particular WorkshiftInstance.
	"""
	shift = get_object_or_404(WorkshiftInstance, pk=pk)
	page_name = shift.title

	return render_to_response("view_instance.html", {
		"page_name": page_name,
		"shift": shift,
	}, context_instance=RequestContext(request))

@workshift_profile_required
def edit_instance_view(request, semester, profile, pk):
	"""
	View for a manager to edit the details of a particular WorkshiftInstance.
	"""
	shift = get_object_or_404(WorkshiftInstance, pk=pk)

	user_profile = UserProfile.objects.get(user=request.user)
	managers = shift.pool.managers.filter(incumbent=user_profile)

	if not request.user.is_superuser and not managers.count():
		messages.add_message(request, messages.ERROR,
							 MESSAGES['ADMINS_ONLY'])
		return HttpResponseRedirect(reverse('workshift:view_semester'))

	page_name = "Edit " + shift.title

	return render_to_response("edit_shift.html", {
		"page_name": page_name,
		"shift": shift,
	}, context_instance=RequestContext(request))

@workshift_profile_required
def list_types_view(request, semester, profile):
	"""
	View the details of a particular WorkshiftType.
	"""
	page_name = "Workshift Types"
	types = WorkshiftType.objects.all()

	return render_to_response("list_types.html", {
		"page_name": page_name,
		"types": types,
	}, context_instance=RequestContext(request))

@workshift_profile_required
def type_view(request, semester, profile, pk):
	"""
	View the details of a particular WorkshiftType.
	"""
	shift = get_object_or_404(WorkshiftType, pk=pk)
	page_name = shift.title

	return render_to_response("view_type.html", {
		"page_name": page_name,
		"shift": shift,
	}, context_instance=RequestContext(request))

@workshift_profile_required
def edit_type_view(request, semester, profile, pk):
	"""
	View for a manager to edit the details of a particular WorkshiftType.
	"""
	shift = get_object_or_404(WorkshiftType, pk=pk)
	user_profile = UserProfile.objects.get(user=request.user)
	managers = Manager.objects.filter(incumbent=user_profile) \
	  .filter(workshift_manager=True)

	if not request.user.is_superuser and not managers.count():
		messages.add_message(request, messages.ERROR,
							 MESSAGES['ADMINS_ONLY'])
		return HttpResponseRedirect(reverse('workshift:view_semester'))

	page_name = "Edit " + shift.title

	return render_to_response("edit_type.html", {
		"page_name": page_name,
		"shift": shift,
	}, context_instance=RequestContext(request))

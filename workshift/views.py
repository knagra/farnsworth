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

from base.models import UserProfile
from managers.models import Manager
from workshift.decorators import workshift_profile_required, \
	workshift_manager_required, semester_required
from workshift.models import Semester, WorkshiftProfile, WorkshiftType, \
	 RegularWorkshift, WorkshiftInstance, OneTimeWorkshift, \
	 WorkshiftPool

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
def view_semester(request, semester=None, profile=None):
	"""
	Displays a table of the workshifts for the week, shift assignees,
	accumulated statistics (Down hours), reminders for any upcoming shifts, and
	links to sign off on shifts. Also links to the rest of the workshift pages.
	"""
	season_name = [j for i, j in Semester.SEASON_CHOICES if i == semester.season][0]
	page_name = "Workshift for {0} {1}".format(season_name, semester.year)
	return render_to_response("semester.html", {
		"page_name": page_name,
		"profile": profile,
	}, context_instance=RequestContext(request))

@workshift_profile_required
def profile_view(request, semester, profile, profile_pk):
	"""
	Show the user their workshift history for the current semester as well as
	upcoming shifts.
	"""
	wprofile = get_object_or_404(WorkshiftProfile, pk=profile_pk)
	page_name = "{0}'s Workshift Profile".format(wprofile.user.get_full_name())
	return render_to_response("preferences.html", {
		"page_name": page_name,
		"profile": wprofile,
	}, context_instance=RequestContext(request))

@workshift_profile_required
def preferences_view(request, semester, profile, profile_pk):
	"""
	Show the user their preferences for the given semester.
	"""
	wprofile = get_object_or_404(WorkshiftProfile, pk=profile_pk)
	page_name = "{0}'s Workshift Preferences".format(wprofile.user.get_full_name())
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
	if request.user.is_superuser or managers.count():
		# Display all workshift pools?
		pass
	else:
		pools.filter(managers__incumbent=user_profile)
		if pools.count():
			pass
		else:
			messages.add_message(request, messages.ERROR,
								 MESSAGES['ADMINS_ONLY'])
			return HttpResponseRedirect(reverse('workshift:view_semester'))
	return render_to_response("manage.html", {
		"page_name": page_name,
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
def shift_view(request, semester, profile, shift_pk):
	"""
	View the details of a particular RegularWorkshift.
	"""
	shift = get_object_or_404(RegularWorkshift, pk=shift_pk)
	page_name = shift.title

	return render_to_response("view_shift.html", {
		"page_name": page_name,
		"shift": shift,
	}, context_instance=RequestContext(request))

@workshift_profile_required
def edit_shift_view(request, semester, profile, shift_pk):
	"""
	View for a manager to edit the details of a particular RegularWorkshift.
	"""
	shift = get_object_or_404(RegularWorkshift, pk=shift_pk)
	page_name = "Edit " + shift.title

	return render_to_response("edit_shift.html", {
		"page_name": page_name,
		"shift": shift,
	}, context_instance=RequestContext(request))

@workshift_profile_required
def instance_view(request, semester, profile, instance_pk):
	"""
	View the details of a particular WorkshiftInstance.
	"""
	shift = get_object_or_404(WorkshiftInstance, pk=instance_pk)
	page_name = shift.weekly_workshift.title

	return render_to_response("view_instance.html", {
		"page_name": page_name,
		"shift": shift,
	}, context_instance=RequestContext(request))

@workshift_profile_required
def edit_instance_view(request, semester, profile, instance_pk):
	"""
	View for a manager to edit the details of a particular WorkshiftInstance.
	"""
	shift = get_object_or_404(WorkshiftInstance, pk=instance_pk)
	page_name = "Edit " + shift.weekly_workshift.title

	return render_to_response("edit_shift.html", {
		"page_name": page_name,
		"shift": shift,
	}, context_instance=RequestContext(request))

@workshift_profile_required
def one_time_view(request, semester, profile, one_time_pk):
	"""
	View the details of a particular OneTimeWorkshift.
	"""
	shift = get_object_or_404(OneTimeWorkshift, pk=one_time_pk)
	page_name = shift.title

	return render_to_response("view_one_time.html", {
		"page_name": page_name,
		"shift": shift,
	}, context_instance=RequestContext(request))

@workshift_profile_required
def edit_one_time_view(request, semester, profile, one_time_pk):
	"""
	View for a manager to edit the details of a particular OneTimeWorkshift.
	"""
	shift = get_object_or_404(OneTimeWorkshift, pk=one_time_pk)
	page_name = "Edit " + shift.title

	return render_to_response("edit_one_time.html", {
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
def type_view(request, semester, profile, type_pk):
	"""
	View the details of a particular WorkshiftType.
	"""
	shift = get_object_or_404(WorkshiftType, pk=type_pk)
	page_name = shift.title

	return render_to_response("view_type.html", {
		"page_name": page_name,
		"shift": shift,
	}, context_instance=RequestContext(request))

@workshift_profile_required
def edit_type_view(request, semester, profile, type_pk):
	"""
	View for a manager to edit the details of a particular WorkshiftType.
	"""
	shift = get_object_or_404(WorkshiftType, pk=type_pk)
	page_name = "Edit " + shift.title

	return render_to_response("edit_type.html", {
		"page_name": page_name,
		"shift": shift,
	}, context_instance=RequestContext(request))

"""
Project: Farnsworth

Authors: Karandeep Singh Nagra and Nader Morshed
"""

from __future__ import division

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.db import models
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
from workshift.forms import *

@workshift_manager_required
def start_semester_view(request):
	"""
	Initiates a semester's worth of workshift, with the option to copy workshift
	types from the previous semester.
	"""
	page_name = "Start Semester"
	today = date.today()
	year = today.year

	if today.month > 3 and today.month <= 7:
		season = Semester.SUMMER
	elif today.month > 7 and today.month <= 10:
		season = Semester.FALL
	else:
		season = Semester.SPRING
		if today.month > 10:
			year += 1

	semester_form = SemesterForm(
		request.POST or None,
		initial={
			"year": year,
			"season": season,
		})

	if semester_form.is_valid():
		# And save this semester
		semester = semester_form.save()
		semester.workshift_managers = \
		  [i.incumbent for i in Managers.objects.filter(workshift_manager=True)]
		semester.save()

	return render_to_response("start_semester.html", {
		"page_name": page_name,
		"semester_form": semester_form,
	}, context_instance=RequestContext(request))

@workshift_profile_required
def view_semester(request, semester, profile):
	"""
	Displays a table of the workshifts for the week, shift assignments,
	accumulated statistics (Down hours), reminders for any upcoming shifts, and
	links to sign off on shifts. Also links to the rest of the workshift pages.
	"""
	template_dict = {}
	season_name = semester.get_season_display()
	template_dict["page_name"] = \
	  "Workshift for {0} {1}".format(season_name, semester.year)

	template_dict["semester_percentage"] = int(
		(date.today() - semester.start_date).days /
		(semester.end_date - semester.start_date).days * 100
		)

	template_dict["profile"] = profile

	# Forms to interact with workshift
	verify_form = VerifyShiftForm(
		request.POST if "verify_shift" in request.POST else None,
		profile=profile,
		)

	blown_form = BlownShiftForm(
		request.POST if "blown_shift" in request.POST else None,
		profile=profile,
		)

	sign_in_form = SignInForm(
		request.POST if "sign_in" in request.POST else None,
		profile=profile,
		)

	sign_out_form = SignOutForm(
		request.POST if "sign_out" in request.POST else None,
		profile=profile,
		)

	for form in [verify_form, blown_form, sign_in_form, sign_out_form]:
		if form.is_valid():
			form.save()
		else:
			# TODO: Place form errors on page somewhere?
			pass

	# We want a form for verification, a notification of upcoming shifts, and a
	# chart displaying the entire house's workshift for the day as well as
	# weekly shifts.
	#
	# The chart should have left and right arrows on the sides to switch the
	# day, with a dropdown menu to select the day from a calendar. Ideally,
	# switching days should use AJAX to appear more seemless to users.

	# Recent History
	day = date.today()
	if "day" in request.GET:
		try:
			day = date(*map(int, request.GET["day"].split("-")))
		except (TypeError, ValueError):
			pass

	template_dict["day"] = day.strftime("%A, %B %e, %Y")
	template_dict["prev_day"] = (day - timedelta(days=1)).strftime("%Y-%m-%d")
	template_dict["next_day"] = (day + timedelta(days=1)).strftime("%Y-%m-%d")

	day_shifts = WorkshiftInstance.objects.filter(date=day)
	day_shift_tuples = []

	for shift in day_shifts:
		forms = []
		if not shift.closed:
			if shift.workshifter:
				pool = shift.pool

				if pool.self_verify or shift.workshifter != profile:
					verify_form = VerifyShiftForm(initial={
						"pk": shift.pk,
						}, profile=profile)
					forms.append(verify_form)

				if pool.any_blown or \
				  pool.managers.filter(incumbent__user=profile.user).count():
					blown_form = BlownShiftForm(initial={
						"pk": shift.pk,
						}, profile=profile)
					forms.append(blown_form)

				if shift.workshifter == profile:
					sign_out_form = SignOutForm(initial={
						"pk": shift.pk,
						}, profile=profile)
					forms.append(sign_out_form)
			else:
				sign_in_form = SignInForm(initial={
					"pk": shift.pk,
					}, profile=profile)
				forms.append(sign_in_form)

		day_shift_tuples.append((shift, forms,))

	template_dict["day_shifts"] = day_shifts

	last_sunday = day - timedelta(days=day.weekday() + 1)
	next_sunday = last_sunday + timedelta(weeks=1)
	template_dict["week_shifts"] = \
	  WorkshiftInstance.objects.filter(date__gt=last_sunday) \
	  .filter(date__lt=next_sunday)

	return render_to_response("semester.html", template_dict,
							   context_instance=RequestContext(request))

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

	edit_form = RegularWorkshiftForm(
		request.POST if "edit_shift" in request.POST else None,
		instance=shift,
		)

	if "delete_shift" in request.POST:
		shift.delete()
		return HttpResponseRedirect(reverse('workshift:manage'))
	elif edit_form.is_valid():
		shift = edit_form.save()

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

	edit_form = WorkshiftInstanceForm(
		request.POST if "edit_shift" in request.POST else None,
		instance=shift,
		)

	if "delete_shift" in request.POST:
		shift.delete()
		HttpResponseRedirect(reverse('workshift:manage'))
	elif edit_form.is_valid():
		shift = edit_form.save()

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

	edit_form = WorkshiftTypeForm(
		request.POST if "edit_shift" in request.POST else None,
		instance=shift,
		)

	if "delete_shift" in request.POST:
		# Ask for password to delete shifts?
		shift.delete()
		HttpResponseRedirect(reverse('workshift:list_types'))
	elif edit_form.is_valid():
		shift = edit_form.save()

	page_name = "Edit " + shift.title

	return render_to_response("edit_type.html", {
		"page_name": page_name,
		"shift": shift,
	}, context_instance=RequestContext(request))

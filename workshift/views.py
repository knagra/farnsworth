"""
Project: Farnsworth

Authors: Karandeep Singh Nagra and Nader Morshed
"""

from __future__ import division, absolute_import

from datetime import date, datetime, timedelta

from django.utils.timezone import utc
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models
from django.forms.models import modelformset_factory
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext

from workshift.templatetags.workshift_tags import wurl

from utils.variables import MESSAGES
from base.models import UserProfile
from managers.models import Manager
from workshift.decorators import get_workshift_profile, \
	workshift_manager_required, semester_required
from workshift.models import *
from workshift.forms import *
from workshift.utils import can_manage

def add_workshift_context(request):
	""" Add workshift variables to all dictionaries passed to templates. """
	if not request.user.is_authenticated():
		return dict()
    # Semester is for populating the current page
	try:
		SEMESTER = request.semester
	except AttributeError:
		try:
			SEMESTER = Semester.objects.get(current=True)
		except Semester.DoesNotExist:
			return dict()
	try:
		workshift_profile = WorkshiftProfile.objects.get(semester=SEMESTER, user=request.user)
	except WorkshiftProfile.DoesNotExist:
		return {'WORKSHIFT_ENABLED': False}
	WORKSHIFT_MANAGER = can_manage(request, SEMESTER)
    # Current semester is for navbar notifications
	try:
		CURRENT_SEMESTER = Semester.objects.get(current=True)
	except Semester.DoesNotExist:
		CURRENT_SEMESTER = None
	except Semester.MultipleObjectsReturned:
		CURRENT_SEMESTER = Semester.objects.all().latest(start_date)
		workshift_emails = []
		for pos in Manager.objects.filter(workshift_manager=True, active=True):
			if pos.email:
				workshift_emails.append(pos.email)
			elif pos.incumbent.email_visible and pos.incumbent.user.email:
				workshift_emails.append(pos.incumbent.user.email)
		if workshift_emails:
			workshift_email_str = " ({0})".format(
				", ".join([i.format('<a href="mailto:{0}">{0}</a>')
						   for i in workshift_emails])
				)
		else:
			workshift_email_str = ""
		messages.add_message(
			request, messages.WARNING,
			MESSAGES['MULTIPLE_CURRENT_SEMESTERS'].format(
				admin_email=settings.ADMINS[0][1],
				workshift_emails=workshift_email_str,
				))
	workshift_profile = WorkshiftProfile.objects.get(semester=SEMESTER, user=request.user)
	now = datetime.utcnow().replace(tzinfo=utc)
	days_passed = (date.today() - SEMESTER.start_date).days # number of days passed in this semester
	total_days = (SEMESTER.end_date - SEMESTER.start_date).days # total number of days in this semester
	semester_percent = round((days_passed / total_days) * 100, 2)
	pool_standings = list() # with items of form (workshift_pool, standing_in_pool)
	# TODO figure out how to get pool standing out to the template
	upcoming_shifts = WorkshiftInstance.objects.filter(
        workshifter=workshift_profile,
        closed=False,
        date__gte=date.today(),
        date__lte=date.today() + timedelta(days=2),
        )
	# TODO: Add a fudge factor of an hour to this?
	# TODO: Do we want now.time() or now.timetz()
	# TODO: Pass a STANDING variable that contains regular workshift up/down hours
	happening_now = [
		shift.week_long or
		(shift.date == date.today() and
		 not shift.start_time or
		 not shift.end_time or
		 (now.time() > shift.start_time and now.time() < shift.end_time))
		for shift in upcoming_shifts
		]
	return {
		'WORKSHIFT_ENABLED': True,
		'SEMESTER': SEMESTER,
		'CURRENT_SEMESTER': CURRENT_SEMESTER,
		'WORKSHIFT_MANAGER': WORKSHIFT_MANAGER,
		'WORKSHIFT_PROFILE': workshift_profile,
		'days_passed': days_passed,
		'total_days': total_days,
		'semester_percent': semester_percent,
		'upcoming_shifts': zip(upcoming_shifts, happening_now),
		}

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
		  [i.incumbent.user for i in Manager.objects.filter(workshift_manager=True)]
		semester.save()
		return HttpResponseRedirect(wurl("workshift:manage",
										 sem_url=semester.sem_url))

	# TODO: Adding workshift pools? Should we do a separate page for that?

	return render_to_response("start_semester.html", {
		"page_name": page_name,
		"semester_form": semester_form,
	}, context_instance=RequestContext(request))

@get_workshift_profile
def view_semester(request, semester, profile=None):
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
	if profile:
		for form in [VerifyShiftForm, BlownShiftForm, SignInForm, SignOutForm]:
			if form.action_name in request.POST:
				f = form(request.POST, profile=profile)
				if f.is_valid():
					f.save()
					return HttpResponseRedirect(wurl("workshift:view_semester",
													 sem_url=semester.sem_url))
				else:
					for error in f.errors.values():
						messages.add_message(request, messages.ERROR, error)

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

	template_dict["day"] = day
	if day > semester.start_date:
		template_dict["prev_day"] = (day - timedelta(days=1)).strftime("%Y-%m-%d")
	if day < semester.end_date:
		template_dict["next_day"] = (day + timedelta(days=1)).strftime("%Y-%m-%d")

	# Grab the shifts for just today, as well as week-long shifts
	last_sunday = day - timedelta(days=day.weekday() + 1)
	next_sunday = last_sunday + timedelta(weeks=1)

	day_shifts = WorkshiftInstance.objects.filter(date=day)
	week_shifts = WorkshiftInstance.objects.filter(date__gt=last_sunday) \
	  .filter(date__lt=next_sunday) \
	  .filter(week_long=True)

	template_dict["day_shifts"] = [(shift, _get_forms(profile, shift))
								   for shift in day_shifts]
	template_dict["week_shifts"] = [(shift, _get_forms(profile, shift))
									for shift in week_shifts]

	return render_to_response("semester.html", template_dict,
							   context_instance=RequestContext(request))

def _get_forms(profile, shift):
	"""
	Gets the forms for profile interacting with a shift. This includes verify
	shift, mark shift as blown, sign in, and sign out.
	"""
	forms = []
	if not shift.closed and profile:
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
	return forms

@get_workshift_profile
def profile_view(request, semester, targetUsername, profile=None):
	"""
	Show the user their workshift history for the current semester as well as
	upcoming shifts.
	"""
	wprofile = get_object_or_404(WorkshiftProfile, user__username=targetUsername)
	page_name = "{0}'s Workshift Profile".format(wprofile.user.get_full_name())
	return render_to_response("profile.html", {
		"page_name": page_name,
		"profile": wprofile,
	}, context_instance=RequestContext(request))

@get_workshift_profile
def preferences_view(request, semester, targetUsername, profile=None):
	"""
	Show the user their preferences for the given semester.
	"""
	wprofile = get_object_or_404(WorkshiftProfile, user__username=targetUsername)

	if wprofile.user != request.user and not can_manage(request, semester):
		messages.add_message(request, messages.ERROR,
							 MESSAGES['ADMINS_ONLY'])
		return HttpResponseRedirect(wurl('workshift:view_semester',
										 sem_url=semester.sem_url))

	types = WorkshiftType.objects.filter(rateable=True)

	# TODO: Is there a way to create the ratings on first submit, rather than
	# first view?
	if types.count() > 0:
		for wtype in types:
			if wprofile.ratings.filter(workshift_type=wtype).count() == 0:
				rating = WorkshiftRating(workshift_type=wtype)
				rating.save()
				wprofile.ratings.add(rating)
		wprofile.save()

	WorkshiftRatingFormSet = modelformset_factory(
		WorkshiftRating, form=WorkshiftRatingForm,
		)
	TimeBlockFormSet = modelformset_factory(TimeBlock)
	rating_formset = WorkshiftRatingFormSet(
		request.POST or None,
		queryset=wprofile.ratings.all(),
		prefix="rating",
		)
	time_formset = TimeBlockFormSet(
		request.POST or None,
		queryset=wprofile.time_blocks.all(),
		prefix="time",
		)
	note_form = ProfileNoteForm(request.POST or None, instance=wprofile)

	if rating_formset.is_valid() and time_formset.is_valid() and \
	  note_form.is_valid():
		rating_formset.save()
		time_formset.save()
		note_form.save()
		return HttpResponseRedirect(wurl('workshift:view_preferences',
										 sem_url=semester.sem_url,
										 targetUsername=request.user.username))

	page_name = "{0}'s Workshift Preferences".format(
		wprofile.user.get_full_name())
	return render_to_response("preferences.html", {
		"page_name": page_name,
		"profile": wprofile,
		"rating_formset": rating_formset,
		"time_formset": time_formset,
		"note_form": note_form,
	}, context_instance=RequestContext(request))

@get_workshift_profile
def manage_view(request, semester, profile=None):
	"""
	View all members' preferences. This view also includes forms to create an
	entire semester's worth of weekly workshifts.
	"""
	page_name = "Manage Workshift"
	pools = WorkshiftPool.objects.filter(semester=semester)
	full_management = can_manage(request, semester)
	semester_form = None

	if not full_management:
		pools = pools.filter(managers__incumbent__user=request.user)
		if not pools.count():
			messages.add_message(request, messages.ERROR,
								 MESSAGES['ADMINS_ONLY'])
			return HttpResponseRedirect(wurl('workshift:view_semester',
											 sem_url=semester.sem_url))
	else:
		semester_form = FullSemesterForm(request.POST or None,
										 instance=semester)

	return render_to_response("manage.html", {
		"page_name": page_name,
		"pools": pools,
		"full_management": full_management,
		"semester_form": semester_form,
	}, context_instance=RequestContext(request))

@semester_required
@workshift_manager_required
def assign_shifts_view(request, semester):
	"""
	View all members' preferences. This view also includes forms to create an
	entire semester's worth of weekly workshifts.
	"""
	page_name = "Assign Shifts"
	return render_to_response("assign_shifts.html", {
		"page_name": page_name,
	}, context_instance=RequestContext(request))

@semester_required
@workshift_manager_required
def add_workshifter_view(request, semester):
	"""
	Add a new member workshift profile, for people who join mid-semester.
	"""
	page_name = "Add Workshifter"

	add_workshifter_form = AddWorkshifterForm(request.POST or None)

	if add_workshifter_form.is_valid():
		add_workshifter_form.save()
		messages.add_message(request, messages.INFO, "Workshifter added.")
		return HttpResponseRedirect(wurl("workshift:manage",
										 sem_url=semester.sem_url))

	return render_to_response("add_workshifter.html", {
		"page_name": page_name,
		"form": add_workshifter_form,
	}, context_instance=RequestContext(request))

@workshift_manager_required
def add_shift_view(request):
	"""
	View for the workshift manager to create new types of workshifts.
	"""
	page_name = "Add Workshift"
	add_shift_form = AddWorkshiftTypeForm(request.POST or None)
	if add_shift_form.is_valid():
		add_shift_form.save()
		return HttpResponseRedirect(wurl("workshift:list_types"))
	return render_to_response("add_shift.html", {
		"page_name": page_name,
		"form": add_shift_form,
	}, context_instance=RequestContext(request))

@get_workshift_profile
def shift_view(request, semester, pk, profile=None):
	"""
	View the details of a particular RegularWorkshift.
	"""
	shift = get_object_or_404(RegularWorkshift, pk=pk)
	page_name = shift.title

	return render_to_response("view_shift.html", {
		"page_name": page_name,
		"shift": shift,
	}, context_instance=RequestContext(request))

@get_workshift_profile
def edit_shift_view(request, semester, pk, profile=None):
	"""
	View for a manager to edit the details of a particular RegularWorkshift.
	"""
	shift = get_object_or_404(RegularWorkshift, pk=pk)

	user_profile = UserProfile.objects.get(user=request.user)
	managers = shift.pool.managers.filter(incumbent=user_profile)

	if not request.user.is_superuser and not managers.count():
		messages.add_message(request, messages.ERROR,
							 MESSAGES['ADMINS_ONLY'])
		return HttpResponseRedirect(wurl('workshift:view_semester',
										 sem_url=semester.sem_url))

	edit_form = RegularWorkshiftForm(
		request.POST if "edit_shift" in request.POST else None,
		instance=shift,
		)

	if "delete_shift" in request.POST:
		shift.delete()
		return HttpResponseRedirect(wurl('workshift:manage',
										 sem_url=semester.sem_url))
	elif edit_form.is_valid():
		shift = edit_form.save()
		return HttpResponseRedirect(wurl('workshift:view_shift',
										 sem_url=semester.sem_url,
										 pk=pk))

	page_name = "Edit " + shift.title

	return render_to_response("edit_shift.html", {
		"page_name": page_name,
		"shift": shift,
        "edit_form": edit_form,
	}, context_instance=RequestContext(request))

@get_workshift_profile
def instance_view(request, semester, pk, profile=None):
	"""
	View the details of a particular WorkshiftInstance.
	"""
	shift = get_object_or_404(WorkshiftInstance, pk=pk)
	page_name = shift.title

	return render_to_response("view_instance.html", {
		"page_name": page_name,
		"shift": shift,
	}, context_instance=RequestContext(request))

@get_workshift_profile
def edit_instance_view(request, semester, pk, profile=None):
	"""
	View for a manager to edit the details of a particular WorkshiftInstance.
	"""
	shift = get_object_or_404(WorkshiftInstance, pk=pk)

	user_profile = UserProfile.objects.get(user=request.user)
	managers = shift.pool.managers.filter(incumbent=user_profile)

	if not request.user.is_superuser and not managers.count():
		messages.add_message(request, messages.ERROR,
							 MESSAGES['ADMINS_ONLY'])
		return HttpResponseRedirect(wurl('workshift:view_semester',
										 sem_url=semester.sem_url))

	edit_form = WorkshiftInstanceForm(
		request.POST if "edit_shift" in request.POST else None,
		instance=shift,
		)

	if "delete_shift" in request.POST:
		shift.delete()
		HttpResponseRedirect(wurl('workshift:manage',
								  sem_url=semester.sem_url))
	elif edit_form.is_valid():
		shift = edit_form.save()
		return HttpResponseRedirect(wurl('workshift:view_instance',
										 sem_url=semester.sem_url,
										 pk=pk))

	page_name = "Edit " + shift.title

	return render_to_response("edit_shift.html", {
		"page_name": page_name,
		"shift": shift,
        "edit_form": edit_form,
	}, context_instance=RequestContext(request))

@login_required
def list_types_view(request):
	"""
	View the details of a particular WorkshiftType.
	"""
	page_name = "Workshift Types"
	shifts = WorkshiftType.objects.all()
	return render_to_response("list_types.html", {
		"page_name": page_name,
		"shifts": shifts,
		"can_edit": can_manage(request),
	}, context_instance=RequestContext(request))

@login_required
def type_view(request, pk):
	"""
	View the details of a particular WorkshiftType.
	"""
	shift = get_object_or_404(WorkshiftType, pk=pk)
	page_name = shift.title
	return render_to_response("view_type.html", {
		"page_name": page_name,
		"shift": shift,
		"can_edit": can_manage(request),
	}, context_instance=RequestContext(request))

@workshift_manager_required
def edit_type_view(request, pk):
	"""
	View for a manager to edit the details of a particular WorkshiftType.
	"""
	shift = get_object_or_404(WorkshiftType, pk=pk)
	edit_form = WorkshiftTypeForm(
		request.POST if "edit_shift" in request.POST else None,
		instance=shift,
		)

	if "delete_shift" in request.POST:
		# Ask for password to delete shifts?
		shift.delete()
		HttpResponseRedirect(wurl('workshift:list_types'))
	elif edit_form.is_valid():
		shift = edit_form.save()
		return HttpResponseRedirect(wurl('workshift:view_type', pk=pk))

	page_name = "Edit " + shift.title

	return render_to_response("edit_type.html", {
		"page_name": page_name,
		"shift": shift,
        "edit_form": edit_form,
	}, context_instance=RequestContext(request))

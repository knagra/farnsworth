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
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext

from workshift.templatetags.workshift_tags import wurl

from utils.variables import MESSAGES
from base.models import User
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
			return {}
	try:
		workshift_profile = WorkshiftProfile.objects.get(semester=SEMESTER, user=request.user)
	except WorkshiftProfile.DoesNotExist:
		return {'WORKSHIFT_ENABLED': False}
	WORKSHIFT_MANAGER = can_manage(request, SEMESTER)
    # Current semester is for navbar notifications
	try:
		CURRENT_SEMESTER = Semester.objects.get(current=True)
	except Semester.MultipleObjectsReturned:
		CURRENT_SEMESTER = Semester.objects.filter(current=True).latest('start_date')
		workshift_emails = []
		for pos in Manager.objects.filter(workshift_manager=True, active=True):
			if pos.email:
				workshift_emails.append(pos.email)
			elif pos.incumbent.email_visible and pos.incumbent.user.email:
				workshift_emails.append(pos.incumbent.user.email)
		if workshift_emails:
			workshift_email_str = " ({0})".format(
				", ".join(['<a href="mailto:{0}">{0}</a>'.format(i)
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

	pool_forms = []
	try:
		prev_semester = Semester.objects.all()[0]
	except IndexError:
		pass
	else:
		for pool in WorkshiftPool.objects.filter(semester=semester):
			form = StartPoolForm(
				request.POST or None,
				copy=pool,
				prefix="pool-{0}".format(pool.pk),
				)
			pool_forms.append(form)

	if semester_form.is_valid() and all(i.is_valid() for i in pool_forms):
		# And save this semester
		semester = semester_form.save()
		semester.workshift_managers = \
		  [i.incumbent.user for i in Manager.objects.filter(workshift_manager=True)]
		semester.save()
		for pool_form in pool_forms:
			pool_form.save(semester=semester)
		return HttpResponseRedirect(wurl("workshift:manage",
										 sem_url=semester.sem_url))

	# TODO: Adding workshift pools? Should we do a separate page for that?

	return render_to_response("start_semester.html", {
		"page_name": page_name,
		"semester_form": semester_form,
		"pool_forms": pool_forms,
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
	# TODO: Permissions? Should this be open for anyone on the site to view?
	wprofile = get_object_or_404(WorkshiftProfile, user__username=targetUsername)
	if wprofile == profile:
		page_name = "My Workshift Profile"
	else:
		page_name = "{0}'s Workshift Profile".format(wprofile.user.get_full_name())
	past_shifts = WorkshiftInstance.objects.filter(workshifter=wprofile, closed=True)
	regular_shifts = RegularWorkshift.objects.filter(active=True,
													 current_assignee=wprofile)
	return render_to_response("profile.html", {
		"page_name": page_name,
		"profile": wprofile,
		"past_shifts": past_shifts,
		"regular_shifts": regular_shifts,
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

	rating_forms = []
	for wtype in WorkshiftType.objects.filter(rateable=True):
		try:
			rating = wprofile.ratings.get(workshift_type=wtype)
		except WorkshiftRating.DoesNotExist:
			rating = WorkshiftRating(workshift_type=wtype)
		form = WorkshiftRatingForm(
			request.POST or None,
			prefix="rating-{0}".format(wtype.pk),
			instance=rating,
			profile=wprofile,
			)
		rating_forms.append(form)

	time_formset = TimeBlockFormSet(
		request.POST or None,
		prefix="time",
        profile=wprofile,
		)
	note_form = ProfileNoteForm(request.POST or None, instance=wprofile)

	if all(i.is_valid() for i in rating_forms) and time_formset.is_valid() and \
	  note_form.is_valid():
		for form in rating_forms:
			form.save()
		time_formset.save()
		instance = note_form.save()
		messages.add_message(request, messages.INFO, "Preferences saved.")
		return HttpResponseRedirect(wurl('workshift:preferences',
										 sem_url=semester.sem_url,
										 targetUsername=request.user.username))

	if wprofile == profile:
		page_name = "My Workshift Preferences"
	else:
		page_name = "{0}'s Workshift Preferences".format(
		wprofile.user.get_full_name())
	return render_to_response("preferences.html", {
		"page_name": page_name,
		"profile": wprofile,
		"rating_forms": rating_forms,
		"time_formset": time_formset,
		"note_form": note_form,
	}, context_instance=RequestContext(request))

@get_workshift_profile
def profiles_view(request, semester, profile=None):
	page_name = "Workshift Profiles"
	profiles = WorkshiftProfile.objects.filter(semester=semester)
	pools = WorkshiftPool.objects.filter(semester=semester)
	# TODO: Make sure pools and pool hours sort together?
	return render_to_response("profiles.html", {
		"page_name": page_name,
		"workshifters": profiles,
		"pools": pools,
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
		semester_form = FullSemesterForm(
			request.POST if "edit_semester" in request.POST else None,
			instance=semester,
			)

	workshifters = WorkshiftProfile.objects.filter(semester=semester)
	pool_hours = [workshifter.pool_hours.filter(pool__in=pools)
				  for workshifter in workshifters]

	return render_to_response("manage.html", {
		"page_name": page_name,
		"pools": pools,
		"full_management": full_management,
		"semester_form": semester_form,
		"workshifters": zip(workshifters, pool_hours),
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

	existing = [
		i.user.pk for i in WorkshiftProfile.objects.filter(semester=semester)
		]
	users = User.objects.exclude(pk__in=existing)

	if users:
		add_workshifter_form = AddWorkshifterForm(
			request.POST or None,
			semester=semester,
			users=users,
			)

		if add_workshifter_form.is_valid():
			add_workshifter_form.save()
			messages.add_message(request, messages.INFO, "Workshifter added.")
			return HttpResponseRedirect(wurl("workshift:manage",
											 sem_url=semester.sem_url))
	else:
		add_workshifter_form = None

	return render_to_response("add_workshifter.html", {
		"page_name": page_name,
		"add_workshifter_form": add_workshifter_form,
	}, context_instance=RequestContext(request))

@semester_required
@workshift_manager_required
def add_pool_view(request, semester):
	"""
	View for the workshift manager to create new workshift pools (i.e. HI Hours).
	"""
	page_name = "Add Workshift Pool"
	add_pool_form = PoolForm(
		request.POST or None,
		semester=semester,
		full_management=True,
		)
	if add_pool_form.is_valid():
		add_pool_form.save()
		messages.add_message(request, messages.INFO, "Workshift pool added.")
		return HttpResponseRedirect(wurl('workshift:manage',
										 sem_url=semester.sem_url))
	return render_to_response("add_pool.html", {
		"page_name": page_name,
		"add_pool_form": add_pool_form,
		}, context_instance=RequestContext(request))

@semester_required
@workshift_manager_required
def add_shift_view(request, semester):
	"""
	View for the workshift manager to create new types of workshifts.
	"""
	page_name = "Add Workshift"
	pools = WorkshiftPool.objects.filter(semester=semester)
	full_management = can_manage(request, semester)
	if not full_management:
		pools = pools.filter(managers__incumbent__user=request.user)
		if not pools.count():
			messages.add_message(request, messages.ERROR,
								 MESSAGES['ADMINS_ONLY'])
			return HttpResponseRedirect(wurl('workshift:view_semester',
											 sem_url=semester.sem_url))

	if full_management:
		add_type_form = WorkshiftTypeForm(
			request.POST if "add_type" in request.POST else None,
			)
	else:
		add_type_form = None

	add_instance_form = WorkshiftInstanceForm(
		request.POST if "add_instance" in request.POST else None,
		pools=pools,
		semester=semester,
		)
	add_shift_form = RegularWorkshiftForm(
		request.POST if "add_shift" in request.POST else None,
		pools=pools,
		)

	if add_type_form and add_type_form.is_valid():
		add_type_form.save()
		return HttpResponseRedirect(wurl("workshift:manage",
										 sem_url=semester.sem_url))
	elif add_instance_form and add_instance_form.is_valid():
		add_instance_form.save()
		return HttpResponseRedirect(wurl("workshift:manage",
										 sem_url=semester.sem_url))
	elif add_shift_form.is_valid():
		add_shift_form.save()
		return HttpResponseRedirect(wurl("workshift:manage",
										 sem_url=semester.sem_url))
	return render_to_response("add_shift.html", {
		"page_name": page_name,
		"add_type_form": add_type_form,
		"add_instance_form": add_instance_form,
		"add_shift_form": add_shift_form,
	}, context_instance=RequestContext(request))

@get_workshift_profile
def pool_view(request, semester, pk, profile=None):
	pool = get_object_or_404(WorkshiftPool, semester=semester, pk=pk)
	page_name = pool.title

	return render_to_response("view_pool.html", {
		"page_name": page_name,
		"pool": pool,
	}, context_instance=RequestContext(request))

@workshift_manager_required
@get_workshift_profile
def edit_pool_view(request, semester, pk, profile=None):
	pool = get_object_or_404(WorkshiftPool, semester=semester, pk=pk)
	page_name = "Edit " + pool.title
	full_management = can_manage(request, semester)
	managers = pool.managers.filter(incumbent__user=request.user)

	if not full_management and not managers.count():
		messages.add_message(request, messages.ERROR,
							 MESSAGES['ADMINS_ONLY'])
		return HttpResponseRedirect(wurl('workshift:view_semester',
										 sem_url=semester.sem_url))

	edit_pool_form = PoolForm(
		request.POST or None,
		instance=pool,
		full_management=full_management,
		)
	if edit_pool_form.is_valid():
		edit_pool_form.save()
		messages.add_message(request, messages.INFO,
							 "Workshift pool successfully updated.")
		return HttpResponseRedirect(wurl('workshift:manage',
										 sem_url=semester.sem_url))

	return render_to_response("edit_pool.html", {
		"page_name": page_name,
		"edit_pool_form": edit_pool_form,
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
	managers = shift.pool.managers.filter(incumbent__user=request.user)

	if not request.user.is_superuser and not managers.count():
		messages.add_message(request, messages.ERROR,
							 MESSAGES['ADMINS_ONLY'])
		return HttpResponseRedirect(wurl('workshift:view_semester',
										 sem_url=semester.sem_url))

	edit_form = RegularWorkshiftForm(
		request.POST if "edit" in request.POST else None,
		instance=shift,
		)

	if "delete" in request.POST:
		instances = WorkshiftInstance.objects.filter(weekly_workshift=shift)
		info = InstanceInfo(
			title=shift.title,
			description=shift.workshift_type.description,
			pool=shift.pool,
			start_time=shift.start_time,
			end_time=shift.end_time,
			)
		info.save()
		for instance in instances:
			instance.weekly_workshift = None
			instance.info = info
			instance.closed = True
			instance.save()
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
	managers = shift.pool.managers.filter(incumbent__user=request.user)

	if not request.user.is_superuser and not managers.count():
		messages.add_message(request, messages.ERROR,
							 MESSAGES['ADMINS_ONLY'])
		return HttpResponseRedirect(wurl('workshift:view_semester',
										 sem_url=semester.sem_url))

	page_name = "Edit " + shift.title

	edit_form = WorkshiftInstanceForm(
		request.POST if "edit" in request.POST else None,
		instance=shift,
		semester=semester,
		)

	if "delete" in request.POST:
		shift.delete()
		return HttpResponseRedirect(wurl('workshift:manage',
										 sem_url=semester.sem_url))
	elif edit_form.is_valid():
		shift = edit_form.save()
		return HttpResponseRedirect(wurl('workshift:view_instance',
										 sem_url=semester.sem_url,
										 pk=pk))

	return render_to_response("edit_instance.html", {
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
		request.POST or None,
		instance=shift,
		)

	if edit_form.is_valid():
		shift = edit_form.save()
		return HttpResponseRedirect(wurl('workshift:view_type', pk=pk))

	page_name = "Edit " + shift.title

	return render_to_response("edit_type.html", {
		"page_name": page_name,
		"shift": shift,
        "edit_form": edit_form,
	}, context_instance=RequestContext(request))

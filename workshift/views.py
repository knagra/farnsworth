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
from workshift.forms import FullSemesterForm, SemesterForm, StartPoolForm, \
    PoolForm, WorkshiftInstanceForm, VerifyShiftForm, \
    BlownShiftForm, SignInForm, SignOutForm, AddWorkshifterForm, \
    AssignShiftForm, RegularWorkshiftForm, WorkshiftTypeForm, \
    WorkshiftRatingForm, TimeBlockForm, BaseTimeBlockFormSet, \
    TimeBlockFormSet, ProfileNoteForm
from workshift import utils

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
	WORKSHIFT_MANAGER = utils.can_manage(request.user, semester=SEMESTER)
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
	year, season = utils.get_year_season()
	start_date, end_date = utils.get_semester_start_end(year, season)

	semester_form = SemesterForm(
		request.POST or None,
		initial={
			"year": year,
			"season": season,
            "start_date": start_date,
            "end_date": end_date,
            })

	pool_forms = []
	try:
		prev_semester = Semester.objects.all()[0]
	except IndexError:
		pass
	else:
		for pool in WorkshiftPool.objects.filter(semester=prev_semester):
			form = StartPoolForm(
				request.POST or None,
				initial={
					"title": pool.title,
					"hours": pool.hours,
					},
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

	# Forms to interact with workshift
	if profile:
		for form in [VerifyShiftForm, BlownShiftForm, SignInForm, SignOutForm]:
			if form.action_name in request.POST:
				f = form(request.POST, profile=profile)
				if f.is_valid():
					f.save()
					return HttpResponseRedirect(
						wurl("workshift:view_semester", sem_url=semester.sem_url) +
						"?day={0}".format(day) if "day" in request.GET else "")
				else:
					for error in f.errors.values():
						messages.add_message(request, messages.ERROR, error)

	# Grab the shifts for just today, as well as week-long shifts
	last_sunday = day - timedelta(days=day.weekday() + 1)
	next_sunday = last_sunday + timedelta(weeks=1)

	day_shifts = WorkshiftInstance.objects.filter(
        date=day, week_long=False,
        )
	week_shifts = WorkshiftInstance.objects.filter(
        date__gt=last_sunday, date__lte=next_sunday,
        week_long=True,
        )

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
	ret = []
	if not shift.closed and profile:
		if shift.workshifter:
			pool = shift.pool

			if pool.self_verify or shift.workshifter != profile and \
              not shift.auto_verify and not utils.past_verify(shift):
				verify_form = VerifyShiftForm(initial={
					"pk": shift.pk,
					}, profile=profile)
				ret.append(verify_form)

			if pool.any_blown or \
			  pool.managers.filter(incumbent__user=profile.user).count():
				blown_form = BlownShiftForm(initial={
					"pk": shift.pk,
					}, profile=profile)
				ret.append(blown_form)

			if shift.workshifter == profile:
				sign_out_form = SignOutForm(initial={
					"pk": shift.pk,
					}, profile=profile)
				ret.append(sign_out_form)
		else:
			sign_in_form = SignInForm(initial={
				"pk": shift.pk,
				}, profile=profile)
			ret.append(sign_in_form)
	return ret

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
	first_standing, second_standing, third_standing = \
	  any(pool_hours.first_date_standing for pool_hours in wprofile.pool_hours.all()), \
	  any(pool_hours.second_date_standing for pool_hours in wprofile.pool_hours.all()), \
	  any(pool_hours.third_date_standing for pool_hours in wprofile.pool_hours.all())
	return render_to_response("profile.html", {
		"page_name": page_name,
		"profile": wprofile,
		"past_shifts": past_shifts,
		"regular_shifts": regular_shifts,
		"first_standing": first_standing,
		"second_standing": second_standing,
		"third_standing": third_standing,
	}, context_instance=RequestContext(request))

@get_workshift_profile
def preferences_view(request, semester, targetUsername, profile=None):
	"""
	Show the user their preferences for the given semester.
	"""
	wprofile = get_object_or_404(WorkshiftProfile, user__username=targetUsername)

	if wprofile.user != request.user and \
	  not utils.can_manage(request.user, semester=semester):
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
	full_management = utils.can_manage(request.user, semester=semester)
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
	assign_forms = []
	for shift in RegularWorkshift.objects.filter(pool__semester=semester,
												 active=True):
		form = AssignShiftForm(
			request.POST or None,
			prefix="shift-{0}".format(shift.pk),
			instance=shift,
			semester=semester,
			)
		assign_forms.append(form)
	if all(i.is_valid() for i in assign_forms):
		for form in assign_forms:
			form.save()
		messages.add_message(request, messages.INFO, "Workshift assignments saved.")
		if "finalize" in request.POST:
			# TODO: Finalize everything, close preferences, etc?
			return HttpResponseRedirect(wurl('workshift:manage',
											 sem_url=semester.sem_url))
		else:
			return HttpResponseRedirect(wurl('workshift:assign_shifts',
											sem_url=semester.sem_url))
	return render_to_response("assign_shifts.html", {
		"page_name": page_name,
		"assign_forms": assign_forms,
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
	users = User.objects.exclude(pk__in=existing, is_active=True)

	add_workshifter_forms = []
	for user in users:
		form = AddWorkshifterForm(
			request.POST or None,
			prefix="user-{0}".format(user.pk),
			user=user,
			semester=semester,
			)
		add_workshifter_forms.append(form)

	if add_workshifter_forms and \
	  all(form.is_valid() for form in add_workshifter_forms):
		for form in add_workshifter_forms:
			form.save()
		messages.add_message(request, messages.INFO, "Workshifters added.")
		return HttpResponseRedirect(wurl("workshift:manage",
										 sem_url=semester.sem_url))

	return render_to_response("add_workshifter.html", {
		"page_name": page_name,
		"add_workshifter_forms": add_workshifter_forms,
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
	full_management = utils.can_manage(request.user, semester=semester)
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
	if WorkshiftType.objects.count():
		add_shift_form = RegularWorkshiftForm(
			request.POST if "add_shift" in request.POST else None,
			pools=pools,
			semester=semester,
			)
	else:
		add_shift_form = None

	if add_type_form and add_type_form.is_valid():
		add_type_form.save()
		return HttpResponseRedirect(wurl("workshift:manage",
										 sem_url=semester.sem_url))
	elif add_instance_form and add_instance_form.is_valid():
		add_instance_form.save()
		return HttpResponseRedirect(wurl("workshift:manage",
										 sem_url=semester.sem_url))
	elif add_shift_form and add_shift_form.is_valid():
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
	shifts = RegularWorkshift.objects.filter(pool=pool, active=True)

	return render_to_response("view_pool.html", {
		"page_name": page_name,
		"pool": pool,
		"shifts": shifts,
	}, context_instance=RequestContext(request))

@workshift_manager_required
@get_workshift_profile
def edit_pool_view(request, semester, pk, profile=None):
	pool = get_object_or_404(WorkshiftPool, semester=semester, pk=pk)
	page_name = "Edit " + pool.title
	full_management = utils.can_manage(request.user, semester=semester)
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
	if "delete" in request.POST:
		pool.delete()
		return HttpResponseRedirect(wurl('workshift:manage',
										 sem_url=semester.sem_url))
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
		semester=semester,
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
										 pk=shift.pk))

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
	instance = get_object_or_404(WorkshiftInstance, pk=pk)
	page_name = instance.title
	interact_forms = _get_forms(profile, instance)

	for form in [VerifyShiftForm, BlownShiftForm, SignInForm, SignOutForm]:
		if form.action_name in request.POST:
			f = form(request.POST, profile=profile)
			if f.is_valid():
				instance = f.save()
				return HttpResponseRedirect(wurl('workshift:view_instance',
												 sem_url=semester.sem_url,
												 pk=instance.pk))
			else:
				for error in f.errors.values():
					messages.add_message(request, messages.ERROR, error)

	return render_to_response("view_instance.html", {
		"page_name": page_name,
		"instance": instance,
        "interact_forms": interact_forms,
	}, context_instance=RequestContext(request))

@get_workshift_profile
def edit_instance_view(request, semester, pk, profile=None):
	"""
	View for a manager to edit the details of a particular WorkshiftInstance.
	"""
	instance = get_object_or_404(WorkshiftInstance, pk=pk)
	managers = instance.pool.managers.filter(incumbent__user=request.user)

	if not request.user.is_superuser and not managers.count():
		messages.add_message(request, messages.ERROR,
							 MESSAGES['ADMINS_ONLY'])
		return HttpResponseRedirect(wurl('workshift:view_semester',
										 sem_url=semester.sem_url))

	page_name = "Edit " + instance.title

	edit_form = WorkshiftInstanceForm(
		request.POST if "edit" in request.POST else None,
		instance=instance,
		semester=semester,
		)

	if "delete" in request.POST:
		instance.delete()
		return HttpResponseRedirect(wurl('workshift:manage',
										 sem_url=semester.sem_url))
	elif edit_form.is_valid():
		instance = edit_form.save()
		return HttpResponseRedirect(wurl('workshift:view_instance',
										 sem_url=semester.sem_url,
										 pk=instance.pk))

	return render_to_response("edit_instance.html", {
		"page_name": page_name,
		"instance": instance,
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
		"can_edit": utils.can_manage(request.user),
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
		"can_edit": utils.can_manage(request.user),
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

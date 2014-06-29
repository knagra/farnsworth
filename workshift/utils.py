"""
Project: Farnsworth

Authors: Karandeep Singh Nagra and Nader Morshed
"""

from datetime import date, timedelta
from weekday_field.utils import ADVANCED_DAY_CHOICES

from managers.models import Manager
from workshift.models import TimeBlock, ShiftLogEntry, WorkshiftInstance, \
	 Semester, PoolHours, WorkshiftProfile, WorkshiftPool

def can_manage(request, semester=None):
	"""
	Whether a user is allowed to manage a workshift semester. This includes the
	current workshift managers, that semester's workshift managers, and site
	superusers.
	"""
	if semester and request.user in semester.workshift_managers.all():
		return True
	if Manager and Manager.objects.filter(incumbent__user=request.user) \
	  .filter(workshift_manager=True).count() > 0:
		return True
	return request.user.is_superuser

def is_available(workshift_profile, regular_workshift):
	"""
	Check whether a specified user is able to do a specified workshift.
	Parameters:
		workshift_profile is the workshift profile for a user
		regular_workshift is a weekly recurring workshift
	Returns:
		True if the user has enough free time between the shift's start time
			and end time to do the shift's required number of hours.
		False otherwise.
	"""
	if regular_workshift.week_long:
		return True
	day = regular_workshift.day
	start_time = regular_workshift.start_time
	end_time = regular_workshift.end_time
	relevant_blocks = list()
	for block in workshift_profile.time_blocks:
		if block.day == day and block.preference == TimeBlock.BUSY \
		  and block.start_time < end_time \
		  and block.end_time > start_time:
			relevant_blocks.append(block)
	if not relevant_blocks:
		return True
	hours = regular_workshift.hours

def get_year_season(day=None):
	"""
	Returns a guess of the year and season of the current semester.
	"""
	if day is None:
		day = date.today()
	year = day.year

	if day.month > 3 and day.month <= 7:
		season = Semester.SUMMER
	elif day.month > 7 and day.month <= 10:
		season = Semester.FALL
	else:
		season = Semester.SPRING
		if day.month > 10:
			year += 1
	return year, season

def get_semester_start_end(year, season):
	"""
	Returns a guess of the start and end dates for given semester.
	"""
	if season == Semester.SPRING:
		start_month, start_day = 1, 20
		end_month, end_day = 5, 17
	elif season == Semester.SUMMER:
		start_month, start_day = 5, 25
		end_month, end_day = 8, 16
	else:
		start_month, start_day = 8, 24
		end_month, end_day = 12, 20

	return date(year, start_month, start_day), date(year, end_month, end_day)

def get_int_days(days):
	"""
	Converts a string, or list of strings into integers for their respective
	days of the week.
	"""
	if not isinstance(days, list) and not isinstance(days, tuple):
		days = [days]
	ret = []
	for day in days:
		day = [i[0] for i in ADVANCED_DAY_CHOICES if i[1] == day][0]
		if isinstance(day, int):
			ret.append(day)
		else:
			for value in day.strip("[]").split(","):
				value = int(value)
				if value not in ret:
					ret.append(value)
	return ret

def _date_range(start, end, step):
	"""
	'range' for datetime.date
	"""
	day = start
	while day <= end:
		yield day
		day += step

def make_instances(semester, shift):
	today = date.today()
	new_instances = []
	for weekday in shift.days:
		next_day = today + timedelta(days=int(weekday) - today.weekday())
		for day in _date_range(next_day, semester.end_date, timedelta(weeks=1)):
			# Create new instances for the entire semester
			prev_instances = WorkshiftInstance.objects.filter(
				weekly_workshift=shift, date=day, closed=False)
			for instance in prev_instances[shift.count:]:
				instance.delete()
			for i in range(prev_instances.count(), shift.count):
				instance = WorkshiftInstance.objects.create(
					weekly_workshift=shift,
					date=day,
					workshifter=shift.current_assignee,
					hours=shift.hours,
					intended_hours=shift.hours,
					auto_verify=shift.auto_verify,
					week_long=shift.week_long,
					)
				new_instances.append(instance)
		if shift.current_assignee:
			# Update the list of assigned workshifters
			for instance in WorkshiftInstance.objects.filter(weekly_workshift=shift,
															 date__gte=today):
				log = ShiftLogEntry(
					person=shift.current_assignee,
					entry_type=ShiftLogEntry.ASSIGNED,
					)
				log.save()
				instance.logs.add(log)
				instance.save()
	return new_instances

def make_workshift_pool_hours(semester, profiles=None, pools=None,
							  primary_hours=None):
	if profiles is None:
		profiles = WorkshiftProfile.objects.filter(semester=semester)
	if pools is None:
		pools = WorkshiftPool.objects.filter(semester=semester)

	for profile in profiles:
		for pool in pools:
			if not profile.pool_hours.filter(pool=pool):
				if pool.is_primary and primary_hours:
					hours = primary_hours
				else:
					hours = pool.hours
				pool_hours = PoolHours.objects.create(
					pool=pool,
					hours=hours,
					)
				profile.pool_hours.add(pool_hours)
		profile.save()

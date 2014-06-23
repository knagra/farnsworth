"""
Project: Farnsworth

Authors: Karandeep Singh Nagra and Nader Morshed
"""

from managers.models import Manager
from workshift.models import TimeBlock

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
	

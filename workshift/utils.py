
try:
	from managers.models import Manager
except ImportError:
	Manager = None

def can_manage(request, semester=None):
	"""
	Whether a user is allowed to manage a workshift semester. This includes the
	current workshift managers, that semester's workshift managers, and site
	superusers.
	"""
	if semester:
		semester_managers = semeter.workshift_managers.all()
	if Manager:
		workshift_managers = Manager.objects.filter(incumbent__user=request.user) \
		  .filter(workshift_manager=True)
	return request.user in semester_managers or \
	  workshift_managers.count() or \
	  request.user.is_superuser

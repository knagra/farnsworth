
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
	if semester and request.user in semester.workshift_managers.all():
		return True
	if Manager and Manager.objects.filter(incumbent__user=request.user) \
	  .filter(workshift_manager=True).count() > 0:
		return True
	return request.user.is_superuser

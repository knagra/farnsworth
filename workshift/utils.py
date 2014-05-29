
from django.shortcuts import get_object_or_404

from workshift.models import Semester

def current_semester():
	"""
	Returns the currently active workshift semester.
	"""
	return get_object_or_404(Semester, current=True)

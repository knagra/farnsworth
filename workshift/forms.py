
from django import forms

from workshift.models import *

class SemesterForm(forms.ModelForm):
	class Meta:
		model = Semester
		exclude = ["workshift_managers", "preferences_open", "current"]

class RegularWorkshiftForm(forms.ModelForm):
	class Meta:
		model = RegularWorkshift
		fields = "__all__"

class WorkshiftInstanceForm(forms.ModelForm):
	class Meta:
		model = WorkshiftInstance
		exclude = ["weekly_workshift", "info", "intended_hours", "log"]

	# Include methods to modify info / weekly_workshift
	def save(self, *args, **kwargs):
		shift = super(WorkshiftInstanceForm, self).save(*args, **kwargs)
		# ...
		return shift

class WorkshiftTypeForm(forms.ModelForm):
	class Meta:
		model = WorkshiftType
		fields = "__all__"

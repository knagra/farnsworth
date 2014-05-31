
from django import forms

from workshift.models import *

class SemesterForm(forms.ModelForm):
	class Meta:
		model = Semester
		exclude = ["workshift_managers", "preferences_open", "current"]

	def save(self, *args, **kwargs):
		semester = super(SemesterForm, self).save(*args, **kwargs)

		# Set current to false for previous semesters
		for semester in Semester.objects.all():
			semester.current = False
			semester.save()

		semester.current = True
		semester.preferences_open = True
		semeseter.save(*args, **kwargs)
		semester.workshift_managers = \
		  [i.incumbent for i in Managers.objects.filter(workshift_manager=True)]

		return semester

class RegularWorkshiftForm(forms.ModelForm):
	class Meta:
		model = RegularWorkshift
		fields = "__all__"

class WorkshiftInstanceForm(forms.ModelForm):
	class Meta:
		model = WorkshiftInstance
		exclude = ["weekly_workshift", "info", "intended_hours", "log"]

	title = forms.CharField(
		widget=forms.Textarea(),
		help_text="Description of the shift.",
		)

	info_fields = ["title", "description", "pool", "start_time", "end_time"]

	def __init__(self, *arg, **kwargs):
		if "instance" in kwargs:
			instance = kwargs["instance"]
			initial = kwargs.get("initial", {})

			for field in self.info_fields:
				initial.setdefault("title", getattr(instance.get_info(), field))

			if instance.weekly_workshift:
				for field in self.info_fields:
					self.fields[field].widget.attrs['readonly'] = True

			kwargs["initial"] = initial

		super(WorkshiftInstanceForm, self).__init__(*args, **kwargs)

	def save(self, *args, **kwargs):
		instance = super(WorkshiftInstanceForm, self).save(*args, **kwargs)
		if instance.info:
			for field in self.info_fields:
				setattr(instance.info, field, self.cleaned_data[field])
		return instance

class WorkshiftTypeForm(forms.ModelForm):
	class Meta:
		model = WorkshiftType
		fields = "__all__"

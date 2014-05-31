
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

class InteractShiftForm(forms.Form):
	pk = forms.IntegerField(widget=forms.HiddenInput())

	def __init__(self, *args, **kwargs):
		self.profile = kwargs.pop("profile")
		super(InteractShiftForm, self).__init__(*args, **kwargs)

	def clean_pk(self):
		try:
			shift = WorkshiftInstance.objects.get(pk=self.cleaned_data["pk"])
		except WorkshiftInstance.DoesNotExist:
			raise ValidationError("Workshift does not exist.")
		if shift.closed:
			raise ValidationError("Workshift has been closed.")
		return shift

class VerifyShiftForm(InteractShiftForm):
	def clean_pk(self):
		shift = super(VerifyShiftForm, self).clean_pk()

		if not shift.workshifter:
			raise ValidationError("Workshift is not filled.")

	def save(self):
		entry = ShiftLogEntry(
			person=self.profile,
			entry_type=ShiftLogEntry.VERIFY,
			)
		entry.save()

		pk = self.cleaned_data["pk"]
		instance = WorkshiftInstance.objects.get(pk=pk)
		instance.verifier = profile
		instance.closed = True
		instance.log.add(entry)
		instance.save()

		instance.workshifter.pool_hours += instance.hours
		instance.workshifter.save()

class BlownShiftForm(InteractShiftForm):
	def clean_pk(self):
		shift = super(BlownShiftForm, self).clean_pk()

		if not shift.workshifter:
			raise ValidationError("Workshift is not filled.")

	def save(self):
		entry = ShiftLogEntry(
			person=self.profile,
			entry_type=ShiftLogEntry.BLOWN,
			)
		entry.save()

		pk = self.cleaned_data["pk"]
		instance = WorkshiftInstance.objects.get(pk=pk)
		instance.blown = True
		instance.closed = True
		instance.log.add(entry)
		instance.save()

		instance.workshifter.pool_hours -= instance.hours
		instance.workshifter.save()

class SignInForm(InteractShiftForm):
	def clean_pk(self):
		shift = super(SignInForm, self).clean_pk()

		if shift.workshifter:
			raise ValidationError("Workshift is currently filled.")

	def save(self):
		entry = ShiftLogEntry(
			person=self.profile,
			entry_type=ShiftLogEntry.SIGNIN,
			)
		entry.save()

		pk = self.cleaned_data["pk"]
		instance = WorkshiftInstance.objects.get(pk=pk)
		instance.workshifter = profile
		instance.log.add(entry)
		instance.save()

class SignOutForm(InteractShiftForm):
	def clean_pk(self):
		shift = super(SignOutForm, self).clean_pk()

		if shift.workshifter != self.profile:
			raise ValidationError("Cannot sign out of others' workshift.")

	def save(self):
		entry = ShiftLogEntry(
			person=self.profile,
			entry_type=ShiftLogEntry.SIGNOUT,
			)
		entry.save()

		pk = self.cleaned_data["pk"]
		instance = WorkshiftInstance.objects.get(pk=pk)
		instance.workshifter = None
		instance.log.add(entry)
		instance.save()

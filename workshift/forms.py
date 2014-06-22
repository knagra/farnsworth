"""
Project: Farnsworth

Authors: Karandeep Singh Nagra and Nader Morshed
"""


from django import forms
from django.forms.models import BaseModelFormSet, modelformset_factory

from base.models import UserProfile
from managers.models import Manager
from workshift.models import Semester, WorkshiftPool, WorkshiftType, \
	TimeBlock, WorkshiftRating, PoolHours, WorkshiftProfile, \
	RegularWorkshift, ShiftLogEntry, InstanceInfo, WorkshiftInstance

valid_time_formats = ['%H:%M', '%I:%M%p', '%I:%M %p']

class FullSemesterForm(forms.ModelForm):
	class Meta:
		model = Semester
		fields = "__all__"

class SemesterForm(forms.ModelForm):
	class Meta:
		model = Semester
		exclude = ("workshift_managers", "preferences_open", "current",)

	def save(self):
		semester = super(SemesterForm, self).save()

		# Set current to false for previous semesters
		for semester in Semester.objects.all():
			semester.current = False
			semester.save()

		semester.current = True
		semester.preferences_open = True
		semester.save()

		# TODO Copy workshift and pools over from previous semester?
		pool = WorkshiftPool(
			semester=semester,
			)
		pool.save()
		pool.managers = Manager.objects.filter(workshift_manager=True)
		pool.save()

		# TODO Create this semester's workshift profiles
		for uprofile in UserProfile.objects.filter(status=UserProfile.RESIDENT):
			profile = WorkshiftProfile(
				user=uprofile.user,
				semester=semester,
				)
			profile.save()

			hours = PoolHours(pool=pool)
			hours.save()

			profile.pool_hours.add(hours)
			profile.save()

		return semester

class StartPoolForm(forms.Form):
	copy_pool = forms.BooleanField(initial=True)

	def __init__(self, *args, **kwargs):
		self.copy = kwargs.pop('copy')
		super(StartPoolForm, self).__init__(*args, **kwargs)

	def save(self, semester):
		if self.cleaned_data['copy_pool']:
			self.copy.pk = None
			self.copy.semester = semester
			self.copy.first_fine_date = None
			self.copy.second_fine_date = None
			self.copy.third_fine_date = None
			self.copy.save()

class PoolForm(forms.ModelForm):
	class Meta:
		model = WorkshiftPool
		exclude = ("semester",)

	def __init__(self, *args, **kwargs):
		self.full_management = kwargs.pop('full_management', False)
		self.semester = kwargs.pop('semester', None)
		super(PoolForm, self).__init__(*args, **kwargs)
		if not self.full_management:
			self.fields['managers'].widget.attrs['readonly'] = True

	def save(self):
		pool = super(PoolForm, self).save(commit=False)
		if self.semester:
			pool.semester = self.semester
		pool.save()
		self.save_m2m()
		for profile in WorkshiftProfile.objects.filter(semester=pool.semester):
			if not profile.pool_hours.filter(pool=pool):
				pool_hours = PoolHours(
					pool=pool,
					hours=pool.hours,
					)
				pool_hours.save()
				profile.pool_hours.add(pool_hours)
				profile.save()
		return pool

class RegularWorkshiftForm(forms.ModelForm):
	class Meta:
		model = RegularWorkshift
		fields = "__all__"

class WorkshiftInstanceForm(forms.ModelForm):
	class Meta:
		model = WorkshiftInstance
		exclude = ("weekly_workshift", "info", "intended_hours", "logs",
				   "blown", "semester", "verifier")

	title = forms.CharField(
		max_length=255,
		help_text="The title for this workshift",
		)
	description = forms.CharField(
		widget=forms.Textarea(),
		required=False,
		help_text="Description of the shift.",
		)
	pool = forms.ModelChoiceField(
		queryset=WorkshiftPool.objects.filter(semester__current=True),
		help_text="The workshift pool for this shift.",
		)
	start_time = forms.TimeField(
		required=False,
		widget=forms.TimeInput(format='%I:%M %p'),
		input_formats=valid_time_formats,
		help_text="The earliest time this shift should be started.",
		)
	end_time = forms.TimeField(
		required=False,
		widget=forms.TimeInput(format='%I:%M %p'),
		input_formats=valid_time_formats,
		help_text="The latest time this shift should be completed.",
		)

	info_fields = ("title", "description", "pool", "start_time", "end_time")

	def __init__(self, *args, **kwargs):
		self.pools = kwargs.pop('pools', None)
		instance = kwargs.get('instance', None)
		self.semester = kwargs.pop('semester')

		if instance:
			initial = kwargs.get("initial", {})

			# Django ModelForms don't play nicely with foreign fields, so we
			# will just manually pre-fill them if an instance is available.
			for field in self.info_fields:
				initial.setdefault(field, getattr(instance, field))

			kwargs["initial"] = initial
			self.new = False
		else:
			self.new = True

		super(WorkshiftInstanceForm, self).__init__(*args, **kwargs)

		# If this is a regular workshift, disable title, description, etc
		# from being edited
		if instance and instance.weekly_workshift:
			for field in self.info_fields:
				self.fields[field].widget.attrs['readonly'] = True
		if self.pools:
			self.fields['pool'].queryset = self.pools

		# Move the forms for title, description, etc to the top
		keys = self.fields.keyOrder
		for field in reversed(self.info_fields):
			keys.remove(field)
			keys.insert(0, field)

	def save(self):
		instance = super(WorkshiftInstanceForm, self).save(commit=False)
		instance.semester = self.semester
		if self.new:
			instance.intended_hours = instance.hours
			if instance.workshifter:
				instance.save()
				log = ShiftLogEntry(
					person=instance.workshifter,
					entry_type=ShiftLogEntry.ASSIGNED,
					)
				log.save()
				instance.logs.add(log)
			info = InstanceInfo()
		elif not instance.info:
			if any(self.cleaned_data[field] != getattr(instance, field)
				   for field in self.info_fields):
				info = InstanceInfo()
				instance.weekly_workshift = None
			else:
				info = None
		else:
			info = instance.info
		if info:
			for field in self.info_fields:
				setattr(info, field, self.cleaned_data[field])
			info.save()
			instance.info = info
		instance.save()
		self.save_m2m()
		return instance

class InteractShiftForm(forms.Form):
	pk = forms.IntegerField(widget=forms.HiddenInput())

	def __init__(self, *args, **kwargs):
		self.profile = kwargs.pop("profile")
		super(InteractShiftForm, self).__init__(*args, **kwargs)

	def clean_pk(self):
		pk = self.cleaned_data["pk"]
		try:
			shift = WorkshiftInstance.objects.get(pk=pk)
		except WorkshiftInstance.DoesNotExist:
			raise forms.ValidationError("Workshift does not exist.")
		if shift.closed:
			raise forms.ValidationError("Workshift has been closed.")
		return shift

# TODO: SellShiftForm

class VerifyShiftForm(InteractShiftForm):
	title_short = "V"
	title_long = "Verify"
	action_name = "verify_shift"

	def clean_pk(self):
		shift = super(VerifyShiftForm, self).clean_pk()

		if not shift.workshifter:
			raise forms.ValidationError("Workshift is not filled.")
		if not shift.pool.self_verify and shift.workshifter == self.profile:
			raise forms.ValidationError("Workshifter cannot verify self.")

		return shift

	def save(self):
		entry = ShiftLogEntry(
			person=self.profile,
			entry_type=ShiftLogEntry.VERIFY,
			)
		entry.save()

		instance = self.cleaned_data["pk"]
		instance.verifier = self.profile
		instance.closed = True
		instance.logs.add(entry)
		instance.save()

		pool_hours = instance.workshifter.pool_hours \
		  .get(pool=instance.get_info().pool)
		pool_hours.standing += instance.hours
		pool_hours.save()

class BlownShiftForm(InteractShiftForm):
	title_short = "B"
	title_long = "Blown"
	action_name = "blown_shift"

	def clean_pk(self):
		shift = super(BlownShiftForm, self).clean_pk()

		if not shift.workshifter:
			raise forms.ValidationError("Workshift is not filled.")
		pool = shift.pool
		if not pool.any_blown and \
		  pool.managers.filter(incumbent__user=self.profile.user).count() == 0:
			raise forms.ValidationError("You are not a workshift manager.")

		return shift

	def save(self):
		entry = ShiftLogEntry(
			person=self.profile,
			entry_type=ShiftLogEntry.BLOWN,
			)
		entry.save()

		instance = self.cleaned_data["pk"]
		instance.blown = True
		instance.closed = True
		instance.logs.add(entry)
		instance.save()

		pool_hours = instance.workshifter.pool_hours \
		  .get(pool=instance.get_info().pool)
		pool_hours.standing -= instance.hours
		pool_hours.save()

class SignInForm(InteractShiftForm):
	title_short = "I"
	title_long = "Sign In"
	action_name = "sign_in"

	def clean_pk(self):
		shift = super(SignInForm, self).clean_pk()

		if shift.workshifter:
			raise forms.ValidationError("Workshift is currently filled.")

		return shift

	def save(self):
		entry = ShiftLogEntry(
			person=self.profile,
			entry_type=ShiftLogEntry.SIGNIN,
			)
		entry.save()

		instance = self.cleaned_data["pk"]
		instance.workshifter = self.profile
		instance.logs.add(entry)
		instance.save()

class SignOutForm(InteractShiftForm):
	title_short = "O"
	title_long = "Sign Out"
	action_name = "sign_out"

	def clean_pk(self):
		shift = super(SignOutForm, self).clean_pk()

		if shift.workshifter != self.profile:
			raise forms.ValidationError("Cannot sign out of others' workshift.")

		return shift

	def save(self):
		entry = ShiftLogEntry(
			person=self.profile,
			entry_type=ShiftLogEntry.SIGNOUT,
			)
		entry.save()

		instance = self.cleaned_data["pk"]
		instance.workshifter = None
		instance.logs.add(entry)
		instance.save()

class AddWorkshifterForm(forms.ModelForm):
	class Meta:
		model = WorkshiftProfile
		exclude = ("semester", "ratings", "pool_hours", "time_blocks",)

	def __init__(self, *args, **kwargs):
		self.semester = kwargs.pop("semester")
		self.users = kwargs.pop('users', None)
		super(AddWorkshifterForm, self).__init__(*args, **kwargs)
		if self.users:
			self.fields["user"].queryset = self.users

	def save(self):
		profile = super(AddWorkshifterForm, self).save(commit=False)

		profile.semester = self.semester
		profile.save()

		for pool in WorkshiftPool.objects.filter(semester=self.semester):
			hours = PoolHours(pool=pool)
			hours.save()
			profile.pool_hours.add(hours)

		profile.save()

		return profile

class RegularWorkshiftForm(forms.ModelForm):
	start_time = forms.TimeField(widget=forms.TimeInput(format='%I:%M %p'),
								 input_formats=valid_time_formats)
	end_time = forms.TimeField(widget=forms.TimeInput(format='%I:%M %p'),
							   input_formats=valid_time_formats)
	class Meta:
		model = RegularWorkshift
		fields = "__all__"

	def __init__(self, *args, **kwargs):
		self.pools = kwargs.pop('pools', None)
		super(RegularWorkshiftForm, self).__init__(*args, **kwargs)
		if self.pools:
			self.fields['pool'].queryset = self.pools

class WorkshiftTypeForm(forms.ModelForm):
	class Meta:
		model = WorkshiftType
		fields = "__all__"

	def __init__(self, *args, **kwargs):
		kwargs.setdefault('auto_id', '%s')
		kwargs.setdefault('label_suffix', '')
		super(WorkshiftTypeForm, self).__init__(*args, **kwargs)

class WorkshiftRatingForm(forms.ModelForm):
	class Meta:
		model = WorkshiftRating
		fields = ("rating",)

	def __init__(self, *args, **kwargs):
		self.profile = kwargs.pop('profile')
		super(WorkshiftRatingForm, self).__init__(*args, **kwargs)
		try:
			self.title = self.instance.workshift_type.title
		except WorkshiftType.DoesNotExist:
			self.title = ""

	def save(self):
		rating = super(WorkshiftRatingForm, self).save()
		if not self.profile.ratings.filter(pk=rating.pk):
			self.profile.ratings.add(rating)
		self.profile.save()
		return rating

class TimeBlockForm(forms.ModelForm):
	start_time = forms.TimeField(widget=forms.TimeInput(format='%I:%M %p'),
								 input_formats=valid_time_formats)
	end_time = forms.TimeField(widget=forms.TimeInput(format='%I:%M %p'),
							   input_formats=valid_time_formats)
	class Meta:
		model = TimeBlock
		fields = "__all__"

	# def clean(self):
	# 	if self.cleaned_data['start_time'] > self.cleaned_data['end_time']:
	# 		raise forms.ValidationError('Start time later than end time.')
	# 	return self.cleaned_data

	def is_valid(self):
		if not super(TimeBlockForm, self).is_valid():
			return False
		if 'start_time' in self.cleaned_data and \
		  'end_time' in self.cleaned_data and \
		  self.cleaned_data['start_time'] > self.cleaned_data['end_time']:
			self._errors['start_time'] = forms.util.ErrorList([u"Start time later than end time."])
			self._errors['end_time'] = forms.util.ErrorList([u"Start time later than end time."])
			return False
		return True

class BaseTimeBlockFormSet(BaseModelFormSet):
	def __init__(self, *args, **kwargs):
		self.profile = kwargs.pop('profile')
		super(BaseTimeBlockFormSet, self).__init__(*args, **kwargs)
		self.queryset = self.profile.time_blocks.all()

	def save(self):
		blocks = super(BaseTimeBlockFormSet, self).save()
		for block in blocks:
			if not self.profile.time_blocks.filter(pk=block.pk):
				self.profile.time_blocks.add(block)
		self.profile.save()
		return blocks

TimeBlockFormSet = modelformset_factory(
	TimeBlock, form=TimeBlockForm, formset=BaseTimeBlockFormSet,
	can_delete=True, extra=1, max_num=50,
	help_texts=dict(preference="", day="", start_time="", end_time=""),
	)

class ProfileNoteForm(forms.ModelForm):
	class Meta:
		model = WorkshiftProfile
		fields = ("note",)

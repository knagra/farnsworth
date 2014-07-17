"""
Project: Farnsworth

Authors: Karandeep Singh Nagra and Nader Morshed
"""

from collections import OrderedDict

from django import forms
from django.conf import settings
from django.db.models import Q
from django.forms.models import BaseModelFormSet, modelformset_factory

from weekday_field.forms import AdvancedWeekdayFormField

from base.models import UserProfile
from managers.models import Manager
from workshift.models import Semester, WorkshiftPool, WorkshiftType, \
    TimeBlock, WorkshiftRating, WorkshiftProfile, \
    RegularWorkshift, ShiftLogEntry, InstanceInfo, WorkshiftInstance, \
    PoolHours, SELF_VERIFY, AUTO_VERIFY, WORKSHIFT_MANAGER_VERIFY, \
    POOL_MANAGER_VERIFY, ANY_MANAGER_VERIFY, OTHER_VERIFY, VERIFY_CHOICES
from workshift import utils

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

        # Create the primary workshift pool
        pool = WorkshiftPool.objects.create(
            semester=semester,
            is_primary=True,
            )
        pool.managers = Manager.objects.filter(workshift_manager=True)
        pool.save()

        # Create this semester's workshift profiles
        for uprofile in UserProfile.objects.filter(status=UserProfile.RESIDENT):
            profile = WorkshiftProfile.objects.create(
                user=uprofile.user,
                semester=semester,
                )

        utils.make_workshift_pool_hours(semester)

        return semester

class StartPoolForm(forms.ModelForm):
    copy_pool = forms.BooleanField(initial=True)

    class Meta:
        model = WorkshiftPool
        fields = ("title", "hours")
        help_texts = {
            "title": "",
            "hours": "",
            }

    def save(self, semester):
        if self.cleaned_data['copy_pool']:
            pool = super(StartPoolForm, self).save(commit=False)
            pool.semester = semester
            pool.save()

            utils.make_workshift_pool_hours(pool.semester, pools=[pool])

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
        prev_pool = self.instance
        new = prev_pool.pk is None
        pool = super(PoolForm, self).save(commit=False)
        if self.semester:
            pool.semester = self.semester
        pool.save()
        self.save_m2m()

        if not new:
            for pool_hours in PoolHours.objects.filter(pool=pool):
                if pool_hours.hours == prev_pool.hours:
                    pool_hours.hours = pool.hours
                    pool_hours.save()
        else:
            utils.make_workshift_pool_hours(self.semester, pools=[pool])
        return pool

class WorkshiftInstanceForm(forms.ModelForm):
    class Meta:
        model = WorkshiftInstance
        exclude = ("weekly_workshift", "info", "intended_hours", "logs",
                   "blown", "semester", "verifier", "liable",)

    weekly_workshift = forms.ModelChoiceField(
        required=False,
        queryset=RegularWorkshift.objects.filter(active=True),
        help_text="Link this instance to a regular shift.",
        )
    title = forms.CharField(
        required=False,
        max_length=255,
        help_text="The title for this workshift",
        )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(),
        help_text="Description of the shift.",
        )
    pool = forms.ModelChoiceField(
        required=False,
        queryset=WorkshiftPool.objects.filter(semester__current=True),
        help_text="The workshift pool for this shift.",
        )
    verify = forms.ChoiceField(
        required=False,
        choices=VERIFY_CHOICES,
        help_text="Who is able to mark this shift as completed.",
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
    week_long = forms.BooleanField(
        required=False,
        help_text="If this shift is for the entire week.",
        )

    info_fields = ("title", "description", "pool", "verify",
                   "start_time", "end_time", "week_long")

    def __init__(self, *args, **kwargs):
        self.pools = kwargs.pop('pools', None)
        self.semester = kwargs.pop('semester')

        super(WorkshiftInstanceForm, self).__init__(*args, **kwargs)

        if self.pools:
            self.fields['pool'].queryset = self.pools
            if self.pools.filter(is_primary=True):
                self.pools.initial = self.pools.filter(is_primary=True)[0]

        # Move the forms for title, description, etc to the top
        keys = ["weekly_workshift"] + list(self.info_fields)
        keys += [i for i in self.fields if i not in keys]
        new_fields = OrderedDict((i, self.fields[i]) for i in keys)
        self.fields = new_fields

        # Fill in the default values
        for field in ["weekly_workshift"] + list(self.info_fields):
            if self.instance.pk is not None:
                self.fields[field].initial = getattr(self.instance, field)

    def clean(self):
        cleaned_data = super(WorkshiftInstanceForm, self).clean()
        shift = cleaned_data["weekly_workshift"]
        title = cleaned_data["title"]
        if not shift and not title:
            self.add_error("weekly_workshift", "Pick a shift or give this instance a title.")
            self.add_error("title", "Pick a shift or give this instance a title.")
        elif not shift and not self.cleaned_data["pool"]:
            self.add_error("pool", "This field is required.")
        return cleaned_data

    def save(self):
        prev_instance = self.instance
        new = prev_instance.pk is None
        instance = super(WorkshiftInstanceForm, self).save(commit=False)
        instance.semester = self.semester
        instance.weekly_workshift = self.cleaned_data["weekly_workshift"]
        if instance.weekly_workshift:
            if instance.info:
                instance.info.delete()
        if new:
            instance.intended_hours = instance.hours
        if not self.cleaned_data["weekly_workshift"]:
            if not instance.info and \
              (not instance.weekly_workshift or
               any(self.cleaned_data[field] != getattr(instance, field)
                   for field in self.info_fields)):
                instance.info = InstanceInfo.objects.create()
                instance.weekly_workshift = None
            if instance.info:
                for field in self.info_fields:
                    setattr(instance.info, field, self.cleaned_data[field])
                instance.info.save()
        instance.save()
        self.save_m2m()
        if new and instance.workshifter or \
          prev_instance.workshifter != instance.workshifter:
            log = ShiftLogEntry.objects.create(
                person=instance.workshifter,
                entry_type=ShiftLogEntry.ASSIGNED,
                )
            instance.logs.add(log)
            instance.save()
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

class VerifyShiftForm(InteractShiftForm):
    title_short = '<span class="glyphicon glyphicon-ok"></span>'
    title_long = "Verify"
    action_name = "verify_shift"

    def clean_pk(self):
        instance = super(VerifyShiftForm, self).clean_pk()

        workshifter = instance.workshifter or instance.liable
        user_profile = UserProfile.objects.get(user=self.profile.user)
        managers = Manager.objects.filter(incumbent=user_profile)

        if not workshifter:
            raise forms.ValidationError("Workshift is not filled.")
        if user_profile.status not in \
          [UserProfile.RESIDENT, UserProfile.BOARDER]:
            raise forms.ValidationError("Verifier is not a member or boarder.")

        if instance.verify == AUTO_VERIFY:
            raise forms.ValidationError("Workshift is automatically verified.")
        elif instance.verify == WORKSHIFT_MANAGER_VERIFY:
            if not any(i.workshift_manager for i in managers):
                raise forms.ValidationError("Verifier is not a workshift manager.")
        elif instance.verify == POOL_MANAGER_VERIFY:
            if not set(managers).intersection(instance.pool.managers):
                raise forms.ValidationError("Verifier is not in the list of managers for this pool.")
        elif instance.verify == ANY_MANAGER_VERIFY:
            if not managers.count():
                raise forms.ValidationError("Verifier is not a manager.")
        elif instance.verify == OTHER_VERIFY:
            if workshifter == self.profile:
                raise forms.ValidationError("Workshifter cannot verify self.")

        if utils.past_verify(instance):
            raise forms.ValidationError("Workshift is past verification period.")

        return instance

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

        workshifter = instance.workshifter or instance.liable

        pool_hours = workshifter.pool_hours.get(pool=instance.get_info().pool)
        pool_hours.standing += instance.hours
        pool_hours.save()

        return instance

class BlownShiftForm(InteractShiftForm):
    title_short = '<span class="glyphicon glyphicon-remove"></span>'
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
        entry = ShiftLogEntry.objects.create(
            person=self.profile,
            entry_type=ShiftLogEntry.BLOWN,
            )

        instance = self.cleaned_data["pk"]
        instance.blown = True
        instance.closed = True
        instance.logs.add(entry)
        instance.save()

        pool_hours = instance.workshifter.pool_hours \
          .get(pool=instance.get_info().pool)
        pool_hours.standing -= instance.hours
        pool_hours.save()

        return instance

class SignInForm(InteractShiftForm):
    title_short = '<span class="glyphicon glyphicon-log-in"></span>'
    title_long = "Sign In"
    action_name = "sign_in"

    def clean_pk(self):
        shift = super(SignInForm, self).clean_pk()

        if shift.workshifter:
            raise forms.ValidationError("Workshift is currently filled.")

        return shift

    def save(self):
        entry = ShiftLogEntry.objects.create(
            person=self.profile,
            entry_type=ShiftLogEntry.SIGNIN,
            )

        instance = self.cleaned_data["pk"]
        instance.workshifter = self.profile
        instance.liable = None
        instance.logs.add(entry)
        instance.save()

        return instance

class SignOutForm(InteractShiftForm):
    title_short = '<span class="glyphicon glyphicon-log-out"></span>'
    title_long = "Sign Out"
    action_name = "sign_out"

    def clean_pk(self):
        shift = super(SignOutForm, self).clean_pk()

        if shift.workshifter != self.profile:
            raise forms.ValidationError("Not signed into workshift.")

        return shift

    def save(self):
        entry = ShiftLogEntry.objects.create(
            person=self.profile,
            entry_type=ShiftLogEntry.SIGNOUT,
            )

        instance = self.cleaned_data["pk"]
        instance.workshifter = None
        if utils.past_sign_out(instance):
            instance.liable = self.profile
        instance.logs.add(entry)
        instance.save()

        return instance

class AddWorkshifterForm(forms.Form):
    add_profile = forms.BooleanField(initial=True)
    hours = forms.DecimalField(min_value=0, max_digits=7, decimal_places=2,
                               initial=settings.DEFAULT_WORKSHIFT_HOURS)

    def __init__(self, *args, **kwargs):
        self.semester = kwargs.pop("semester")
        self.user = kwargs.pop("user")
        if "initial" not in kwargs:
            try:
                pool = WorkshiftPool.objects.get(semester=self.semester,
                                                 is_primary=True)
            except (WorkshiftPool.DoesNotExist, WorkshiftPool.MultipleObjectsReturned):
                pass
            else:
                kwargs["initial"] = {"hours": pool.hours}
        super(AddWorkshifterForm, self).__init__(*args, **kwargs)

    def save(self):
        if self.cleaned_data['add_profile']:
            profile = WorkshiftProfile.objects.create(
                user=self.user,
                semester=self.semester,
                )

            utils.make_workshift_pool_hours(
                self.semester, profiles=[profile],
                primary_hours=self.cleaned_data["hours"],
                )

            return profile

class AssignShiftForm(forms.ModelForm):
    class Meta:
        model = RegularWorkshift
        fields = ("current_assignees",)
        labels = {
            "current_assignees": "",
            }
        help_texts = {
            "current_assignees": "",
            }

    def __init__(self, *args, **kwargs):
        self.semester = kwargs.pop('semester')
        super(AssignShiftForm, self).__init__(*args, **kwargs)
        start, end = self.instance.start_time, self.instance.end_time
        if start and end:
            query = []
            for profile in WorkshiftProfile.objects.filter(semester=self.semester):
                time_blocks = profile.time_blocks.filter(
                    Q(start_time__lt=start, end_time__gt=start) |
                    Q(start_time__lt=end, end_time__gt=end) |
                    Q(start_time__gt=start, end_time__lt=end),
                    preference=TimeBlock.BUSY, day__in=self.instance.days,
                    )
                if not time_blocks:
                    query.append(profile.pk)

            self.fields['current_assignees'].queryset = \
              WorkshiftProfile.objects.filter(pk__in=query)

class RegularWorkshiftForm(forms.ModelForm):
    days = AdvancedWeekdayFormField()
    start_time = forms.TimeField(widget=forms.TimeInput(format='%I:%M %p'),
                                 input_formats=valid_time_formats)
    end_time = forms.TimeField(widget=forms.TimeInput(format='%I:%M %p'),
                               input_formats=valid_time_formats)
    class Meta:
        model = RegularWorkshift
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        self.pools = kwargs.pop('pools', None)
        self.semester = kwargs.pop('semester')
        super(RegularWorkshiftForm, self).__init__(*args, **kwargs)
        if self.pools:
            self.fields['pool'].queryset = self.pools

    def clean(self):
        data = super(RegularWorkshiftForm, self).clean()
        if data['week_long']:
            data["days"] = []
        if data['count'] < len(data['current_assignees']):
            raise forms.ValidationError(
                "Not enough shifts to cover the workshifters you selected."
                )
        return data

    def save(self):
        prev_shift = self.instance
        new = prev_shift.pk is None
        shift = super(RegularWorkshiftForm, self).save()
        if not new:
            # Nuke all future instances and just re-create them anew
            WorkshiftInstance.objects.filter(
                weekly_workshift=shift, closed=False).delete()
            utils.make_instances(
                semester=self.semester,
                shifts=[shift],
                )
        else:
            utils.make_instances(
                semester=self.semester,
                shifts=[shift],
                )
        return shift

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

    def clean(self):
        cleaned_data = super(TimeBlockForm, self).clean()
        if 'start_time' in cleaned_data and \
          'end_time' in cleaned_data and \
          cleaned_data['start_time'] > cleaned_data['end_time']:
            self.add_error('start_time', u"Start time later than end time.")
            self.add_error('end_time', u"Start time later than end time.")
        return cleaned_data

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

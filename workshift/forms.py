"""
Project: Farnsworth

Authors: Karandeep Singh Nagra and Nader Morshed
"""

from __future__ import absolute_import

from collections import OrderedDict

from django import forms
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Q
from django.forms.models import BaseModelFormSet, modelformset_factory

from notifications import notify
from django_select2.widgets import Select2MultipleWidget, Select2Widget

from base.models import UserProfile
from managers.models import Manager
from workshift.models import Semester, WorkshiftPool, WorkshiftType, \
    TimeBlock, WorkshiftRating, WorkshiftProfile, \
    RegularWorkshift, ShiftLogEntry, InstanceInfo, WorkshiftInstance, \
    PoolHours, AUTO_VERIFY, WORKSHIFT_MANAGER_VERIFY, \
    POOL_MANAGER_VERIFY, ANY_MANAGER_VERIFY, OTHER_VERIFY, VERIFY_CHOICES
from workshift import utils
from workshift.templatetags.workshift_tags import currency

valid_time_formats = ['%H:%M', '%I:%M%p', '%I:%M %p']


class FullSemesterForm(forms.ModelForm):
    class Meta:
        model = Semester
        exclude = (
            "workshift_managers",
        )


class SemesterForm(forms.ModelForm):
    class Meta:
        model = Semester
        exclude = (
            "workshift_managers",
            "preferences_open",
            "current",
        )


class StartPoolForm(forms.ModelForm):
    copy_pool = forms.BooleanField(initial=True)

    class Meta:
        model = WorkshiftPool
        fields = (
            "title",
            "hours",
        )
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


class CloseSemesterForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.semester = kwargs.pop("semester")
        super(CloseSemesterForm, self).__init__(*args, **kwargs)

    def save(self):
        self.semester.current = False
        self.semester.save(update_fields=["current"])


class OpenSemesterForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.semester = kwargs.pop("semester")
        super(OpenSemesterForm, self).__init__(*args, **kwargs)

    def save(self):
        for semester in Semester.objects.filter(current=True):
            semester.current = False
            semester.save(update_fields=["current"])
        self.semester.current = True
        self.semester.save(update_fields=["current"])


class PoolForm(forms.ModelForm):
    class Meta:
        model = WorkshiftPool
        exclude = (
            "semester",
        )
        widgets = {
            "managers": Select2MultipleWidget(),
        }

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
        pool.save(update_fields=["semester"])
        self.save_m2m()
        return pool


class SwitchSemesterForm(forms.Form):
    semester = forms.ModelChoiceField(
        queryset=Semester.objects.all(),
    )

    def save(self):
        return self.cleaned_data["semester"]


class WorkshiftInstanceForm(forms.ModelForm):
    class Meta:
        model = WorkshiftInstance
        exclude = (
            "weekly_workshift",
            "info",
            "intended_hours",
            "logs",
            "blown",
            "semester",
            "verifier",
            "liable",
            "closed",
        )
        widgets = {
            "workshifter": Select2Widget,
        }

    weekly_workshift = forms.ModelChoiceField(
        required=False,
        queryset=RegularWorkshift.objects.filter(active=True),
        help_text="Link this instance to a regular shift.",
        widget=Select2Widget,
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
        widget=Select2Widget,
    )
    verify = forms.ChoiceField(
        required=False,
        choices=VERIFY_CHOICES,
        help_text="Who is able to mark this shift as completed.",
        widget=Select2Widget,
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

    info_fields = (
        "title",
        "description",
        "pool",
        "verify",
        "start_time",
        "end_time",
        "week_long",
    )

    def __init__(self, *args, **kwargs):
        self.pools = kwargs.pop('pools', None)
        self.semester = kwargs.pop('semester')
        self.edit_hours = kwargs.pop("edit_hours", True)

        super(WorkshiftInstanceForm, self).__init__(*args, **kwargs)

        self.fields["weekly_workshift"].queryset = \
            self.fields["weekly_workshift"].queryset.filter(
                pool__semester=self.semester,
            )

        # Don't allow editing hours through this form if a view doesn't allow
        # it, we have a separate form for that which requires a note as well.
        if not self.edit_hours:
            del self.fields["hours"]

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
        return instance


class AnonymousUserLogin(forms.Form):
    """
    Allows members logged in as the anonymous user to quickly enter their
    username and password from the semester page in order to verify a shift or
    mark it as blown.
    """
    profile = forms.ModelChoiceField(
        queryset=WorkshiftProfile.objects.all(),
        widget=Select2Widget,
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput,
    )

    def __init__(self, *args, **kwargs):
        self.semester = kwargs.pop("semester")
        super(AnonymousUserLogin, self).__init__(*args, **kwargs)
        self.fields["profile"].queryset = WorkshiftProfile.objects.filter(
            semester=self.semester,
        )

    def clean(self):
        profile = self.cleaned_data.get("profile")
        password = self.cleaned_data.get("password")

        if profile and password:
            user_cache = authenticate(
                username=profile.user.username,
                password=password,
            )
            if user_cache is None:
                raise forms.ValidationError(
                    "Password is incorrect. Note that this field is case-sensitive.",
                    code="invalid_login",
                )
            elif not user_cache.is_active:
                raise forms.ValidationError(
                    AuthenticationForm.error_messages["inactive"],
                    code="inactive",
                )

        return self.cleaned_data

    def confirm_login_allowed(self, user):
        super(AnonymousUserLogin, self).confirm_login_allowed(user)
        if WorkshiftProfile.objects.filter(
                user=user,
                semester=self.semester,
        ).count() == 0:
            raise forms.ValidationError(
                "You do not have a workshift profile for this semester.",
            )

    def save(self):
        return self.cleaned_data["profile"]


class InteractShiftForm(forms.Form):
    pk = forms.IntegerField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        self.profile = kwargs.pop("profile")
        self.undo = kwargs.pop("undo", False)
        super(InteractShiftForm, self).__init__(*args, **kwargs)

    def clean_pk(self):
        pk = self.cleaned_data["pk"]
        if self.profile is None:
            raise forms.ValidationError(
                "You do not have a workshift profile for this semester.",
            )
        try:
            shift = WorkshiftInstance.objects.get(pk=pk)
        except WorkshiftInstance.DoesNotExist:
            raise forms.ValidationError("Workshift does not exist.")
        if shift.closed and not self.undo:
            raise forms.ValidationError("Workshift has been closed.")
        return shift


def _undo_verify_blown(instance, pool_hours):
    if instance.blown:
        instance.blown = False
        instance.closed = False
        pool_hours.standing += instance.hours

    if instance.verifier:
        instance.verifier = None
        instance.closed = False
        pool_hours.standing -= instance.hours


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

        if utils.past_verify(instance) and not self.undo:
            raise forms.ValidationError("Workshift is past verification period.")

        return instance

    def save(self, note=None):
        instance = self.cleaned_data["pk"]
        workshifter = instance.workshifter or instance.liable
        pool_hours = workshifter.pool_hours.get(pool=instance.pool)

        # Check if the shift was previously verified or marked as blown
        _undo_verify_blown(instance, pool_hours)

        instance.verifier = self.profile
        instance.closed = True
        instance.save(update_fields=["blown", "verifier", "closed"])

        instance.logs.add(
            ShiftLogEntry.objects.create(
                person=self.profile,
                entry_type=ShiftLogEntry.VERIFY,
                note=note,
            )
        )

        pool_hours.standing += instance.hours
        pool_hours.save(update_fields=["standing"])

        if self.profile != workshifter:
            notify.send(
                self.profile.user,
                verb="verified",
                action_object=instance,
                recipient=workshifter.user,
            )

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
           not utils.can_manage(self.profile.user, semester=shift.semester, pool=pool):
            raise forms.ValidationError("You are not a workshift manager.")

        return shift

    def save(self, note=None):
        instance = self.cleaned_data["pk"]
        workshifter = instance.workshifter or instance.liable
        pool_hours = workshifter.pool_hours.get(pool=instance.pool)

        # Check if the shift was previously verified or marked as blown
        _undo_verify_blown(instance, pool_hours)

        # Close the shift
        instance.blown = True
        instance.closed = True
        instance.save(update_fields=["blown", "verifier", "closed"])

        instance.logs.add(
            ShiftLogEntry.objects.create(
                person=self.profile,
                entry_type=ShiftLogEntry.BLOWN,
                note=note,
            )
        )

        # Update the workshifter's hours
        pool_hours.standing -= instance.hours
        pool_hours.save(update_fields=["standing"])

        # Notify the workshifter as well as the workshift manager
        targets = []
        if self.profile != instance.workshifter:
            targets.append(instance.workshifter.user)
        for manager in instance.pool.managers.all():
            if manager.incumbent and manager.incumbent.user != self.profile.user:
                targets.append(manager.incumbent.user)
        for target in targets:
            notify.send(
                self.profile.user,
                verb="marked as blown",
                action_object=instance,
                recipient=target,
            )

        return instance


class UndoShiftForm(InteractShiftForm):
    title_short = '<span class="glyphicon glyphicon-remove-circle"></span>'
    title_long = "Undo"
    action_name = "undo"

    def __init__(self, *args, **kwargs):
        super(UndoShiftForm, self).__init__(*args, **kwargs)
        self.undo = True

    @staticmethod
    def check_marked_blown(instance, profile):
        if instance.logs.count() > 0:
            latest = instance.logs.latest("entry_time")
            if latest.entry_type == ShiftLogEntry.BLOWN and latest.person == profile:
                return True

        return False

    def clean_pk(self):
        instance = super(UndoShiftForm, self).clean_pk()

        if self.profile is not None:
            if instance.verifier != self.profile and \
               not UndoShiftForm.check_marked_blown(instance, self.profile):
                raise forms.ValidationError(
                    "You cannot undo anything for this workshift.",
                )

        return instance

    def save(self, note=None):
        instance = self.cleaned_data["pk"]
        workshifter = instance.workshifter or instance.liable
        pool_hours = workshifter.pool_hours.get(pool=instance.pool)

        # Check if the shift was previously verified or marked as blown
        marked_blown = UndoShiftForm.check_marked_blown(instance, self.profile)

        _undo_verify_blown(instance, pool_hours)
        instance.save(update_fields=["verifier", "blown", "closed"])
        pool_hours.save(update_fields=["standing"])

        if marked_blown:
            instance.logs.add(
                ShiftLogEntry.objects.create(
                    person=self.profile,
                    entry_type=ShiftLogEntry.UNBLOWN,
                    note=note,
                )
            )
            verb = "marked as unblown"
        else:
            instance.logs.add(
                ShiftLogEntry.objects.create(
                    person=self.profile,
                    entry_type=ShiftLogEntry.UNVERIFY,
                    note=note,
                )
            )
            verb = "unverified"

        # Notify the workshifter as well as the workshift manager
        targets = []

        if self.profile != instance.workshifter:
            targets.append(workshifter.user)

        for manager in instance.pool.managers.all():
            if manager.incumbent and manager.incumbent.user != self.profile.user:
                targets.append(manager.incumbent.user)

        for target in targets:
            notify.send(
                self.profile,
                verb=verb,
                action_object=instance,
                recipient=target,
            )

        return instance


class NoteForm(forms.Form):
    note = forms.CharField(
        required=False,
    )

    def save(self):
        return self.cleaned_data["note"]


class SignInForm(InteractShiftForm):
    title_short = '<span class="glyphicon glyphicon-log-in"></span>'
    title_long = "Sign In"
    action_name = "sign_in"

    def clean_pk(self):
        shift = super(SignInForm, self).clean_pk()

        if shift.workshifter:
            raise forms.ValidationError("Workshift is currently filled.")

        return shift

    def save(self, note=None):
        instance = self.cleaned_data["pk"]
        instance.workshifter = self.profile
        instance.liable = None
        instance.save(update_fields=["workshifter", "liable"])

        instance.logs.add(
            ShiftLogEntry.objects.create(
                person=self.profile,
                entry_type=ShiftLogEntry.SIGNIN,
                note=note,
            )
        )

        return instance


class SignOutForm(InteractShiftForm):
    title_short = '<span class="glyphicon glyphicon-log-out"></span>'
    title_long = "Sign Out"
    action_name = "sign_out"

    def clean_pk(self):
        shift = super(SignOutForm, self).clean_pk()

        if shift.workshifter is None and shift.liable is None:
            raise forms.ValidationError(
                "No one is signed into this workshift.",
            )

        return shift

    def save(self, note=None):
        instance = self.cleaned_data["pk"]
        liable = False
        workshifter = instance.workshifter or instance.liable

        if workshifter != self.profile:
            notify.send(
                self.profile.user,
                verb="signed you out of",
                action_object=instance,
                recipient=workshifter.user,
            )
            if note is None:
                note = "Signed out by {}".format(
                    self.profile
                )
        else:
            if utils.past_sign_out(instance):
                liable = True

        instance.workshifter = None

        if liable:
            instance.liable = workshifter
        else:
            instance.liable = None

        instance.save(update_fields=["workshifter", "liable"])

        instance.logs.add(
            ShiftLogEntry.objects.create(
                person=workshifter,
                entry_type=ShiftLogEntry.SIGNOUT,
                note=note,
            )
        )

        return instance


class EditHoursForm(forms.Form):
    hours = forms.DecimalField(
        min_value=0,
        max_digits=7,
        decimal_places=2,
        initial=settings.DEFAULT_WORKSHIFT_HOURS,
    )
    note = forms.CharField(
        required=True,
    )

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop("instance")
        self.profile = kwargs.pop("profile")
        if "initial" not in kwargs:
            kwargs["initial"] = {}
        kwargs["initial"].setdefault("hours", self.instance.hours)
        super(EditHoursForm, self).__init__(*args, **kwargs)

    def save(self):
        hours = self.cleaned_data["hours"]

        if self.instance.workshifter and self.instance.closed:
            # Remove the hours we gave them previously
            pool_hours = self.instance.workshifter.pool_hours.get(
                pool=self.instance.pool,
            )
            pool_hours.standing -= self.instance.hours

            # Then give them the hours for this shift
            pool_hours.standing += hours
            pool_hours.save(update_fields=["standing"])

        self.instance.hours = hours
        self.instance.save(update_fields=["hours"])

        self.instance.logs.add(
            ShiftLogEntry.objects.create(
                person=self.profile,
                note=self.cleaned_data["note"],
                hours=hours,
                entry_type=ShiftLogEntry.MODIFY_HOURS,
            )
        )

        return self.instance


class AddWorkshifterForm(forms.Form):
    add_profile = forms.BooleanField(
        initial=True,
        required=False,
    )
    hours = forms.DecimalField(
        min_value=0,
        max_digits=7,
        decimal_places=2,
        initial=settings.DEFAULT_WORKSHIFT_HOURS,
    )

    def __init__(self, *args, **kwargs):
        self.semester = kwargs.pop("semester")
        self.user = kwargs.pop("user")
        if "initial" not in kwargs:
            try:
                pool = WorkshiftPool.objects.get(
                    semester=self.semester,
                    is_primary=True,
                )
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


class FillShiftsForm(forms.Form):
    message = "Created"

    def __init__(self, *args, **kwargs):
        self.name = "fill_{}_shifts".format(self.shift_name)
        self.button_text = "Fill in {} shifts".format(self.shift_name)

        if self.name not in kwargs.get("data", {}):
            kwargs["data"] = None

        self.semester = kwargs.pop("semester")

        super(FillShiftsForm, self).__init__(*args, **kwargs)


class FillRegularShiftsForm(FillShiftsForm):
    shift_name = "regular"

    def save(self):
        from workshift.fill import fill_regular_shifts
        return fill_regular_shifts(semester=self.semester)


class FillSocialShiftsForm(FillShiftsForm):
    shift_name = "social"

    def save(self):
        from workshift.fill import fill_social_shifts
        return fill_social_shifts(semester=self.semester)


class FillHumorShiftsForm(FillShiftsForm):
    shift_name = "humor"

    def save(self):
        from workshift.fill import fill_humor_shifts
        return fill_humor_shifts(semester=self.semester)


class FillBathroomShiftsForm(FillShiftsForm):
    shift_name = "bathroom"

    def save(self):
        from workshift.fill import fill_bathroom_shifts
        return fill_bathroom_shifts(semester=self.semester)


class FillHIShiftsForm(FillShiftsForm):
    shift_name = "HI"

    def save(self):
        from workshift.fill import fill_hi_shifts
        return fill_hi_shifts(semester=self.semester)


class ResetAllShiftsForm(forms.Form):
    name = "reset_all_shifts"
    button_text = "Remove all shifts"
    message = "Removed"

    def __init__(self, *args, **kwargs):
        if self.name not in kwargs.get("data", {}):
            kwargs["data"] = None

        self.semester = kwargs.pop("semester")

        super(ResetAllShiftsForm, self).__init__(*args, **kwargs)

    def save(self):
        from workshift.fill import reset_all_shifts
        return reset_all_shifts(semester=self.semester)


class AutoAssignShiftForm(forms.Form):
    name = "auto_assign_shifts"
    text = "Auto assign shifts"

    pool = forms.ModelChoiceField(
        required=True,
        queryset=WorkshiftPool.objects.filter(semester__current=True),
        help_text="Auto-assign all recurring workshifts for this pool.",
    )

    def __init__(self, *args, **kwargs):
        self.semester = kwargs.pop('semester')
        super(AutoAssignShiftForm, self).__init__(*args, **kwargs)
        self.fields['pool'].queryset = \
          WorkshiftPool.objects.filter(semester=self.semester)
        try:
            primary = self.fields['pool'].queryset.get(is_primary=True)
        except WorkshiftPool.DoesNotExist:
            pass
        else:
            self.fields['pool'].initial = primary

    def save(self):
        unfinished = utils.auto_assign_shifts(
            self.semester, pool=self.cleaned_data['pool'],
        )
        return unfinished


class RandomAssignInstancesForm(forms.Form):
    name = "random_assign_instances"
    text = "Randomly assign shift instances"

    pool = forms.ModelChoiceField(
        required=True,
        queryset=WorkshiftPool.objects.filter(semester__current=True),
        help_text="Randomly assign all single instances of workshifts for this pool.",
    )

    def __init__(self, *args, **kwargs):
        self.semester = kwargs.pop('semester')
        super(RandomAssignInstancesForm, self).__init__(*args, **kwargs)
        for title in ["Humor", "Bathroom"]:
            try:
                primary = self.fields['pool'].queryset.get(title__contains=title)
            except (WorkshiftPool.DoesNotExist, WorkshiftPool.MultipleObjectsReturned):
                pass
            else:
                self.fields['pool'].initial = primary
                break

    def save(self):
        unfinished = utils.randomly_assign_instances(
            self.semester, self.cleaned_data["pool"],
        )
        return unfinished


class ClearAssignmentsForm(forms.Form):
    name = "clear_assignments"
    text = "Clear all shift assignments"

    pool = forms.ModelChoiceField(
        required=True,
        queryset=WorkshiftPool.objects.filter(semester__current=True),
        help_text="Clear all recurring workshift assignments for this pool.",
    )

    def __init__(self, *args, **kwargs):
        self.semester = kwargs.pop('semester')
        super(ClearAssignmentsForm, self).__init__(*args, **kwargs)
        self.fields['pool'].queryset = \
          WorkshiftPool.objects.filter(semester=self.semester)
        try:
            primary = self.fields['pool'].queryset.get(is_primary=True)
        except WorkshiftPool.DoesNotExist:
            pass
        else:
            self.fields['pool'].initial = primary

    def save(self):
        utils.clear_all_assignments(self.semester, self.cleaned_data["pool"])


class AssignShiftForm(forms.ModelForm):
    class Meta:
        model = RegularWorkshift
        fields = (
            "current_assignees",
        )
        labels = {
            "current_assignees": "",
        }
        help_texts = {
            "current_assignees": "",
        }
        widgets = {
            "current_assignees": Select2MultipleWidget(),
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
                    preference=TimeBlock.BUSY, day=self.instance.day,
                )
                if not time_blocks:
                    query.append(profile.pk)

            self.fields['current_assignees'].queryset = \
              WorkshiftProfile.objects.filter(pk__in=query)


class AdjustHoursForm(forms.ModelForm):
    class Meta:
        model = PoolHours
        fields = (
            "hours",
            "hour_adjustment",
        )
        help_texts = {
            "hours": "",
            "hour_adjustment": "",
        }
        labels = {
            "hours": "Hour Requirement",
            "hour_adjustment": "Hour Adjustment",
        }


class RegularWorkshiftForm(forms.ModelForm):
    start_time = forms.TimeField(
        widget=forms.TimeInput(format='%I:%M %p'),
        input_formats=valid_time_formats,
        required=False,
    )
    end_time = forms.TimeField(
        widget=forms.TimeInput(format='%I:%M %p'),
        input_formats=valid_time_formats,
        required=False,
    )

    class Meta:
        model = RegularWorkshift
        exclude = (
            "week_long",
            "is_manager_shift",
        )
        widgets = {
            "workshift_type": Select2Widget,
            "pool": Select2Widget,
            "day": Select2Widget,
            "verify": Select2Widget,
            "current_assignees": Select2MultipleWidget,
        }
        help_texts = {
            "current_assignees": "",
        }

    def __init__(self, *args, **kwargs):
        self.pools = kwargs.pop('pools', None)
        self.semester = kwargs.pop('semester')
        super(RegularWorkshiftForm, self).__init__(*args, **kwargs)
        if self.pools:
            self.fields['pool'].queryset = self.pools
        self.fields["current_assignees"].queryset = WorkshiftProfile.objects.filter(
            semester=self.semester,
        )

    def clean(self):
        data = super(RegularWorkshiftForm, self).clean()
        if data['count'] < len(data['current_assignees']):
            raise forms.ValidationError(
                "Not enough shifts to cover the workshifters you selected."
            )
        return data


class WorkshiftTypeForm(forms.ModelForm):
    class Meta:
        model = WorkshiftType
        fields = "__all__"
        widgets = {
            "assignment": Select2Widget,
        }

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('auto_id', '%s')
        kwargs.setdefault('label_suffix', '')
        read_only = kwargs.pop("read_only", False)

        super(WorkshiftTypeForm, self).__init__(*args, **kwargs)

        if read_only:
            for field in self.fields.keys():
                self.fields[field].widget.attrs['readonly'] = True


class WorkshiftRatingForm(forms.ModelForm):
    class Meta:
        model = WorkshiftRating
        fields = (
            "rating",
        )

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
        return rating


class TimeBlockForm(forms.ModelForm):
    start_time = forms.TimeField(
        widget=forms.TimeInput(format='%I:%M %p'),
        input_formats=valid_time_formats,
    )
    end_time = forms.TimeField(
        widget=forms.TimeInput(format='%I:%M %p'),
        input_formats=valid_time_formats,
    )
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
        return blocks


TimeBlockFormSet = modelformset_factory(
    TimeBlock, form=TimeBlockForm, formset=BaseTimeBlockFormSet,
    can_delete=True, extra=1, max_num=50,
    help_texts=dict(preference="", day="", start_time="", end_time=""),
)


class AddRegularWorkshiftForm(forms.ModelForm):
    start_time = forms.TimeField(
        widget=forms.TimeInput(format='%I:%M %p'),
        input_formats=valid_time_formats,
        required=False,
    )
    end_time = forms.TimeField(
        widget=forms.TimeInput(format='%I:%M %p'),
        input_formats=valid_time_formats,
        required=False,
    )

    class Meta:
        model = RegularWorkshift
        fields = (
            "pool",
            "day",
            "count",
            "hours",
            "start_time",
            "end_time",
        )
        help_texts = {
            "pool": "",
            "day": "",
            "count": "",
            "hours": "",
            "start_time": "",
            "end_time": "",
        }
        widgets = {
            "pool": Select2Widget,
            "day": Select2Widget,
        }

    def clean(self):
        cleaned_data = super(AddRegularWorkshiftForm, self).clean()
        if 'start_time' in cleaned_data and \
          'end_time' in cleaned_data and \
          cleaned_data['start_time'] is not None and \
          cleaned_data['end_time'] is not None and \
          cleaned_data['start_time'] > cleaned_data['end_time']:
            self.add_error('start_time', u"Start time later than end time.")
            self.add_error('end_time', u"Start time later than end time.")
        return cleaned_data


class BaseRegularWorkshiftFormSet(BaseModelFormSet):
    def __init__(self, *args, **kwargs):
        self.pools = kwargs.pop("pools", None)

        super(BaseRegularWorkshiftFormSet, self).__init__(*args, **kwargs)

        if self.pools:
            for form in self.forms:
                form.fields["pool"].queryset = self.pools

    def save(self, workshift_type):
        shifts = super(BaseRegularWorkshiftFormSet, self).save(commit=False)

        for shift in shifts:
            shift.workshift_type = workshift_type
            shift.save()

        return shifts


RegularWorkshiftFormSet = modelformset_factory(
    RegularWorkshift, form=AddRegularWorkshiftForm,
    formset=BaseRegularWorkshiftFormSet,
    can_delete=True, extra=1, max_num=50,
)


class ProfileNoteForm(forms.ModelForm):
    class Meta:
        model = WorkshiftProfile
        fields = (
            "note",
        )


# I recommend red wine and a late night walk along a lake
FINE_DATE_CHOICES = (
    ("1", "First Fine Date"),
    ("2", "Second Fine Date"),
    ("3", "Third Fine Date"),
)


class FineDateForm(forms.Form):
    pool = forms.ModelChoiceField(
        queryset=WorkshiftPool.objects.none(),
        help_text="The workshift pool to calculate fines for.",
        widget=Select2Widget,
    )
    period = forms.ChoiceField(
        choices=FINE_DATE_CHOICES,
        help_text="Which period to generate fines for. This will overwrite previous "
        "fines if any have been calculated for that period.",
    )
    offset = forms.DecimalField(
        max_digits=7,
        decimal_places=2,
        initial=0,
        help_text="Offset (in hours) to apply to everyone's workshift standing, "
        "useful if you are fining people after their standings were reduced on "
        "Sunday by 5 hours.",
    )
    threshold = forms.DecimalField(
        max_value=0,
        max_digits=7,
        decimal_places=2,
        initial=-2,
        help_text="Only members below this threshold (in hours) will be fined, "
        "though they will be fined for all of their hours, including those up to "
        "the threshold.",
    )

    def __init__(self, *args, **kwargs):
        self.semester = kwargs.pop("semester")
        super(FineDateForm, self).__init__(*args, **kwargs)
        self.fields["pool"].queryset = WorkshiftPool.objects.filter(semester=self.semester)
        try:
            self.fields["pool"].initial = WorkshiftPool.objects.get(
                semester=self.semester,
                is_primary=True,
            )
        except (WorkshiftPool.DoesNotExist, WorkshiftPool.MultipleObjectsReturned):
            pass

    def save(self, clear=False):
        pool = self.cleaned_data["pool"]
        period = self.cleaned_data["period"]
        offset = self.cleaned_data["offset"]
        threshold = self.cleaned_data["threshold"]

        fined = []

        for profile in WorkshiftProfile.objects.filter(semester=self.semester):
            pool_hours = profile.pool_hours.get(pool=pool)
            if clear:
                if period == "1":
                    pool_hours.first_date_standing = None
                elif period == "2":
                    pool_hours.second_date_standing = None
                else:
                    pool_hours.third_date_standing = None
                pool_hours.save(update_fields=[
                    "first_date_standing",
                    "second_date_standing",
                    "third_date_standing",
                ])
                notify.send(
                    pool,
                    verb="had its workshift fine cleared.",
                    recipient=profile.user,
                )
                continue

            standing = pool_hours.standing + offset

            if standing < threshold or clear:
                fine = standing * self.semester.rate
                if period == "1":
                    pool_hours.first_date_standing = fine
                elif period == "2":
                    pool_hours.second_date_standing = fine
                else:
                    pool_hours.third_date_standing = fine
                pool_hours.save(update_fields=[
                    "first_date_standing",
                    "second_date_standing",
                    "third_date_standing",
                ])
                fined.append(profile)
                notify.send(
                    pool,
                    verb="generated a workshift fine of {0}"
                    .format(currency(fine)),
                    recipient=profile.user,
                )

        return fined

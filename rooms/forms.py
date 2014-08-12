"""
Project: Farnsworth

Authors: Karandeep Singh Nagra and Nader Morshed
"""

from django import forms
from django.forms.models import BaseModelFormSet, modelformset_factory

from utils.funcs import form_add_error
from utils.variables import MESSAGES
from base.models import UserProfile
from rooms.models import Room, PreviousResident

class RoomForm(forms.ModelForm):
    ''' Form to create or edit a room. '''
    class Meta:
        model = Room
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super(RoomForm, self).__init__(*args, **kwargs)
        self.fields["current_residents"].queryset = UserProfile.objects.filter(status=UserProfile.RESIDENT)

    def clean_title(self):
        title = self.cleaned_data["title"]
        query = Room.objects.filter(title=title)
        if self.instance:
            query = query.exclude(pk=self.instance.pk)
        if query.count():
            raise forms.ValidationError("A room with this title already exists.")
        return title

    def clean(self):
        occupancy = self.cleaned_data.get("occupancy", 1)
        if self.cleaned_data["current_residents"].count() > occupancy:
            raise forms.ValidationError("There are more residents than the room has occupancy for.")
        return self.cleaned_data

class ResidentForm(forms.ModelForm):
    class Meta:
        model = PreviousResident
        fields = ("resident", "start_date", "end_date")

class BaseResidentFormSet(BaseModelFormSet):
    def __init__(self, *args, **kwargs):
        self.room = kwargs.pop('room')
        super(BaseResidentFormSet, self).__init__(*args, **kwargs)
        self.queryset = PreviousResident.objects.filter(room=self.room)

    def save(self):
        prev_residents = super(BaseResidentFormSet, self).save(commit=False)
        for prev in prev_residents:
            prev.room = self.room
            prev.save()
        for prev in self.deleted_objects:
            prev.delete()
        return prev_residents

ResidentFormSet = modelformset_factory(
    PreviousResident, form=ResidentForm, formset=BaseResidentFormSet,
    can_delete=True, extra=1, max_num=50,
    help_texts=dict(resident="", start_date="", end_date="")
    )

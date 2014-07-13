"""
Project: Farnsworth

Authors: Karandeep Singh Nagra and Nader Morshed
"""

from django import forms

from utils.variables import MESSAGES
from base.models import UserProfile
from rooms.models import Room

class RoomForm(forms.ModelForm):
    ''' Form to create or edit a room. '''
    class Meta:
        model = Room
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super(RoomForm, self).__init__(*args, **kwargs)
        self.fields["current_residents"].queryset = UserProfile.objects.filter(status=UserProfile.RESIDENT)

    def is_valid(self, instance=False):
        if not super(RoomForm, self).is_valid():
            return False
        elif self.cleaned_data["current_residents"].count() > self.cleaned_data["occupancy"]:
            self._errors['current_residents'] = forms.util.ErrorList([u"There are more current residents than occupancy"])
            return False
        return True

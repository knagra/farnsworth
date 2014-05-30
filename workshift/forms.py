
from django import forms

from workshift.models import *

class SemesterForm(forms.ModelForm):
    class Meta:
        model = Semester
        exclude = ["workshift_managers", "preferences_open", "current"]

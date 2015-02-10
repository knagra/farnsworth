'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''

from django import forms
from django.conf import settings
from django.utils.timezone import now

from notifications import notify
from django_select2.widgets import Select2Widget

from utils.variables import time_formats, ANONYMOUS_USERNAME, MESSAGES
from managers.models import Manager
from events.models import Event

class EventForm(forms.Form):
    ''' A form to post an event. '''
    title = forms.CharField(
        max_length=100,
        widget=forms.TextInput(),
        )
    description = forms.CharField(
        widget=forms.Textarea(),
        )
    location = forms.CharField(
        max_length=100,
        widget=forms.TextInput(),
        )
    rsvp = forms.BooleanField(
        required=False,
        label="RSVP",
        )
    start_time = forms.DateTimeField(
        widget=forms.DateTimeInput(format=time_formats[0]),
        input_formats=time_formats,
        )
    end_time = forms.DateTimeField(
        widget=forms.DateTimeInput(format=time_formats[0]),
        input_formats=time_formats,
        )
    as_manager = forms.ModelChoiceField(
        required=False,
        queryset=Manager.objects.none(),
        label="As manager (if manager event)",
        widget=Select2Widget,
    )
    cancelled = forms.BooleanField(
        required=False,
        label="Mark Cancelled",
        )

    def __init__(self, *args, **kwargs):
        self.profile = kwargs.pop("profile")
        self.manager_positions = Manager.objects.filter(incumbent=self.profile)
        if 'instance' in kwargs:
            self.instance = kwargs.pop('instance')
            kwargs.setdefault(
                "initial",
                {
                    'title': self.instance.title,
                    'description': self.instance.description,
                    'location': self.instance.location,
                    'rsvp': self.profile in self.instance.rsvps.all(),
                    'start_time': self.instance.start_time,
                    'end_time': self.instance.end_time,
                    'as_manager': self.instance.as_manager,
                    'cancelled': self.instance.cancelled,
                })
        else:
            self.instance = None
        kwargs.setdefault(
            "initial",
            {"rsvp": True, "location": settings.HOUSE},
            )
        super(EventForm, self).__init__(*args, **kwargs)
        if self.manager_positions:
            self.fields['as_manager'].queryset = self.manager_positions
            self.fields["as_manager"].empty_label = "------"
            self.fields["as_manager"].initial = self.manager_positions[0].pk
        else:
            self.fields["as_manager"].widget = forms.HiddenInput()
            self.fields["as_manager"].queryset = Manager.objects.none()
        if self.profile.user.username == ANONYMOUS_USERNAME:
            self.fields["rsvp"].widget = forms.HiddenInput()
        if not self.instance:
            self.fields["cancelled"].widget = forms.HiddenInput()

    def is_valid(self):
        if not super(EventForm, self).is_valid():
            return False
        start_time = self.cleaned_data['start_time']
        end_time = self.cleaned_data['end_time']
        if start_time > end_time:
            self.errors['__all__'] = self.error_class(["Start time is later than end time. Unless this event involves time travel, please change the start or end time."])
            return False
        return True

    def save(self):
        if not self.instance:
            event = Event(
                owner=self.profile,
                title=self.cleaned_data['title'],
                description=self.cleaned_data['description'],
                location=self.cleaned_data['location'],
                start_time=self.cleaned_data['start_time'],
                end_time=self.cleaned_data['end_time'],
                )
        else:
            self.instance.title = self.cleaned_data['title']
            self.instance.description = self.cleaned_data['description']
            self.instance.location = self.cleaned_data['location']
            self.instance.start_time = self.cleaned_data['start_time']
            self.instance.end_time = self.cleaned_data['end_time']
            self.instance.cancelled = self.cleaned_data['cancelled']
            event = self.instance
        event.save()
        if self.cleaned_data['rsvp'] and \
          self.profile.user.username != ANONYMOUS_USERNAME:
              event.rsvps.add(self.profile)
        as_manager = self.cleaned_data['as_manager']
        if as_manager:
            event.as_manager = as_manager
        else:
            event.as_manager = None
        event.save()

        for profile in event.rsvps.all():
            if profile.user == self.profile.user:
                continue
            notify.send(self.profile.user, verb="updated", action=event,
                        recipient=profile.user)
        return event

class RsvpForm(forms.Form):
    ''' Form to RSVP or un-RSVP from an event. '''
    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop('instance')
        self.profile = kwargs.pop("profile")
        super(RsvpForm, self).__init__(*args, **kwargs)

    def clean(self):
        if self.instance.end_time <= now():
            raise forms.ValidationError(MESSAGES['ALREADY_PAST'])
        return self.cleaned_data

    def save(self):
        if self.profile in self.instance.rsvps.all():
            self.instance.rsvps.remove(self.profile)
            rsvpd = False
        else:
            self.instance.rsvps.add(self.profile)
            rsvpd = True
        self.instance.save()
        return rsvpd

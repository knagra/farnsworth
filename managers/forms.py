'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''

from smtplib import SMTPException

from django import forms
from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.core.mail import EmailMultiAlternatives

from notifications import notify
from django_select2.widgets import Select2Widget

from utils.variables import ANNOUNCEMENT_SUBJECT, ANNOUNCEMENT_EMAIL, \
    MESSAGES
from utils.funcs import convert_to_url, verify_url
from base.models import UserProfile
from managers.models import Manager, Announcement, RequestType, Request, Response

class ManagerForm(forms.ModelForm):
    ''' Form to create or modify a manager position. '''
    class Meta:
        model = Manager
        exclude = (
            "url_title",
        )
        widgets = {
            "incumbent": Select2Widget,
        }

    def __init__(self, *args, **kwargs):
        super(ManagerForm, self).__init__(*args, **kwargs)
        self.fields['incumbent'].queryset = UserProfile.objects.exclude(status=UserProfile.ALUMNUS)

    def clean_title(self):
        title = self.cleaned_data['title']
        if Manager.objects.filter(title=title).count() and Manager.objects.get(title=title) != self.instance:
            raise forms.ValidationError("A manager with this title already exists.")
        if not verify_url(title):
            raise forms.ValidationError("Invalid title. Must be characters A-Z, a-z, 0-9, space, or _&-'?$^%@!#*()=+;:|/.,")
        url_title = convert_to_url(title)
        if Manager.objects.filter(url_title=url_title).count() and Manager.objects.get(url_title=url_title) != self.instance:
            raise forms.ValidationError('This manager title maps to a url that is already taken.  Please note, "Site Admin" and "sITe_adMIN" map to the same URL.')
        return title

    def clean(self):
        ''' TinyMCE adds a placeholder <br> if no data is inserted.  In this case, remove it. '''
        cleaned_data = super(ManagerForm, self).clean()
        compensation = cleaned_data.get("compensation")
        duties = cleaned_data.get("duties")
        if compensation == '<br data-mce-bogus="1">':
            cleaned_data["compensation"] = ""
        if duties == '<br data-mce-bogus="1">':
            cleaned_data["duties"] = ""
        return cleaned_data

    def save(self):
        manager = super(ManagerForm, self).save(commit=False)
        manager.url_title = convert_to_url(manager.title)
        manager.save()
        return manager

class RequestTypeForm(forms.ModelForm):
    ''' Form to add or modify a request type. '''
    class Meta:
        model = RequestType
        exclude = ("url_name",)
        help_texts = {
            'name': "Unique name identifying this request type. Characters A-Z, a-z, 0-9, space, or _&-'?$^%@!#*()=+;:|/.,. Capitalize first letter of each word.",
            "enabled": "Whether users can post new requests of this type.",
            "glyphicon": 'Optional glyphicon for this request type (e.g., cutlery).  Check <a target="_blank" href="//getbootstrap.com/components/#glyphicons">Bootstrap Documentation</a> for list of options.  Insert &lt;name> for glyphicon-&lt;name>.',
            }

    def clean_name(self):
        name = self.cleaned_data['name']
        if not verify_url(name):
            raise forms.ValidationError("Invalid name. Must be characters A-Z, a-z, 0-9, space, or _&-'?$^%@!#*()=+;:|/.,")
        if RequestType.objects.filter(name=name).count() and \
          RequestType.objects.get(name=name) != self.instance:
            raise forms.ValidationError("A request type with this name already exists.")
        url_name = convert_to_url(name)
        if RequestType.objects.filter(url_name=url_name).count() and \
          RequestType.objects.get(url_name=url_name) != self.instance:
            raise forms.ValidationError('This request type name maps to a url that is already taken.  Please note, "Waste Reduction" and "wasTE_RedUCtiON" map to the same URL.')
        return name

    def save(self):
        rt = super(RequestTypeForm, self).save()
        rt.url_name = convert_to_url(rt.name)
        rt.save()
        return rt

class RequestForm(forms.ModelForm):
    ''' Form to create a new Request. '''
    class Meta:
        model = Request
        fields = ("body", "private")
        help_texts = {
            "body": "",
            }

    def __init__(self, *args, **kwargs):
        self.profile = kwargs.pop('profile')
        self.request_type = kwargs.pop('request_type', None)
        super(RequestForm, self).__init__(*args, **kwargs)

    def save(self):
        request = super(RequestForm, self).save(commit=False)
        request.owner = self.profile
        request.request_type = self.request_type
        request.save()
        for manager in request.request_type.managers.all():
            if manager.incumbent:
                notify.send(self.profile.user, verb="posted", action_object=request,
                            target=self.request_type, recipient=manager.incumbent.user)
        return request

class ResponseForm(forms.ModelForm):
    '''' Form for a regular user to create a new Response. '''
    class Meta:
        model = Response
        fields = ("body",)
        help_texts = {
            "body": "",
            }

    def __init__(self, *args, **kwargs):
        self.profile = kwargs.pop('profile')
        self.request = kwargs.pop("request")
        super(ResponseForm, self).__init__(*args, **kwargs)

    def save(self):
        response = super(ResponseForm, self).save(commit=False)
        response.owner = self.profile
        response.request = self.request
        response.save()

        for follower in self.request.followers.all():
            notify.send(self.profile.user, verb="posted", action_object=response,
                        target=self.request, recipient=follower.user)

        self.request.number_of_responses += 1
        self.request.save()

        return response

class ManagerResponseForm(ResponseForm):
    ''' Form for a manager to create a new Response. '''
    class Meta:
        model = Response
        fields = ("body", "action")

    def __init__(self, *args, **kwargs):
        super(ManagerResponseForm, self).__init__(*args, **kwargs)
        if self.request.closed:
            self.fields['action'].choices = (choice for choice in Response.ACTION_CHOICES if choice != Response.CLOSED)
        elif self.request.open:
            self.fields['action'].choices = (choice for choice in Response.ACTION_CHOICES if choice != Response.REOPENED)
        elif self.request.filled:
            self.fields['action'].choices = (choice for choice in Response.ACTION_CHOICES if choice != Response.FILLED)
        elif self.request.expired:
            self.fields['action'].choices = (choice for choice in Response.ACTION_CHOICES if choice != Response.EXPIRED)

    def save(self):
        response = super(ManagerResponseForm, self).save()
        response.manager = True
        response.save()

        actions = {
            Response.CLOSED: Request.CLOSED,
            Response.REOPENED: Request.OPEN,
            Response.FILLED: Request.FILLED,
            Response.EXPIRED: Request.EXPIRED,
            Response.NONE: response.request.status,
            }
        response.request.status = actions[response.action]
        response.request.save()

        return response

class VoteForm(forms.Form):
    ''' Form to cast an up vote for a request. '''
    def __init__(self, *args, **kwargs):
        self.profile = kwargs.pop("profile")
        self.request = kwargs.pop("request")

        super(VoteForm, self).__init__(*args, **kwargs)

    def save(self):
        if self.profile in self.request.upvotes.all():
            self.request.upvotes.remove(self.profile)
        else:
            self.request.upvotes.add(self.profile)
        self.request.save()
        return self.request

class AnnouncementForm(forms.ModelForm):
    email_members = forms.BooleanField(
        required=False,
        help_text="Send an e-mail to residents and boarders in database."
        )
    email_alumni = forms.BooleanField(
        required=False,
        help_text="Send an e-mail to alumni addresses in database."
        )

    class Meta:
        model = Announcement
        fields = (
            "manager",
            "body",
        )
        widgets = {
            "manager": Select2Widget,
        }

    def __init__(self, *args, **kwargs):
        self.profile = kwargs.pop("profile")
        self.manager_positions = Manager.objects.filter(incumbent=self.profile, active=True)
        if 'editing' in kwargs:
            self.editing = kwargs.pop('editing')
        else:
            self.editing = False
        super(AnnouncementForm, self).__init__(*args, **kwargs)
        if self.manager_positions:
            self.fields["manager"].queryset = self.manager_positions
            self.fields["manager"].initial = self.manager_positions[0].pk
            self.fields["manager"].empty_label = None
        else:
            self.fields["manager"].widget = forms.HiddenInput()
            self.fields["manager"].queryset = Manager.objects.none()
        if self.editing:
            self.fields.pop('email_members')
            self.fields.pop('email_alumni')

    def is_valid(self):
        if not super(AnnouncementForm, self).is_valid():
            return False
        if not self.manager_positions and not self.profile.user.is_superuser:
            self._errors['__all__'] = forms.util.ErrorList([u"You do not have permission to post an announcement."])
        return True

    def save(self, request=None):
        announcement = super(AnnouncementForm, self).save(commit=False)
        if announcement.pk is None:
            announcement.incumbent = self.profile
        announcement.save()
        # If not sending an e-mail, skip rest of function
        if self.editing or not settings.SEND_EMAILS \
                or not self.cleaned_data['email_members'] \
                and not self.cleaned_data['email_alumni']:
            return announcement
        url = request.build_absolute_uri(reverse(
            'managers:view_announcement',
            kwargs={'announcement_pk': announcement.pk},
        ))
        profile_url = request.build_absolute_uri(reverse('my_profile'))
        email_body = ANNOUNCEMENT_EMAIL.format(
            announcement=announcement,
            url=url,
            profile_url=profile_url,
        )
        email_to = []
        if self.cleaned_data['email_members']:
            for member in UserProfile.objects.filter(
                    email_announcement_notifications=True).exclude(
                    status=UserProfile.ALUMNUS):
                if member != self.profile \
                        and member.email_announcement_notifications:
                    email_to.append(member.user.email)
        if self.cleaned_data['email_alumni']:
            for member in UserProfile.objects.filter(
                    email_announcement_notifications=True,
                    status=UserProfile.ALUMNUS):
                if member != self.profile \
                        and member.email_announcement_notifications:
                    email_to.append(member.user.email)
        try:
            email_msg = EmailMultiAlternatives(
                subject=ANNOUNCEMENT_SUBJECT.format(
                    house=settings.HOUSE,
                    manager=announcement.manager,
                ),
                body=email_body,
                from_email=settings.EMAIL_HOST_USER,
                bcc=email_to,
            )
            email_msg.attach_alternative(email_body, 'text/html')
            email_msg.send(fail_silently=False,)
            messages.add_message(
                request,
                messages.SUCCESS,
                MESSAGES['ANNOUNCEMENT_SUCCESS'],
            )
        except SMTPException as e:
            messages.add_message(
                request,
                messages.ERROR,
                MESSAGES['ANNOUNCEMENT_FAIL'],
            )
        return announcement

class PinForm(forms.ModelForm):
    ''' Form to repin or unpin an announcement. '''
    class Meta:
        model = Announcement
        fields = ("pinned",)
        widgets = {
            "pinned": forms.HiddenInput(),
            }

    def __init__(self, *args, **kwargs):
        if "instance" in kwargs:
            kwargs.setdefault("initial", {"pinned": not kwargs["instance"].pinned})
        super(PinForm, self).__init__(*args, **kwargs)

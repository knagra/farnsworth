'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''

from datetime import datetime

from django import forms
from django.utils.timezone import utc

from utils.funcs import convert_to_url, verify_url
from managers.models import Manager, Announcement, RequestType, Request, Response


class ManagerForm(forms.ModelForm):
	''' Form to create or modify a manager position. '''
	class Meta:
		model = Manager
		exclude = ("url_title",)

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
		manager.url_title = convert_to_url(self.cleaned_data['title'])
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
			raise forms.ValdiationError("A request type with this name already exists.")
		if RequestType.objects.filter(url_name=url_name).count() and \
		  RequestType.objects.get(url_name=url_name) != self.instance:
			raise forms.ValidationError('This request type name maps to a url that is already taken.  Please note, "Waste Reduction" and "wasTE_RedUCtiON" map to the same URL.')
		return name

	def save(self):
		rtype = super(RequestTypeForm, self).save(commit=False)
		rtype.url_name = convert_to_url(self.cleaned_data['name'])
		rtype.save()
		return rtype

class RequestForm(forms.Form):
	''' Form to create a new Request. '''
	type_pk = forms.IntegerField(widget=forms.HiddenInput(), required=False)
	body = forms.CharField(widget=forms.Textarea())

	def __init__(self, *args, **kwargs):
		self.profile = kwargs.pop('profile')
		self.request_type = kwargs.pop('request_type', None)
		super(RequestForm, self).__init__(*args, **kwargs)

	def clean_type_pk(self):
		if self.request_type:
			return self.request_type
		type_pk = self.cleaned_data['type_pk']
		try:
			request_type = RequestType.objects.get(pk=type_pk)
		except RequestType.DoesNotExist:
			raise forms.ValidationError("The request type was not recognized.  Please contact an admin for support.")
		return request_type

	def save(self):
		request = Request(
			owner=self.profile,
			body=self.cleaned_data['body'],
			request_type=self.cleaned_data['type_pk'],
			)
		request.save()
		return request

class ResponseForm(forms.Form):
	'''' Form for a regular user to create a new Response. '''
	request_pk = forms.IntegerField(widget=forms.HiddenInput(), required=False)
	body = forms.CharField(widget=forms.Textarea())

	def __init__(self, *args, **kwargs):
		self.profile = kwargs.pop('profile')
		super(ResponseForm, self).__init__(*args, **kwargs)

	def clean_request_pk(self):
		request_pk = self.cleaned_data['request_pk']
		try:
			request = Request.objects.get(pk=request_pk)
		except Request.DoesNotExist:
			raise forms.ValidationError("Request does not exist.")
		return request

	def save(self):
		response = Response(
			owner=self.profile,
			body=self.cleaned_data['body'],
			request=self.cleaned_data['request_pk'],
			)
		response.request.change_date = datetime.utcnow().replace(tzinfo=utc)
		response.request.number_of_responses += 1
		response.request.save()
		response.save()
		return response

class ManagerResponseForm(ResponseForm):
	''' Form for a manager to create a new Response. '''
	mark_filled = forms.BooleanField(required=False)
	mark_closed = forms.BooleanField(required=False)

	def save(self):
		response = super(ManagerResponseForm, self).save()
		response.manager = True
		response.save()
		request = self.cleaned_data['request_pk']
		request.closed = self.cleaned_data['mark_closed']
		request.filled = self.cleaned_data['mark_filled']
		request.save()
		return response

class VoteForm(forms.Form):
	''' Form to cast an up or down vote for a request. '''
	request_pk = forms.IntegerField(widget=forms.HiddenInput())

	def __init__(self, *args, **kwargs):
		self.profile = kwargs.pop("profile")
		super(VoteForm, self).__init__(*args, **kwargs)

	def save(self, pk=None):
		if pk is None:
			pk = self.cleaned_data['request_pk']
		relevant_request = Request.objects.get(pk=pk)
		if self.profile in relevant_request.upvotes.all():
			relevant_request.upvotes.remove(self.profile)
		else:
			relevant_request.upvotes.add(self.profile)
		relevant_request.save()

class AnnouncementForm(forms.ModelForm):
	class Meta:
		model = Announcement
		fields = ("manager", "body")

	def __init__(self, *args, **kwargs):
		self.profile = kwargs.pop("profile")
		self.manager_positions = Manager.objects.filter(incumbent=self.profile)
		super(AnnouncementForm, self).__init__(*args, **kwargs)
		if self.manager_positions:
			self.fields["manager"].queryset = self.manager_positions
			self.fields["manager"].empty_label = None
			self.fields["manager"].initial = self.manager_positions[0].pk
		else:
			self.fields["manager"].widget = forms.HiddenInput()
			self.fields["manager"].queryset = Manager.objects.none()

	def is_valid(self):
		if not super(AnnouncementForm, self).is_valid():
			return False
		if not self.manager_positions and not self.profile.user.is_superuser:
			raise forms.ValidationError("You do not have permission to post an announcement.")
		return True

	def save(self, *args, **kwargs):
		announcement = super(AnnouncementForm, self).save(commit=False)
		if announcement.pk is None:
			announcement.pinned = True
			announcement.incumbent = self.profile
		announcement.save()

class UnpinForm(forms.Form):
	''' Form to repin or unpin an announcement. '''
	announcement_pk = forms.IntegerField(required=False, widget=forms.HiddenInput())

	def __init__(self, *args, **kwargs):
		self.announce = kwargs.pop('announce', None)
		super(UnpinForm, self).__init__(*args, **kwargs)

	def clean_announcement_pk(self):
		if self.announce:
			return self.announce
		announcement_pk = self.cleaned_data['announcement_pk']
		try:
			announce = Announcement.objects.get(pk=announcement_pk)
		except Announcement.DoesNotExist:
			raise forms.ValidationError("Announcement does not exist.")
		return announce

	def save(self):
		announce = self.cleaned_data['announcement_pk']
		announce.pinned = not announce.pinned
		announce.save()

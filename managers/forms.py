'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''
from django import forms

from base.models import UserProfile
from managers.models import Manager, Announcement

from utils.funcs import verify_url

class ManagerForm(forms.Form):
	''' Form to create or modify a manager position. '''
	title = forms.CharField(max_length=255, help_text="A unique title for this manager position. Characters A-Z, a-z, 0-9, space, or _&-'?$^%@!#*()=+;:|/.,")
	incumbent = forms.ModelChoiceField(queryset=UserProfile.objects.all().exclude(status=UserProfile.ALUMNUS),
		help_text="Current incumbent for this manager position.  List excludes alumni.", required=False)
	compensation = forms.CharField(widget=forms.Textarea(), required=False)
	duties = forms.CharField(widget=forms.Textarea(), required=False)
	email = forms.EmailField(max_length=255, required=False, help_text="Manager e-mail (optional)")
	president = forms.BooleanField(help_text="Whether this manager has president privileges (edit and add managers, etc.)", required=False)
	workshift_manager = forms.BooleanField(help_text="Whether this is a workshift manager position", required=False)
	active = forms.BooleanField(help_text="Whether this is an active manager positions (visible in directory, etc.)", required=False)

	def is_valid(self):
		''' Validate form.
		Return True if the form is valid by Django's requirements and the title obeys the parameters.
		Return False otherwise.
		'''
		if not super(ManagerForm, self).is_valid():
			return False
		elif not verify_url(self.cleaned_data['title']):
			self._errors['title'] = self.error_class([u"Invalid title. Must be characters A-Z, a-z, 0-9, space, or _&-'?$^%@!#*()=+;:|/.,"])
			return False
		return True

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

class RequestTypeForm(forms.Form):
	''' Form to add or modify a request type. '''
	name = forms.CharField(max_length=255,
		help_text="Unique name identifying this request type. Characters A-Z, a-z, 0-9, space, or _&-'?$^%@!#*()=+;:|/.,. Capitalize first letter of each word.")
	relevant_managers = forms.ModelMultipleChoiceField(queryset=Manager.objects.all(),
		help_text="Managers responsible for addressing this type of request; list excludes inactive managers.", required=False)
	enabled = forms.BooleanField(required=False, help_text="Whether users can post new requests of this type.")
	glyphicon = forms.CharField(max_length=100, required=False,
		help_text='Optional glyphicon for this request type (e.g., cutlery).  Check <a target="_blank" href="//getbootstrap.com/components/#glyphicons">Bootstrap Documentation</a> for list of options.  Insert &lt;name> for glyphicon-&lt;name>.')

	def is_valid(self):
		''' Validate form.
		Return True if the form is valid by Django's requirements and the name obeys the parameters.
		Return False otherwise.
		'''
		if not super(RequestTypeForm, self).is_valid():
			return False
		elif not verify_url(self.cleaned_data['name']):
			self._errors['name'] = self.error_class([u"Invalid name. Must be characters A-Z, a-z, 0-9, space, or _&-'?$^%@!#*()=+;:|/.,"])
			return False
		return True

class RequestForm(forms.Form):
	''' Form to create a new Request. '''
	type_pk = forms.IntegerField(widget=forms.HiddenInput(), required=False)
	body = forms.CharField(widget=forms.Textarea())

	def __init__(self, *args, **kwargs):
		self.profile = kwargs.pop('profile')
		self.request_type = kwargs.pop('request_type', None)
		super(RequestForm, self).__init__(*args, **kwargs)

	def clean_type_pk(self):
		if self.request_Type:
			return self.request_type
		type_pk = self.cleaned_data['type_pk']
		try:
			request_type = RequestType.objects.get(pk=type_pk)
		except RequestType.DoesNotExist:
			raise ValidationError("The request type was not recognized.  Please contact an admin for support.")
		return request_type

	def save(self):
		request = Request(
			owner=self.profile,
			body=self.cleaned_data['body'],
			request_type=self.cleaned_data['request_type'],
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
			raise ValidationError("Request does not exist.")
		return request

	def save(self):
		request = self.cleaned_data['request']
		response = Response(
			owner=self.profile,
			body=self.cleaned_data['body'],
			request=request,
			)
		request.change_date = datetime.utcnow().replace(tzinfo=utc)
		request.number_of_responses += 1
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
		request = self.cleaned_data['request']
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
			pk = vote_form.cleaned_data['request_pk']
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
		self.new = "instance" not in kwargs
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
			raise ValidationError("You do not have permission to post an announcement.")
		return True

	def save(self, *args, **kwargs):
		announcement = super(AnnouncementForm, self).save(commit=False)
		if self.new:
			announcement.pinned = True
			announcement.incumbent = self.profile
		announcement.save()

class UnpinForm(forms.Form):
	''' Form to repin or unpin an announcement. '''
	announcement_pk = forms.IntegerField(required=False, widget=forms.HiddenInput())

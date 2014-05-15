'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''
from django import forms
from django.contrib.auth.models import Group

from base.models import UserProfile
from managers.models import Manager
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

class ResponseForm(forms.Form):
	'''' Form for a regular user to create a new Response. '''
	request_pk = forms.IntegerField(widget=forms.HiddenInput(), required=False)
	body = forms.CharField(widget=forms.Textarea())

class ManagerResponseForm(forms.Form):
	''' Form for a manager to create a new Response. '''
	request_pk = forms.IntegerField(widget=forms.HiddenInput(), required=False)
	body = forms.CharField(widget=forms.Textarea())
	mark_filled = forms.BooleanField(required=False)
	mark_closed = forms.BooleanField(required=False)

class VoteForm(forms.Form):
	''' Form to cast an up or down vote for a request. '''
	request_pk = forms.IntegerField(widget=forms.HiddenInput())

def AnnouncementForm(manager_positions, post=None):
	''' Return a form to post an announcement, has an as_manager field if the user is a manager.
	Parameters:
		manager_positions should be a choice set containing manager positions the user making the request currently holds.
		post should be a request.POST
	'''
	class InnerAnnouncementForm(forms.Form):
		as_manager = forms.ModelChoiceField(queryset=manager_positions, empty_label=None)
		body = forms.CharField(widget=forms.Textarea())
	if post is None:
		return InnerAnnouncementForm(initial={'as_manager': manager_positions[0].pk})
	else:
		return InnerAnnouncementForm(post)

class UnpinForm(forms.Form):
	''' Form to repin or unpin an announcement. '''
	announcement_pk = forms.IntegerField(widget=forms.HiddenInput())

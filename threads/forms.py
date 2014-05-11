'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''

from django import forms

from managers.models import Manager
from threads.models import UserProfile

class ThreadForm(forms.Form):
	''' Form to post a new thread. '''
	subject = forms.CharField(max_length=300, widget=forms.TextInput(attrs={'size':'100'}))
	body = forms.CharField(widget=forms.Textarea())

class MessageForm(forms.Form):
	''' Form to post a new message. '''
	thread_pk = forms.IntegerField(widget=forms.HiddenInput())
	body = forms.CharField(widget=forms.Textarea())

class VoteForm(forms.Form):
	''' Form to cast an up or down vote for a request. '''
	request_pk = forms.IntegerField(widget=forms.HiddenInput())

class UnpinForm(forms.Form):
	''' Form to repin or unpin an announcement. '''
	announcement_pk = forms.IntegerField(widget=forms.HiddenInput())

class RsvpForm(forms.Form):
	''' Form to RSVP or un-RSVP from an event. '''
	event_pk = forms.IntegerField(widget=forms.HiddenInput())

class ManagerForm(forms.Form):
	''' Form to create or modify a manager position. '''
	title = forms.CharField(max_length=255, help_text="A unique title for this manager position.")
	incumbent = forms.ModelChoiceField(queryset=UserProfile.objects.all().exclude(status=UserProfile.ALUMNUS), help_text="Current incumbent for this manager position.  List excludes alumni.", required=False)
	compensation = forms.CharField(widget=forms.Textarea(), required=False)
	duties = forms.CharField(widget=forms.Textarea(), required=False)
	email = forms.EmailField(max_length=255, required=False, help_text="Manager e-mail (optional)")
	president = forms.BooleanField(help_text="Whether this manager has president privileges (edit and add managers, etc.)", required=False)
	workshift_manager = forms.BooleanField(help_text="Whether this is a workshift manager position", required=False)
	active = forms.BooleanField(help_text="Whether this is an active manager positions (visible in directory, etc.)", required=False)
	
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
	name = forms.CharField(max_length=255, help_text="A unique name identifying this request type. Capitalize first letter of each word.")
	relevant_managers = forms.ModelMultipleChoiceField(queryset=Manager.objects.filter(active=True), help_text="Managers responsible for addressing this type of request; list excludes inactive managers.", required=False)
	enabled = forms.BooleanField(required=False, help_text="Whether users can post new requests of this type.")
	glyphicon = forms.CharField(max_length=100, required=False, help_text='Optional glyphicon for this request type (e.g., cutlery).  Check <a target="_blank" href="//getbootstrap.com/components/#glyphicons">Bootstrap Documentation</a> for list of options.  Insert &lt;name> for glyphicon-&lt;name>.')

class UpdateProfileForm(forms.Form):
	current_room = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}), required=False)
	former_rooms = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}), required=False)
	former_houses = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}), required=False)
	email = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'size':'50'}), required=False)
	email_visible_to_others = forms.BooleanField(required=False)
	phone_number = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'size':'50'}), required=False)
	phone_visible_to_others = forms.BooleanField(required=False)
	enter_password = forms.CharField(max_length=100, widget=forms.PasswordInput(attrs={'size':'50'}))

class LoginForm(forms.Form):
	username = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}))
	password = forms.CharField(max_length=100, widget=forms.PasswordInput(attrs={'size':'50'}))

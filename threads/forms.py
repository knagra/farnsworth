'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''

from django import forms

from base.models import UserProfile

class ThreadForm(forms.Form):
	''' Form to post a new thread. '''
	subject = forms.CharField(max_length=300, widget=forms.TextInput(attrs={'size':'100'}))
	body = forms.CharField(widget=forms.Textarea())

class MessageForm(forms.Form):
	''' Form to post a new message. '''
	thread_pk = forms.IntegerField(widget=forms.HiddenInput())
	body = forms.CharField(widget=forms.Textarea())

class UpdateProfileForm(forms.Form):
	''' Form for a user to update own profile. '''
	current_room = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}), required=False)
	former_rooms = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}), required=False)
	former_houses = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}), required=False)
	email = forms.EmailField(max_length=255, required=False)
	email_visible_to_others = forms.BooleanField(required=False)
	phone_number = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'size':'50'}), required=False)
	phone_visible_to_others = forms.BooleanField(required=False)
	enter_password = forms.CharField(max_length=100, widget=forms.PasswordInput(attrs={'size':'50'}))

class LoginForm(forms.Form):
	''' Form to login. '''
	username = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}))
	password = forms.CharField(max_length=100, widget=forms.PasswordInput(attrs={'size':'50'}))

class ChangePasswordForm(forms.Form):
	''' Form for a user to change own password. '''
	current_password = forms.CharField(max_length=100, widget=forms.PasswordInput(attrs={'size':'50'}))
	new_password = forms.CharField(max_length=100, widget=forms.PasswordInput(attrs={'size':'50'}))
	confirm_password = forms.CharField(max_length=100, widget=forms.PasswordInput(attrs={'size':'50'}))

	def is_valid(self):
		if not super(ChangePasswordForm, self).is_valid():
			return False
		new_password = self.cleaned_data['new_password']
		confirm_password = self.cleaned_data['confirm_password']
		if new_password != confirm_password:
			self.errors['__all__'] = self.error_class([u"Passwords don't match."])
			return False
		return True

'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''
from django import forms
from django.contrib.auth.models import Group
from django.contrib.auth import hashers

from utils.funcs import verify_username
from utils.variables import MESSAGES
from base.models import UserProfile

class ProfileRequestForm(forms.Form):
	''' Form to create a new profile request. '''
	username = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}), help_text='Characters A-Z, a-z, 0-9, or _.')
	first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}))
	last_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}))
	email = forms.EmailField(max_length=100)
	affiliation_with_the_house = forms.ChoiceField(choices=UserProfile.STATUS_CHOICES)
	password = forms.CharField(max_length=100, widget=forms.PasswordInput(attrs={'size':'50'}))
	confirm_password = forms.CharField(max_length=100, widget=forms.PasswordInput(attrs={'size':'50'}))

	def is_valid(self):
		''' Validate form.
		Return True if Django validates the form, the username obeys the parameters, and passwords match.
		Return False otherwise.
		'''
		if not super(ProfileRequestForm, self).is_valid():
			return False
		validity = True
		if not verify_username(self.cleaned_data['username']):
			self._errors['username'] = self.error_class([MESSAGES['INVALID_USERNAME']])
			validity = False
		if self.cleaned_data['password'] != self.cleaned_data['confirm_password']:
			self._errors['password'] = forms.util.ErrorList([u"Passwords don't match."])
			self._errors['confirm_password'] = forms.util.ErrorList([u"Passwords don't match."])
			validity = False
		return validity

class AddUserForm(forms.Form):
	''' Form to add a new user and associated profile. '''
	username = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}), help_text='Characters A-Z, a-z, 0-9, or _.')
	first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}))
	last_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}))
	email = forms.EmailField(max_length=100, required=False)
	email_visible_to_others = forms.BooleanField(required=False)
	phone_number = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'size':'50'}))
	phone_visible_to_others = forms.BooleanField(required=False)
	status = forms.ChoiceField(choices=UserProfile.STATUS_CHOICES)
	current_room = forms.CharField(max_length=30, widget=forms.TextInput(attrs={'size':'50'}), required=False)
	former_rooms = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}), required=False)
	former_houses = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size': '50'}), required=False, label="Other houses",
		help_text="Other houses where this user has boarded or lived.")
	is_active = forms.BooleanField(required=False)
	is_staff = forms.BooleanField(required=False)
	is_superuser = forms.BooleanField(required=False)
	groups = forms.ModelMultipleChoiceField(queryset=Group.objects.all(), required=False)
	user_password = forms.CharField(max_length=100, widget=forms.PasswordInput(attrs={'size':'50'}))
	confirm_password = forms.CharField(max_length=100, widget=forms.PasswordInput(attrs={'size':'50'}))

	def is_valid(self):
		''' Validate form.
		Return True if Django validates the form, the username obeys the parameters, and passwords match.
		Return False otherwise.
		'''
		if not super(AddUserForm, self).is_valid():
			return False
		validity = True
		if not verify_username(self.cleaned_data['username']):
			self._errors['username'] = self.error_class([MESSAGES['INVALID_USERNAME']])
			validity = False
		if self.cleaned_data['user_password'] != self.cleaned_data['confirm_password']:
			self._errors['user_password'] = forms.util.ErrorList([u"Passwords don't match."])
			self._errors['confirm_password'] = forms.util.ErrorList([u"Passwords don't match."])
			validity = False
		return validity

class DeleteUserForm(forms.Form):
	''' Form to add a new user and associated profile. '''
	username = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}), help_text="Enter member's username to confirm deletion.")
	password = forms.CharField(max_length=100, widget=forms.PasswordInput(attrs={'size':'50'}), label="Your password")

	def is_valid(self):
		''' Validate form.
		Return True if Django validates the form, the username obeys the parameters, and passwords match.
		Return False otherwise.
		'''
		if not super(DeleteUserForm, self).is_valid():
			return False
		validity = True
		if not verify_username(self.cleaned_data['username']):
			self._errors['username'] = self.error_class([MESSAGES['INVALID_USERNAME']])
			validity = False
		return validity

class ModifyUserForm(forms.Form):
	''' Form to modify an existing user and profile. '''
	first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}))
	last_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}))
	email = forms.EmailField(max_length=100, required=False)
	email_visible_to_others = forms.BooleanField(required=False)
	phone_number = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'size':'50'}))
	phone_visible_to_others = forms.BooleanField(required=False)
	status = forms.ChoiceField(choices=UserProfile.STATUS_CHOICES)
	current_room = forms.CharField(max_length=30, widget=forms.TextInput(attrs={'size':'50'}), required=False)
	former_rooms = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}), required=False)
	former_houses = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}), required=False, label="Other houses",
		help_text="Other houses where this user has boarded or lived.")
	is_active = forms.BooleanField(required=False, help_text="Whether this user can login.")
	is_staff = forms.BooleanField(required=False, help_text="Whether this user can access the Django admin interface.")
	is_superuser = forms.BooleanField(required=False, help_text="Whether this user has admin privileges.")
	groups = forms.ModelMultipleChoiceField(queryset=Group.objects.all(), required=False)

class ChangeUserPasswordForm(forms.Form):
	''' Form for an admin to change a user's password. '''
	user_password = forms.CharField(max_length=100, widget=forms.PasswordInput(attrs={'size':'50'}))
	confirm_password = forms.CharField(max_length=100, widget=forms.PasswordInput(attrs={'size':'50'}))

	def __init__(self, user, *args, **kwargs):
		self.user = user
		super(ChangeUserPasswordForm, self).__init__(*args, **kwargs)

	def clean_user_password(self):
		hashed_password = hashers.make_password(self.cleaned_data['user_password'])
		if not hashers.is_password_usable(hashed_password):
			raise forms.ValidationError("Password didn't hash properly.  Please try again.")
		return hashed_password

	def clean_confirm_password(self):
		hashed_password = hashers.make_password(self.cleaned_data['confirm_password'])
		if not hashers.is_password_usable(hashed_password):
			raise forms.ValidationError("Password didn't hash properly.  Please try again.")
		return hashed_password

	def is_valid(self):
		''' Validate form.
		Return True if Django validates form and the passwords match.
		Return False otherwise.
		'''
		if not super(ChangeUserPasswordForm, self).is_valid():
			return False
		elif self.cleaned_data['user_password'] != self.cleaned_data['confirm_password']:
			self._errors['user_password'] = forms.util.ErrorList([u"Passwords don't match."])
			self._errors['confirm_password'] = forms.util.ErrorList([u"Passwords don't match."])
			return False
		return True

	def save(self):
		self.user.password = self.cleaned_data['user_password']
		self.user.save()

class ModifyProfileRequestForm(forms.Form):
	''' Form to modify a profile request. '''
	username = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}), help_text='Characters A-Z, a-z, 0-9, or _.')
	first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}))
	last_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}))
	email = forms.EmailField(max_length=100, required=False)
	email_visible_to_others = forms.BooleanField(required=False)
	phone_number = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'size':'50'}))
	phone_visible_to_others = forms.BooleanField(required=False)
	status = forms.ChoiceField(choices=UserProfile.STATUS_CHOICES)
	current_room = forms.CharField(max_length=30, widget=forms.TextInput(attrs={'size':'50'}), required=False)
	former_rooms = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}), required=False)
	former_houses = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size': '50'}), required=False, label="Other houses",
		help_text="Other houses where this user has boarded or lived.")
	is_active = forms.BooleanField(required=False, help_text="Whether this user can login.")
	is_staff = forms.BooleanField(required=False, help_text="Whether this user can access the Django admin interface.")
	is_superuser = forms.BooleanField(required=False, help_text="Whether this user has admin privileges.")
	groups = forms.ModelMultipleChoiceField(queryset=Group.objects.all(), required=False)

	def is_valid(self):
		''' Validate form.
		Return True if the form is valid by Django's requirements and the username obeys the parameters.
		Return False otherwise.
		'''
		if not super(ModifyProfileRequestForm, self).is_valid():
			return False
		elif not verify_username(self.cleaned_data['username']):
			self._errors['username'] = self.error_class([MESSAGES['INVALID_USERNAME']])
			return False
		return True

class UpdateProfileForm(forms.Form):
	''' Form for a user to update own profile. '''
	current_room = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}), required=False)
	former_rooms = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}), required=False)
	former_houses = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}), required=False, label="Other houses",
		help_text="Other houses where you have boarded or lived.")
	email = forms.EmailField(max_length=255, required=False)
	email_visible_to_others = forms.BooleanField(required=False,
		help_text="Make your e-mail address visible to other members in member directory, your profile, and elsewhere.")
	phone_number = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'size':'50'}), required=False,
		help_text="In format #-###-###-####, for best sortability.")
	phone_visible_to_others = forms.BooleanField(required=False,
		help_text="Make your phone number visible to other members in member directory, your profile, and elsewhere.")
	enter_password = forms.CharField(required=False, max_length=100, widget=forms.PasswordInput(attrs={'size':'50'}))

class LoginForm(forms.Form):
	''' Form to login. '''
	username_or_email = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}))
	password = forms.CharField(max_length=100, widget=forms.PasswordInput(attrs={'size':'50'}))

class ChangePasswordForm(forms.Form):
	''' Form for a user to change own password. '''
	current_password = forms.CharField(max_length=100, widget=forms.PasswordInput(attrs={'size':'50'}))
	new_password = forms.CharField(max_length=100, widget=forms.PasswordInput(attrs={'size':'50'}))
	confirm_password = forms.CharField(max_length=100, widget=forms.PasswordInput(attrs={'size':'50'}))

	def __init__(self, user, *args, **kwargs):
		self.user = user
		super(ChangePasswordForm, self).__init__(*args, **kwargs)

	def clean_current_password(self):
		current_password = self.cleaned_data['current_password']
		if not hashers.check_password(current_password, self.user.password):
			raise forms.ValidationError("Wrong password.")
		return None

	def clean_new_password(self):
		hashed_password = hashers.make_password(self.cleaned_data['new_password'])
		if not hashers.is_password_usable(hashed_password):
			raise forms.ValidationError("Password didn't hash properly.  Please try again.")
		return hashed_password

	def clean_confirm_password(self):
		hashed_password = hashers.make_password(self.cleaned_data['confirm_password'])
		if not hashers.is_password_usable(hashed_password):
			raise forms.ValidationError("Password didn't hash properly.  Please try again.")
		return hashed_password

	def is_valid(self):
		if not super(ChangePasswordForm, self).is_valid():
			return False
		elif self.cleaned_data['new_password'] != self.cleaned_data['confirm_password']:
			self._errors['new_password'] = forms.util.ErrorList([u"Passwords don't match."])
			self._errors['confirm_password'] = forms.util.ErrorList([u"Passwords don't match."])
			return False
		return True

	def save(self):
		self.user.password = self.cleaned_data['new_password']
		self.user.save()

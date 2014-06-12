'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''
from django import forms
from django.contrib.auth.models import Group, User
from django.contrib.auth import hashers

from social.apps.django_app.default.models import UserSocialAuth

from utils.funcs import verify_username
from utils.variables import MESSAGES
from base.models import UserProfile, ProfileRequest

class ProfileRequestForm(forms.Form):
	''' Form to create a new profile request. '''
	username = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}), help_text='Characters A-Z, a-z, 0-9, or _.')
	first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}))
	last_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}))
	email = forms.EmailField(max_length=100)
	affiliation_with_the_house = forms.ChoiceField(choices=UserProfile.STATUS_CHOICES)
	password = forms.CharField(max_length=100, widget=forms.PasswordInput(attrs={'size':'50'}))
	confirm_password = forms.CharField(max_length=100, widget=forms.PasswordInput(attrs={'size':'50'}))

	def clean_username(self):
		username = self.cleaned_data["username"]
		if not verify_username(username):
			raise forms.ValidationError(MESSAGES['INVALID_USERNAME'])
		return username

	def clean_password(self):
		password = self.cleaned_data["password"]
		hashed_password = hashers.make_password(password)
		if not hashers.is_password_usable(hashed_password):
			raise forms.ValidationError(MESSAGES["PASSWORD_UNHASHABLE"])
		return password

	def clean_confirm_password(self):
		password = self.cleaned_data["confirm_password"]
		hashed_password = hashers.make_password(password)
		if not hashers.is_password_usable(hashed_password):
			raise forms.ValidationError(MESSAGES["PASSWORD_UNHASHABLE"])
		return password

	def is_valid(self):
		''' Validate form.
		Return True if Django validates the form, the username obeys the parameters, and passwords match.
		Return False otherwise.
		'''
		if not super(ProfileRequestForm, self).is_valid():
			return False
		validity = True
		if self.cleaned_data['password'] != self.cleaned_data['confirm_password']:
			self._errors['password'] = forms.util.ErrorList([u"Passwords don't match."])
			self._errors['confirm_password'] = forms.util.ErrorList([u"Passwords don't match."])
			validity = False
		return validity

	def save(self):
		hashed_password = hashers.make_password(self.cleaned_data['password'])
		profile_request = ProfileRequest(
			username=self.cleaned_data['username'],
			first_name=self.cleaned_data['first_name'],
			last_name=self.cleaned_data['last_name'],
			email=self.cleaned_data['email'],
			affiliation=self.cleaned_data['affiliation_with_the_house'],
			password=hashed_password,
			)
		profile_request.save()
		return profile_request

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

	def clean_username(self):
		username = self.cleaned_data['username']
		if not verify_username(self.cleaned_data['username']):
			raise forms.ValidationError(MESSAGES['INVALID_USERNAME'])
		if User.objects.filter(username=username).count():
			raise forms.ValidationError(MESSAGES["USERNAME_TAKEN"].format(username=username))
		return username

	def clean_email(self):
		email = self.cleaned_data['email']
		if User.objects.filter(email=email).count():
			raise forms.ValidationError(MESSAGES["EMAIL_TAKEN"])
		return email

	def is_valid(self):
		''' Validate form.
		Return True if Django validates the form, the username obeys the parameters, and passwords match.
		Return False otherwise.
		'''
		if not super(AddUserForm, self).is_valid():
			return False
		first_name = self.cleaned_data['first_name']
		last_name = self.cleaned_data['last_name']
		if User.objects.filter(first_name=first_name, last_name=last_name).count():
			non_field_error = "A profile for {0} {1} already exists with username {2}." \
			  .format(first_name, last_name,
					  User.objects.get(first_name=first_name, last_name=last_name).username)
			self._errors['__all__'] = forms.util.ErrorList([non_field_error])
		if self.cleaned_data['user_password'] != self.cleaned_data['confirm_password']:
			self._errors['user_password'] = forms.util.ErrorList([u"Passwords don't match."])
			self._errors['confirm_password'] = forms.util.ErrorList([u"Passwords don't match."])
			return False
		return True

	def save(self):
		new_user = User.objects.create_user(
			username=self.cleaned_data['username'],
			email=self.cleaned_data['email'],
			first_name=self.cleaned_data['first_name'],
			last_name=self.cleaned_data['last_name'],
			password=self.cleaned_data['user_password'],
			)
		new_user.is_active = self.cleaned_data['is_active']
		new_user.is_staff = self.cleaned_data['is_staff']
		new_user.is_superuser = self.cleaned_data['is_superuser']
		new_user.groups = self.cleaned_data['groups']
		new_user.save()
		new_user_profile = UserProfile.objects.get(user=new_user)
		new_user_profile.email_visible = self.cleaned_data['email_visible_to_others']
		new_user_profile.phone_number = self.cleaned_data['phone_number']
		new_user_profile.phone_visible = self.cleaned_data['phone_visible_to_others']
		new_user_profile.status = self.cleaned_data['status']
		new_user_profile.save()
		new_user_profile.current_room = self.cleaned_data['current_room']
		new_user_profile.former_rooms = self.cleaned_data['former_rooms']
		new_user_profile.former_houses = self.cleaned_data['former_houses']
		new_user_profile.save()

class DeleteUserForm(forms.Form):
	''' Form to add a new user and associated profile. '''
	username = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}), help_text="Enter member's username to confirm deletion.")
	password = forms.CharField(max_length=100, widget=forms.PasswordInput(attrs={'size':'50'}), label="Your password")

	def __init__(self, *args, **kwargs):
		self.user = kwargs.pop('user')
		self.request = kwargs.pop('request')
		super(DeleteUserForm, self).__init__(*args, **kwargs)

	def clean_password(self):
		password = self.cleaned_data['password']
		if not hashers.check_password(password, self.request.user.password):
			raise forms.ValidationError("Wrong password.")
		return None

	def clean_username(self):
		username = self.cleaned_data['username']
		if username != self.user.username:
			raise forms.ValidationError("Username incorrect.")
		return None

	def is_valid(self):
		''' Validate form.
		Return True if Django validates the form, the username obeys the parameters, and passwords match.
		Return False otherwise.
		'''
		if not super(DeleteUserForm, self).is_valid():
			return False
		if self.user == self.request.user:
			self._errors["__all__"] = self.error_class([MESSAGES['SELF_DELETE']])
			return False
		return True

	def save(self):
		self.user.delete()

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

	def __init__(self, *args, **kwargs):
		self.user = kwargs.pop('user')
		self.profile = UserProfile.objects.get(user=self.user)
		self.request = kwargs.pop('request')
		if 'initial' not in kwargs:
			kwargs['initial'] = {
				'first_name': self.user.first_name,
				'last_name': self.user.last_name,
				'email': self.user.email,
				'email_visible_to_others': self.profile.email_visible,
				'phone_number': self.profile.phone_number,
				'phone_visible_to_others': self.profile.phone_visible,
				'status': self.profile.status,
				'current_room': self.profile.current_room,
				'former_rooms': self.profile.former_rooms,
				'former_houses': self.profile.former_houses,
				'is_active': self.user.is_active,
				'is_staff': self.user.is_staff,
				'is_superself.user': self.user.is_superuser,
				'groups': self.user.groups.all(),
				}
		super(ModifyUserForm, self).__init__(*args, **kwargs)

	def clean_is_superuser(self):
		is_superuser = self.cleaned_data["is_superuser"]
		if self.user == self.request.user and \
		  User.objects.filter(is_superuser=True).count() <= 1 and \
		  not is_superuser:
			raise forms.ValidationError(MESSAGES['LAST_SUPERADMIN'])
		return is_superuser

	def clean_email(self):
		email = self.cleaned_data["email"]
		if User.objects.filter(email=email).count() > 0 and \
		  User.objects.get(email=email) != self.user:
			raise forms.ValidationError(MESSAGES['EMAIL_TAKEN'])
		return email

	def save(self):
 		self.user.first_name = self.cleaned_data['first_name']
		self.user.last_name = self.cleaned_data['last_name']
		self.user.is_active = self.cleaned_data['is_active']
		self.user.is_staff = self.cleaned_data['is_staff']
		self.user.is_superuser = self.cleaned_data['is_superuser']
		self.user.email = self.cleaned_data['email']
		self.user.groups = self.cleaned_data['groups']
		self.user.save()
		self.profile.email_visible = self.cleaned_data['email_visible_to_others']
		self.profile.phone_number = self.cleaned_data['phone_number']
		self.profile.phone_visible = self.cleaned_data['phone_visible_to_others']
		self.profile.status = self.cleaned_data['status']
		self.profile.current_room = self.cleaned_data['current_room']
		self.profile.former_rooms = self.cleaned_data['former_rooms']
		self.profile.former_houses = self.cleaned_data['former_houses']
		self.profile.save()

class ChangeUserPasswordForm(forms.Form):
	''' Form for an admin to change a user's password. '''
	user_password = forms.CharField(max_length=100, widget=forms.PasswordInput(attrs={'size':'50'}))
	confirm_password = forms.CharField(max_length=100, widget=forms.PasswordInput(attrs={'size':'50'}))

	def __init__(self, *args, **kwargs):
		self.user = kwargs.pop('user')
		self.request = kwargs.pop('request')
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
		if self.user == self.request.user:
			self._errors["__all__"] = MESSAGES['ADMIN_PASSWORD']
			return False
		if self.cleaned_data['user_password'] != self.cleaned_data['confirm_password']:
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
		first_name = self.cleaned_data["first_name"]
		last_name = self.cleaned_data["last_name"]
		if User.objects.filter(first_name=first_name, last_name=last_name).count():
			non_field_error = "A profile for {0} {1} already exists with username {2}." \
			  .format(first_name, last_name,
					  User.objects.get(first_name=first_name,
									   last_name=last_name).username)
			self._errors['__all__'] = forms.util.ErrorList([non_field_error])
		return True

	def clean_username(self):
		username = self.cleaned_data["username"]
		if not verify_username(username):
			raise forms.ValidationError(MESSAGES['INVALID_USERNAME'])
		if User.objects.filter(username=username).count():
			raise forms.ValidationError(
				"This username is taken.  Try one of {0}_1 through {0}_10."
				.format(username))
		return username

	def clean_email(self):
		email = self.cleaned_data["email"]
		if User.objects.filter(email=email).count():
			raise forms.ValidationError(MESSAGES["EMAIL_TAKEN"])
		return email

	def save(self, profile_request):
		user = User.objects.create_user(
			username=self.cleaned_data['username'],
			email=self.cleaned_data['email'],
			first_name=self.cleaned_data['first_name'],
			last_name=self.cleaned_data['last_name'],
			)
		user.password = profile_request.password
		user.is_active = self.cleaned_data['is_active']
		user.is_staff = self.cleaned_data['is_staff']
		user.is_superuser = self.cleaned_data['is_superuser']
		user.groups = self.cleaned_data['groups']
		user.save()

		if profile_request.provider and profile_request.uid:
			social = UserSocialAuth(
				user=user,
				provider = profile_request.provider,
				uid = profile_request.uid,
				)
			social.save()

		user_profile = UserProfile.objects.get(user=user)
		user_profile.email_visible = self.cleaned_data['email_visible_to_others']
		user_profile.phone_number = self.cleaned_data['phone_number']
		user_profile.phone_visible = self.cleaned_data['phone_visible_to_others']
		user_profile.status = self.cleaned_data['status']
		user_profile.save()
		user_profile.current_room = self.cleaned_data['current_room']
		user_profile.former_rooms = self.cleaned_data['former_rooms']
		user_profile.former_houses = self.cleaned_data['former_houses']
		user_profile.save()

		return user

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

	def __init__(self, *args, **kwargs):
		self.user = kwargs.pop("user")
		super(UpdateProfileForm, self).__init__(*args, **kwargs)

	def clean_enter_password(self):
		try:
			social_auth = UserSocialAuth.objects.get(user=user)
		except UserSocialAuth.DoesNotExist:
			social_auth = None
		password = self.cleaned_data["enter_password"]
		if not social_auth and not hashers.check_password(password, self.user.password):
			raise forms.ValidationError("Wrong password.")
		return None

	def clean_email(self):
		email = self.cleaned_data["email"]
		if User.objects.filter(email=email).count() > 0 and \
		  User.objects.get(email=email) != self.user:
			raise forms.ValidationError(MESSAGES['EMAIL_TAKEN'])
		return email

	def save(self):
		profile = UserProfile.objects.get(user=self.user)
		profile.current_room = self.cleaned_data["current_room"]
		profile.former_rooms = self.cleaned_data["former_rooms"]
		profile.former_houses = self.cleaned_data["former_houses"]
		profile.email_visible = self.cleaned_data["email_visible_to_others"]
		profile.phone_number = self.cleaned_data["phone_number"]
		profile.phone_visible = self.cleaned_data["phone_visible_to_others"]
		profile.save()
		self.user.email = self.cleaned_data["email"]
		self.user.save()

class LoginForm(forms.Form):
	''' Form to login. '''
	username_or_email = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size':'50'}))
	password = forms.CharField(max_length=100, widget=forms.PasswordInput(attrs={'size':'50'}))

class ChangePasswordForm(forms.Form):
	''' Form for a user to change own password. '''
	current_password = forms.CharField(max_length=100, widget=forms.PasswordInput(attrs={'size':'50'}))
	new_password = forms.CharField(max_length=100, widget=forms.PasswordInput(attrs={'size':'50'}))
	confirm_password = forms.CharField(max_length=100, widget=forms.PasswordInput(attrs={'size':'50'}))

	def __init__(self, *args, **kwargs):
		self.user = kwargs.pop('user')
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

import time
from smtplib import SMTPException
from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout, login, authenticate, hashers
from django.contrib.auth.models import User
from django.contrib.auth.views import password_reset, password_reset_confirm
from django.core.urlresolvers import reverse
from django.core.mail import send_mail
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, render, get_object_or_404
from django.template import RequestContext
from django.utils.timezone import utc

from datetime import datetime, timedelta

from farnsworth.settings import HOUSE_NAME, SHORT_HOUSE_NAME, ADMINS, \
	 home_max_announcements, home_max_threads, SEND_EMAILS
from utils.variables import ANONYMOUS_USERNAME, MESSAGES, APPROVAL_SUBJECT, \
	APPROVAL_EMAIL, DELETION_SUBJECT, DELETION_EMAIL, SUBMISSION_SUBJECT, \
	SUBMISSION_EMAIL
from base.models import UserProfile, ProfileRequest
from base.redirects import red_ext, red_home
from base.decorators import profile_required, admin_required
from base.forms import ProfileRequestForm, AddUserForm, ModifyUserForm, \
	 ModifyProfileRequestForm, ChangeUserPasswordForm, LoginForm, ChangePasswordForm, \
	 UpdateProfileForm, DeleteUserForm
from threads.models import Thread, Message
from threads.forms import ThreadForm
from managers.models import RequestType, Manager, Request, Response, Announcement
from managers.forms import AnnouncementForm, ManagerResponseForm, VoteForm, UnpinForm
from events.models import Event
from events.forms import RsvpForm

try:
	from farnsworth.settings import EMAIL_HOST_USER, EMAIL_BLACKLIST
except ImportError:
	EMAIL_HOST_USER, EMAIL_BLACKLIST = None, None

def add_context(request):
	''' Add variables to all dictionaries passed to templates. '''
	PRESIDENT = False # whether the user has president privileges
	try:
		userProfile = UserProfile.objects.get(user=request.user)
	except (UserProfile.DoesNotExist, TypeError):
		pass
	else:
		for pos in Manager.objects.filter(incumbent=userProfile):
			if pos.president:
				PRESIDENT = True
				break
	if request.user.username == ANONYMOUS_USERNAME:
		request.session['ANONYMOUS_SESSION'] = True
	ANONYMOUS_SESSION = request.session.get('ANONYMOUS_SESSION', False)
	request_types = list() # A list with items of form (RequestType, number_of_open_requests)
	for request_type in RequestType.objects.filter(enabled=True):
		request_types.append((request_type, Request.objects.filter(request_type=request_type, filled=False, closed=False).count()))
	return {
		'REQUEST_TYPES': request_types,
		'HOUSE': HOUSE_NAME,
		'ANONYMOUS_USERNAME':ANONYMOUS_USERNAME,
		'SHORT_HOUSE': SHORT_HOUSE_NAME,
		'ADMIN': ADMINS[0],
		'NUM_OF_PROFILE_REQUESTS': ProfileRequest.objects.all().count(),
		'ANONYMOUS_SESSION': ANONYMOUS_SESSION,
		'PRESIDENT': PRESIDENT,
		}

def landing_view(request):
	''' The external landing.'''
	return render_to_response('external.html', {
			'page_name': "Landing",
			}, context_instance=RequestContext(request))

@profile_required(redirect_no_user='external', redirect_profile=red_ext)
def homepage_view(request, message=None):
	''' The view of the homepage. '''
	userProfile = UserProfile.objects.get(user=request.user)
	request_types = RequestType.objects.filter(enabled=True)
	manager_request_types = list() # List of request types for which the user is a relevant manager
	for request_type in request_types:
		for position in request_type.managers.filter(active=True):
			if userProfile == position.incumbent:
				manager_request_types.append(request_type)
				break
	requests_dict = list() # Pseudo-dictionary, list with items of form (request_type, (request, [list_of_request_responses], response_form))
	# Generate a dict of unfilled, unclosed requests for each request_type for which the user is a relevant manager:
	if manager_request_types:
		for request_type in manager_request_types:
			requests_list = list() # Items of form (request, [list_of_request_responses], response_form, upvote, vote_form)
			# Select only unclosed, unfilled requests of type request_type:
			type_requests = Request.objects.filter(request_type=request_type, filled=False, closed=False)
			for req in type_requests:
				response_list = Response.objects.filter(request=req)
				form = ManagerResponseForm(
					initial={'request_pk': req.pk},
					profile=userProfile,
					)
				upvote = userProfile in req.upvotes.all()
				vote_form = VoteForm(
					initial={'request_pk': req.pk},
					profile=userProfile,
					)
				requests_list.append((req, response_list, form, upvote, vote_form))
			requests_dict.append((request_type, requests_list))
	announcement_form = None
	announcements_dict = list() # Pseudo-dictionary, list with items of form (announcement, announcement_unpin_form)
	announcements = Announcement.objects.filter(pinned=True)
	x = 0 # Number of announcements loaded
	for a in announcements:
		unpin_form = None
		if (a.manager.incumbent == userProfile) or request.user.is_superuser:
			unpin_form = UnpinForm(initial={'announcement_pk': a.pk})
		announcements_dict.append((a, unpin_form))
		x += 1
		if x >= home_max_announcements:
			break
	now = datetime.utcnow().replace(tzinfo=utc)
	tomorrow = now + timedelta(hours=24)
	# Get only next 24 hours of events:
	events_list = Event.objects.all().exclude(start_time__gte=tomorrow).exclude(end_time__lte=now)
	events_dict = list() # Pseudo-dictionary, list with items of form (event, ongoing, rsvpd, rsvp_form)
	for event in events_list:
		form = RsvpForm(initial={'event_pk': event.pk})
		ongoing = ((event.start_time <= now) and (event.end_time >= now))
		rsvpd = (userProfile in event.rsvps.all())
		events_dict.append((event, ongoing, rsvpd, form))
	response_form = ManagerResponseForm(
		request.POST if 'add_response' in request.POST else None,
		profile=userProfile,
		)
	announcement_form = AnnouncementForm(
		request.POST if 'post_announcement' in request.POST else None,
		profile=userProfile,
		)
	unpin_form = UnpinForm(
		request.POST if 'unpin' in request.POST else None,
		)
	rsvp_form = RsvpForm(
		request.POST if 'rsvp' in request.POST else None,
		)
	thread_form = ThreadForm(
		request.POST if 'submit_thread_form' in request.POST else None,
		profile=userProfile,
		)
	vote_form = VoteForm(
		request.POST if 'upvote' in request.POST else None,
		profile=userProfile,
		)
	thread_set = [] # List of with items of form (thread, most_recent_message_in_thread)
	for thread in Thread.objects.all()[:home_max_threads]:
		try:
			latest_message = Message.objects.filter(thread=thread).latest('post_date')
		except Message.DoesNotExist:
			latest_message = None
		thread_set.append((thread, latest_message))
	if response_form.is_valid():
		response_form.save()
		if relevant_request.closed:
			messages.add_message(request, messages.SUCCESS, MESSAGES['REQ_CLOSED'])
		if relevant_request.filled:
			messages.add_message(request, messages.SUCCESS, MESSAGES['REQ_FILLED'])
		return HttpResponseRedirect(reverse('homepage'))
	if announcement_form.is_valid():
		announcement_form.save()
		return HttpResponseRedirect(reverse('homepage'))
	if unpin_form.is_valid():
		announcement_pk = unpin_form.cleaned_data['announcement_pk']
		relevant_announcement = Announcement.objects.get(pk=announcement_pk)
		relevant_announcement.pinned = False
		relevant_announcement.save()
		return HttpResponseRedirect(reverse('homepage'))
	if rsvp_form.is_valid():
		event_pk = rsvp_form.cleaned_data['event_pk']
		relevant_event = Event.objects.get(pk=event_pk)
		if userProfile in relevant_event.rsvps.all():
			relevant_event.rsvps.remove(userProfile)
			message = MESSAGES['RSVP_REMOVE'].format(event=relevant_event.title)
			messages.add_message(request, messages.SUCCESS, message)
		else:
			relevant_event.rsvps.add(userProfile)
			message = MESSAGES['RSVP_ADD'].format(event=relevant_event.title)
			messages.add_message(request, messages.SUCCESS, message)
		relevant_event.save()
		return HttpResponseRedirect(reverse('homepage'))
	if thread_form.is_valid():
		thread_form.save()
		return HttpResponseRedirect(reverse('homepage'))
	if vote_form.is_valid():
		vote_form.save()
		return HttpResponseRedirect(reverse('homepage'))
	return render_to_response('homepage.html', {
			'page_name': "Home",
			'requests_dict': requests_dict,
			'announcements_dict': announcements_dict,
			'announcement_form': announcement_form,
			'events_dict': events_dict,
			'thread_set': thread_set,
			'thread_form': thread_form,
			}, context_instance=RequestContext(request))

def help_view(request):
	''' The view of the helppage. '''
	return render_to_response('helppage.html', {
			'page_name': "Help Page",
			},  context_instance=RequestContext(request))

def site_map_view(request):
	''' The view of the site map. '''
	page_name = "Site Map"
	return render_to_response('site_map.html', {
			'page_name': page_name,
			}, context_instance=RequestContext(request))

@profile_required
def my_profile_view(request):
	''' The view of the profile page. '''
	page_name = "Profile Page"
	if request.user.username == ANONYMOUS_USERNAME:
		return red_home(request, MESSAGES['SPINELESS'])
	user = request.user
	userProfile = UserProfile.objects.get(user=request.user)
	change_password_form = ChangePasswordForm(
		request.POST if 'submit_password_form' in request.POST else None,
		user=user,
		)
	update_profile_form = UpdateProfileForm(
		request.POST if 'submit_profile_form' in request.POST else None,
		user=request.user,
		initial={
			'current_room': userProfile.current_room,
			'former_rooms': userProfile.former_rooms,
			'former_houses': userProfile.former_houses,
			'email': user.email,
			'email_visible_to_others': userProfile.email_visible,
			'phone_number': userProfile.phone_number,
			'phone_visible_to_others': userProfile.phone_visible,
			})
	if change_password_form.is_valid():
		change_password_form.save()
		messages.add_message(request, messages.SUCCESS, "Your password was successfully changed.")
		return HttpResponseRedirect(reverse('my_profile'))
	if update_profile_form.is_valid():
		update_profile_form.save()
		messages.add_message(request, messages.SUCCESS, "Your profile has been successfully updated.")
		return HttpResponseRedirect(reverse('my_profile'))
	return render_to_response('my_profile.html', {
			'page_name': page_name,
			'update_profile_form': update_profile_form,
			'change_password_form': change_password_form,
			}, context_instance=RequestContext(request))

def login_view(request):
	''' The view of the login page. '''
	ANONYMOUS_SESSION = request.session.get('ANONYMOUS_SESSION', False)
	page_name = "Login Page"
	redirect_to = request.REQUEST.get('next', reverse('homepage'))
	if (request.user.is_authenticated() and not ANONYMOUS_SESSION) or (ANONYMOUS_SESSION and request.user.username != ANONYMOUS_USERNAME):
		return HttpResponseRedirect(redirect_to)
	form = LoginForm(request.POST or None)
	if form.is_valid():
		username_or_email = form.cleaned_data['username_or_email']
		password = form.cleaned_data['password']
		username = None
		if username == ANONYMOUS_USERNAME:
			return red_ext(request, MESSAGES['ANONYMOUS_DENIED'])
		temp_user = None
		try:
			temp_user = User.objects.get(username=username_or_email)
			username = username_or_email
		except User.DoesNotExist:
			try:
				temp_user = User.objects.get(email=username_or_email)
				username = User.objects.get(email=username_or_email).username
			except User.DoesNotExist:
				form.errors['__all__'] = form.error_class(["Invalid username/password combination. Please try again."])
		if temp_user is not None:
			if temp_user.is_active:
				user = authenticate(username=username, password=password)
				if user is not None:
					login(request, user)
					if ANONYMOUS_SESSION:
						request.session['ANONYMOUS_SESSION'] = True
					return HttpResponseRedirect(redirect_to)
				else:
					reset_url = request.build_absolute_uri(reverse('reset_pw'))
					messages.add_message(request, messages.INFO, MESSAGES['RESET_MESSAGE'].format(reset_url=reset_url))
					form.errors['__all__'] = form.error_class([MESSAGES['INVALID_LOGIN']])
					time.sleep(1) # Invalid login - delay 1 second as rudimentary security against brute force attacks
			else:
				form.errors['__all__'] = form.error_class(["Your account is not active. Please contact the site administrator to activate your account."])

	return render_to_response('login.html', {
			'page_name': page_name,
			'form': form,
			'oauth_providers': _get_oauth_providers(),
			'redirect_to': redirect_to,
			}, context_instance=RequestContext(request))

def _get_oauth_providers():
	matches = {
		"facebook": ("Facebook", "fb.png"),
		"google-oauth": ("Google", "google.png"),
		"google-oauth2": ("Google", "google.png"),
		"github": ("Github", "github.ico"),
		}

	providers = []
	for provider in settings.AUTHENTICATION_BACKENDS:
		if provider.startswith("social"):
			module_name, backend = provider.rsplit(".", 1)
			module = __import__(module_name, fromlist=[''])
			if module and getattr(module, backend, ""):
				backend_name = getattr(module, backend).name
				full_name, icon = matches.get(backend_name,
											  ("Unknown", "unknown.png"))
				providers.append((backend_name, full_name, icon))
	return providers

def logout_view(request):
	''' Log the user out. '''
	ANONYMOUS_SESSION = request.session.get('ANONYMOUS_SESSION', False)
	if ANONYMOUS_SESSION:
		if request.user.username != ANONYMOUS_USERNAME:
			logout(request)
			try:
				spineless = User.objects.get(username=ANONYMOUS_USERNAME)
			except User.DoesNotExist:
				random_password = User.objects.make_random_password()
				spineless = User.objects.create_user(username=ANONYMOUS_USERNAME, first_name="Anonymous", last_name="Coward", password=random_password)
				spineless.is_active = False
				spineless.save()
				spineless_profile = UserProfile.objects.get(user=spineless)
				spineless_profile.status = UserProfile.ALUMNUS
				spineless_profile.save()
			spineless.backend = 'django.contrib.auth.backends.ModelBackend'
			login(request, spineless)
			request.session['ANONYMOUS_SESSION'] = True
		else:
			messages.add_message(request, messages.ERROR, MESSAGES['ANONYMOUS_DENIED'])
	else:
		logout(request)
	return HttpResponseRedirect(reverse('homepage'))

@profile_required
def member_directory_view(request):
	''' View of member directory. '''
	page_name = "Member Directory"
	residents = UserProfile.objects.filter(status=UserProfile.RESIDENT)
	boarders = UserProfile.objects.filter(status=UserProfile.BOARDER)
	alumni = UserProfile.objects.filter(status=UserProfile.ALUMNUS) \
	  .exclude(user__username=ANONYMOUS_USERNAME)
	return render_to_response('member_directory.html', {
			'page_name': page_name,
			'residents': residents,
			'boarders': boarders,
			'alumni': alumni,
			}, context_instance=RequestContext(request))

@profile_required
def member_profile_view(request, targetUsername):
	''' View a member's Profile. '''
	if targetUsername == request.user.username and targetUsername != ANONYMOUS_USERNAME:
		return HttpResponseRedirect(reverse('my_profile'))
	page_name = "%s's Profile" % targetUsername
	userProfile = UserProfile.objects.get(user=request.user)
	targetUser = get_object_or_404(User, username=targetUsername)
	targetProfile = get_object_or_404(UserProfile, user=targetUser)
	number_of_threads = Thread.objects.filter(owner=targetProfile).count()
	number_of_requests = Request.objects.filter(owner=targetProfile).count()
	return render_to_response('member_profile.html', {
			'page_name': page_name,
			'targetUser': targetUser,
			'targetProfile': targetProfile,
			'number_of_threads': number_of_threads,
			'number_of_requests': number_of_requests,
			}, context_instance=RequestContext(request))

def request_profile_view(request):
	''' The page to request a user profile on the site. '''
	page_name = "Profile Request Page"
	redirect_to = request.REQUEST.get('next', reverse('homepage'))
	if request.user.is_authenticated() and request.user.username != ANONYMOUS_USERNAME:
		return HttpResponseRedirect(redirect_to)
	form = ProfileRequestForm(request.POST or None)
	if form.is_valid():
		username = form.cleaned_data['username']
		first_name = form.cleaned_data['first_name']
		last_name = form.cleaned_data['last_name']
		email = form.cleaned_data['email']
		if User.objects.filter(username=username).count():
			reset_url = request.build_absolute_uri(reverse('reset_pw'))
			form._errors['username'] = forms.util.ErrorList([MESSAGES["USERNAME_TAKEN"].format(username=username)])
			messages.add_message(request, messages.INFO, MESSAGES['RESET_MESSAGE'].format(reset_url=reset_url))
		elif User.objects.filter(email=email).count():
			reset_url = request.build_absolute_uri(reverse('reset_pw'))
			messages.add_message(request, messages.INFO, MESSAGES['RESET_MESSAGE'].format(reset_url=reset_url))
			form._errors['email'] = forms.util.ErrorList([MESSAGES["EMAIL_TAKEN"]])
		elif ProfileRequest.objects.filter(first_name=first_name, last_name=last_name).count():
			form.errors['__all__'] = form.error_class([MESSAGES["PROFILE_TAKEN"].format(first_name=first_name, last_name=last_name)])
		elif User.objects.filter(first_name=first_name, last_name=last_name).count():
			reset_url = request.build_absolute_uri(reverse('reset_pw'))
			messages.add_message(request, messages.INFO, MESSAGES['PROFILE_REQUEST_RESET'].format(reset_url=reset_url))
		else:
			form.save()
			messages.add_message(request, messages.SUCCESS, MESSAGES['PROFILE_SUBMITTED'])
			if SEND_EMAILS and (email not in EMAIL_BLACKLIST):
				submission_subject = SUBMISSION_SUBJECT.format(house=HOUSE_NAME)
				submission_email = SUBMISSION_EMAIL.format(house=HOUSE_NAME, full_name=first_name + " " + last_name, admin_name=ADMINS[0][0],
					admin_email=ADMINS[0][1])
				try:
					send_mail(submission_subject, submission_email, EMAIL_HOST_USER, [email], fail_silently=False)
					# Add logging here
				except SMTPException:
					pass # Add logging here
			return HttpResponseRedirect(redirect_to)
	return render(request, 'request_profile.html', {
			'form': form,
			'page_name': page_name,
			'oauth_providers': _get_oauth_providers(),
			'redirect_to': redirect_to,
			})

@admin_required
def manage_profile_requests_view(request):
	''' The page to manager user profile requests. '''
	page_name = "Admin - Manage Profile Requests"
	profile_requests = ProfileRequest.objects.all()
	return render_to_response(
		'manage_profile_requests.html', {
			'page_name': page_name,
			'choices': UserProfile.STATUS_CHOICES,
			'profile_requests': profile_requests
			},
		context_instance=RequestContext(request))

@admin_required
def modify_profile_request_view(request, request_pk):
	''' The page to modify a user's profile request. request_pk is the pk of the profile request. '''
	page_name = "Admin - Profile Request"
	profile_request = get_object_or_404(ProfileRequest, pk=request_pk)
	mod_form = ModifyProfileRequestForm(
		request.POST if 'add_user' in request.POST else None,
		initial={
			'status': profile_request.affiliation,
			'username': profile_request.username,
			'first_name': profile_request.first_name,
			'last_name': profile_request.last_name,
			'email': profile_request.email,
			'is_active': True,
			})
	addendum = ""
	if 'delete_request' in request.POST:
		if SEND_EMAILS and (profile_request.email not in EMAIL_BLACKLIST):
			deletion_subject = DELETION_SUBJECT.format(house=HOUSE_NAME)
			deletion_email = DELETION_EMAIL.format(house=HOUSE_NAME, full_name=profile_request.first_name + " " + profile_request.last_name,
				admin_name=ADMINS[0][0], admin_email=ADMINS[0][1])
			try:
				send_mail(deletion_subject, deletion_email, EMAIL_HOST_USER, [profile_request.email], fail_silently=False)
				addendum = MESSAGES['PROFILE_REQUEST_DELETION_EMAIL'].format(full_name=profile_request.first_name + ' ' + profile_request.last_name,
					email=profile_request.email)
			except SMTPException:
				message = MESSAGES['EMAIL_FAIL'].format(email=profile_request.email, error=e)
				messages.add_message(request, messages.ERROR, message)
		profile_request.delete()
		message = MESSAGES['PREQ_DEL'].format(first_name=profile_request.first_name, last_name=profile_request.last_name, username=profile_request.username)
		messages.add_message(request, messages.SUCCESS, message + addendum)
		return HttpResponseRedirect(reverse('manage_profile_requests'))
	if mod_form.is_valid():
		new_user = mod_form.save(profile_request)
		if new_user.is_active and SEND_EMAILS and (new_user.email not in EMAIL_BLACKLIST):
			approval_subject = APPROVAL_SUBJECT.format(house=HOUSE_NAME)
			if profile_request.provider:
				username_bit = profile_request.provider.title()
			elif new_user.username == profile_request.username:
				username_bit = "the username and password you selected"
			else:
				username_bit = "the username %s and the password you selected" % new_user.username
			login_url = request.build_absolute_uri(reverse('login'))
			approval_email = APPROVAL_EMAIL.format(house=HOUSE_NAME, full_name=new_user.get_full_name(), admin_name=ADMINS[0][0],
				admin_email=ADMINS[0][1], login_url=login_url, username_bit=username_bit, request_date=profile_request.request_date)
			try:
				send_mail(approval_subject, approval_email, EMAIL_HOST_USER, [new_user.email], fail_silently=False)
				addendum = MESSAGES['PROFILE_REQUEST_APPROVAL_EMAIL'].format(full_name="{0} {1}".format(new_user.first_name, new_user.last_name),
					email=new_user.email)
			except SMTPException as e:
				message = MESSAGES['EMAIL_FAIL'].format(email=new_user.email, error=e)
				messages.add_message(request, messages.ERROR, message)
		profile_request.delete()
		message = MESSAGES['USER_ADDED'].format(username=new_user.username)
		messages.add_message(request, messages.SUCCESS, message + addendum)
		return HttpResponseRedirect(reverse('manage_profile_requests'))
	return render_to_response('modify_profile_request.html', {
			'page_name': page_name,
			'add_user_form': mod_form,
			'provider': profile_request.provider,
			'uid': profile_request.uid,
			}, context_instance=RequestContext(request))

@admin_required
def custom_manage_users_view(request):
	page_name = "Admin - Manage Users"
	residents = UserProfile.objects.filter(status=UserProfile.RESIDENT)
	boarders = UserProfile.objects.filter(status=UserProfile.BOARDER)
	alumni = UserProfile.objects.filter(status=UserProfile.ALUMNUS).exclude(user__username=ANONYMOUS_USERNAME)
	return render_to_response('custom_manage_users.html', {
			'page_name': page_name,
			'residents': residents,
			'boarders': boarders,
			'alumni': alumni,
			}, context_instance=RequestContext(request))

@admin_required
def custom_modify_user_view(request, targetUsername):
	''' The page to modify a user. '''
	if targetUsername == ANONYMOUS_USERNAME:
		messages.add_message(request, messages.WARNING, MESSAGES['ANONYMOUS_EDIT'])
	page_name = "Admin - Modify User"
	targetUser = get_object_or_404(User, username=targetUsername)
	targetProfile = get_object_or_404(UserProfile, user=targetUser)

	modify_user_form = ModifyUserForm(
		request.POST if "update_user_profile" in request.POST else None,
		user=targetUser,
		request=request,
		)
	change_user_password_form = ChangeUserPasswordForm(
		request.POST if 'change_user_password' in request.POST else None,
		user=targetUser,
		request=request,
		)
	delete_user_form = DeleteUserForm(
		request.POST if 'delete_user' in request.POST else None,
		user=targetUser,
		request=request,
		)
	if modify_user_form.is_valid():
		modify_user_form.save()
		messages.add_message(
			request, messages.SUCCESS,
			MESSAGES['USER_PROFILE_SAVED'].format(username=targetUser.username),
			)
		return HttpResponseRedirect(reverse('custom_modify_user',
											kwargs={'targetUsername': targetUsername}))
	if change_user_password_form.is_valid():
		change_user_password_form.save()
		messages.add_message(
			request, messages.SUCCESS,
			MESSAGES['USER_PW_CHANGED'].format(username=targetUser.username),
			)
		return HttpResponseRedirect(reverse('custom_modify_user',
											kwargs={'targetUsername': targetUsername}))
	if delete_user_form.is_valid():
		delete_user_form.save()
		messages.add_message(
			request, messages.SUCCESS,
			MESSAGES['USER_DELETED'].format(username=targetUser.username),
			)
		return HttpResponseRedirect(reverse("custom_manage_users"))

	return render_to_response('custom_modify_user.html', {
			'targetUser': targetUser,
			'targetProfile': targetProfile,
			'page_name': page_name,
			'modify_user_form': modify_user_form,
			'change_user_password_form': change_user_password_form,
			'delete_user_form': delete_user_form,
			'thread_count': Thread.objects.filter(owner=targetProfile).count(),
			'message_count': Message.objects.filter(owner=targetProfile).count(),
			'request_count': Request.objects.filter(owner=targetProfile).count(),
			'response_count': Response.objects.filter(owner=targetProfile).count(),
			'announcement_count': Announcement.objects.filter(incumbent=targetProfile).count(),
			'event_count': Event.objects.filter(owner=targetProfile).count(),
			}, context_instance=RequestContext(request))

@admin_required
def custom_add_user_view(request):
	''' The page to add a new user. '''
	page_name = "Admin - Add User"
	add_user_form = AddUserForm(request.POST or None, initial={
		'status': UserProfile.RESIDENT,
		})
	if add_user_form.is_valid():
		add_user_form.save()
		message = MESSAGES['USER_ADDED'].format(
			username=add_user_form.cleaned_data["username"])
		messages.add_message(request, messages.SUCCESS, message)
		return HttpResponseRedirect(reverse('custom_add_user'))
	return render_to_response('custom_add_user.html', {
			'page_name': page_name,
			'add_user_form': add_user_form,
			}, context_instance=RequestContext(request))

@admin_required
def utilities_view(request):
	''' View for an admin to do maintenance tasks on the site. '''
	return render_to_response('utilities.html', {
			'page_name': "Admin - Site Utilities",
			}, context_instance=RequestContext(request))

@profile_required
def bylaws_view(request):
	""" View for bylaws. """
	return render_to_response('bylaws.html', {
			'page_name': "House Bylaws",
			}, context_instance=RequestContext(request))

def reset_pw_view(request):
	""" View to send an e-mail to reset password. """
	return password_reset(request,
		template_name="reset.html",
		email_template_name="reset_email.html",
		subject_template_name="reset_subject.txt",
		post_reset_redirect=reverse('login'))

def reset_pw_confirm_view(request, uidb64=None, token=None):
	""" View to confirm resetting password. """
	return password_reset_confirm(request,
		template_name="reset_confirmation.html",
		uidb64=uidb64, token=token, post_reset_redirect=reverse('login'))

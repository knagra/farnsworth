from django.shortcuts import render

from django.shortcuts import render_to_response, render, get_object_or_404
from django.http import HttpResponseRedirect
from django import forms
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.contrib.auth import logout, login, authenticate, hashers
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta
from django.utils.timezone import utc
from django.contrib import messages

from farnsworth.settings import house, ADMINS, max_threads, max_messages, \
    home_max_announcements, home_max_threads
from utils.variables import ANONYMOUS_USERNAME, MESSAGES
from threads.models import UserProfile, Thread, Message
from threads.forms import *
from threads.redirects import red_ext, red_home
from threads.decorators import profile_required
from managers.models import RequestType, Manager, Request, Response, Announcement
from managers.forms import AnnouncementForm, ManagerResponseForm, VoteForm, UnpinForm
from events.models import Event
from events.forms import RsvpForm

def landing_view(request):
	''' The external landing.'''
	return render_to_response('external.html', {
			'page_name': "Landing",
			}, context_instance=RequestContext(request))

@profile_required(redirect_user='external', redirect_profile=red_ext)
def homepage_view(request, message=None):
	''' The view of the homepage. '''
	userProfile = UserProfile.objects.get(user=request.user)
	request_types = RequestType.objects.filter(enabled=True)
	manager_request_types = list() # List of request types for which the user is a relevant manager
	for request_type in request_types:
		for position in request_type.managers.all():
			if userProfile == position.incumbent:
				manager_request_types.append(request_type)
				break
	requests_dict = list() # Pseudo-dictionary, list with items of form (request_type, (request, [list_of_request_responses], response_form))
	# Generate a dict of unfilled, unclosed requests for each request_type for which the user is a relevant manager:
	if manager_request_types:
		for request_type in manager_request_types:
			requests_list = list() # Items of form (request, [list_of_request_responses], response_form, upvote, downvote, vote_form)
			# Select only unclosed, unfilled requests of type request_type:
			type_requests = Request.objects.filter(request_type=request_type, filled=False, closed=False)
			for req in type_requests:
				response_list = Response.objects.filter(request=req)
				form = ManagerResponseForm(initial={'request_pk': req.pk})
				upvote = userProfile in req.upvotes.all()
				downvote = userProfile in req.downvotes.all()
				vote_form = VoteForm(initial={'request_pk': req.pk})
				requests_list.append((req, response_list, form, upvote, downvote, vote_form))
			requests_dict.append((request_type, requests_list))
	announcement_form = None
	manager_positions = Manager.objects.filter(incumbent=userProfile)
	if manager_positions:
		announcement_form = AnnouncementForm(manager_positions)
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
	thread_form = ThreadForm()
	threads = list() # List of recent threads
	x = 0
	for thread in Thread.objects.all():
		threads.append(thread)
		x += 1
		if x >= home_max_threads:
			break
	if request.method == 'POST':
		if 'add_response' in request.POST:
			response_form = ManagerResponseForm(request.POST)
			if response_form.is_valid():
				request_pk = response_form.cleaned_data['request_pk']
				body = response_form.cleaned_data['body']
				relevant_request = Request.objects.get(pk=request_pk)
				new_response = Response(owner=userProfile, body=body, request=relevant_request)
				relevant_request.closed = response_form.cleaned_data['mark_closed']
				relevant_request.filled = response_form.cleaned_data['mark_filled']
				new_response.manager = True
				relevant_request.change_date = datetime.utcnow().replace(tzinfo=utc)
				relevant_request.save()
				new_response.save()
				if relevant_request.closed:
					messages.add_message(request, messages.SUCCESS, MESSAGES['REQ_CLOSED'])
				if relevant_request.filled:
					messages.add_message(request, messages.SUCCESS, MESSAGES['REQ_FILLED'])
				return HttpResponseRedirect(reverse('homepage'))
			else:
				messages.add_message(request, messages.ERROR, MESSAGES['INVALID_FORM'])
		elif 'post_announcement' in request.POST:
			announcement_form = AnnouncementForm(manager_positions, post=request.POST)
			if announcement_form.is_valid():
				body = announcement_form.cleaned_data['body']
				manager = announcement_form.cleaned_data['as_manager']
				new_announcement = Announcement(manager=manager, body=body, incumbent=userProfile, pinned=True)
				new_announcement.save()
				return HttpResponseRedirect(reverse('homepage'))
			else:
				messages.add_message(request, messages.ERROR, MESSAGES['INVALID_FORM'])
		elif 'unpin' in request.POST:
			unpin_form = UnpinForm(request.POST)
			if unpin_form.is_valid():
				announcement_pk = unpin_form.cleaned_data['announcement_pk']
				relevant_announcement = Announcement.objects.get(pk=announcement_pk)
				relevant_announcement.pinned = False
				relevant_announcement.save()
				return HttpResponseRedirect(reverse('homepage'))
			else:
				messages.add_message(request, messages.ERROR, MESSAGES['INVALID_FORM'])
		elif 'rsvp' in request.POST:
			rsvp_form = RsvpForm(request.POST)
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
			else:
				messages.add_message(request, messages.ERROR, MESSAGES['INVALID_FORM'])
		elif 'submit_thread_form' in request.POST:
			thread_form = ThreadForm(request.POST)
			if thread_form.is_valid():
				subject = thread_form.cleaned_data['subject']
				body = thread_form.cleaned_data['body']
				thread = Thread(owner=userProfile, subject=subject, number_of_messages=1, active=True)
				thread.save()
				message = Message(body=body, owner=userProfile, thread=thread)
				message.save()
				return HttpResponseRedirect(reverse('homepage'))
			else:
				messages.add_message(request, messages.ERROR, MESSAGES['THREAD_ERROR'])
		elif 'upvote' in request.POST:
			vote_form = VoteForm(request.POST)
			if vote_form.is_valid():
				request_pk = vote_form.cleaned_data['request_pk']
				relevant_request = Request.objects.get(pk=request_pk)
				if userProfile in relevant_request.upvotes.all():
					relevant_request.upvotes.remove(userProfile)
				else:
					relevant_request.upvotes.add(userProfile)
					relevant_request.downvotes.remove(userProfile)
				relevant_request.save()
				return HttpResponseRedirect(reverse('homepage'))
			else:
				messages.add_message(request, messages.ERROR, MESSAGES['INVALID_FORM'])
		elif 'downvote' in request.POST:
			vote_form = VoteForm(request.POST)
			if vote_form.is_valid():
				request_pk = vote_form.cleaned_data['request_pk']
				relevant_request = Request.objects.get(pk=request_pk)
				if userProfile in relevant_request.downvotes.all():
					relevant_request.downvotes.remove(userProfile)
				else:
					relevant_request.downvotes.add(userProfile)
					relevant_request.upvotes.remove(userProfile)
				relevant_request.save()
				return HttpResponseRedirect(reverse('homepage'))
			else:
				messages.add_message(request, messages.ERROR, MESSAGES['INVALID_FORM'])
		else:
			messages.add_message(request, messages.ERROR, MESSAGES['UNKNOWN_FORM'])
	return render_to_response('homepage.html', {
			'page_name': "Home",
			'requests_dict': requests_dict,
			'announcements_dict': announcements_dict,
			'announcement_form': announcement_form,
			'events_dict': events_dict, 
			'threads': threads,
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
	change_password_form = ChangePasswordForm()
	update_profile_form = UpdateProfileForm(initial={
			'current_room': userProfile.current_room,
			'former_rooms': userProfile.former_rooms,
			'former_houses': userProfile.former_houses,
			'email': user.email,
			'email_visible_to_others': userProfile.email_visible,
			'phone_number': userProfile.phone_number,
			'phone_visible_to_others': userProfile.phone_visible,
			})
	if request.method == 'POST':
		if 'submit_password_form' in request.POST:
			change_password_form = ChangePasswordForm(request.POST)
			if change_password_form.is_valid():
				current_password = change_password_form.cleaned_data['current_password']
				new_password = change_password_form.cleaned_data['new_password']
				confirm_password = change_password_form.cleaned_data['confirm_password']
				if hashers.check_password(current_password, user.password):
					hashed_password = hashers.make_password(new_password)
					if hashers.is_password_usable(hashed_password):
						user.password = hashed_password
						user.save()
						messages.add_message(request, messages.SUCCESS, "Your password was successfully changed.")
						return HttpResponseRedirect(reverse('my_profile'))
					else:
						password_non_field_error = "Password didn't hash properly.  Please try again."
						change_password_form.errors['__all__'] = change_password_form.error_class([password_non_field_error])
						return render_to_response('my_profile.html', {
								'page_name': page_name,
								'update_profile_form': update_profile_form,
								'change_password_form': change_password_form,
								}, context_instance=RequestContext(request))
				else:
					change_password_form._errors['current_password'] = forms.util.ErrorList([u"Wrong password."])
		elif 'submit_profile_form' in request.POST:
			update_profile_form = UpdateProfileForm(request.POST)
			if update_profile_form.is_valid():
				current_room = update_profile_form.cleaned_data['current_room']
				former_rooms = update_profile_form.cleaned_data['former_rooms']
				former_houses = update_profile_form.cleaned_data['former_houses']
				email = update_profile_form.cleaned_data['email']
				email_visible_to_others = update_profile_form.cleaned_data['email_visible_to_others']
				phone_number = update_profile_form.cleaned_data['phone_number']
				phone_visible_to_others = update_profile_form.cleaned_data['phone_visible_to_others']
				enter_password = update_profile_form.cleaned_data['enter_password']
				if hashers.check_password(enter_password, user.password):
					userProfile.current_room = current_room
					userProfile.former_rooms = former_rooms
					userProfile.former_houses = former_houses
					user.email = email
					userProfile.email_visible = email_visible_to_others
					userProfile.phone_number = phone_number
					userProfile.phone_visible = phone_visible_to_others
					userProfile.save()
					messages.add_message(request, messages.SUCCESS, "Your profile has been successfully updated.")
					return HttpResponseRedirect(reverse('my_profile'))
				else:
					update_profile_form._errors['enter_password'] = forms.util.ErrorList([u"Wrong password"])
		else:
			return red_home(request, MESSAGES['UNKNOWN_FORM'])
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
	if request.method == 'POST' and form.is_valid():
		username = form.cleaned_data['username']
		password = form.cleaned_data['password']
		if username == ANONYMOUS_USERNAME:
			return red_ext(request, MESSAGES['ANONYMOUS_DENIED'])
		try:
			temp_user = User.objects.get(username=username)
			if temp_user is not None:
				if temp_user.is_active:
					user = authenticate(username=username, password=password)
					if user is not None:
						login(request, user)
						if ANONYMOUS_SESSION:
							request.session['ANONYMOUS_SESSION'] = True
						return HttpResponseRedirect(redirect_to)
					else:
						form.errors['__all__'] = form.error_class(["Invalid username/password combination.  Please try again."])
				else:
					form.errors['__all__'] = form.error_class(["Your account is not active.  Please contact the site administrator to activate your account."])
		except User.DoesNotExist:
			form.errors['__all__'] = form.error_class(["User not found"])
	return render_to_response('login.html', {
			'page_name': page_name,
			'form': form,
			}, context_instance=RequestContext(request))

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
	alumni = UserProfile.objects.filter(status=UserProfile.ALUMNUS)
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

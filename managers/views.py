'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''

from datetime import datetime
from django.shortcuts import render_to_response, render, get_object_or_404
from django.http import HttpResponseRedirect
from django import forms
from django.core.urlresolvers import reverse
from django.contrib.auth import hashers, logout, login
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.utils.timezone import utc
from django.contrib import messages

from farnsworth.settings import house, short_house, ADMINS, max_requests, max_responses
from utils.variables import ANONYMOUS_USERNAME, MESSAGES
from utils.funcs import convert_to_url
from base.decorators import admin_required, profile_required, president_admin_required
from base.models import UserProfile, ProfileRequest
from base.redirects import red_ext, red_home
from threads.models import Thread, Message
from managers.models import Manager, RequestType, Request, Response, Announcement
from managers.forms import ManagerForm, RequestTypeForm, RequestForm, ResponseForm, \
    ManagerResponseForm, VoteForm, AnnouncementForm, UnpinForm

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
	return {
		'REQUEST_TYPES': RequestType.objects.filter(enabled=True),
		'HOUSE': house,
		'ANONYMOUS_USERNAME':ANONYMOUS_USERNAME,
		'SHORT_HOUSE': short_house,
		'ADMIN': ADMINS[0],
		'NUM_OF_PROFILE_REQUESTS': ProfileRequest.objects.all().count(),
		'ANONYMOUS_SESSION': ANONYMOUS_SESSION,
		'PRESIDENT': PRESIDENT,
		}

@admin_required
def anonymous_login_view(request):
	''' View for an admin to log her/himself out and login the anonymous user. '''
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
	messages.add_message(request, messages.INFO, MESSAGES['ANONYMOUS_LOGIN'])
	return HttpResponseRedirect(reverse('homepage'))

@admin_required
def end_anonymous_session_view(request):
	''' End the anonymous session if the user is a superuser. '''
	request.session['ANONYMOUS_SESSION'] = False
	messages.add_message(request, messages.INFO, MESSAGES['ANONYMOUS_SESSION_ENDED'])
	return HttpResponseRedirect(reverse('utilities'))

@profile_required
def list_managers_view(request):
	''' Show a list of manager positions with links to view in detail. '''
	managerset = Manager.objects.filter(active=True)
	return render_to_response('list_managers.html', {
			'page_name': "Managers",
			'managerset': managerset,
			}, context_instance=RequestContext(request))

@profile_required
def manager_view(request, managerTitle):
	''' View the details of a manager position.
	Parameters:
		request is an HTTP request
		managerTitle is the URL title of the manager.
	'''
	targetManager = get_object_or_404(Manager, url_title=managerTitle)

	if not targetManager.active:
		messages.add_message(request, messages.ERROR, MESSAGES['INACTIVE_MANAGER'].format(managerTitle=targetManager.title))
		return HttpResponseRedirect(reverse('list_managers'))
	else:
		return render_to_response('view_manager.html', {
				'page_name': "View Manager",
				'targetManager': targetManager,
				}, context_instance=RequestContext(request))

@president_admin_required
def meta_manager_view(request):
	'''
	A manager of managers.  Display a list of current managers, with links to modify them.
	Also display a link to add a new manager.  Restricted to presidents and superadmins.
	'''
	userProfile = UserProfile.objects.get(user=request.user)
	managerset = Manager.objects.all()
	return render_to_response('meta_manager.html', {
			'page_name': "Admin - Meta-Manager",
			'managerset': managerset,
			}, context_instance=RequestContext(request))

@president_admin_required
def add_manager_view(request):
	''' View to add a new manager position. Restricted to superadmins and presidents. '''
	userProfile = UserProfile.objects.get(user=request.user)
	if request.method == 'POST':
		form = ManagerForm(request.POST)
		if form.is_valid():
			title = form.cleaned_data['title']
			incumbent = form.cleaned_data['incumbent']
			compensation = form.cleaned_data['compensation']
			duties = form.cleaned_data['duties']
			email = form.cleaned_data['email']
			president = form.cleaned_data['president']
			workshift_manager = form.cleaned_data['workshift_manager']
			active = form.cleaned_data['active']
			url_title = convert_to_url(title)
			if Manager.objects.filter(title=title).count():
				form._errors['title'] = forms.util.ErrorList([u"A manager with this title already exists."])
			elif Manager.objects.filter(url_title=url_title).count():
				form._errors['title'] = forms.util.ErrorList([u'This manager title maps to a url that is already taken.  Please note, "Site Admin" and "sITe_adMIN" map to the same URL.'])
			else:
				new_manager = Manager(
					title=title,
					url_title=url_title,
					compensation=compensation,
					duties=duties, email=email,
					president=president,
					workshift_manager=workshift_manager,
					active=active,
					)
				if incumbent:
					new_manager.incumbent = incumbent
				new_manager.save()
				messages.add_message(request, messages.SUCCESS,
						     MESSAGES['MANAGER_ADDED'].format(managerTitle=title))
				return HttpResponseRedirect(reverse('add_manager'))
	else:
		form = ManagerForm()
	return render_to_response('edit_manager.html', {
			'page_name': "Admin - Add Manager",
			'form': form,
			}, context_instance=RequestContext(request))

@president_admin_required
def edit_manager_view(request, managerTitle):
	''' View to modify an existing manager. 
	Parameters:
		request is an HTTP request
		managerTitle is URL title of the manager.
	'''
	userProfile = UserProfile.objects.get(user=request.user)
	targetManager = get_object_or_404(Manager, url_title=managerTitle)

	if request.method == 'POST':
		form = ManagerForm(request.POST)
		if form.is_valid():
			title = form.cleaned_data['title']
			incumbent = form.cleaned_data['incumbent']
			compensation = form.cleaned_data['compensation']
			duties = form.cleaned_data['duties']
			email = form.cleaned_data['email']
			president = form.cleaned_data['president']
			workshift_manager = form.cleaned_data['workshift_manager']
			active = form.cleaned_data['active']
			url_title = convert_to_url(title)
			if Manager.objects.filter(title=title).count() and Manager.objects.get(title=title) != targetManager:
				form._errors['title'] = forms.util.ErrorList([u"A manager with this title already exists."])
			elif Manager.objects.filter(url_title=url_title).count() and Manager.objects.get(url_title=url_title) != targetManager:
				form._errors['title'] = forms.util.ErrorList([u'This manager title maps to a url that is already taken.  Please note, "Site Admin" and "sITe_adMIN" map to the same URL.'])
			else:
				targetManager.title = title
				targetManager.url_title = url_title
				targetManager.incumbent = incumbent
				targetManager.compensation = compensation
				targetManager.duties = duties
				targetManager.email = email
				targetManager.president = president
				targetManager.workshift_manager = workshift_manager
				targetManager.active = active
				targetManager.save()
				messages.add_message(request, messages.SUCCESS, MESSAGES['MANAGER_SAVED'].format(managerTitle=title))
				return HttpResponseRedirect(reverse('meta_manager'))
		else:
			messages.add_message(request, messages.ERROR, MESSAGES['INVALID_FORM'])
	else:
		form = ManagerForm(initial={
				'title': targetManager.title,
				'incumbent': targetManager.incumbent,
				'compensation': targetManager.compensation,
				'duties': targetManager.duties,
				'email': targetManager.email,
				'president': targetManager.president,
				'workshift_manager': targetManager.workshift_manager,
				'active': targetManager.active,
				})
	return render_to_response('edit_manager.html', {
			'page_name': "Admin - Edit Manager",
			'form': form,
			'manager_title': targetManager.title,
			}, context_instance=RequestContext(request))

@president_admin_required
def manage_request_types_view(request):
	''' Manage requests.  Display a list of request types with links to edit them.
	Also display a link to add a new request type.  Restricted to presidents and superadmins.
	'''
	userProfile = UserProfile.objects.get(user=request.user)
	request_types = RequestType.objects.all()
	return render_to_response('manage_request_types.html', {
			'page_name': "Admin - Manage Request Types",
			'request_types': request_types},
			context_instance=RequestContext(request))

@president_admin_required
def add_request_type_view(request):
	''' View to add a new request type.  Restricted to presidents and superadmins. '''
	userProfile = UserProfile.objects.get(user=request.user)
	if request.method == 'POST':
		form = RequestTypeForm(request.POST)
		if form.is_valid():
			name = form.cleaned_data['name']
			relevant_managers = form.cleaned_data['relevant_managers']
			enabled = form.cleaned_data['enabled']
			glyphicon = form.cleaned_data['glyphicon']
			url_name = convert_to_url(name)
			if RequestType.objects.filter(name=name).count():
				form._errors['name'] = forms.util.ErrorList([u"A request type with this name already exists."])
			elif RequestType.objects.filter(url_name=url_name).count():
				form._errors['name'] = forms.util.ErrorList([u'This request type name maps to a url that is already taken.  Please note, "Waste Reduction" and "wasTE_RedUCtiON" map to the same URL.'])
			else:
				new_request_type = RequestType(name=name, url_name=url_name, enabled=enabled, glyphicon=glyphicon)
				new_request_type.save()
				for pos in relevant_managers:
					new_request_type.managers.add(pos)
				new_request_type.save()
				messages.add_message(request, messages.SUCCESS, MESSAGES['REQUEST_TYPE_ADDED'].format(typeName=name))
				return HttpResponseRedirect(reverse('manage_request_types'))
		else:
			messages.add_message(request, messages.ERROR, MESSAGES['INVALID_FORM'])
	else:
		form = RequestTypeForm()
	return render_to_response('edit_request_type.html', {
			'page_name': "Admin - Add Request Type",
			'form': form,
			}, context_instance=RequestContext(request))

@president_admin_required
def edit_request_type_view(request, typeName):
	''' View to edit a new request type.  Restricted to presidents and superadmins.
	Parameters:
		request is an HTTP request
		typeName is the request type's URL name.
	'''
	userProfile = UserProfile.objects.get(user=request.user)
	requestType = get_object_or_404(RequestType, url_name=typeName)

	if request.method == 'POST':
		form = RequestTypeForm(request.POST)
		if form.is_valid():
			name = form.cleaned_data['name']
			relevant_managers = form.cleaned_data['relevant_managers']
			enabled = form.cleaned_data['enabled']
			glyphicon = form.cleaned_data['glyphicon']
			url_name = convert_to_url(name)
			if RequestType.objects.filter(name=name).count() and RequestType.objects.get(name=name) != requestType:
				form._errors['name'] = forms.util.ErrorList([u"A request type with this name already exists."])
			elif RequestType.objects.filter(url_name=url_name).count() and RequestType.objects.get(url_name=url_name) != requestType:
				form._errors['name'] = forms.util.ErrorList([u'This request type name maps to a url that is already taken.  Please note, "Waste Reduction" and "wasTE_RedUCtiON" map to the same URL.'])
			else:
				requestType.name = name
				requestType.url_name = url_name
				requestType.managers = relevant_managers
				requestType.enabled = enabled
				requestType.glyphicon = glyphicon
				requestType.save()
				messages.add_message(request, messages.SUCCESS, MESSAGES['REQUEST_TYPE_SAVED'].format(typeName=name))
				return HttpResponseRedirect(reverse('manage_request_types'))
		else:
			messages.add_message(request, messages.ERROR, MESSAGES['INVALID_FORM'])
	else:
		form = RequestTypeForm(initial={
				'name': requestType.name,
				'relevant_managers': requestType.managers.all(),
				'enabled': requestType.enabled,
				'glyphicon': requestType.glyphicon,
				})
	return render_to_response('edit_request_type.html', {
			'page_name': "Admin - Edit Request Type",
			'form': form,
			'requestType': requestType,
			}, context_instance=RequestContext(request))

@profile_required
def requests_view(request, requestType):
	'''
	Generic request view.  Parameters:
		request is the HTTP request
		requestType is URL name of a RequestType.
			e.g. "food", "maintenance", "network", "site" 
	'''
	userProfile = UserProfile.objects.get(user=request.user)
	request_type = get_object_or_404(RequestType, url_name=requestType)
	page_name = "%s Requests" % request_type.name.title()
	if not request_type.enabled:
		message = "%s requests have been disabled." % request_type.name.title()
		return red_home(request, message)
	relevant_managers = request_type.managers.all()
	manager = any(i.incumbent == userProfile for i in relevant_managers)
	if request.method == 'POST':
		if 'submit_request' in request.POST:
			request_form = RequestForm(request.POST)
			if request_form.is_valid():
				body = request_form.cleaned_data['body']
				new_request = Request(owner=userProfile, body=body, request_type=request_type)
				new_request.save()
				return HttpResponseRedirect(reverse('requests', kwargs={'requestType': requestType}))
		elif 'add_response' in request.POST:
			if manager:
				form = ManagerResponseForm
			else:
				form = ResponseForm
			response_form = form(request.POST)
			if response_form.is_valid():
				request_pk = response_form.cleaned_data['request_pk']
				body = response_form.cleaned_data['body']
				relevant_request = Request.objects.get(pk=request_pk)
				new_response = Response(owner=userProfile, body=body, request=relevant_request)
				if manager:
					mark_filled = response_form.cleaned_data['mark_filled']
					mark_closed = response_form.cleaned_data['mark_closed']
					relevant_request.closed = mark_closed
					relevant_request.filled = mark_filled
					new_response.manager = True
				relevant_request.change_date = datetime.utcnow().replace(tzinfo=utc)
				relevant_request.save()
				new_response.save()
				return HttpResponseRedirect(reverse('requests', kwargs={'requestType': requestType}))
		elif 'upvote' in request.POST:
			vote_form = VoteForm(request.POST)
			if vote_form.is_valid():
				request_pk = vote_form.cleaned_data['request_pk']
				relevant_request = Request.objects.get(pk=request_pk)
				if userProfile in relevant_request.upvotes.all():
					relevant_request.upvotes.remove(userProfile)
				else:
					relevant_request.upvotes.add(userProfile)
				relevant_request.save()
		else:
			return red_home(request, MESSAGES['UNKNOWN_FORM'])
	request_form = RequestForm()
	x = 0 # number of requests loaded
	requests_dict = list() # A pseudo-dictionary, actually a list with items of form (request, [request_responses_list], response_form, upvote, vote_form)
	for req in Request.objects.filter(request_type=request_type):
		request_responses = Response.objects.filter(request=req)
		if manager:
			resp_form = ManagerResponseForm(initial={
					'request_pk': req.pk,
					'mark_filled': req.filled,
					'mark_closed': req.closed,
					})
		else:
			resp_form = ResponseForm(initial={'request_pk': req.pk})
		upvote = userProfile in req.upvotes.all()
		vote_form = VoteForm(initial={'request_pk': req.pk})
		requests_dict.append((req, request_responses, resp_form, upvote, vote_form))
		x += 1
		if x >= max_requests:
			break
	return render_to_response('requests.html', {
			'manager': manager,
			'request_type': request_type.name.title(),
			'page_name': page_name,
			'request_form': request_form,
			'requests_dict': requests_dict,
			}, context_instance=RequestContext(request))

@profile_required
def my_requests_view(request):
	'''
	Show user his/her requests, sorted by request_type.
	'''
	page_name = "My Requests"
	userProfile = UserProfile.objects.get(user=request.user)
	if request.method == 'POST':
		if 'submit_request' in request.POST:
			request_form = RequestForm(request.POST)
			if request_form.is_valid():
				type_pk = request_form.cleaned_data['type_pk']
				body = request_form.cleaned_data['body']
				try:
					request_type = RequestType.objects.get(pk=type_pk)
				except RequestType.DoesNotExist:
					message = "The request type was not recognized.  Please contact an admin for support."
					return red_home(request, message)
				new_request = Request(owner=userProfile, body=body, request_type=request_type)
				new_request.save()
				return HttpResponseRedirect(reverse('my_requests'))
		elif 'add_response' in request.POST:
			response_form = ManagerResponseForm(request.POST)
			if response_form.is_valid():
				request_pk = response_form.cleaned_data['request_pk']
				body = response_form.cleaned_data['body']
				relevant_request = Request.objects.get(pk=request_pk)
				new_response = Response(owner=userProfile, body=body, request=relevant_request)
				for manager_position in relevant_request.request_type.managers.all():
					if manager_position.incumbent == userProfile:
						mark_filled = response_form.cleaned_data['mark_filled']
						mark_closed = response_form.cleaned_data['mark_closed']
						relevant_request.filled = mark_filled
						relevant_request.closed = mark_closed
						relevant_request.change_date = datetime.utcnow().replace(tzinfo=utc)
						relevant_request.save()
						new_response.manager = True
						break
				new_response.save()
		elif 'upvote' in request.POST:
			vote_form = VoteForm(request.POST)
			if vote_form.is_valid():
				request_pk = vote_form.cleaned_data['request_pk']
				relevant_request = Request.objects.get(pk=request_pk)
				if userProfile in relevant_request.upvotes.all():
					relevant_request.upvotes.remove(userProfile)
				else:
					relevant_request.upvotes.add(userProfile)
				relevant_request.save()
		else:
			return red_home(request, MESSAGES['UNKNOWN_FORM'])
	my_requests = Request.objects.filter(owner=userProfile)
	request_dict = list() # A pseudo dictionary, actually a list with items of form (request_type.name.title(), request_form, type_manager, [(request, [list_of_request_responses], response_form, upvote, vote_form),...])
	for request_type in RequestType.objects.all():
		relevant_managers = request_type.managers.all()
		type_manager = any(i.incumbent == userProfile for i in relevant_managers)
		requests_list = list() # Items are of form (request, [list_of_request_responses], response_form),...])
		type_requests = my_requests.filter(request_type=request_type)
		for req in type_requests:
			responses_list = Response.objects.filter(request=req)
			if type_manager:
				form = ManagerResponseForm(initial={
						'request_pk': req.pk,
						'mark_filled': req.filled,
						'mark_closed': req.closed,
						})
			else:
				form = ResponseForm(initial={'request_pk': req.pk})
			upvote = userProfile in req.upvotes.all()
			vote_form = VoteForm(initial={'request_pk': req.pk})
			requests_list.append((req, responses_list, form, upvote, vote_form))
		request_form = RequestForm(initial={'type_pk': request_type.pk})
		request_form.fields['type_pk'].widget = forms.HiddenInput()
		request_dict.append((request_type, request_form, type_manager, requests_list))
	return render_to_response('my_requests.html', {
			'page_name': page_name,
			'request_dict': request_dict,
			}, context_instance=RequestContext(request))

@profile_required
def list_my_requests_view(request):
	'''
	Show user his/her requests in list form.
	'''
	userProfile = UserProfile.objects.get(user=request.user)
	requests = Request.objects.filter(owner=userProfile)
	return render_to_response('list_requests.html', {
			'page_name': "My Requests",
			'requests': requests,
			}, context_instance=RequestContext(request))

@profile_required
def list_user_requests_view(request, targetUsername):
	'''
	Show user his/her requests in list form.
	'''
	if targetUsername == request.user.username:
		return list_my_requests_view(request)

	targetUser = get_object_or_404(User, username=targetUsername)
	targetProfile = get_object_or_404(UserProfile, user=targetUser)
	page_name = "%s's Requests" % targetUsername
	requests = Request.objects.filter(owner=targetProfile)
	return render_to_response('list_requests.html', {
			'page_name': page_name,
			'requests': requests,
			'targetUsername': targetUsername,
			}, context_instance=RequestContext(request))

@profile_required
def all_requests_view(request):
	'''
	Show user a list of enabled request types, the number of requests of each type and a link to see them all.
	'''
	types_dict = list() # Pseudo-dictionary, actually a list with items of form (request_type.name.title(), number_of_type_requests, name, enabled, glyphicon)
	for request_type in RequestType.objects.all():
		number_of_requests = Request.objects.filter(request_type=request_type).count()
		types_dict.append((request_type.name.title(), number_of_requests, request_type.url_name, request_type.enabled, request_type.glyphicon))
	return render_to_response('all_requests.html', {
			'page_name': "Archives - All Requests",
			'types_dict': types_dict,
			}, context_instance=RequestContext(request))

@profile_required
def list_all_requests_view(request, requestType):
	'''
	Show user his/her requests in list form.
	'''
	request_type = get_object_or_404(RequestType, url_name=requestType)
	requests = Request.objects.filter(request_type=request_type)
	page_name = "Archives - All %s Requests" % request_type.name.title()
	return render_to_response('list_requests.html', {
			'page_name': page_name,
			'requests': requests,
			'request_type': request_type,
			}, context_instance=RequestContext(request))

@profile_required
def request_view(request, request_pk):
	'''
	The view of a single request.
	'''
	relevant_request = get_object_or_404(Request, pk=request_pk)
	userProfile = UserProfile.objects.get(user=request.user)
	request_responses = Response.objects.filter(request=relevant_request)
	relevant_managers = relevant_request.request_type.managers.all()
	manager = any(i.incumbent == userProfile for i in relevant_managers)
	if manager:
		response_form = ManagerResponseForm(initial={
				'request_pk': relevant_request.pk,
				'mark_filled': relevant_request.filled,
				'mark_closed': relevant_request.closed,
				})
	else:
		response_form = ResponseForm(initial={
				'request_pk': relevant_request.pk,
				})
	upvote = userProfile in relevant_request.upvotes.all()
	vote_form = VoteForm()
	if request.method == 'POST':
		if 'add_response' in request.POST:
			if manager:
				response_form = ManagerResponseForm(request.POST)
			else:
				response_form = ResponseForm(request.POST)
			if response_form.is_valid():
				request_pk = response_form.cleaned_data['request_pk']
				body = response_form.cleaned_data['body']
				new_response = Response(owner=userProfile, body=body, request=relevant_request)
				if manager:
					relevant_request.filled = response_form.cleaned_data['mark_filled']
					relevant_request.closed = response_form.cleaned_data['mark_closed']
					relevant_request.number_of_responses += 1
					relevant_request.change_date = datetime.utcnow().replace(tzinfo=utc)
					relevant_request.save()
					new_response.manager = True
				new_response.save()
				return HttpResponseRedirect(reverse('view_request', kwargs={'request_pk': relevant_request.pk}))
		elif 'upvote' in request.POST:
			if userProfile in relevant_request.upvotes.all():
				relevant_request.upvotes.remove(userProfile)
			else:
				relevant_request.upvotes.add(userProfile)
			relevant_request.save()
			return HttpResponseRedirect(reverse('view_request', kwargs={'request_pk': relevant_request.pk}))
		else:
			return red_home(request, MESSAGES['UNKNOWN_FORM'])
	if manager:
		response_form = ManagerResponseForm(initial={
				'request_pk': relevant_request.pk,
				'mark_filled': relevant_request.filled,
				'mark_closed': relevant_request.closed,
				})
	else:
		response_form = ResponseForm(initial={
				'request_pk': relevant_request.pk,
				})
	upvote = userProfile in relevant_request.upvotes.all()
	vote_form = VoteForm()
	return render_to_response('view_request.html', {
			'page_name': "View Request",
			'relevant_request': relevant_request,
			'request_responses': request_responses,
			'upvote': upvote,
			'response_form': response_form,
			'vote_form': vote_form,
			'response_form': response_form,
			}, context_instance=RequestContext(request))

@profile_required
def announcements_view(request):
	''' The view of manager announcements. '''
	page_name = "Manager Announcements"
	userProfile = None
	userProfile = UserProfile.objects.get(user=request.user)
	announcement_form = None
	manager_positions = Manager.objects.filter(incumbent=userProfile)
	if manager_positions:
		announcement_form = AnnouncementForm(manager_positions)
	if request.method == 'POST':
		if 'unpin' in request.POST:
			unpin_form = UnpinForm(request.POST)
			if unpin_form.is_valid():
				announcement_pk = unpin_form.cleaned_data['announcement_pk']
				relevant_announcement = Announcement.objects.get(pk=announcement_pk)
				relevant_announcement.pinned = False
				relevant_announcement.save()
				return HttpResponseRedirect(reverse('announcements'))
		elif 'post_announcement' in request.POST:
			announcement_form = AnnouncementForm(manager_positions, post=request.POST)
			if announcement_form.is_valid():
				body = announcement_form.cleaned_data['body']
				manager = announcement_form.cleaned_data['as_manager']
				new_announcement = Announcement(manager=manager, body=body, incumbent=userProfile, pinned=True)
				new_announcement.save()
				return HttpResponseRedirect(reverse('announcements'))
	announcements = Announcement.objects.filter(pinned=True)
	announcements_dict = list() # A pseudo-dictionary, actually a list with items of form (announcement, announcement_unpin_form)
	for a in announcements:
		unpin_form = None
		if (a.manager.incumbent == userProfile) or request.user.is_superuser:
			unpin_form = UnpinForm(initial={'announcement_pk': a.pk})
		announcements_dict.append((a, unpin_form))
	return render_to_response('announcements.html', {
			'page_name': page_name,
			'manager_positions': manager_positions,
			'announcements_dict': announcements_dict,
			'announcement_form': announcement_form,
			}, context_instance=RequestContext(request))

@profile_required
def all_announcements_view(request):
	''' The view of manager announcements. '''
	page_name = "Archives - All Announcements"
	userProfile = UserProfile.objects.get(user=request.user)
	announcement_form = None
	manager_positions = Manager.objects.filter(incumbent=userProfile)
	if manager_positions:
		announcement_form = AnnouncementForm(manager_positions)
	if request.method == 'POST':
		if 'unpin' in request.POST:
			unpin_form = UnpinForm(request.POST)
			if unpin_form.is_valid():
				announcement_pk = unpin_form.cleaned_data['announcement_pk']
				relevant_announcement = Announcement.objects.get(pk=announcement_pk)
				if relevant_announcement.pinned:
					relevant_announcement.pinned = False
				else:
					relevant_announcement.pinned = True
				relevant_announcement.save()
				return HttpResponseRedirect(reverse('all_announcements'))
		elif ('post_announcement' in request.POST) and manager_positions:
			announcement_form = AnnouncementForm(manager_positions, post=request.POST)
			if announcement_form.is_valid():
				body = announcement_form.cleaned_data['body']
				manager = announcement_form.cleaned_data['as_manager']
				new_announcement = Announcement(manager=manager, body=body, incumbent=userProfile, pinned=True)
				new_announcement.save()
				return HttpResponseRedirect(reverse('all_announcements'))
	announcements = Announcement.objects.all()
	announcements_dict = list() # A pseudo-dictionary, actually a list with items of form (announcement, announcement_pin_form)
	for a in announcements:
		form = None
		if ((a.manager.incumbent == userProfile) or request.user.is_superuser) and not a.pinned:
			form = UnpinForm(initial={'announcement_pk': a.pk})
		elif ((a.manager.incumbent == userProfile) or request.user.is_superuser) and a.pinned:
			form = UnpinForm(initial={'announcement_pk': a.pk})
		announcements_dict.append((a, form))
	return render_to_response('announcements.html', {
			'page_name': page_name,
			'manager_positions': manager_positions,
			'announcements_dict': announcements_dict,
			'announcement_form': announcement_form,
			}, context_instance=RequestContext(request))

@admin_required
def recount_view(request):
	''' Recount number_of_messages for all threads and number_of_responses for all requests. '''
	requests_changed = 0
	for req in Request.objects.all():
		recount = Response.objects.filter(request=req).count()
		if req.number_of_responses != recount:
			req.number_of_responses = recount
			req.save()
			requests_changed += 1
	threads_changed = 0
	for thread in Thread.objects.all():
		recount = Message.objects.filter(thread=thread).count()
		if thread.number_of_messages != recount:
			thread.number_of_messages = recount
			thread.save()
			threads_changed += 1
	messages.add_message(request, messages.SUCCESS, MESSAGES['RECOUNTED'].format(requests_changed=requests_changed, request_count=Request.objects.all().count(),
			threads_changed=threads_changed, thread_count=Thread.objects.all().count()))
	return HttpResponseRedirect(reverse('utilities'))

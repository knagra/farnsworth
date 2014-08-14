'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''

from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout, login
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.timezone import now

from utils.variables import ANONYMOUS_USERNAME, MESSAGES
from base.decorators import admin_required, profile_required, president_admin_required
from base.models import UserProfile
from base.redirects import red_home
from managers.models import Manager, RequestType, Request, Response, Announcement
from managers.forms import ManagerForm, RequestTypeForm, RequestForm, ResponseForm, \
     ManagerResponseForm, VoteForm, AnnouncementForm, PinForm
from threads.models import Thread, Message

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
        return HttpResponseRedirect(reverse('managers:list_managers'))
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
    managers = Manager.objects.all()
    return render_to_response('meta_manager.html', {
        'page_name': "Admin - Meta-Manager",
        'managerset': managers,
        }, context_instance=RequestContext(request))

@president_admin_required
def add_manager_view(request):
    ''' View to add a new manager position. Restricted to superadmins and presidents. '''
    form = ManagerForm(request.POST or None)
    if form.is_valid():
        manager = form.save()
        messages.add_message(request, messages.SUCCESS,
                             MESSAGES['MANAGER_ADDED'].format(managerTitle=manager.title))
        return HttpResponseRedirect(reverse('managers:add_manager'))
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
    targetManager = get_object_or_404(Manager, url_title=managerTitle)
    form = ManagerForm(
        request.POST or None,
        instance=targetManager,
        )
    if form.is_valid():
        manager = form.save()
        messages.add_message(request, messages.SUCCESS,
                             MESSAGES['MANAGER_SAVED'].format(managerTitle=manager.title))
        return HttpResponseRedirect(reverse('managers:meta_manager'))
    return render_to_response('edit_manager.html', {
        'page_name': "Admin - Edit Manager",
        'form': form,
        "managerset": Manager.objects.all(),
        'manager_title': targetManager.title,
        }, context_instance=RequestContext(request))

@president_admin_required
def manage_request_types_view(request):
    ''' Manage requests.  Display a list of request types with links to edit them.
    Also display a link to add a new request type.  Restricted to presidents and superadmins.
    '''
    request_types = RequestType.objects.all()
    return render_to_response('manage_request_types.html', {
        'page_name': "Admin - Manage Request Types",
        'request_types': request_types
        }, context_instance=RequestContext(request))

@president_admin_required
def add_request_type_view(request):
    ''' View to add a new request type.  Restricted to presidents and superadmins. '''
    form = RequestTypeForm(request.POST or None)
    if form.is_valid():
        rtype = form.save()
        messages.add_message(request, messages.SUCCESS,
                             MESSAGES['REQUEST_TYPE_ADDED'].format(typeName=rtype.name))
        return HttpResponseRedirect(reverse('managers:manage_request_types'))
    return render_to_response('edit_request_type.html', {
        'page_name': "Admin - Add Request Type",
        'request_types': RequestType.objects.all(),
        'form': form,
        }, context_instance=RequestContext(request))

@president_admin_required
def edit_request_type_view(request, typeName):
    ''' View to edit a new request type.  Restricted to presidents and superadmins.
    Parameters:
        request is an HTTP request
        typeName is the request type's URL name.
    '''
    requestType = get_object_or_404(RequestType, url_name=typeName)
    form = RequestTypeForm(
        request.POST or None,
        instance=requestType,
        )
    if form.is_valid():
        rtype = form.save()
        messages.add_message(request, messages.SUCCESS,
                             MESSAGES['REQUEST_TYPE_SAVED'].format(typeName=rtype.name))
        return HttpResponseRedirect(reverse('managers:manage_request_types'))
    return render_to_response('edit_request_type.html', {
        'page_name': "Admin - Edit Request Type",
        'request_types': RequestType.objects.all(),
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
    page_name = "{0} Requests".format(request_type.name.title())
    if not request_type.enabled:
        message = "{0} requests have been disabled.".format(request_type.name.title())
        return red_home(request, message)
    relevant_managers = request_type.managers.filter(active=True)
    manager = any(i.incumbent == userProfile for i in relevant_managers)
    request_form = RequestForm(
        request.POST if "submit_request" in request.POST else None,
        profile=userProfile,
        request_type=request_type,
        )
    if request_form.is_valid():
        request_form.save()
        return HttpResponseRedirect(reverse('managers:requests', kwargs={'requestType': requestType}))
    # number of requests loaded
    x = 0
    # A pseudo-dictionary, actually a list with items of form (request,
    # [request_responses_list], response_form, upvote, vote_form)
    requests_dict = list()
    requests = Request.objects.filter(request_type=request_type)
    if not request_type.managers.filter(incumbent__user=request.user):
        requests = requests.exclude(
            ~Q(owner__user=request.user), private=True,
            )
    for req in requests:
        request_responses = Response.objects.filter(request=req)
        if manager:
            response_form = ManagerResponseForm(
                request.POST if "add_response-{0}".format(req.pk) in request.POST else None,
                initial={'action': Response.NONE},
                prefix="{0}".format(req.pk),
                profile=userProfile,
                request=req,
                )
        else:
            response_form = ResponseForm(
                request.POST if "add_response-{0}".format(req.pk) in request.POST else None,
                prefix="{0}".format(req.pk),
                profile=userProfile,
                request=req,
                )
        upvote = userProfile in req.upvotes.all()
        vote_form = VoteForm(
            request.POST if "vote-{0}".format(req.pk) in request.POST else None,
            profile=userProfile,
            request=req,
            )
        if response_form.is_valid():
            response_form.save()
            return HttpResponseRedirect(reverse('managers:requests',
                                                kwargs={'requestType': requestType}))
        if vote_form.is_valid():
            vote_form.save()
            return HttpResponseRedirect(reverse('managers:requests',
                                                kwargs={'requestType': requestType}))
        requests_dict.append((req, request_responses, response_form, upvote, vote_form))
        x += 1
        if x >= settings.MAX_REQUESTS:
            break
    return render_to_response('requests.html', {
        'manager': manager,
        'request_type': request_type.name.title(),
        'page_name': page_name,
        'request_form': request_form,
        'requests_dict': requests_dict,
        'relevant_managers': relevant_managers,
        }, context_instance=RequestContext(request))

@profile_required
def my_requests_view(request):
    '''
    Show user his/her requests, sorted by request_type.
    '''
    page_name = "My Requests"
    userProfile = UserProfile.objects.get(user=request.user)
    my_requests = Request.objects.filter(owner=userProfile)
    # A pseudo dictionary, actually a list with items of form
    # (request_type.name.title(), request_form, type_manager, [(request,
    # [list_of_request_responses], response_form, upvote, vote_form),...],
    # relevant_managers)
    request_dict = list()
    for request_type in RequestType.objects.all():
        relevant_managers = request_type.managers.filter(active=True)
        type_manager = any(i.incumbent == userProfile for i in
                           relevant_managers)
        # Items are of form (request, [list_of_request_responses],
        # response_form),...])
        requests_list = list()
        type_requests = my_requests.filter(request_type=request_type)
        for req in type_requests:
            responses_list = Response.objects.filter(request=req)
            if type_manager:
                response_form = ManagerResponseForm(
                    request.POST if "add_response-{0}".format(req.pk) in request.POST else None,
                    initial={'action': Response.NONE},
                    profile=userProfile,
                    request=req,
                    )
            else:
                response_form = ResponseForm(
                    request.POST if "add_response-{0}".format(req.pk) in request.POST else None,
                    profile=userProfile,
                    request=req,
                    )

            upvote = userProfile in req.upvotes.all()
            vote_form = VoteForm(
                request.POST if "vote-{0}".format(req.pk) in request.POST else None,
                request.POST or None,
                profile=userProfile,
                request=req,
                )

            if response_form.is_valid():
                response_form.save()
                return HttpResponseRedirect(reverse('managers:my_requests'))
            if vote_form.is_valid():
                vote_form.save()
                return HttpResponseRedirect(reverse('managers:my_requests'))

            requests_list.append((req, responses_list, response_form, upvote, vote_form))
        request_form = RequestForm(
            request.POST if "submit_request" in request.POST else None,
            profile=userProfile,
            request_type=request_type,
            )
        if request_form.is_valid():
            request_form.save()
            return HttpResponseRedirect(reverse('managers:my_requests'))
        request_dict.append((request_type, request_form, type_manager,
                             requests_list, relevant_managers))
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
    page_name = "{0}'s Requests".format(targetUsername)
    requests = Request.objects.filter(owner=targetProfile).exclude(
        ~Q(owner__user=request.user), private=True,
        )
    return render_to_response('list_requests.html', {
        'page_name': page_name,
        'requests': requests,
        'targetUsername': targetUsername,
        }, context_instance=RequestContext(request))

@profile_required
def all_requests_view(request):
    '''
    Show user a list of enabled request types, the number of requests of each
    type and a link to see them all.
    '''
    # Pseudo-dictionary, actually a list with items of form
    # (request_type.name.title(), number_of_type_requests, name, enabled,
    # glyphicon)
    types_dict = list()
    for request_type in RequestType.objects.all():
        requests = Request.objects.filter(request_type=request_type)
        # Hide the count for private requests
        if not request_type.managers.filter(incumbent__user=request.user):
            requests = requests.exclude(
                ~Q(owner__user=request.user), private=True,
                )

        number_of_requests = requests.count()
        types_dict.append((
            request_type.name.title(), number_of_requests,
            request_type.url_name, request_type.enabled,
            request_type.glyphicon,
            ))
    return render_to_response('all_requests.html', {
        'page_name': "Archives - All Requests",
        'types_dict': types_dict,
        }, context_instance=RequestContext(request))

@profile_required
def list_all_requests_view(request, requestType):
    '''
    Show all the requests for a given type in list form.
    '''
    request_type = get_object_or_404(RequestType, url_name=requestType)
    requests = Request.objects.filter(request_type=request_type)
    # Hide the count for private requests
    if not request_type.managers.filter(incumbent__user=request.user):
        requests = requests.exclude(
            ~Q(owner__user=request.user), private=True,
            )

    page_name = "Archives - All {0} Requests".format(request_type.name.title())
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

    if relevant_request.private:
        if relevant_request.owner.user != request.user or \
          relevant_request.request_type.managers.filter(incumbent__user=request.user):
          return HttpResponseRedirect(
              reverse("managers:requests",
                      kwargs={"requestType": relevant_request.request_type.url_name}))

    userProfile = UserProfile.objects.get(user=request.user)
    request_responses = Response.objects.filter(request=relevant_request)
    relevant_managers = relevant_request.request_type.managers.filter(active=True)
    manager = any(i.incumbent == userProfile for i in relevant_managers)
    if manager:
        response_form = ManagerResponseForm(
            request.POST if "add_response" in request.POST else None,
            initial={'action': Response.NONE},
            profile=userProfile,
            request=relevant_request,
            )
    else:
        response_form = ResponseForm(
            request.POST if "add_response" in request.POST else None,
            profile=userProfile,
            request=relevant_request,
            prefix="response",
            )
    upvote = userProfile in relevant_request.upvotes.all()
    vote_form = VoteForm(
        request.POST if "vote" in request.POST else None,
        profile=UserProfile,
        request=relevant_request,
        )
    if response_form.is_valid():
        response_form.save()
        return HttpResponseRedirect(reverse('managers:view_request', kwargs={
            'request_pk': relevant_request.pk,
            }))
    if vote_form.is_valid():
        vote_form.save(pk=request_pk)
        return HttpResponseRedirect(reverse('managers:view_request', kwargs={
            'request_pk': relevant_request.pk,
            }))
    upvote = userProfile in relevant_request.upvotes.all()
    return render_to_response('view_request.html', {
        'page_name': "View Request",
        'relevant_request': relevant_request,
        'request_responses': request_responses,
        'upvote': upvote,
        'vote_form': vote_form,
        'response_form': response_form,
        'relevant_managers': relevant_managers,
        }, context_instance=RequestContext(request))

@profile_required
def announcement_view(request, announcement_pk):
    ''' The view of a single manager announcement. '''
    announce = get_object_or_404(Announcement, pk=announcement_pk)
    page_name = "View Announcement"
    profile = UserProfile.objects.get(user=request.user)
    pin_form = PinForm(
        request.POST if "pin" in request.POST else None,
        instance=announce,
        )
    can_edit = announce.incumbent == profile or request.user.is_superuser
    if pin_form.is_valid():
        pin_form.save()
        return HttpResponseRedirect(
            reverse('managers:view_announcement', kwargs={"announcement_pk": announcement_pk}),
            )
    return render_to_response('view_announcement.html', {
        'page_name': page_name,
        'pin_form': pin_form,
        'can_edit': can_edit,
        'announcement': announce,
        }, context_instance=RequestContext(request))

@profile_required
def edit_announcement_view(request, announcement_pk):
    ''' The view of a single manager announcement. '''
    announce = get_object_or_404(Announcement, pk=announcement_pk)
    profile = UserProfile.objects.get(user=request.user)
    if not (announce.incumbent == profile or request.user.is_superuser):
        return HttpResponseRedirect(
            reverse('managers:view_announcement', kwargs={"announcement_pk": announcement_pk}),
            )
    page_name = "Edit Announcement"

    announcement_form = AnnouncementForm(
        request.POST or None,
        instance=announce,
        profile=profile,
        )
    if announcement_form.is_valid():
        announcement_form.save()
        return HttpResponseRedirect(
            reverse('managers:view_announcement', kwargs={"announcement_pk": announcement_pk}),
            )

    return render_to_response('edit_announcement.html', {
        'page_name': page_name,
        'announcement_form': announcement_form,
        }, context_instance=RequestContext(request))

@profile_required
def announcements_view(request):
    ''' The view of manager announcements. '''
    page_name = "Manager Announcements"
    userProfile = UserProfile.objects.get(user=request.user)
    announcement_form = None
    manager_positions = Manager.objects.filter(incumbent=userProfile)
    if manager_positions:
        announcement_form = AnnouncementForm(
            request.POST if "post_announcement"in request.POST else None,
            profile=userProfile,
            )
    if announcement_form and announcement_form.is_valid():
        announcement_form.save()
        return HttpResponseRedirect(reverse('managers:announcements'))

    # A pseudo-dictionary, actually a list with items of form:
    # (announcement, announcement_pin_form)
    announcements_dict = list()
    for a in Announcement.objects.filter(pinned=True):
        pin_form = None
        if (a.manager.incumbent == userProfile) or request.user.is_superuser:
            pin_form = PinForm(
                request.POST if "pin-{0}".format(a.pk) else None,
                instance=a,
                )
            if pin_form.is_valid():
                pin_form.save()
                return HttpResponseRedirect(reverse('managers:announcements'))
        announcements_dict.append((a, pin_form))
    # Oldest genesis of an pinned announcement to be displayed.
    within_life = now() - timedelta(hours=settings.ANNOUNCEMENT_LIFE)
    for a in Announcement.objects.filter(pinned=False, post_date__gte=within_life):
        pin_form = None
        if request.user.is_superuser or (a.manager.incumbent == userProfile):
            pin_form = PinForm(
                request.POST if "pin-{0}".format(a.pk) else None,
                instance=a,
                )
        announcements_dict.append((a, pin_form))
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
        announcement_form = AnnouncementForm(
            request.POST if "post_announcement" in request.POST else None,
            profile=userProfile,
            )
        if announcement_form.is_valid():
            announcement_form.save()
            return HttpResponseRedirect(reverse('managers:all_announcements'))

    # A pseudo-dictionary, actually a list with items of form (announcement,
    # announcement_pin_form)
    announcements_dict = list()
    for a in Announcement.objects.all():
        pin_form = None
        if a.manager.incumbent == userProfile or request.user.is_superuser:
            pin_form = PinForm(
                request.POST if "pin-{0}".format(a.pk) in request.POST else None,
                instance=a,
                )
            if pin_form.is_valid():
                pin_form.save()
                return HttpResponseRedirect(reverse('managers:all_announcements'))
        announcements_dict.append((a, pin_form))
    return render_to_response('announcements.html', {
        'page_name': page_name,
        'manager_positions': manager_positions,
        'announcements_dict': announcements_dict,
        'announcement_form': announcement_form,
        }, context_instance=RequestContext(request))

@admin_required
def recount_view(request):
    '''
    Recount number_of_messages for all threads and number_of_responses for all
    requests.
    '''
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
    messages.add_message(
        request, messages.SUCCESS,
        MESSAGES['RECOUNTED'].format(
            requests_changed=requests_changed,
            request_count=Request.objects.all().count(),
            threads_changed=threads_changed,
            thread_count=Thread.objects.all().count(),
            ),
        )
    return HttpResponseRedirect(reverse('utilities'))

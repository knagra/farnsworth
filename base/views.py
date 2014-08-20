"""
Project: Farnsworth

Authors: Karandeep Singh Nagra and Nader Morshed


Views for base application.
"""

from datetime import timedelta
import time
from smtplib import SMTPException

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.forms import PasswordChangeForm, \
    AdminPasswordChangeForm
from django.contrib.auth.models import User
from django.contrib.auth.views import password_reset, password_reset_confirm
from django.core.urlresolvers import reverse
from django.core.mail import send_mail
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, render, get_object_or_404
from django.template import RequestContext
from django.utils.timezone import now

from wiki.models import Revision

from utils.funcs import form_add_error
from utils.variables import ANONYMOUS_USERNAME, MESSAGES, APPROVAL_SUBJECT, \
    APPROVAL_EMAIL, DELETION_SUBJECT, DELETION_EMAIL, SUBMISSION_SUBJECT, \
    SUBMISSION_EMAIL
from base.models import UserProfile, ProfileRequest
from base.redirects import red_ext, red_home
from base.decorators import profile_required, admin_required
from base.forms import ProfileRequestForm, AddUserForm, \
    UpdateUserForm, FullProfileForm, \
    ModifyProfileRequestForm, LoginForm, \
    UpdateEmailForm, UpdateProfileForm, DeleteUserForm
from threads.models import Thread, Message
from threads.forms import ThreadForm
from managers.models import RequestType, Manager, Request, Response, Announcement
from managers.forms import AnnouncementForm, ManagerResponseForm, VoteForm, PinForm
from events.models import Event
from events.forms import RsvpForm
from rooms.models import Room, PreviousResident
from workshift.models import Semester, WorkshiftProfile, ShiftLogEntry, \
    WorkshiftInstance

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
    # A list with items of form (RequestType, number_of_open_requests)
    request_types = list()
    if request.user.is_authenticated():
        for request_type in RequestType.objects.filter(enabled=True):
            requests = Request.objects.filter(request_type=request_type, status=Request.OPEN)
            if not request_type.managers.filter(incumbent__user=request.user):
                requests = requests.exclude(
                    ~Q(owner__user=request.user), private=True,
                    )
            request_types.append((request_type, requests.count()))
    return {
        'REQUEST_TYPES': request_types,
        'HOUSE': settings.HOUSE_NAME,
        'ANONYMOUS_USERNAME': ANONYMOUS_USERNAME,
        'SHORT_HOUSE': settings.SHORT_HOUSE_NAME,
        'ADMIN': settings.ADMINS[0],
        'NUM_OF_PROFILE_REQUESTS': ProfileRequest.objects.all().count(),
        'ANONYMOUS_SESSION': ANONYMOUS_SESSION,
        'PRESIDENT': PRESIDENT,
        "WIKI_ENABLED": "farnswiki" in settings.INSTALLED_APPS,
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
    # List of request types for which the user is a relevant manager
    manager_request_types = list()
    for request_type in request_types:
        for position in request_type.managers.filter(active=True):
            if userProfile == position.incumbent:
                manager_request_types.append(request_type)
                break
    # Pseudo-dictionary, list with items of form (request_type, (request,
    # [list_of_request_responses], response_form))
    requests_dict = list()
    # Generate a dict of open requests for each request_type for which the user
    # is a relevant manager:
    if manager_request_types:
        for request_type in manager_request_types:
            # Items of form (request, [list_of_request_responses],
            # response_form, upvote, vote_form)
            requests_list = list()
            # Select only open requests of type request_type:
            requests = Request.objects.filter(
                request_type=request_type, status=Request.OPEN,
                )
            for req in requests:
                response_form = ManagerResponseForm(
                    request.POST if "add_response-{0}".format(req.pk) in request.POST else None,
                    initial={'action': Response.NONE},
                    profile=userProfile,
                    request=req,
                    prefix="{}-response".format(req.pk),
                    )
                vote_form = VoteForm(
                    request.POST if "vote-{0}".format(req.pk) in request.POST else None,
                    profile=userProfile,
                    request=req,
                    prefix="vote",
                    )

                if response_form.is_valid():
                    response = response_form.save()
                    if response.request.closed:
                        messages.add_message(request, messages.SUCCESS,
                                             MESSAGES['REQ_CLOSED'])
                    if response.request.filled:
                        messages.add_message(request, messages.SUCCESS,
                                             MESSAGES['REQ_FILLED'])
                    return HttpResponseRedirect(reverse('homepage'))
                if vote_form.is_valid():
                    vote_form.save()
                    return HttpResponseRedirect(reverse('homepage'))

                response_list = Response.objects.filter(request=req)
                upvote = userProfile in req.upvotes.all()
                requests_list.append(
                    (req, response_list, response_form, upvote, vote_form)
                    )
            requests_dict.append((request_type, requests_list))

    ### Announcements
    # Pseudo-dictionary, list with items of form (announcement,
    # announcement_unpin_form)
    announcements_dict = list()

    # Oldest genesis of an unpinned announcement to be displayed.
    within_life = now() - timedelta(hours=settings.ANNOUNCEMENT_LIFE)
    announcements = \
      list(Announcement.objects.filter(pinned=True)) + \
      list(Announcement.objects.filter(pinned=False, post_date__gte=within_life))
    for a in announcements:
        pin_form = None
        if request.user.is_superuser or a.manager.incumbent == userProfile:
            pin_form = PinForm(
                request.POST if "pin-{0}".format(a.pk) in request.POST else None,
                instance=a,
                prefix="pin",
                )
            if pin_form.is_valid():
                pin_form.save()
                return HttpResponseRedirect(reverse('homepage'))
        announcements_dict.append((a, pin_form))

    announcement_form = AnnouncementForm(
        request.POST if "post_announcement" in request.POST else None,
        profile=userProfile,
        prefix="announce",
        )

    if announcement_form.is_valid():
        announcement_form.save()
        return HttpResponseRedirect(reverse('homepage'))

    ### Events
    week_from_now = now() + timedelta(days=7)
    # Get only next 7 days of events:
    events_list = Event.objects.exclude(
        start_time__gte=week_from_now
    ).exclude(
        end_time__lte=now(),
    )
    # Pseudo-dictionary, list with items of form (event, ongoing, rsvpd, rsvp_form)
    events_dict = list()
    for event in events_list:
        ongoing = ((event.start_time <= now()) and (event.end_time >= now()))
        rsvpd = (userProfile in event.rsvps.all())

        rsvp_form = RsvpForm(
            request.POST if "rsvp-{0}".format(event.pk) in request.POST else None,
            profile=userProfile,
            instance=event,
            prefix="rsvp",
            )

        if rsvp_form.is_valid():
            rsvpd = rsvp_form.save()
            if rsvpd:
                message = MESSAGES['RSVP_REMOVE'].format(event=event.title)
                messages.add_message(request, messages.SUCCESS, message)
            else:
                message = MESSAGES['RSVP_ADD'].format(event=event.title)
                messages.add_message(request, messages.SUCCESS, message)
            return HttpResponseRedirect(reverse('homepage'))

        events_dict.append((event, ongoing, rsvpd, rsvp_form))

    ### Threads
    thread_form = ThreadForm(
        request.POST if "submit_thread_form" in request.POST else None,
        profile=userProfile,
        prefix="thread",
        )
    if thread_form.is_valid():
        thread_form.save()
        return HttpResponseRedirect(reverse('homepage'))

    # List of with items of form (thread, most_recent_message_in_thread)
    thread_set = []
    for thread in Thread.objects.all()[:settings.HOME_MAX_THREADS]:
        try:
            latest_message = Message.objects.filter(thread=thread).latest('post_date')
        except Message.DoesNotExist:
            latest_message = None
        thread_set.append((thread, latest_message))

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
        }, context_instance=RequestContext(request))

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
    userProfile = UserProfile.objects.get(user=request.user)
    change_password_form = PasswordChangeForm(
        request.user,
        request.POST if "submit_password_form" in request.POST else None,
        )
    update_email_form = UpdateEmailForm(
        request.POST if "submit_profile_form" in request.POST else None,
        instance=request.user,
        prefix="user",
        )
    update_profile_form = UpdateProfileForm(
        request.POST if "submit_profile_form" in request.POST else None,
        instance=userProfile,
        prefix="profile",
        )
    if change_password_form.is_valid():
        change_password_form.save()
        messages.add_message(request, messages.SUCCESS,
                             "Your password was successfully changed.")
        return HttpResponseRedirect(reverse('my_profile'))
    if update_email_form.is_valid() and update_profile_form.is_valid():
        update_email_form.save()
        update_profile_form.save()
        messages.add_message(request, messages.SUCCESS,
                             "Your profile has been successfully updated.")
        return HttpResponseRedirect(reverse('my_profile'))
    return render_to_response('my_profile.html', {
        'page_name': page_name,
        "update_email_form": update_email_form,
        'update_profile_form': update_profile_form,
        'change_password_form': change_password_form,
        }, context_instance=RequestContext(request))

@profile_required
def notifications_view(request):
    """
    Show a user their notifications.
    """
    page_name = "Your Notifications"
    # Copy the notifications so that they are still unread when we render the page
    notifications = list(request.user.notifications.all())
    request.user.notifications.mark_all_as_read()
    return render_to_response("list_notifications.html", {
        "page_name": page_name,
        "notifications": notifications,
        }, context_instance=RequestContext(request))

def login_view(request):
    ''' The view of the login page. '''
    ANONYMOUS_SESSION = request.session.get('ANONYMOUS_SESSION', False)
    page_name = "Login Page"
    redirect_to = request.GET.get('next', reverse('homepage'))
    if (request.user.is_authenticated() and not ANONYMOUS_SESSION) or (ANONYMOUS_SESSION and request.user.username != ANONYMOUS_USERNAME):
        return HttpResponseRedirect(redirect_to)
    form = LoginForm(request.POST or None)
    if form.is_valid():
        user = form.save()
        login(request, user)
        if ANONYMOUS_SESSION:
            request.session['ANONYMOUS_SESSION'] = True
        return HttpResponseRedirect(redirect_to)
    elif request.method == "POST":
        reset_url = request.build_absolute_uri(reverse('reset_pw'))
        messages.add_message(request, messages.INFO,
                             MESSAGES['RESET_MESSAGE'].format(reset_url=reset_url))

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
    page_name = "{0}'s Profile".format(targetUsername)
    targetUser = get_object_or_404(User, username=targetUsername)
    targetProfile = get_object_or_404(UserProfile, user=targetUser)
    number_of_threads = Thread.objects.filter(owner=targetProfile).count()
    number_of_messages = Message.objects.filter(owner=targetProfile).count()
    number_of_requests = Request.objects.filter(owner=targetProfile).count()
    rooms = Room.objects.filter(current_residents=targetProfile)
    prev_rooms = PreviousResident.objects.filter(resident=targetProfile)
    return render_to_response('member_profile.html', {
        'page_name': page_name,
        'targetUser': targetUser,
        'targetProfile': targetProfile,
        'number_of_threads': number_of_threads,
        'number_of_messages': number_of_messages,
        'number_of_requests': number_of_requests,
        "rooms": rooms,
        "prev_rooms": prev_rooms,
        }, context_instance=RequestContext(request))

def request_profile_view(request):
    ''' The page to request a user profile on the site. '''
    page_name = "Profile Request Page"
    redirect_to = request.GET.get('next', reverse('homepage'))
    if request.user.is_authenticated() and request.user.username != ANONYMOUS_USERNAME:
        return HttpResponseRedirect(redirect_to)
    form = ProfileRequestForm(
        request.POST or None,
        )
    if form.is_valid():
        username = form.cleaned_data['username']
        first_name = form.cleaned_data['first_name']
        last_name = form.cleaned_data['last_name']
        email = form.cleaned_data['email']
        if User.objects.filter(username=username).count():
            reset_url = request.build_absolute_uri(reverse('reset_pw'))
            form_add_error(form, 'username',
                           MESSAGES["USERNAME_TAKEN"].format(username=username))
            messages.add_message(request, messages.INFO,
                                 MESSAGES['RESET_MESSAGE'].format(reset_url=reset_url))
        elif User.objects.filter(email=email).count():
            reset_url = request.build_absolute_uri(reverse('reset_pw'))
            messages.add_message(request, messages.INFO,
                                 MESSAGES['RESET_MESSAGE'].format(reset_url=reset_url))
            form_add_error(form, "email", MESSAGES["EMAIL_TAKEN"])
        elif ProfileRequest.objects.filter(first_name=first_name, last_name=last_name).count():
            form_add_error(
                form, '__all__',
                MESSAGES["PROFILE_TAKEN"].format(first_name=first_name,
                                                 last_name=last_name))
        elif User.objects.filter(first_name=first_name, last_name=last_name).count():
            reset_url = request.build_absolute_uri(reverse('reset_pw'))
            messages.add_message(request, messages.INFO, MESSAGES['PROFILE_REQUEST_RESET'].format(reset_url=reset_url))
        else:
            form.save()
            messages.add_message(request, messages.SUCCESS, MESSAGES['PROFILE_SUBMITTED'])
            if settings.SEND_EMAILS and (email not in settings.EMAIL_BLACKLIST):
                submission_subject = SUBMISSION_SUBJECT.format(house=settings.HOUSE_NAME)
                submission_email = SUBMISSION_EMAIL.format(house=settings.HOUSE_NAME, full_name=first_name + " " + last_name, admin_name=settings.ADMINS[0][0],
                    admin_email=settings.ADMINS[0][1])
                try:
                    send_mail(submission_subject, submission_email, settings.EMAIL_HOST_USER, [email], fail_silently=False)
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
    ''' The page to manage user profile requests. '''
    page_name = "Admin - Manage Profile Requests"
    profile_requests = ProfileRequest.objects.all()
    return render_to_response('manage_profile_requests.html', {
        'page_name': page_name,
        'choices': UserProfile.STATUS_CHOICES,
        'profile_requests': profile_requests
        }, context_instance=RequestContext(request))

@admin_required
def modify_profile_request_view(request, request_pk):
    ''' The page to modify a user's profile request. request_pk is the pk of the profile request. '''
    page_name = "Admin - Profile Request"
    profile_request = get_object_or_404(ProfileRequest, pk=request_pk)
    mod_form = ModifyProfileRequestForm(
        request.POST if "add_user" in request.POST else None,
        instance=profile_request,
        )
    addendum = ""
    if 'delete_request' in request.POST:
        if settings.SEND_EMAILS and (profile_request.email not in settings.EMAIL_BLACKLIST):
            deletion_subject = DELETION_SUBJECT.format(house=settings.HOUSE_NAME)
            deletion_email = DELETION_EMAIL.format(house=settings.HOUSE_NAME, full_name=profile_request.first_name + " " + profile_request.last_name,
                admin_name=settings.ADMINS[0][0], admin_email=settings.ADMINS[0][1])
            try:
                send_mail(deletion_subject, deletion_email, settings.EMAIL_HOST_USER, [profile_request.email], fail_silently=False)
                addendum = MESSAGES['PROFILE_REQUEST_DELETION_EMAIL'].format(full_name=profile_request.first_name + ' ' + profile_request.last_name,
                    email=profile_request.email)
            except SMTPException as e:
                message = MESSAGES['EMAIL_FAIL'].format(email=profile_request.email, error=e)
                messages.add_message(request, messages.ERROR, message)
        profile_request.delete()
        message = MESSAGES['PREQ_DEL'].format(first_name=profile_request.first_name, last_name=profile_request.last_name, username=profile_request.username)
        messages.add_message(request, messages.SUCCESS, message + addendum)
        return HttpResponseRedirect(reverse('manage_profile_requests'))
    if mod_form.is_valid():
        new_user = mod_form.save(profile_request)
        if new_user.is_active and settings.SEND_EMAILS and (new_user.email not in settings.EMAIL_BLACKLIST):
            approval_subject = APPROVAL_SUBJECT.format(house=settings.HOUSE_NAME)
            if profile_request.provider:
                username_bit = profile_request.provider.title()
            elif new_user.username == profile_request.username:
                username_bit = "the username and password you selected"
            else:
                username_bit = "the username {0} and the password you selected".format(new_user.username)
            login_url = request.build_absolute_uri(reverse('login'))
            approval_email = APPROVAL_EMAIL.format(house=settings.HOUSE_NAME, full_name=new_user.get_full_name(), admin_name=settings.ADMINS[0][0],
                admin_email=settings.ADMINS[0][1], login_url=login_url, username_bit=username_bit, request_date=profile_request.request_date)
            try:
                send_mail(approval_subject, approval_email, settings.EMAIL_HOST_USER, [new_user.email], fail_silently=False)
                addendum = MESSAGES['PROFILE_REQUEST_APPROVAL_EMAIL'].format(full_name="{0} {1}".format(new_user.first_name, new_user.last_name),
                    email=new_user.email)
            except SMTPException as e:
                message = MESSAGES['EMAIL_FAIL'].format(email=new_user.email, error=e)
                messages.add_message(request, messages.ERROR, message)
        message = MESSAGES['USER_ADDED'].format(username=new_user.username)
        messages.add_message(request, messages.SUCCESS, message + addendum)
        return HttpResponseRedirect(reverse('manage_profile_requests'))
    return render_to_response('modify_profile_request.html', {
        'page_name': page_name,
        'add_user_form': mod_form,
        'provider': profile_request.provider,
        'uid': profile_request.uid,
        'affiliation_message': profile_request.message,
        'members': User.objects.all().exclude(username=ANONYMOUS_USERNAME),
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

    update_user_form = UpdateUserForm(
        request.POST if "update_user_profile" in request.POST else None,
        instance=targetUser,
        profile = UserProfile.objects.get(user=request.user),
        prefix="user",
        )
    update_profile_form = FullProfileForm(
        request.POST if "update_user_profile" in request.POST else None,
        instance=targetProfile,
        prefix="profile",
        )
    change_user_password_form = AdminPasswordChangeForm(
        targetUser,
        request.POST if "change_user_password" in request.POST else None,
        )
    delete_user_form = DeleteUserForm(
        request.POST if "delete_user" in request.POST else None,
        user=targetUser,
        request=request,
        )
    if update_user_form.is_valid() and update_profile_form.is_valid():
        update_user_form.save()
        update_profile_form.save()
        messages.add_message(
            request, messages.SUCCESS,
            MESSAGES['USER_PROFILE_SAVED'].format(username=targetUser.username),
            )
        return HttpResponseRedirect(reverse(
            'custom_modify_user', kwargs={'targetUsername': targetUsername}
            ))
    if change_user_password_form.is_valid():
        change_user_password_form.save()
        messages.add_message(
            request, messages.SUCCESS,
            MESSAGES['USER_PW_CHANGED'].format(username=targetUser.username),
            )
        return HttpResponseRedirect(reverse(
            'custom_modify_user', kwargs={'targetUsername': targetUsername})
            )
    if delete_user_form.is_valid():
        delete_user_form.save()
        messages.add_message(
            request, messages.SUCCESS,
            MESSAGES['USER_DELETED'].format(username=targetUser.username),
            )
        return HttpResponseRedirect(reverse("custom_manage_users"))

    template_dict = {
        'targetUser': targetUser,
        'targetProfile': targetProfile,
        'page_name': page_name,
        'update_user_form': update_user_form,
        'update_profile_form': update_profile_form,
        'change_user_password_form': change_user_password_form,
        'delete_user_form': delete_user_form,
        }

    if "wiki" in settings.INSTALLED_APPS:
        from wiki.models import Revision
        template_dict["revision_count"] = \
          Revision.objects.filter(created_by=targetUser).count()

    template_dict['thread_count'] = \
      Thread.objects.filter(owner=targetProfile).count()
    template_dict['message_count'] = \
      Message.objects.filter(owner=targetProfile).count()
    template_dict['request_count'] = \
      Request.objects.filter(owner=targetProfile).count()
    template_dict['response_count'] = \
      Response.objects.filter(owner=targetProfile).count()
    template_dict['announcement_count'] = \
      Announcement.objects.filter(incumbent=targetProfile).count()
    template_dict['event_count'] = \
      Event.objects.filter(owner=targetProfile).count()

    return render_to_response(
        'custom_modify_user.html',
        template_dict,
        context_instance=RequestContext(request),
        )

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
        'members': User.objects.all().exclude(username=ANONYMOUS_USERNAME),
        }, context_instance=RequestContext(request))

@admin_required
def utilities_view(request):
    ''' View for an admin to do maintenance tasks on the site. '''
    return render_to_response('utilities.html', {
        'page_name': "Admin - Site Utilities",
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

@admin_required
def recount_view(request):
    """
    Recount number_of_messages for all threads and number_of_responses for all requests.
    Also set the change_date for every thread to the post_date of the latest message
    associated with that thread.
    """
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
    dates_changed = 0
    for thread in Thread.objects.all():
        if thread.change_date != thread.message_set.latest('post_date').post_date:
            thread.change_date = thread.message_set.latest('post_date').post_date
            thread.save()
            dates_changed += 1
    messages.add_message(request, messages.SUCCESS, MESSAGES['RECOUNTED'].format(
        requests_changed=requests_changed,
        request_count=Request.objects.all().count(),
        threads_changed=threads_changed,
        thread_count=Thread.objects.all().count(),
        dates_changed=dates_changed,
        ))
    return HttpResponseRedirect(reverse('utilities'))

@profile_required
def archives_view(request):
    """ View of the archives page. """
    resident_count = UserProfile.objects.filter(status=UserProfile.RESIDENT).count()
    boarder_count = UserProfile.objects.filter(status=UserProfile.BOARDER).count()
    alumni_count = UserProfile.objects.filter(status=UserProfile.ALUMNUS).exclude(user__username=ANONYMOUS_USERNAME).count()
    return render_to_response('archives.html', {
        'page_name': "Archives",
        'resident_count': resident_count,
        'boarder_count': boarder_count,
        'alumni_count': alumni_count,
        'member_count': resident_count + boarder_count + alumni_count,
        'thread_count': Thread.objects.all().count(),
        'message_count': Message.objects.all().count(),
        'request_count': Request.objects.all().count(),
        'expired_count': Request.objects.filter(status=Request.EXPIRED).count(),
        'filled_count': Request.objects.filter(status=Request.FILLED).count(),
        'closed_count': Request.objects.filter(status=Request.CLOSED).count(),
        'open_count': Request.objects.filter(status=Request.OPEN).count(),
        'response_count': Response.objects.all().count(),
        'announcement_count': Announcement.objects.all().count(),
        'event_count': Event.objects.all().count(),
        'semester_count': Semester.objects.all().count(),
        'workshift_profile_count': WorkshiftProfile.objects.all().count(),
        'shift_log_entry_count': ShiftLogEntry.objects.all().count(),
        'workshift_instance_count': WorkshiftInstance.objects.all().count(),
        }, context_instance=RequestContext(request))

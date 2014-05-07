'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''

from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from haystack.forms import FacetedSearchForm
from haystack.query import SearchQuerySet
from haystack.views import FacetedSearchView
admin.autodiscover()

sqs = SearchQuerySet().facet('exact_user').facet('exact_location').facet('exact_manager').facet('exact_status')

urlpatterns = patterns('',
	url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
	url(r'^admin/', include(admin.site.urls)),
	url(r'^search/$', login_required(FacetedSearchView(form_class=FacetedSearchForm, searchqueryset=sqs)), name='haystack_search'),
)

urlpatterns += patterns('threads.views',
	url(r'^$', 'homepage_view', name='homepage'),
	url(r'^landing/$', 'landing_view', name='external'),
	url(r'^help/$', 'help_view', name='helppage'),
	url(r'^login/$', 'login_view', name='login'),
	url(r'^logout/$', 'logout_view', name='logout'),
	url(r'^member_forums/$', 'member_forums_view', name='member_forums'),
	url(r'^archives/all_threads/$', 'all_threads_view', name='all_threads'),
	url(r'^archives/list_all_threads/$', 'list_all_threads_view', name="list_all_threads"),
	url(r'^my_threads/$', 'my_threads_view', name='my_threads'),
	url(r'^thread/(?P<thread_pk>\w+)/$', 'thread_view', name='view_thread'),
	url(r'^site_map/$', 'site_map_view', name='site_map'),
	url(r'^member_directory/$', 'member_directory_view', name='member_directory'),
	url(r'^profile/$', 'my_profile_view', name='my_profile'),
	url(r'^profile/(?P<targetUsername>\w+)/$', 'member_profile_view', name='member_profile'),
	url(r'^profile/(?P<targetUsername>\w+)/threads/$', 'list_user_threads_view', name="list_user_threads"),
	url(r'^house_map/$', 'house_map_view', name='house_map'),
)

urlpatterns += patterns('events.views',
	url(r'^events/$', 'list_events_view', name='events'),
	url(r'^archives/all_events/$', 'list_all_events_view', name='all_events'),
	url(r'^edit_event/(?P<event_pk>\w+)/$', 'edit_event_view', name='edit_event'),
)

urlpatterns += patterns('requests.views',
	url(r'^request_profile/$', 'request_profile_view', name='request_profile'),
	url(r'^custom_admin/profile_requests/$', 'manage_profile_requests_view', name='manage_profile_requests'),
	url(r'^custom_admin/profile_requests/(?P<request_pk>\w+)/$', 'modify_profile_request_view', name='modify_profile_request'),
	url(r'^custom_admin/manage_users/$', 'custom_manage_users_view', name='custom_manage_users'),
	url(r'^custom_admin/modify_user/(?P<targetUsername>\w+)/$', 'custom_modify_user_view', name='custom_modify_user'),
	url(r'^custom_admin/add_user/$', 'custom_add_user_view', name='custom_add_user'),
	url(r'^custom_admin/utilities/$', 'utilities_view', name='utilities'),
	url(r'^custom_admin/anonymous_login/$', 'anonymous_login_view', name='anonymous_login'),
	url(r'^custom_admin/end_anonymous_session/$', 'end_anonymous_session_view', name='end_anonymous_session'),
	url(r'^custom_admin/recount/$', 'recount_view', name='recount'),
	url(r'^profile/(?P<targetUsername>\w+)/requests/$', 'list_user_requests_view', name='list_user_requests'),
	url(r'^requests/(?P<requestType>\w+)/$', 'requests_view', name='requests'),
	url(r'^archives/all_requests/$', 'all_requests_view', name='all_requests'),
	url(r'^requests/(?P<requestType>\w+)/all/$', 'list_all_requests_view', name='list_all_requests'),
	url(r'^my_requests/$', 'my_requests_view', name='my_requests'),
	url(r'^request/(?P<request_pk>\w+)/$', 'request_view', name='view_request'),
	url(r'^announcements/$', 'announcements_view', name='announcements'),
	url(r'^archives/all_announcements/$', 'all_announcements_view', name='all_announcements'),
)

# Catch any other urls here
urlpatterns += patterns('threads.views',
	url(r'', 'homepage_view', name='homepage'),
)

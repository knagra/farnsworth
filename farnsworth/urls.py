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
    url(r'', include('social.apps.django_app.urls', namespace='social')),
    url(r'', include('workshift.urls', namespace="workshift")),
	url(r'', include('threads.urls', namespace='threads')),
	url(r'', include('rooms.urls', namespace='rooms')),
	url(r'', include('events.urls', namespace='events')),
	url(r'', include('managers.urls', namespace='managers')),
)

urlpatterns += patterns('base.views',
    url(r'^$', 'homepage_view', name='homepage'),
    url(r'^landing/$', 'landing_view', name='external'),
    url(r'^help/$', 'help_view', name='helppage'),
    url(r'^login/$', 'login_view', name='login'),
    url(r'^logout/$', 'logout_view', name='logout'),
    url(r'^site_map/$', 'site_map_view', name='site_map'),
    url(r'^member_directory/$', 'member_directory_view', name='member_directory'),
    url(r'^profile/$', 'my_profile_view', name='my_profile'),
    url(r'^profile/(?P<targetUsername>[-\w]+)/$', 'member_profile_view', name='member_profile'),
    url(r'^request_profile/$', 'request_profile_view', name='request_profile'),
    url(r'^custom_admin/profile_requests/$', 'manage_profile_requests_view', name='manage_profile_requests'),
    url(r'^custom_admin/profile_requests/(?P<request_pk>\d+)/$', 'modify_profile_request_view', name='modify_profile_request'),
    url(r'^custom_admin/manage_users/$', 'custom_manage_users_view', name='custom_manage_users'),
    url(r'^custom_admin/manage_user/(?P<targetUsername>[-\w]+)/$', 'custom_modify_user_view', name='custom_modify_user'),
    url(r'^custom_admin/add_user/$', 'custom_add_user_view', name='custom_add_user'),
    url(r'^custom_admin/utilities/$', 'utilities_view', name='utilities'),
    url(r'^reset/$', 'reset_pw_view', name='reset_pw'),
    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        'reset_pw_confirm_view', name='reset_pw_confirm'),
    url(r'^recount/$', "recount_view", name="recount"),
    url(r'^archives/$', 'archives_view', name='archives'),
)

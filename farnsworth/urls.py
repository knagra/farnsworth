'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''

from django.conf.urls import patterns, include, url
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
	url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
	url(r'^admin/', include(admin.site.urls)),
)

urlpatterns += patterns('threads.views',
	url(r'^$', 'homepage_view', name='homepage'),
	url(r'^external/$', 'red_ext', name='external'),
	url(r'^help/$', 'help_view', name='helppage'),
	url(r'^login/$', 'login_view', name='login'),
	url(r'^logout/$', 'logout_view', name='logout'),
	url(r'^member_forums/$', 'member_forums_view', name='member_forums'),
	url(r'^all_threads/$', 'all_threads_view', name='all_threads'),
	url(r'^my_threads/$', 'my_threads_view', name='my_threads'),
	url(r'^site_map/$', 'site_map_view', name='site_map'),
	url(r'^member_directory/$', 'member_directory_view', name='member_directory'),
	url(r'^profile/$', 'my_profile_view', name='my_profile'),
	url(r'^profile/(?P<targetUsername>\w+)/$', 'member_profile_view', name='member_profile'),
)

urlpatterns += patterns('events.views',
	
)

urlpatterns += patterns('requests.views',
	url(r'^request_profile/$', 'request_profile_view', name='request_profile'),
	url(r'^custom_admin/profile_requests/$', 'manage_profile_requests_view', name='manage_profile_requests'),
	url(r'^custom_admin/manage_users/$', 'custom_manage_users_view', name='custom_manage_users'),
	url(r'^custom_admin/modify_user/(?P<targetUsername>\w+)/$', 'custom_modify_user_view', name='custom_modify_user'),
	url(r'^custom_admin/add_user/$', 'custom_add_user_view', name='custom_add_user'),
	url(r'^requests/(?P<requestType>\w+)/$', 'requests_view', name='requests'),
	url(r'^my_requests/$', 'my_requests_view', name='my_requests'),
)

# Catch any other urls here
urlpatterns += patterns('threads.views',
	url(r'', 'homepage_view', name='homepage'),
)

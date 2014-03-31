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
	url(r'^tinymce/', include('tinymce.urls')),
)

urlpatterns += patterns('threads.views',
	url(r'^$', 'homepage_view', name='homepage'),
	url(r'^external/$', 'external_view', name='external'),
	url(r'^help/$', 'help_view', name='helppage'),
	url(r'^login/$', 'login_view', name='login'),
	url(r'^logout/$', 'logout_view', name='logout'),
	url(r'^member_forums/$', 'member_forums_view', name='member_forums'),
)

urlpatterns += patterns('events.views',
	
)

urlpatterns += patterns('requests.views',
	url(r'^request_profile/$', 'request_profile_view', name='request_profile'),
)

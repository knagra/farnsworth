'''
Project: Farnsworth

Author: Karandeep Singh Nagra
'''

from django.conf.urls import patterns, include, url
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'farnsworth.views.home', name='home'),
    # url(r'^farnsworth/', include('farnsworth.foo.urls')),

	url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
	url(r'^admin/', include(admin.site.urls)),
)

urlpatterns += patterns('threads.views',
	url(r'^$', 'homepage', name='homepage'),
	url(r'^help/$', 'helppage', name='helppage'),
)

urlpatterns += patterns('events.views',
	
)

urlpatterns += patterns('requests.views',
	
)

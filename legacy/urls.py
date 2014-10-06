"""
Project: Farnsworth

Author: Karandeep Singh Nagra

URLs for legacy Kingman site.
"""


from django.conf.urls import url

from legacy import views


urlpatterns = [
    url(r'^legacy/notes/$', views.legacy_notes_view, name='legacy_notes'),
    url(r'^legacy/events/$', views.legacy_events_view, name='legacy_events'),
    url(r'^legacy/(?P<rtype>[-\w]+)/$', views.legacy_requests_view, name='legacy_requests'),
]


from django.conf.urls import url

from events import views

urlpatterns = [
	url(r'^events/$', views.list_events_view, name='list'),
	url(r'^events/all/$', views.list_all_events_view, name='all'),
	url(r'^events/(?P<event_pk>\d+)/$', views.event_view, name='view'),
	url(r'^events/(?P<event_pk>\d+)/edit/$', views.edit_event_view, name='edit'),
]

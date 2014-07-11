
from django.conf.urls import url

from threads import views

urlpatterns = [
	url(r'^threads/$', views.member_forums_view, name='member_forums'),
	url(r'^threads/(?P<thread_pk>\d+)/$', views.thread_view, name='view_thread'),
	url(r'^threads/all/$', views.all_threads_view, name='all_threads'),
	url(r'^threads/list/$', views.list_all_threads_view, name="list_all_threads"),
	url(r'^profile/(?P<targetUsername>[-\w]+)/threads/$', views.list_user_threads_view, name="list_user_threads"),
	url(r'^profile/(?P<targetUsername>[-\w]+)/messages/$', views.list_user_messages_view, name="list_user_messages"),
]

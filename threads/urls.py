
from django.conf.urls import url

from threads import views

urlpatterns = [
    url(r'^threads/$', views.list_all_threads_view, name="list_all_threads"),
    url(r'^threads/(?P<pk>\d+)/$', views.thread_view, name='view_thread'),
    url(r'^profile/(?P<targetUsername>[-\w]+)/threads/$', views.list_user_threads_view, name="list_user_threads"),
    url(r'^profile/(?P<targetUsername>[-\w]+)/messages/$', views.list_user_messages_view, name="list_user_messages"),
    ]

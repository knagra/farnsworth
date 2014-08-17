
from django.conf.urls import url

from rooms import views

urlpatterns = [
    url(r'^rooms/$', views.list_rooms, name="list"),
    url(r'^rooms/add$', views.add_room, name="add"),
    url(r'^room/(?P<room_title>\w+)/$', views.view_room, name="view"),
    url(r'^room/(?P<room_title>\w+)/edit$', views.edit_room, name="edit"),
    ]

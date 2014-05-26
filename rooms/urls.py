from django.conf.urls import url

from rooms import views

urlpatterns = [
	url(r'^rooms/$', views.room_list, name="room_list"),
	url(r'^rooms/add$', views.add_room, name="add_room"),
	url(r'^room/(?P<room_title>\w+)/$', views.view_room, name="view_room"),
	url(r'^room/(?P<room_title>\w+)/edit$', views.edit_room, name="edit_room"),
]

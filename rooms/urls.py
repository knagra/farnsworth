from django.conf.urls import url

from rooms import views

urlpatterns = [
	url(r'^rooms/$', views.list_rooms, name="list_rooms"),
	url(r'^rooms/add$', views.add_room, name="add_room"),
	url(r'^room/(?P<room_title>\w+)/$', views.view_room, name="view_room"),
	url(r'^room/(?P<room_title>\w+)/edit$', views.edit_room, name="edit_room"),
]

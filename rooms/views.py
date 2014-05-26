
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404

from base.decorators import profile_required, president_admin_required
from rooms.models import Room
from rooms.forms import AddRoomForm, EditRoomForm

@profile_required
def room_list(request):
	rooms = Room.objects.all()
	page_name = "Room List"
	return render_to_response('room_list.html', {
		'page_name': page_name,
		'rooms': rooms,
	})

@president_admin_required
def add_room(request):
	page_name = "Add Room"
	add_form = AddRoomForm(request.POST or None)

	if add_form.is_valid():
		room = Room(
			title
			)

	return render_to_response('room_add.html', {
		'page_name': page_name,
		'add_form': add_form,
	})

@profile_required
def view_room(request, room_title):
	room = get_object_or_404(Room, title=room_title)
	page_name = room_title

	return render_to_response('room_view.html', {
		'page_name': page_name,
	})

@president_admin_required
def edit_room(request, room_title):
	room = get_object_or_404(Room, title=room_title)
	page_name = "Edit {0}".format(room_title)
	edit_form = EditRoomForm(request.POST or None)

	return render_to_response('room_edit.html', {
		'page_name': page_name,
		'edit_form': edit_form,
	})

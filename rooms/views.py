
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404

from base.decorators import profile_required, admin_required
from base.models import UserProfile
from rooms.models import Room
from rooms.forms import AddRoomForm, EditRoomForm

@profile_required
def list_rooms(request):
	rooms = Room.objects.all()
	page_name = "Room List"
	return render_to_response('list_rooms.html', {
		'page_name': page_name,
		'rooms': rooms,
	})

@admin_required
def add_room(request):
	page_name = "Add Room"
	add_form = AddRoomForm(request.POST or None)

	if add_form.is_valid():
		room = Room(
			title=add_form.cleaned_data["title"],
			unofficial_name=add_form.cleaned_data["unofficial_name"],
			description=add_form.cleaned_data["description"],
			occupancy=add_form.cleaned_data["occupancy"],
			)
		room.save()
		room.residents = add_form.cleaned_data["residents"]
		room.save()
		return HttpResponseRedirect(reverse('room_list'))

	return render_to_response('add_room.html', {
		'page_name': page_name,
		'add_form': add_form,
	})

@profile_required
def view_room(request, room_title):
	room = get_object_or_404(Room, title=room_title)
	page_name = room_title
	if room.unofficial_name:
		page_name += " ({0})".format(room.unofficial_name)
	profile = UserProfile.objects.get(user=request.user)
	can_edit = (profile in room.residents.all() or request.user.is_superuser)

	return render_to_response('view_room.html', {
		'page_name': page_name,
		'can_edit': can_edit,
		'room': room,
	})

@admin_required
def edit_room(request, room_title):
	room = get_object_or_404(Room, title=room_title)
	page_name = "Edit {0}".format(room_title)
	edit_form = EditRoomForm(request.POST or None)

	if edit_form.is_valid():
		room.unofficial_name = edit_form.cleaned_data["unofficial_name"]
		room.description = edit_form.cleaned_data["description"]
		room.occupancy = edit_form.cleaned_data["occupancy"]
		room.residents = edit_form.cleaned_data["residents"]
		room.save()
		return HttpResponseRedirect(reverse('view_room', kwargs={'room_title': room_title}))

	return render_to_response('edit_room.html', {
		'page_name': page_name,
		'room': room,
		'edit_form': edit_form,
	})

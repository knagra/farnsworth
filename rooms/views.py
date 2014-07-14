
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext

from base.decorators import profile_required, admin_required
from rooms.models import Room, PreviousResident
from rooms.forms import RoomForm, RoomForm, ResidentFormSet

@profile_required
def list_rooms(request):
    """ Display a list of rooms. """
    return render_to_response('list_rooms.html', {
        'page_name': "Room List",
        'rooms': Room.objects.all(),
        }, context_instance=RequestContext(request))

@admin_required
def add_room(request):
    page_name = "Add Room"
    form = RoomForm(request.POST or None)

    if form.is_valid():
        form.save()
        return HttpResponseRedirect(reverse('rooms:list'))

    return render_to_response('add_room.html', {
        'page_name': page_name,
        'form': form,
        }, context_instance=RequestContext(request))

@profile_required
def view_room(request, room_title):
    room = get_object_or_404(Room, title=room_title)
    page_name = room_title
    if room.unofficial_name:
        page_name += " ({0})".format(room.unofficial_name)
    previous_residents = PreviousResident.objects.filter(room=room)

    return render_to_response('view_room.html', {
        'page_name': page_name,
        'room': room,
        "previous_residents": previous_residents,
        }, context_instance=RequestContext(request))

@profile_required
def edit_room(request, room_title):
    room = get_object_or_404(Room, title=room_title)
    page_name = "Edit {0}".format(room_title)
    if room.unofficial_name:
        page_name += " ({0})".format(room.unofficial_name)
    form = RoomForm(
        request.POST or None,
        instance=room,
        prefix="room",
        )

    resident_formset = ResidentFormSet(
        request.POST or None,
        prefix="residents",
        room=room,
        )

    if form.is_valid() and resident_formset.is_valid():
        room = form.save()
        resident_formset.save()
        return HttpResponseRedirect(
            reverse('rooms:view', kwargs={'room_title': room.title}),
            )

    return render_to_response('add_room.html', {
        'page_name': page_name,
        'room': room,
        'form': form,
        "resident_formset": resident_formset,
        'editing': True,
        }, context_instance=RequestContext(request))

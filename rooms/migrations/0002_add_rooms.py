# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

from django.db import models, migrations
from django.utils.timezone import now

def _fix_room_title(title):
    title = title.replace("eye", "I") \
      .replace("many", "") \
      .replace("guru", "1A") \
      .replace("Enchanted Forest", "3F") \
      .replace("Boarder")

    if "ST." in title:
        return ""

    title = re.sub(r"\(.*\)", "", title)

    if not all(i.isalpha() or i.isdigit() for i in title):
        return ""

    return title.strip().upper()

def forwards_func(apps, schema_editor):
    UserProfile = apps.get_model("base", "UserProfile")
    Room = apps.get_model("rooms", "Room")
    PreviousResident = apps.get_model("rooms", "PreviousResident")
    db_alias = schema_editor.connection.alias
    today = now().date()
    for profile in UserProfile.objects.all():
        title = _fix_room_title(profile.current_room)
        if title:
            room, created = Room.objects.get_or_create(
                title=title,
                using=db_alias,
                )
            room.current_residents.add(profile)
            if not created:
                room.occupancy += 1
            room.save(using=db_alias, update_fields=["occupancy", "current_residents"])
        if profile.former_rooms:
            titles = [_fix_room_title(i) for i in profile.former_rooms.split(",")]
            for title in titles:
                if not title:
                    continue
                room, created = Room.objects.get_or_create(
                    title=title,
                    using=db_alias,
                    )
                PreviousResident.objects.get_or_create(
                    room=room,
                    resident=profile,
                    defaults=dict(start_date=today, end_date=today),
                    using=db_alias,
                    )

class Migration(migrations.Migration):

    dependencies = [
        ('rooms', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            forwards_func
        ),
    ]

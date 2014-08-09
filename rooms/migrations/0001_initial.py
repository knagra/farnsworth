# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

from django.db import models, migrations
from django.utils.timezone import now
import django.core.validators

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
            room.save()
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
                    )

class Migration(migrations.Migration):

    dependencies = [
        ('base', '0002_auto_20140801_1108'),
    ]

    operations = [
        migrations.CreateModel(
            name='PreviousResident',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start_date', models.DateField(help_text=b"Start date of this person's residence in this room.")),
                ('end_date', models.DateField(help_text=b"End date of this person's residence in this room.")),
                ('resident', models.ForeignKey(help_text='The resident.', to='base.UserProfile')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Room',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(help_text=b"The title of the room (e.g., '2E'). Characters A-Z, 0-9.", unique=True, max_length=100, validators=[django.core.validators.RegexValidator('^[0-9A-Za-z]+$', 'Only alphanumeric characters are allowed.')])),
                ('unofficial_name', models.CharField(help_text=b"The unofficial name of the room (e.g., 'Starry Night')", max_length=100, null=True, blank=True)),
                ('description', models.TextField(help_text='The description of this room.', null=True, blank=True)),
                ('occupancy', models.IntegerField(default=1, help_text='The total number of people that this room should house.', validators=[django.core.validators.MinValueValidator(0)])),
                ('current_residents', models.ManyToManyField(to='base.UserProfile', blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='previousresident',
            name='room',
            field=models.ForeignKey(help_text='The relevant room.', to='rooms.Room'),
            preserve_default=True,
        ),
        migrations.RunPython(
            forwards_func
        ),
    ]

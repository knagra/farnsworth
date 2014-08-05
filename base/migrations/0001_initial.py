# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ProfileRequest',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('username', models.CharField(help_text=b'Username if this user is created.', max_length=100, null=True)),
                ('first_name', models.CharField(help_text=b'First name if user is created.', max_length=100)),
                ('last_name', models.CharField(help_text=b'Last name if user is created.', max_length=100)),
                ('email', models.CharField(help_text=b'E-mail address if user is created.', max_length=255)),
                ('request_date', models.DateTimeField(help_text=b'Whether this request has been granted.', auto_now_add=True)),
                ('affiliation', models.CharField(default=b'R', help_text=b"User's affiliation with the house.", max_length=1, choices=[(b'R', b'Current Resident'), (b'B', b'Current Boarder'), (b'A', b'Alumna/Alumnus')])),
                ('password', models.CharField(help_text=b"User's password.  Stored as hash", max_length=255, blank=True)),
                ('provider', models.CharField(max_length=32, blank=True)),
                ('uid', models.CharField(max_length=255, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('current_room', models.CharField(help_text=b"User's current room number", max_length=100, null=True, blank=True)),
                ('former_rooms', models.CharField(help_text=b"List of user's former room numbers", max_length=100, null=True, blank=True)),
                ('former_houses', models.CharField(help_text=b"List of user's former BSC houses", max_length=100, null=True, blank=True)),
                ('phone_number', models.CharField(help_text=b"User's phone number", max_length=20, null=True, blank=True)),
                ('email_visible', models.BooleanField(default=False, help_text=b'Whether the email is visible in the directory')),
                ('phone_visible', models.BooleanField(default=False, help_text=b'Whether the phone number is visible in the directory')),
                ('status', models.CharField(default=b'R', help_text=b'Member status (resident, boarder, alumnus)', max_length=1, choices=[(b'R', b'Current Resident'), (b'B', b'Current Boarder'), (b'A', b'Alumna/Alumnus')])),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('base', '0003_update_rooms'),
        ('rooms', '0002_add_rooms'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userprofile',
            name='tmp_phone_number',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='current_room',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='former_rooms',
        ),
    ]

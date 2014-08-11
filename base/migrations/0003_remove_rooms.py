# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('base', '0002_auto_20140801_1108'),
        ('rooms', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userprofile',
            name='current_room',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='former_rooms',
        ),
    ]

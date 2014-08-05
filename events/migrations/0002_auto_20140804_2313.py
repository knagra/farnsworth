# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='public',
            field=models.BooleanField(default=False, help_text=b'Whether this event can be seen by non-members.'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='event',
            name='change_date',
            field=models.DateTimeField(help_text=b'The date this event was last modified.', auto_now=True),
        ),
    ]

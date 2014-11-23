# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0002_auto_20140804_2313'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='owner',
            field=models.ForeignKey(related_name=b'poster', to='base.UserProfile', help_text=b'The user who posted this event.'),
        ),
        migrations.AlterField(
            model_name='event',
            name='rsvps',
            field=models.ManyToManyField(help_text=b'The users who plan to attend this event.', related_name=b'rsvps', null=True, to=b'base.UserProfile', blank=True),
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('managers', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='manager',
            name='semester_hours',
            field=models.DecimalField(default=5, help_text=b'Number of hours this manager receives during the fall and spring.', max_digits=5, decimal_places=2),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='manager',
            name='summer_hours',
            field=models.DecimalField(default=5, help_text=b'Number of hours this manager receives during the summer.', max_digits=5, decimal_places=2),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='request',
            name='followers',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='request',
            name='private',
            field=models.BooleanField(default=False, help_text=b'Only show this request to the manager, other members cannot view it.'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='request',
            name='status',
            field=models.CharField(default=b'O', help_text=b'Status of this request.', max_length=1, choices=[(b'O', b'Open'), (b'C', b'Closed'), (b'F', b'Filled'), (b'E', b'Expired')]),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='response',
            name='action',
            field=models.CharField(default=b'N', help_text=b"A mark action (e.g., 'Marked closed'), if any.", max_length=1, choices=[(b'N', b'None'), (b'C', b'Mark closed'), (b'O', b'Mark open'), (b'F', b'Mark filled'), (b'E', b'Mark expired')]),
            preserve_default=True,
        ),
        migrations.RemoveField(
            model_name='request',
            name='closed',
        ),
        migrations.RemoveField(
            model_name='request',
            name='filled',
        ),
        migrations.AlterField(
            model_name='request',
            name='change_date',
            field=models.DateTimeField(help_text=b'The last time this request was modified.', auto_now=True),
        ),
        migrations.AlterField(
            model_name='request',
            name='upvotes',
            field=models.ManyToManyField(to=b'base.UserProfile', blank=True),
        ),
    ]

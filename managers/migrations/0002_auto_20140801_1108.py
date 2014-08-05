# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings

from managers.models import Request as Rq

def forwards_func(apps, schema_editor):
    Request = apps.get_model("managers", "Request")
    db_alias = schema_editor.connection.alias
    for req in Request.objects.all():
        if req.filled:
            req.status = Rq.FILLED
        elif req.closed:
            req.status = Rq.CLOSED
        else:
            req.status = Rq.OPEN
        req.save()

class Migration(migrations.Migration):

    dependencies = [
        ('managers', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='manager',
            name='semester_hours',
            field=models.DecimalField(default=5, help_text='Number of hours this manager receives during the fall and spring.', max_digits=5, decimal_places=2),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='manager',
            name='summer_hours',
            field=models.DecimalField(default=5, help_text='Number of hours this manager receives during the summer.', max_digits=5, decimal_places=2),
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
            field=models.BooleanField(default=False, help_text='Only show this request to the manager, other members cannot view it.'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='request',
            name='status',
            field=models.CharField(default='O', help_text='Status of this request.', max_length=1, choices=[('O', 'Open'), ('C', 'Closed'), ('F', 'Filled'), ('E', 'Expired')]),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='response',
            name='action',
            field=models.CharField(default='N', help_text="A mark action (e.g., 'Marked closed'), if any.", max_length=1, choices=[('N', 'None'), ('C', 'Mark closed'), ('O', 'Mark open'), ('F', 'Mark filled'), ('E', 'Mark expired')]),
            preserve_default=True,
        ),
        migrations.RunPython(
            forwards_func,
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
            field=models.DateTimeField(help_text='The last time this request was modified.', auto_now=True),
        ),
        migrations.AlterField(
            model_name='request',
            name='upvotes',
            field=models.ManyToManyField(to='base.UserProfile', blank=True),
        ),
    ]

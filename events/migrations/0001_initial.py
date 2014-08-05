# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('managers', '0001_initial'),
        ('base', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(help_text=b'The title of this event.', max_length=255)),
                ('description', models.TextField(help_text=b'Description of this event.')),
                ('location', models.CharField(help_text=b'Location of event.', max_length=255, null=True, blank=True)),
                ('start_time', models.DateTimeField(help_text=b'When this event starts.')),
                ('end_time', models.DateTimeField(help_text=b'When this event ends.')),
                ('post_date', models.DateTimeField(help_text=b'The date this event was posted.', auto_now_add=True)),
                ('change_date', models.DateTimeField(help_text=b'The date this event was last modified.', auto_now=True, auto_now_add=True)),
                ('cancelled', models.BooleanField(default=False, help_text=b'Optional cancellation field.')),
                ('as_manager', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='managers.Manager', help_text=b'The manager position this event is posted, if this is a manager event.', null=True)),
                ('owner', models.ForeignKey(help_text=b'The user who posted this event.', to='base.UserProfile')),
                ('rsvps', models.ManyToManyField(to='base.UserProfile', null=True, blank=True)),
            ],
            options={
                'ordering': [b'-start_time'],
            },
            bases=(models.Model,),
        ),
    ]

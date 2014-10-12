# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='TeacherEvent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField(help_text=b'Date of this event.', null=True, blank=True)),
                ('title', models.CharField(help_text=b'The title of this event.', max_length=56, null=True, blank=True)),
                ('description', models.TextField(help_text=b'The description of this event.', null=True, blank=True)),
            ],
            options={
                'ordering': ['-date'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TeacherNote',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.DateTimeField(help_text=b'Date and time when this note was posted.', null=True, blank=True)),
                ('name', models.CharField(help_text=b'The name given by the user who posted this request.', max_length=56, null=True, blank=True)),
                ('body', models.TextField(help_text=b'The body of this note.', null=True, blank=True)),
            ],
            options={
                'ordering': ['-timestamp'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TeacherRequest',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('request_type', models.CharField(help_text=b'The request type for this request.', max_length=15, null=True, blank=True)),
                ('teacher_key', models.CharField(help_text=b'Legacy primary key based on datetime.', max_length=24, null=True, blank=True)),
                ('timestamp', models.DateTimeField(help_text=b'Date and time when this request was posted.', null=True, blank=True)),
                ('name', models.CharField(help_text=b'The name given by the user who posted this request.', max_length=56, null=True, blank=True)),
                ('body', models.TextField(help_text=b'The body of this request.', null=True, blank=True)),
            ],
            options={
                'ordering': ['-timestamp'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TeacherResponse',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.DateTimeField(help_text=b'Date and time when this response was posted.', null=True, blank=True)),
                ('name', models.CharField(help_text=b'The name given by the user who posted this request.', max_length=56, null=True, blank=True)),
                ('body', models.TextField(help_text=b'The body of this response.', null=True, blank=True)),
                ('request', models.ForeignKey(help_text=b'The request to which this is a response.', to='legacy.TeacherRequest')),
            ],
            options={
                'ordering': ['-timestamp'],
            },
            bases=(models.Model,),
        ),
    ]

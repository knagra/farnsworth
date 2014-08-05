# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


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
    ]

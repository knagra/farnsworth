# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import workshift.fields
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('managers', '0002_auto_20140801_1108'),
    ]

    operations = [
        migrations.CreateModel(
            name='InstanceInfo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(help_text=b'Title for this shift.', max_length=255, null=True, blank=True)),
                ('description', models.TextField(help_text=b'Description of the shift.', null=True, blank=True)),
                ('verify', models.CharField(default=b'O', help_text=b'Who is able to mark this shift as completed.', max_length=1, choices=[(b'W', b'Workshift Managers only'), (b'P', b'Pool Managers only'), (b'M', b'Any Manager'), (b'O', b'Another member'), (b'S', b'Any member (including self)'), (b'A', b'Automatically verified')])),
                ('start_time', models.TimeField(help_text=b'Start time for this workshift.', null=True, blank=True)),
                ('end_time', models.TimeField(help_text=b'End time for this workshift.', null=True, blank=True)),
                ('week_long', models.BooleanField(default=False, help_text=b'If this shift is for the entire week.')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PoolHours',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('hours', models.DecimalField(default=5, help_text=b'Periodic hour requirement.', max_digits=5, decimal_places=2)),
                ('standing', models.DecimalField(default=0, help_text=b'Current hours standing, below or above requirement.', max_digits=5, decimal_places=2)),
                ('hour_adjustment', models.DecimalField(default=0, help_text=b'Manual hour requirement adjustment.', max_digits=5, decimal_places=2)),
                ('first_date_standing', models.DecimalField(decimal_places=2, default=0, max_digits=5, blank=True, help_text=b'The hourly fines or repayment at the first fine date. Stored in a field for manual adjustment.', null=True)),
                ('second_date_standing', models.DecimalField(decimal_places=2, default=0, max_digits=5, blank=True, help_text=b'The hourly fines or repayment at the second fine date. Stored in a field for manual adjustment.', null=True)),
                ('third_date_standing', models.DecimalField(decimal_places=2, default=0, max_digits=5, blank=True, help_text=b'The hourly fines or repayment at the third fine date. Stored in a field for manual adjustment.', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RegularWorkshift',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('day', workshift.fields.DayField(blank=True, max_length=1, null=True, help_text=b'The day of the week when this workshift takes place.', choices=[(0, b'Monday'), (1, b'Tuesday'), (2, b'Wednesday'), (3, b'Thursday'), (4, b'Friday'), (5, b'Saturday'), (6, b'Sunday')])),
                ('count', models.PositiveSmallIntegerField(default=1, help_text=b'Number of instances to create with each occurrence.', max_length=4)),
                ('hours', models.DecimalField(default=5, help_text=b'Number of hours for this shift.', max_digits=5, decimal_places=2)),
                ('active', models.BooleanField(default=True, help_text=b'Whether this shift is actively being used currently (displayed in list of shifts, given hours, etc.).')),
                ('start_time', models.TimeField(help_text=b'Start time for this workshift.', null=True, blank=True)),
                ('end_time', models.TimeField(help_text=b'End time for this workshift.', null=True, blank=True)),
                ('verify', models.CharField(default=b'O', help_text=b'Who is able to mark this shift as completed.', max_length=1, choices=[(b'W', b'Workshift Managers only'), (b'P', b'Pool Managers only'), (b'M', b'Any Manager'), (b'O', b'Another member'), (b'S', b'Any member (including self)'), (b'A', b'Automatically verified')])),
                ('week_long', models.BooleanField(default=False, help_text=b'If this shift is for the entire week.')),
                ('addendum', models.TextField(default=b'', help_text=b'Addendum to the description for this workshift.')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Semester',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('season', models.CharField(default=b'Sp', help_text=b'Season of the year (spring, summer, fall) of this semester.', max_length=2, choices=[(b'Sp', b'Spring'), (b'Su', b'Summer'), (b'Fa', b'Fall')])),
                ('year', models.PositiveSmallIntegerField(help_text=b'Year of this semester.', max_length=4)),
                ('rate', models.DecimalField(help_text=b'Workshift rate for this semester.', null=True, max_digits=7, decimal_places=2, blank=True)),
                ('policy', models.URLField(help_text=b'Link to the workshift policy for this semester.', max_length=255, null=True, blank=True)),
                ('start_date', models.DateField(help_text=b'Start date of this semester.')),
                ('end_date', models.DateField(help_text=b'End date of this semester.')),
                ('preferences_open', models.BooleanField(default=False, help_text=b'Whether members can enter their workshift preferences.')),
                ('current', models.BooleanField(default=True, help_text=b'If this semester is the current semester.')),
                ('workshift_managers', models.ManyToManyField(to=settings.AUTH_USER_MODEL, blank=True)),
            ],
            options={
                'ordering': [b'-start_date'],
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='semester',
            unique_together=set([(b'season', b'year')]),
        ),
        migrations.CreateModel(
            name='ShiftLogEntry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('entry_time', models.DateTimeField(help_text=b'Time this entry was made.', auto_now_add=True)),
                ('hours', models.DecimalField(help_text=b'Hours associated with a change in workshift credit.', null=True, max_digits=5, decimal_places=2, blank=True)),
                ('note', models.TextField(help_text=b"Message to the workshift manager. (e.g. 'Can't cook because of flu')", null=True, blank=True)),
                ('entry_type', models.CharField(default=b'V', max_length=1, choices=[(b'A', b'Assigned'), (b'B', b'Blown'), (b'I', b'Sign In'), (b'O', b'Sign Out'), (b'V', b'Verify'), (b'M', b'Modify Hours'), (b'S', b'Sell')])),
            ],
            options={
                'ordering': [b'-entry_time'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TimeBlock',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('preference', models.PositiveSmallIntegerField(default=0, help_text=b"The user's preference for this time block.", max_length=1, choices=[(0, b'Busy'), (1, b'Preferred')])),
                ('day', workshift.fields.DayField(help_text=b'Day of the week for this time block.', max_length=1, choices=[(0, b'Monday'), (1, b'Tuesday'), (2, b'Wednesday'), (3, b'Thursday'), (4, b'Friday'), (5, b'Saturday'), (6, b'Sunday')])),
                ('start_time', models.TimeField(help_text=b'Start time for this time block.')),
                ('end_time', models.TimeField(help_text=b'End time for this time block.')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='WorkshiftInstance',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField(help_text=b'Date of this workshift.')),
                ('closed', models.BooleanField(default=False, help_text=b'If this shift has been completed.')),
                ('blown', models.BooleanField(default=False, help_text=b'If this shift has been blown.')),
                ('intended_hours', models.DecimalField(default=5, help_text=b'Intended hours given for this shift.', max_digits=5, decimal_places=2)),
                ('hours', models.DecimalField(default=5, help_text=b'Number of hours actually given for this shift.', max_digits=5, decimal_places=2)),
                ('info', models.ForeignKey(blank=True, to='workshift.InstanceInfo', help_text=b'The weekly workshift of which this is an instance.', null=True)),
                ('logs', models.ManyToManyField(to='workshift.ShiftLogEntry', blank=True)),
                ('semester', models.ForeignKey(help_text=b'The semester for this workshift.', to='workshift.Semester')),
                ('weekly_workshift', models.ForeignKey(blank=True, to='workshift.RegularWorkshift', help_text=b'The weekly workshift of which this is an instance.', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='WorkshiftPool',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(default=b'Regular Workshift', help_text=b'The title of this workshift pool (i.e. HI Hours)', max_length=100)),
                ('sign_out_cutoff', models.PositiveSmallIntegerField(default=24, help_text=b'Cutoff for signing out of workshifts without requiring a substitute, in hours.')),
                ('verify_cutoff', models.PositiveSmallIntegerField(default=8, help_text=b'Cutoff for verifying a workshift after it has finished, in hours. After this cutoff, the shift will be marked as blown.')),
                ('hours', models.DecimalField(default=5, help_text=b'Default hours required per member per period (e.g., 2 weeks per period and 2 hours required per period means 2 hours required every two weeks).', max_digits=5, decimal_places=2)),
                ('weeks_per_period', models.PositiveSmallIntegerField(default=1, help_text=b'Number of weeks for requirement period (e.g., 2 weeks per period and 2 hours required per period means 2 hours required every two weeks). 0 makes this a semesterly requirement')),
                ('first_fine_date', models.DateField(help_text=b'First fine date for this semester, optional.', null=True, blank=True)),
                ('second_fine_date', models.DateField(help_text=b'Second fine date for this semester, optional.', null=True, blank=True)),
                ('third_fine_date', models.DateField(help_text=b'Third fine date for this semester, optional.', null=True, blank=True)),
                ('any_blown', models.BooleanField(default=False, help_text=b'If any member is allowed to mark a shift as blown.')),
                ('is_primary', models.BooleanField(default=False, help_text=b'Is the primary workshift pool for the house.')),
                ('managers', models.ManyToManyField(to='managers.Manager', blank=True)),
                ('semester', models.ForeignKey(help_text=b'The semester associated with this pool of workshift hours.', to='workshift.Semester')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='regularworkshift',
            name='pool',
            field=models.ForeignKey(help_text=b'The workshift pool for this shift.', to='workshift.WorkshiftPool'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='poolhours',
            name='pool',
            field=models.ForeignKey(help_text=b'The pool associated with these hours.', to='workshift.WorkshiftPool'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='instanceinfo',
            name='pool',
            field=models.ForeignKey(blank=True, to='workshift.WorkshiftPool', help_text=b'The workshift pool for this shift.', null=True),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='workshiftpool',
            unique_together=set([(b'semester', b'title')]),
        ),
        migrations.CreateModel(
            name='WorkshiftProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('note', models.TextField(help_text=b'Note for this profile. For communication between the workshifter and the workshift manager(s).', null=True, blank=True)),
                ('preference_save_time', models.DateTimeField(help_text=b'The time this member first saved their preferences.', null=True, blank=True)),
                ('pool_hours', models.ManyToManyField(to='workshift.PoolHours', blank=True)),
                ('semester', models.ForeignKey(help_text=b'The semester for this workshift profile.', to='workshift.Semester')),
                ('time_blocks', models.ManyToManyField(to='workshift.TimeBlock', blank=True)),
                ('user', models.ForeignKey(help_text=b'The user for this workshift profile.', to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='workshiftinstance',
            name='workshifter',
            field=models.ForeignKey(blank=True, to='workshift.WorkshiftProfile', help_text=b'Workshifter who was signed into this shift at the time it started.', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='workshiftinstance',
            name='verifier',
            field=models.ForeignKey(blank=True, to='workshift.WorkshiftProfile', help_text=b'Workshifter who verified that this shift was completed.', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='workshiftinstance',
            name='liable',
            field=models.ForeignKey(blank=True, to='workshift.WorkshiftProfile', help_text=b'Workshifter who is liable for this shift if no one else signs in.', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='shiftlogentry',
            name='person',
            field=models.ForeignKey(blank=True, to='workshift.WorkshiftProfile', help_text=b'Person who made this entry.', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='regularworkshift',
            name='current_assignees',
            field=models.ManyToManyField(to='workshift.WorkshiftProfile', blank=True),
            preserve_default=True,
        ),
        migrations.CreateModel(
            name='WorkshiftRating',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('rating', models.PositiveSmallIntegerField(default=1, help_text=b'Rating for the workshift type.', max_length=1, choices=[(0, b'Dislike'), (1, b'Indifferent'), (2, b'Like')])),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='workshiftprofile',
            name='ratings',
            field=models.ManyToManyField(to='workshift.WorkshiftRating', blank=True),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='workshiftprofile',
            unique_together=set([(b'user', b'semester')]),
        ),
        migrations.CreateModel(
            name='WorkshiftType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(help_text=b'The title of this workshift type (e.g., "Pots"), must be unique.', unique=True, max_length=255)),
                ('description', models.TextField(help_text=b'A description for this workshift type.', null=True, blank=True)),
                ('quick_tips', models.TextField(help_text=b'Quick tips to the workshifter.', null=True, blank=True)),
                ('rateable', models.BooleanField(default=True, help_text=b'Whether this workshift type is shown in preferences.')),
                ('assignment', models.CharField(default=b'A', help_text=b'How assignment to this workshift works. This can be automatic, manual-only, or no assignment (i.e. Manager shifts, which are internally assigned.', max_length=1, choices=[(b'A', b'Auto-assign'), (b'M', b'Manually assign'), (b'O', b'No assignment')])),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='workshiftrating',
            name='workshift_type',
            field=models.ForeignKey(help_text=b'The workshift type being rated.', to='workshift.WorkshiftType'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='regularworkshift',
            name='workshift_type',
            field=models.ForeignKey(help_text=b'The workshift type for this weekly workshift.', to='workshift.WorkshiftType'),
            preserve_default=True,
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings

def calculate_assigned_hours(apps, schema_editor):
    WorkshiftProfile = apps.get_model("workshift", "WorkshiftProfile")
    RegularWorkshift = apps.get_model("workshift", "RegularWorkshift")
    db_alias = schema_editor.connection.alias
    for workshifter in WorkshiftProfile.objects.using(db_alias).all():
        for pool_hours in workshifter.pool_hours.all():
            shifts = RegularWorkshift.objects.using(db_alias).filter(current_assignees=workshifter)
            pool_hours.assigned_hours = sum(i.hours for i in shifts)
            pool_hours.save(using=db_alias, update_fields=["assigned_hours"])

def update_manager_shifts(apps, schema_editor):
    if "managers" in settings.INSTALLED_APPS:
        Manager = apps.get_model("managers", "Manager")
        RegularWorkshift = apps.get_model("workshift", "RegularWorkshift")
        db_alias = schema_editor.connection.alias
        titles = [i.title for i in Manager.objects.using(db_alias).all()]
        for shift in RegularWorkshift.objects.using(db_alias).all():
            if shift.workshift_type.title in titles:
                shift.is_manager_shift = True
                shift.save(using=db_alias, update_fields=["is_manager_shift"])

class Migration(migrations.Migration):

    dependencies = [
        ('workshift', '0002_auto_20140812_1435'),
    ]

    operations = [
        migrations.AddField(
            model_name='poolhours',
            name='assigned_hours',
            field=models.DecimalField(default=0, help_text='Total hours satisfied by periodic shifts.', max_digits=5, decimal_places=2),
            preserve_default=True,
        ),
        migrations.RunPython(
            calculate_assigned_hours,
        ),
        migrations.AddField(
            model_name='regularworkshift',
            name='is_manager_shift',
            field=models.BooleanField(default=False, help_text='If this shift was automatically generated from the managers module'),
            preserve_default=True,
        ),
        migrations.RunPython(
            update_manager_shifts,
        ),
        migrations.AlterField(
            model_name='regularworkshift',
            name='current_assignees',
            field=models.ManyToManyField(help_text='The workshifter currently assigned to this weekly workshift.', to='workshift.WorkshiftProfile', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='semester',
            name='workshift_managers',
            field=models.ManyToManyField(help_text='The users who were/are Workshift Managers for this semester.', to=settings.AUTH_USER_MODEL, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='workshiftinstance',
            name='liable',
            field=models.ForeignKey(related_name='instance_liable', blank=True, to='workshift.WorkshiftProfile', help_text='Workshifter who is liable for this shift if no one else signs in.', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='workshiftinstance',
            name='logs',
            field=models.ManyToManyField(help_text='The entries for sign ins, sign outs, and verification.', to='workshift.ShiftLogEntry', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='workshiftinstance',
            name='verifier',
            field=models.ForeignKey(related_name='instance_verifier', blank=True, to='workshift.WorkshiftProfile', help_text='Workshifter who verified that this shift was completed.', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='workshiftinstance',
            name='workshifter',
            field=models.ForeignKey(related_name='instance_workshifter', blank=True, to='workshift.WorkshiftProfile', help_text='Workshifter who was signed into this shift at the time it started.', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='workshiftpool',
            name='managers',
            field=models.ManyToManyField(help_text='Managers who are able to control this workshift category.', to='managers.Manager', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='workshiftprofile',
            name='pool_hours',
            field=models.ManyToManyField(help_text='Hours required for each workshift pool for this profile.', to='workshift.PoolHours', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='workshiftprofile',
            name='ratings',
            field=models.ManyToManyField(help_text='The workshift ratings for this workshift profile.', to='workshift.WorkshiftRating', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='workshiftprofile',
            name='time_blocks',
            field=models.ManyToManyField(help_text='The time blocks for this workshift profile.', to='workshift.TimeBlock', blank=True),
            preserve_default=True,
        ),
    ]

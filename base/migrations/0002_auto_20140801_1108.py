# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import phonenumber_field.modelfields

class Migration(migrations.Migration):

    dependencies = [
        ('base', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='profilerequest',
            name='message',
            field=models.CharField(default='', help_text="Details on how you're affiliated with us.  Optional.", max_length=255, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='userprofile',
            name='email_announcement_notifications',
            field=models.BooleanField(default=True, help_text='Whether important manager announcements are e-mailed to you.'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='userprofile',
            name='email_request_notifications',
            field=models.BooleanField(default=False, help_text='Whether notifications are e-mailed to you about request updates.'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='userprofile',
            name='email_thread_notifications',
            field=models.BooleanField(default=False, help_text='Whether notifications are e-mailed to you about thread updates.'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='userprofile',
            name='email_workshift_notifications',
            field=models.BooleanField(default=True, help_text='Whether notifications are e-mailed to you about workshift updates.'),
            preserve_default=True,
        ),
        migrations.RenameField(
            model_name='userprofile',
            old_name='phone_number',
            new_name='tmp_phone_number',
        ),
        migrations.AddField(
            model_name='userprofile',
            name='phone_number',
            field=phonenumber_field.modelfields.PhoneNumberField(max_length=128, null=True, blank=True),
        ),
    ]

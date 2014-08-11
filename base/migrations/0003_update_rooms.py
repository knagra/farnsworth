# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

def forwards_func(apps, schema_editor):
    UserProfile = apps.get_model("base", "UserProfile")
    db_alias = schema_editor.connection.alias
    for profile in UserProfile.objects.all():
        if profile.tmp_phone_number:
            phone_number = profile.tmp_phone_number \
              .replace('-', '') \
              .replace(' ', '') \
              .replace('(', '') \
              .replace(')', '')
            if not phone_number.startswith("+"):
                if phone_number.startswith("1"):
                    phone_number = "+" + phone_number
                else:
                    phone_number = "+1" + phone_number
            profile.phone_number = phone_number
            if profile.phone_number.is_valid():
                profile.save(using=db_alias, update_fields=["phone_number"])

class Migration(migrations.Migration):

    dependencies = [
        ('base', '0002_auto_20140801_1108'),
    ]

    operations = [
        migrations.RunPython(
            forwards_func,
        ),
    ]

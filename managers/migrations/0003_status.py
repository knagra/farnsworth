# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def forwards_func(apps, schema_editor):
    Request = apps.get_model("managers", "Request")
    db_alias = schema_editor.connection.alias
    for req in Request.objects.using(db_alias).all():
        if req.filled:
            req.status = 'F'
        elif req.closed:
            req.status = 'C'
        else:
            req.status = 'O'
        req.save(using=db_alias, update_fields=["status"])

class Migration(migrations.Migration):

    dependencies = [
        ('managers', '0002_auto_20140801_1108'),
    ]

    operations = [
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
    ]

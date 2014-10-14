# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('legacy', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='teacherresponse',
            options={'ordering': ['timestamp']},
        ),
        migrations.AlterField(
            model_name='teacherevent',
            name='title',
            field=models.CharField(help_text=b'The title of this event.', max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='teachernote',
            name='name',
            field=models.CharField(help_text=b'The name given by the user who posted this request.', max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='teacherrequest',
            name='name',
            field=models.CharField(help_text=b'The name given by the user who posted this request.', max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='teacherresponse',
            name='name',
            field=models.CharField(help_text=b'The name given by the user who posted this request.', max_length=255, null=True, blank=True),
        ),
    ]

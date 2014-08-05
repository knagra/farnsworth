# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('threads', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='thread',
            name='followers',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='thread',
            name='views',
            field=models.PositiveIntegerField(default=0, help_text=b'The number times this thread has been viewed.'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='thread',
            name='change_date',
            field=models.DateTimeField(help_text=b'The last time this thread was modified.', auto_now=True),
        ),
    ]

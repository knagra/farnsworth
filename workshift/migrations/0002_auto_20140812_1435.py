# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('workshift', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='regularworkshift',
            name='addendum',
            field=models.TextField(default='', help_text='Addendum to the description for this workshift.', null=True, blank=True),
        ),
    ]

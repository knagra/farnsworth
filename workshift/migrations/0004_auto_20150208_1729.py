# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('workshift', '0003_auto_20150127_1646'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shiftlogentry',
            name='entry_type',
            field=models.CharField(default='V', max_length=1, choices=[('A', 'Assigned'), ('B', 'Blown'), ('C', 'Undo Blown'), ('I', 'Sign In'), ('O', 'Sign Out'), ('V', 'Verify'), ('U', 'Undo Verify'), ('M', 'Modify Hours'), ('S', 'Sell')]),
            preserve_default=True,
        ),
    ]

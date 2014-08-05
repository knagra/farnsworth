# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('body', models.TextField(help_text=b'Body of this message.')),
                ('post_date', models.DateTimeField(help_text=b'The date this message was posted.', auto_now_add=True)),
                ('owner', models.ForeignKey(help_text=b'The user who posted this message.', to='base.UserProfile')),
            ],
            options={
                'ordering': [b'post_date'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Thread',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('subject', models.CharField(help_text=b'Subject of this thread.', max_length=254)),
                ('start_date', models.DateTimeField(help_text=b'The date this thread was started.', auto_now_add=True)),
                ('change_date', models.DateTimeField(help_text=b'The last time this thread was modified.', auto_now_add=True)),
                ('number_of_messages', models.PositiveSmallIntegerField(default=1, help_text=b'The number of messages in this thread.')),
                ('active', models.BooleanField(default=True, help_text=b'Whether this thread is still active.')),
                ('owner', models.ForeignKey(help_text=b'The user who started this thread.', to='base.UserProfile')),
            ],
            options={
                'ordering': [b'-change_date'],
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='message',
            name='thread',
            field=models.ForeignKey(help_text=b'The thread to which this message belongs.', to='threads.Thread'),
            preserve_default=True,
        ),
    ]
